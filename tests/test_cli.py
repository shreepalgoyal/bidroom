from __future__ import annotations

import json
from pathlib import Path

from bidroom.cli import main

ROOT = Path(__file__).resolve().parents[1]


def _demo(tmp_path: Path) -> int:
    return main([
        "demo",
        "--source", str(ROOT / "examples" / "northwind"),
        "--out", str(tmp_path / "demo"),
        "--force",
    ])


def test_demo_runs_and_writes_artifacts(tmp_path: Path):
    assert _demo(tmp_path) == 0
    output = tmp_path / "demo"
    for name in ("rfp.json", "matrix.json", "draft.md", "review.json", "report.html"):
        assert (output / name).exists(), name
    draft = (output / "draft.md").read_text(encoding="utf-8")
    assert "[[GAP]]" in draft
    assert "[E-" in draft


def test_signoff_refuses_open_gaps_without_written_acceptance(tmp_path: Path):
    assert _demo(tmp_path) == 0
    workspace = str(tmp_path / "demo")
    assert main(["-w", workspace, "signoff", "--by", "Priya Raman", "--note", "Reviewed."]) == 1
    assert not (tmp_path / "demo" / "signoff.json").exists()


def test_signoff_with_accepted_gaps_and_report(tmp_path: Path):
    assert _demo(tmp_path) == 0
    workspace = str(tmp_path / "demo")
    code = main([
        "-w", workspace,
        "signoff",
        "--by", "Priya Raman, Bid Lead",
        "--accept-gaps",
        "--note",
        "The remaining mandatory gaps are IDOX integration and the ISO certificate, both out of scope for this bid.",
    ])
    assert code == 0
    assert (tmp_path / "demo" / "signoff.json").exists()
    assert main(["-w", workspace, "report"]) == 0
    report = (tmp_path / "demo" / "report.html").read_text(encoding="utf-8")
    assert "Signed off by Priya Raman" in report


def test_full_demo_replays_human_gate_and_signs(tmp_path: Path):
    assert main([
        "demo",
        "--source", str(ROOT / "examples" / "northwind"),
        "--out", str(tmp_path / "demo"),
        "--force",
        "--full",
    ]) == 0
    output = tmp_path / "demo"
    matrix = json.loads((output / "matrix.json").read_text(encoding="utf-8"))
    summary = matrix["summary"]
    assert summary["by_status"] == {
        "compliant": 57,
        "partial": 6,
        "needs-approval": 2,
        "gap": 12,
    }
    assert summary["coverage_pct"] == 77.9
    assert summary["evidence"] == {
        "total": 54,
        "approved": 52,
        "unapproved": 2,
        "stale": 0,
    }
    signoff = json.loads((output / "signoff.json").read_text(encoding="utf-8"))
    assert signoff["decision"] == "approved-with-accepted-gaps"
    assert signoff["readiness_score"] == 70
    report = (output / "report.html").read_text(encoding="utf-8")
    assert "Signed off by Demo bid lead" in report


def test_evidence_approval_flows_into_matrix(tmp_path: Path):
    assert _demo(tmp_path) == 0
    workspace = str(tmp_path / "demo")
    assert main([
        "-w", workspace,
        "evidence", "approve", "E-DEL-08",
        "--by", "Dana Whitfield",
        "--note", "Legal review complete.",
    ]) == 0
    assert main(["-w", workspace, "matrix"]) == 0
    assert main([
        "-w", workspace,
        "requirements", "--status", "needs-approval",
    ]) == 0
    matrix = (tmp_path / "demo" / "matrix.json").read_text(encoding="utf-8")
    assert "E-DEL-08" in matrix
