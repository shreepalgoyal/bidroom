from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

from .models import Evidence, Finding, Matrix, Review
from .util import days_until, now_iso

CITATION = re.compile(r"\[(E-[A-Za-z0-9][A-Za-z0-9._-]*)\]")
SECTION = re.compile(r"^###\s+(R-\d+)\b.*$", re.M)

CLAIM_MARKERS = re.compile(
    r"\b(we|our|us|iso\s?\d+|soc\s?2|cyber essentials|wcag|99\.\d|24/7|24x7|"
    r"certified|accredited|guarantee|award|years?|percent|%)\b",
    re.I,
)
META_MARKERS = re.compile(
    r"\b(gap|pending|not approved|do not submit|owned by|action|remaining|"
    r"evidence exists|placeholder|todo|tbd)\b",
    re.I,
)


def _sections(draft: str) -> dict[str, str]:
    matches = list(SECTION.finditer(draft))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(draft)
        result[match.group(1)] = draft[match.end() : end]
    return result


def _response_text(block: str) -> str:
    match = re.search(r"\*\*Response\.\*\*\s*(.+?)(?=\n\s*\n|\n\*\*|$)", block, re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _claim_units(text: str) -> list[str]:
    """Split a response into claim-sized units.

    A citation only vouches for the unit it sits in, so we split after every
    citation as well as at sentence ends. That stops one citation at the start
    of a paragraph from laundering every claim that follows it.
    """
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])|(?<=\])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def review_draft(draft: str, matrix: Matrix, evidence: list[Evidence]) -> Review:
    evidence_by_id = {item.id: item for item in evidence}
    rows_by_id = {row.requirement_id: row for row in matrix.rows}
    sections = _sections(draft)
    findings: list[Finding] = []
    counter = 0

    def add(severity: str, kind: str, message: str, requirement_id: str = "", location: str = "", evidence_id: str = "") -> None:
        nonlocal counter
        counter += 1
        findings.append(
            Finding(
                id=f"F-{counter:03d}",
                severity=severity,
                kind=kind,
                message=message,
                requirement_id=requirement_id,
                location=location,
                evidence_id=evidence_id,
            )
        )

    for requirement_id, row in rows_by_id.items():
        block = sections.get(requirement_id)
        if block is None:
            severity = "blocker" if row.kind in {"mandatory", "scored"} else "low"
            add(
                severity,
                "missing-requirement",
                f"No drafted response for {requirement_id} ({row.kind}, {row.category}).",
                requirement_id,
            )
            continue
        response = _response_text(block)
        if not response:
            add("high", "empty-response", f"{requirement_id} has no response text.", requirement_id)
            continue

        if row.status == "gap":
            if re.search(r"\b(yes|fully compliant|compliant\.)\b", response, re.I) and "[[GAP]]" not in response:
                add(
                    "blocker",
                    "claim-without-evidence",
                    f"{requirement_id} is a gap in the matrix but the draft claims compliance.",
                    requirement_id,
                    response,
                )
            if "[[GAP]]" in response:
                add(
                    "high",
                    "open-gap",
                    f"{requirement_id} still carries a [[GAP]] marker.",
                    requirement_id,
                    response,
                )

        citations = CITATION.findall(response)
        for evidence_id in citations:
            item = evidence_by_id.get(evidence_id)
            if not item:
                add(
                    "blocker",
                    "unknown-evidence",
                    f"{requirement_id} cites {evidence_id}, which is not in the evidence library.",
                    requirement_id,
                    response,
                    evidence_id,
                )
                continue
            if not item.approved:
                add(
                    "blocker",
                    "unapproved-evidence",
                    f"{requirement_id} cites {evidence_id}, but {item.title} is not approved.",
                    requirement_id,
                    response,
                    evidence_id,
                )
            ref = next((ref for ref in row.evidence if ref.id == evidence_id), None)
            if ref and ref.score < 0.20:
                add(
                    "medium",
                    "weak-evidence",
                    f"{requirement_id} cites {evidence_id}, but the matcher scored it {ref.score:.2f} against this requirement.",
                    requirement_id,
                    response,
                    evidence_id,
                )

        for sentence in _claim_units(response):
            if not CLAIM_MARKERS.search(sentence):
                continue
            if META_MARKERS.search(sentence):
                continue
            if CITATION.search(sentence):
                continue
            if len(sentence.split()) < 5:
                continue
            add(
                "blocker",
                "unsupported-claim",
                f"{requirement_id} makes a claim without a citation: “{sentence[:180]}”",
                requirement_id,
                sentence,
            )

    known_ids = set(rows_by_id)
    for stray in set(re.findall(r"\bR-\d{3}\b", draft)) - known_ids:
        add("medium", "unknown-requirement", f"Draft mentions {stray}, which is not in the matrix.")

    if not CITATION.search(draft):
        add("blocker", "no-citations", "The draft contains no evidence citations at all.")

    stale = []
    for item in evidence:
        if not item.last_verified:
            continue
        try:
            verified = date.fromisoformat(item.last_verified)
        except ValueError:
            continue
        if (date.today() - verified).days > 365:
            stale.append(item)
    for item in stale:
        add(
            "high",
            "stale-evidence",
            f"{item.id} ({item.title}) was last verified on {item.last_verified}.",
            evidence_id=item.id,
        )

    remaining_days = days_until(matrix.due_date)
    if remaining_days is not None:
        if remaining_days < 0:
            add("blocker", "deadline-passed", f"The submission deadline ({matrix.due_date}) has passed.")
        elif remaining_days <= 5:
            add("high", "deadline-soon", f"Only {remaining_days} day(s) left before the deadline.")

    severity_counts = Counter(finding.severity for finding in findings)
    gap_count = int(matrix.summary.get("by_status", {}).get("gap", 0))
    mandatory_gaps = int(matrix.summary.get("mandatory_gaps", 0))
    coverage = float(matrix.summary.get("coverage_pct", 0))
    non_gap_high = sum(
        1 for finding in findings if finding.severity == "high" and finding.kind != "open-gap"
    )
    # Coverage is the anchor. Open gaps are already priced into it, so they
    # only add a small risk discount; unsupported claims and blockers are
    # separate defects and cost more.
    score = (
        coverage
        - severity_counts["blocker"] * 12
        - non_gap_high * 5
        - severity_counts["medium"] * 1
        - min(10.0, mandatory_gaps * 0.75)
        - min(5.0, gap_count * 0.2)
    )
    score = max(0, min(100, round(score)))
    cited = set(CITATION.findall(draft))
    summary = {
        "requirements": len(rows_by_id),
        "drafted": len(sections),
        "cited_evidence": len(cited),
        "findings": dict(severity_counts),
        "blockers": severity_counts["blocker"],
        "high": severity_counts["high"],
        "medium": severity_counts["medium"],
        "low": severity_counts["low"],
        "gaps": matrix.summary.get("by_status", {}).get("gap", 0),
        "coverage_pct": matrix.summary.get("coverage_pct", 0),
    }
    return Review(generated_at=now_iso(), score=score, findings=findings, summary=summary)


def review_to_markdown(review: Review, matrix: Matrix) -> str:
    summary = review.summary
    lines = [
        f"# Red-team review — {matrix.client or 'RFP'}",
        "",
        f"**Readiness score:** {review.score}/100  ",
        f"**Generated:** {review.generated_at}",
        "",
        "## What blocks submission",
        "",
    ]
    blockers = [f for f in review.findings if f.severity == "blocker"]
    if blockers:
        for finding in blockers:
            lines.append(f"- **{finding.id}** `{finding.kind}` {finding.message}")
    else:
        lines.append("- None. A human still has to sign off.")
    lines.extend(["", "## All findings", ""])
    if review.findings:
        lines.append("| ID | Severity | Kind | Requirement | Finding |")
        lines.append("| --- | --- | --- | --- | --- |")
        for finding in review.findings:
            message = finding.message.replace("|", "\\|")
            lines.append(
                f"| {finding.id} | {finding.severity} | {finding.kind} | "
                f"{finding.requirement_id or '—'} | {message} |"
            )
    else:
        lines.append("No findings.")
    lines.extend([
        "",
        "## Summary",
        "",
        f"- Requirements reviewed: {summary['requirements']}",
        f"- Responses found: {summary['drafted']}",
        f"- Distinct evidence cited: {summary['cited_evidence']}",
        f"- Matrix coverage: {summary['coverage_pct']}%",
        f"- Blockers: {summary['blockers']}",
        f"- High: {summary['high']}",
        f"- Medium: {summary['medium']}",
        f"- Low: {summary['low']}",
        "",
    ])
    return "\n".join(lines)


def write_review(review: Review, matrix: Matrix, workspace: Path) -> None:
    workspace = Path(workspace)
    (workspace / "review.md").write_text(review_to_markdown(review, matrix), encoding="utf-8")
