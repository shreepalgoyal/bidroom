from __future__ import annotations

from bidroom.models import Evidence, EvidenceRef, Matrix, MatrixRow
from bidroom.review import review_draft
from bidroom.util import now_iso


def _evidence(evidence_id: str = "E-001", approved: bool = True) -> Evidence:
    return Evidence(
        id=evidence_id,
        title="Test record",
        claim="We do the thing.",
        body="",
        tags=["delivery"],
        categories=["delivery"],
        approved=approved,
        owner="Owner",
        last_verified=now_iso()[:10],
        source="trust.example/test",
        path="",
    )


def _matrix(status: str = "compliant", evidence_id: str = "E-001") -> Matrix:
    row = MatrixRow(
        requirement_id="R-001",
        text="The supplier must do the thing.",
        section="Requirements",
        kind="mandatory",
        category="delivery",
        status=status,
        score=0.8,
        evidence=[EvidenceRef(id=evidence_id, title="Test record", score=0.8, approved=True)],
        owner="Programme lead",
        action="",
    )
    return Matrix(
        client="Test Council",
        reference="T-001",
        due_date="2099-01-01",
        generated_at=now_iso(),
        rows=[row],
        summary={
            "total_requirements": 1,
            "by_status": {"compliant": 1, "partial": 0, "needs-approval": 0, "gap": 0},
            "coverage_pct": 100.0,
            "mandatory_gaps": 0,
        },
    )


def _draft(response: str) -> str:
    return (
        "# Response draft\n\n"
        "### R-001 — Do the thing\n\n"
        f"**Response.** {response}\n\n"
        "**Owner.** Programme lead\n"
    )


def test_cited_claim_passes():
    review = review_draft(_draft("Yes. We do the thing. [E-001]"), _matrix(), [_evidence()])
    assert [f for f in review.findings if f.kind == "unsupported-claim"] == []


def test_claim_after_a_citation_still_needs_its_own_receipt():
    draft = _draft("Yes. We do the thing. [E-001] We are also ISO/IEC 27001 certified.")
    review = review_draft(draft, _matrix(), [_evidence()])
    unsupported = [f for f in review.findings if f.kind == "unsupported-claim"]
    assert len(unsupported) == 1
    assert unsupported[0].severity == "blocker"


def test_unapproved_evidence_is_a_blocker():
    review = review_draft(_draft("Yes. We do the thing. [E-001]"), _matrix(), [_evidence(approved=False)])
    kinds = {finding.kind for finding in review.findings if finding.severity == "blocker"}
    assert "unapproved-evidence" in kinds


def test_unknown_evidence_is_a_blocker():
    review = review_draft(_draft("Yes. We do the thing. [E-999]"), _matrix(), [_evidence()])
    kinds = {finding.kind for finding in review.findings if finding.severity == "blocker"}
    assert "unknown-evidence" in kinds


def test_gap_marked_as_compliant_is_a_blocker():
    draft = _draft("Yes. We are fully compliant.")
    review = review_draft(draft, _matrix(status="gap"), [_evidence()])
    kinds = {finding.kind for finding in review.findings if finding.severity == "blocker"}
    assert "claim-without-evidence" in kinds
