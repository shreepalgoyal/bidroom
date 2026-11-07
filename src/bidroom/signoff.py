from __future__ import annotations

from pathlib import Path

from .models import Evidence, Matrix, Review
from .util import human_date, now_iso, write_json
from .evidence import evidence_digest, evidence_summary

MIN_GAP_NOTE = 20


class SignoffRefused(Exception):
    """Raised when the evidence or review state does not allow a sign-off."""


def _open_gap_ids(matrix: Matrix) -> list[str]:
    return [row.requirement_id for row in matrix.rows if row.status == "gap"]


def create_signoff(
    matrix: Matrix,
    review: Review | None,
    evidence: list[Evidence],
    workspace: Path,
    by: str,
    note: str = "",
    accept_gaps: bool = False,
) -> dict:
    by = (by or "").strip()
    note = (note or "").strip()
    if not by:
        raise SignoffRefused("A sign-off needs the bid lead's name (--by).")
    if review is None:
        raise SignoffRefused("Run `bidroom review` before signing off. There is no red-team verdict.")
    blockers = [finding for finding in review.findings if finding.severity == "blocker"]
    if blockers:
        detail = "; ".join(f"{f.id} {f.message}" for f in blockers[:3])
        raise SignoffRefused(
            f"{len(blockers)} blocker(s) must be fixed before sign-off: {detail}"
        )
    counts = matrix.summary["by_status"]
    mandatory_gaps = int(matrix.summary.get("mandatory_gaps", 0))
    gap_ids = _open_gap_ids(matrix)
    if gap_ids and not accept_gaps:
        raise SignoffRefused(
            f"{len(gap_ids)} gap(s) remain, including {mandatory_gaps} mandatory. "
            "Fix them, or pass --accept-gaps with a written reason."
        )
    if accept_gaps and gap_ids and len(note) < MIN_GAP_NOTE:
        raise SignoffRefused(
            f"Accepting {len(gap_ids)} gap(s) needs a written reason of at least "
            f"{MIN_GAP_NOTE} characters in --note."
        )
    if accept_gaps and not gap_ids:
        raise SignoffRefused("Nothing to accept: there are no gaps in the matrix.")

    summary = evidence_summary(evidence)
    record = {
        "decision": "approved-with-accepted-gaps" if gap_ids else "approved-to-submit",
        "client": matrix.client,
        "reference": matrix.reference,
        "due_date": matrix.due_date,
        "signed_by": by,
        "signed_at": now_iso(),
        "note": note,
        "readiness_score": review.score,
        "coverage_pct": matrix.summary.get("coverage_pct", 0),
        "requirements": matrix.summary.get("total_requirements", 0),
        "compliant": counts.get("compliant", 0),
        "partial": counts.get("partial", 0),
        "needs_approval": counts.get("needs-approval", 0),
        "gaps": counts.get("gap", 0),
        "mandatory_gaps": mandatory_gaps,
        "accepted_gap_ids": gap_ids,
        "evidence": {
            "total": summary["total"],
            "approved": summary["approved"],
            "unapproved": summary["unapproved"],
            "stale": summary["stale"],
            "digest": evidence_digest(evidence),
        },
        "review_generated_at": review.generated_at,
        "findings": review.summary.get("findings", {}),
    }
    workspace = Path(workspace)
    write_json(workspace / "signoff.json", record)
    (workspace / "signoff.md").write_text(signoff_to_markdown(record), encoding="utf-8")
    return record


def signoff_to_markdown(record: dict) -> str:
    accepted = record.get("accepted_gap_ids") or []
    lines = [
        f"# Bid sign-off — {record.get('client') or 'RFP'}",
        "",
        f"**Decision:** {record.get('decision')}  ",
        f"**Signed by:** {record.get('signed_by')}  ",
        f"**Signed at:** {record.get('signed_at')}  ",
        f"**Reference:** {record.get('reference') or 'not stated'}  ",
        f"**Due:** {human_date(record.get('due_date'))}",
        "",
        "## Declaration",
        "",
        (
            f"I, {record.get('signed_by')}, have reviewed this response and the red-team "
            "findings. I confirm that every compliance claim cites an approved evidence "
            "record, and that the open gaps below are accepted deliberately rather than "
            "overlooked."
        ),
        "",
        "## Readiness at sign-off",
        "",
        f"- Requirements: {record.get('requirements')}",
        f"- Compliant: {record.get('compliant')}",
        f"- Partial: {record.get('partial')}",
        f"- Gaps: {record.get('gaps')} ({record.get('mandatory_gaps')} mandatory)",
        f"- Coverage: {record.get('coverage_pct')}%",
        f"- Readiness score: {record.get('readiness_score')}/100",
        f"- Evidence records approved: {record.get('evidence', {}).get('approved')} of {record.get('evidence', {}).get('total')}",
        f"- Evidence digest: `{record.get('evidence', {}).get('digest')}`",
        "",
    ]
    if accepted:
        lines.extend(["## Accepted gaps", ""])
        lines.extend(f"- {gap_id}" for gap_id in accepted)
        lines.append("")
    if record.get("note"):
        lines.extend(["## Reason recorded by the bid lead", "", record["note"], ""])
    lines.extend([
        "---",
        "",
        "This file is written by `bidroom signoff`. The evidence digest pins the exact",
        "library that was reviewed; if any record changes, the digest changes and the",
        "sign-off no longer applies.",
        "",
    ])
    return "\n".join(lines)


def load_signoff(workspace: Path) -> dict | None:
    from .util import load_json

    path = Path(workspace) / "signoff.json"
    if not path.exists():
        return None
    return load_json(path)


def signoff_state(workspace: Path, evidence: list[Evidence]) -> dict:
    """Return none / current / stale for the recorded sign-off.

    The digest pins the exact evidence library. If any record is approved,
    revoked or edited after sign-off, the signature is stale and the report
    says so instead of pretending the bid is still covered.
    """
    record = load_signoff(workspace)
    if not record:
        return {"status": "none", "record": None}
    recorded = str(record.get("evidence", {}).get("digest", ""))
    current = evidence_digest(evidence)
    status = "current" if recorded and recorded == current else "stale"
    return {"status": status, "record": record, "current_digest": current}
