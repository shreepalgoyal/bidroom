from __future__ import annotations

from pathlib import Path

from bidroom.ingest import ingest

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "northwind" / "rfp.md"


def test_ingest_reads_metadata_and_requirements():
    rfp = ingest(EXAMPLE)
    assert rfp.client == "Northwind City Council"
    assert rfp.reference == "NCC-2026-114"
    assert rfp.due_date == "2026-11-20"
    assert len(rfp.requirements) == 77


def test_ingest_skips_background_and_question_sections():
    rfp = ingest(EXAMPLE)
    texts = " ".join(requirement.text.lower() for requirement in rfp.requirements)
    assert "seven different systems" not in texts
    assert "the council wishes to appoint" not in texts


def test_ingest_classifies_kind_and_category():
    rfp = ingest(EXAMPLE)
    by_id = {requirement.id: requirement for requirement in rfp.requirements}
    assert by_id["R-001"].category == "delivery"
    assert by_id["R-004"].category == "hosting"
    assert by_id["R-010"].category == "integration"
    mandatory = [requirement for requirement in rfp.requirements if requirement.kind == "mandatory"]
    assert len(mandatory) == 65


def test_ingest_does_not_match_sla_inside_translated():
    rfp = ingest(EXAMPLE)
    translated = next(r for r in rfp.requirements if "translated content" in r.text)
    assert translated.category == "accessibility"
