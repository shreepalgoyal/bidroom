from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path

from .evidence import EvidenceIndex, evidence_summary
from .ingest import ACTION_BY_CATEGORY, OWNER_BY_CATEGORY
from .models import Evidence, EvidenceRef, Matrix, MatrixRow, RFP
from .util import escape_md_cell, now_iso

COMPLIANT_THRESHOLD = 0.52
PARTIAL_THRESHOLD = 0.27


def _status(score: float, approved: bool) -> str:
    if score >= COMPLIANT_THRESHOLD and approved:
        return "compliant"
    if score >= PARTIAL_THRESHOLD and approved:
        return "partial"
    if score >= PARTIAL_THRESHOLD and not approved:
        return "needs-approval"
    return "gap"


def _action(status: str, category: str, best_title: str) -> str:
    base = ACTION_BY_CATEGORY.get(category, ACTION_BY_CATEGORY["other"])
    if status == "compliant":
        return ""
    if status == "partial":
        return f"Strengthen the answer around “{best_title}”. {base}"
    if status == "needs-approval":
        return f"Get “{best_title}” approved by its owner. {base}"
    return "No approved evidence answers this requirement. Add a record that proves it, or record a no-bid decision."


def build_matrix(rfp: RFP, evidence: list[Evidence]) -> Matrix:
    index = EvidenceIndex(evidence)
    rows: list[MatrixRow] = []
    for requirement in rfp.requirements:
        matches = index.search(requirement.text, requirement.category, limit=3)
        best = matches[0] if matches else None
        score = best[1] if best else 0.0
        approved = best[0].approved if best else False
        status = _status(score, approved)
        refs = [
            EvidenceRef(id=item.id, title=item.title, score=round(match_score, 4), approved=item.approved)
            for item, match_score in matches
        ]
        if status == "gap":
            refs = []
        elif status == "needs-approval":
            refs = refs[:1]
        elif status == "partial":
            refs = [ref for ref in refs if ref.score >= PARTIAL_THRESHOLD][:2]
        else:
            refs = [ref for ref in refs if ref.score >= 0.45][:2]
        best_title = refs[0].title if refs else (best[0].title if best else "")
        rows.append(
            MatrixRow(
                requirement_id=requirement.id,
                text=requirement.text,
                section=requirement.section_path,
                kind=requirement.kind,
                category=requirement.category,
                status=status,
                score=round(score, 4),
                evidence=refs,
                owner=OWNER_BY_CATEGORY.get(requirement.category, OWNER_BY_CATEGORY["other"]),
                action=_action(status, requirement.category, best_title),
            )
        )

    status_counts = Counter(row.status for row in rows)
    category_counts = Counter(row.category for row in rows)
    kind_counts = Counter(row.kind for row in rows)
    total = len(rows)
    coverage = (
        (status_counts["compliant"] + 0.5 * status_counts["partial"]) / total if total else 0.0
    )
    mandatory_gaps = sum(1 for row in rows if row.kind == "mandatory" and row.status == "gap")
    summary = {
        "total_requirements": total,
        "by_status": {
            "compliant": status_counts["compliant"],
            "partial": status_counts["partial"],
            "needs-approval": status_counts["needs-approval"],
            "gap": status_counts["gap"],
        },
        "by_kind": dict(kind_counts),
        "by_category": dict(category_counts.most_common()),
        "coverage_pct": round(coverage * 100, 1),
        "mandatory_gaps": mandatory_gaps,
        "open_actions": sum(1 for row in rows if row.status != "compliant"),
        "evidence": evidence_summary(evidence),
    }
    return Matrix(
        client=rfp.client,
        reference=rfp.reference,
        due_date=rfp.due_date,
        generated_at=now_iso(),
        rows=rows,
        summary=summary,
    )


def matrix_to_markdown(matrix: Matrix) -> str:
    summary = matrix.summary
    lines = [
        f"# Compliance matrix — {matrix.client or 'RFP'}",
        "",
        f"**Reference:** {matrix.reference or 'not stated'}  ",
        f"**Due:** {matrix.due_date or 'not stated'}  ",
        f"**Generated:** {matrix.generated_at}",
        "",
        "## Summary",
        "",
        f"- Requirements: **{summary['total_requirements']}**",
        f"- Compliant: **{summary['by_status']['compliant']}**",
        f"- Partial: **{summary['by_status']['partial']}**",
        f"- Needs approval: **{summary['by_status']['needs-approval']}**",
        f"- Gap: **{summary['by_status']['gap']}**",
        f"- Coverage: **{summary['coverage_pct']}%**",
        f"- Mandatory gaps: **{summary['mandatory_gaps']}**",
        "",
        "## Requirements",
        "",
        "| ID | Requirement | Category | Kind | Status | Score | Evidence | Owner |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in matrix.rows:
        evidence = ", ".join(ref.id for ref in row.evidence[:2]) or "—"
        lines.append(
            "| {id} | {text} | {category} | {kind} | {status} | {score:.2f} | {evidence} | {owner} |".format(
                id=row.requirement_id,
                text=escape_md_cell(row.text),
                category=row.category,
                kind=row.kind,
                status=row.status,
                score=row.score,
                evidence=evidence,
                owner=escape_md_cell(row.owner),
            )
        )
    lines.append("")
    return "\n".join(lines)


def matrix_to_csv(matrix: Matrix) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "section", "category", "kind", "status", "score",
        "evidence", "owner", "requirement", "action",
    ])
    for row in matrix.rows:
        writer.writerow([
            row.requirement_id,
            row.section,
            row.category,
            row.kind,
            row.status,
            f"{row.score:.4f}",
            "; ".join(ref.id for ref in row.evidence),
            row.owner,
            row.text,
            row.action,
        ])
    return buffer.getvalue()


def write_matrix(matrix: Matrix, workspace: Path) -> None:
    workspace = Path(workspace)
    (workspace / "matrix.md").write_text(matrix_to_markdown(matrix), encoding="utf-8")
    (workspace / "matrix.csv").write_text(matrix_to_csv(matrix), encoding="utf-8")
