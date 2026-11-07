from __future__ import annotations

from pathlib import Path

import pytest

from bidroom.evidence import (
    EvidenceIndex,
    evidence_digest,
    import_evidence,
    load_evidence,
    set_approval,
)

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "northwind" / "evidence"


def _index() -> tuple[list, EvidenceIndex]:
    evidence = load_evidence(EXAMPLE)
    return evidence, EvidenceIndex(evidence)


def test_qualifier_penalty_blocks_generic_security_record_for_iso_requirement():
    evidence, index = _index()
    by_id = {item.id: item for item in evidence}
    requirement = "The supplier must hold ISO/IEC 27001 certification covering the services in scope."
    generic = index.score(requirement, "security", by_id["E-SEC-01"])
    assert generic < 0.30


def test_index_does_not_let_soc2_answer_idox_integration():
    evidence, index = _index()
    by_id = {item.id: item for item in evidence}
    requirement = (
        "The solution must integrate with the Council's existing IDOX Uniform system "
        "for planning and environmental health records."
    )
    assert index.score(requirement, "integration", by_id["E-DEL-02"]) < 0.30


def test_approval_requires_a_named_human(tmp_path: Path):
    target = tmp_path / "evidence"
    target.mkdir()
    source = EXAMPLE / "e-del-08-delegated-access.md"
    (target / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError):
        set_approval(target, True, by="", evidence_id="E-DEL-08")


def test_approval_updates_frontmatter_and_digest(tmp_path: Path):
    target = tmp_path / "evidence"
    target.mkdir()
    source = EXAMPLE / "e-del-08-delegated-access.md"
    path = target / source.name
    path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    before = evidence_digest(load_evidence(target))
    item = set_approval(target, True, by="Priya Raman", note="Legal review complete.", evidence_id="E-DEL-08")
    after_evidence = load_evidence(target)
    assert item.approved is True
    assert evidence_digest(after_evidence) != before
    text = path.read_text(encoding="utf-8")
    assert "approved_by: Priya Raman" in text
    assert "approved_at:" in text


def test_import_lands_unapproved_even_if_source_is_approved(tmp_path: Path):
    source = tmp_path / "incoming"
    source.mkdir()
    (source / "extra.md").write_text(
        "---\n"
        "id: E-TEST-01\n"
        "title: A test record\n"
        "claim: A claim that still needs a human.\n"
        "tags: [test]\n"
        "categories: [other]\n"
        "approved: true\n"
        "owner: Test owner\n"
        "last_verified: 2026-10-01\n"
        "source: trust.example/test\n"
        "---\n\nBody.\n",
        encoding="utf-8",
    )
    target = tmp_path / "library"
    imported = import_evidence(source, target)
    assert imported[0][0] == "E-TEST-01"
    assert load_evidence(target)[0].approved is False
