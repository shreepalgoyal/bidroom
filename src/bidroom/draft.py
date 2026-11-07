from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from .models import Evidence, Matrix, MatrixRow
from .util import now_iso, truncate

STATUS_LABEL = {
    "compliant": "Compliant",
    "partial": "Partially compliant",
    "needs-approval": "Evidence pending approval",
    "gap": "Gap — not yet evidenced",
}


def _top_section(row: MatrixRow) -> str:
    return row.section.split(" > ")[0] if row.section else "Requirements"


def _response(row: MatrixRow, evidence_by_id: dict[str, Evidence]) -> str:
    refs: list[Evidence] = []
    for index, ref in enumerate(row.evidence):
        item = evidence_by_id.get(ref.id)
        if not item or not item.approved:
            continue
        if index > 0 and ref.score < 0.60:
            continue
        refs.append(item)
    if row.status == "compliant" and refs:
        primary = refs[0]
        text = primary.claim or primary.title
        citation = " ".join(f"[{item.id}]" for item in refs[:2])
        return f"Yes. {text} {citation}".strip()
    if row.status == "partial" and refs:
        primary = refs[0]
        text = primary.claim or primary.title
        return (
            f"Partially. {text} [{primary.id}] "
            f"The remaining gap is owned by {row.owner}: {row.action}"
        ).strip()
    if row.status == "needs-approval":
        pending = row.evidence[0] if row.evidence else None
        name = pending.title if pending else "the supporting record"
        return (
            f"Evidence exists but is not approved yet: {name}. "
            f"Do not submit this answer until {row.owner} approves it."
        )
    if row.status == "gap":
        return f"[[GAP]] No approved evidence yet. {row.action}"
    return "Acknowledged."


def build_draft(matrix: Matrix, evidence: list[Evidence]) -> str:
    evidence_by_id = {item.id: item for item in evidence}
    groups: "OrderedDict[str, list[MatrixRow]]" = OrderedDict()
    for row in matrix.rows:
        groups.setdefault(_top_section(row), []).append(row)

    summary = matrix.summary
    lines = [
        f"# Response draft — {matrix.client or 'RFP'}",
        "",
        f"**Reference:** {matrix.reference or 'not stated'}  ",
        f"**Due:** {matrix.due_date or 'not stated'}  ",
        f"**Generated:** {now_iso()}",
        "",
        "> **Drafting rule.** Every claim in this draft must cite an approved evidence record.",
        "> Text marked `[[GAP]]` is not a response yet. Do not remove a citation or invent a",
        "> claim to make a section look complete. The red-team checks this file before a human",
        "> signs it off.",
        "",
        "## Readiness at a glance",
        "",
        f"- {summary['total_requirements']} requirements in scope",
        f"- {summary['by_status']['compliant']} compliant, "
        f"{summary['by_status']['partial']} partial, "
        f"{summary['by_status']['needs-approval']} awaiting approval, "
        f"{summary['by_status']['gap']} gaps",
        f"- Evidence coverage: {summary['coverage_pct']}%",
        f"- Mandatory gaps: {summary['mandatory_gaps']}",
        "",
    ]
    for section, rows in groups.items():
        lines.extend([f"## {section}", ""])
        for row in rows:
            lines.append(f"### {row.requirement_id} — {truncate(row.text, 72)}")
            lines.append("")
            lines.append(f"**Requirement.** {row.text}")
            lines.append("")
            lines.append(f"**Status.** {STATUS_LABEL.get(row.status, row.status)} · {row.category} · {row.kind}")
            lines.append("")
            lines.append(f"**Response.** {_response(row, evidence_by_id)}")
            lines.append("")
            if row.evidence:
                refs = []
                for ref in row.evidence:
                    item = evidence_by_id.get(ref.id)
                    if item:
                        refs.append(f"[{item.id}] {item.title} — {truncate(item.claim, 140)}")
                    else:
                        refs.append(f"[{ref.id}] {ref.title}")
                lines.append("**Evidence.** " + " · ".join(refs))
                lines.append("")
            lines.append(f"**Owner.** {row.owner}")
            lines.append("")

    gaps = [row for row in matrix.rows if row.status != "compliant"]
    if gaps:
        lines.extend(["## Open actions before submission", ""])
        lines.append("| ID | Status | Owner | Action |")
        lines.append("| --- | --- | --- | --- |")
        for row in gaps:
            action = row.action.replace("|", "\\|")
            lines.append(f"| {row.requirement_id} | {row.status} | {row.owner} | {action} |")
        lines.append("")
    return "\n".join(lines)


def write_draft(matrix: Matrix, evidence: list[Evidence], workspace: Path) -> str:
    text = build_draft(matrix, evidence)
    (Path(workspace) / "draft.md").write_text(text, encoding="utf-8")
    return text
