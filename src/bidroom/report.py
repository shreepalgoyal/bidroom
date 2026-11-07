from __future__ import annotations

import html
from pathlib import Path

from .models import Evidence, Matrix, Review
from .util import human_date, truncate

STATUS_CLASS = {
    "compliant": "ok",
    "partial": "warn",
    "needs-approval": "info",
    "gap": "bad",
}
STATUS_LABEL = {
    "compliant": "Compliant",
    "partial": "Partial",
    "needs-approval": "Needs approval",
    "gap": "Gap",
}
SEVERITY_CLASS = {
    "blocker": "bad",
    "high": "warn",
    "medium": "info",
    "low": "muted",
}

CSS = """
:root {
  --ink: #16202a;
  --muted: #667085;
  --line: #e6e4df;
  --paper: #f6f4ef;
  --card: #fffdf9;
  --accent: #0f6b60;
  --accent-soft: #e3f2ee;
  --ok: #157347;
  --ok-soft: #e6f4ec;
  --warn: #a35a00;
  --warn-soft: #fdf2df;
  --bad: #a5281f;
  --bad-soft: #fbe9e7;
  --info: #315a8a;
  --info-soft: #e9f0f8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background:
    radial-gradient(1200px 500px at 85% -10%, #e8efe9 0%, transparent 60%),
    var(--paper);
  color: var(--ink);
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.wrap { max-width: 1180px; margin: 0 auto; padding: 48px 28px 80px; }
.eyebrow {
  font: 600 11px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing: .14em; text-transform: uppercase; color: var(--accent);
}
h1 { font-size: 40px; line-height: 1.05; letter-spacing: -.03em; margin: 10px 0 8px; }
h2 { font-size: 22px; letter-spacing: -.015em; margin: 0 0 4px; }
h3 { font-size: 15px; margin: 0; }
.sub { color: var(--muted); margin: 0; }
.meta { display: flex; flex-wrap: wrap; gap: 8px 22px; margin-top: 18px; color: var(--muted); font-size: 13px; }
.meta b { color: var(--ink); font-weight: 600; }
.hero {
  display: grid; grid-template-columns: 220px 1fr; gap: 28px; align-items: center;
  background: var(--card); border: 1px solid var(--line); border-radius: 18px;
  padding: 28px; margin: 30px 0 18px;
  box-shadow: 0 1px 0 rgba(22,32,42,.03), 0 12px 40px -30px rgba(22,32,42,.35);
}
.donut {
  width: 180px; height: 180px; border-radius: 50%;
  display: grid; place-items: center;
  background: conic-gradient(var(--accent) calc(var(--score) * 1%), #e7e4dc 0);
  position: relative;
}
.donut::after { content: ""; position: absolute; inset: 16px; background: var(--card); border-radius: 50%; }
.donut .num { position: relative; z-index: 1; font-size: 44px; font-weight: 700; letter-spacing: -.04em; }
.donut .den { position: relative; z-index: 1; font-size: 11px; color: var(--muted); margin-top: -2px; }
.hero-copy p { color: var(--muted); margin: 8px 0 0; max-width: 640px; }
.verdict { display: inline-flex; align-items: center; gap: 8px; margin-top: 14px; font-weight: 600; font-size: 13px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin: 18px 0 34px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 13px; padding: 14px 16px; }
.kpi .v { font-size: 26px; font-weight: 700; letter-spacing: -.03em; line-height: 1.1; }
.kpi .l { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .07em; margin-top: 4px; }
.bar { display: flex; height: 10px; border-radius: 999px; overflow: hidden; background: #e7e4dc; margin: 10px 0 6px; }
.bar span { display: block; height: 100%; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: 12px; }
.legend i { width: 8px; height: 8px; border-radius: 2px; display: inline-block; margin-right: 6px; }
.panel { background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 22px 24px; margin: 0 0 18px; overflow: hidden; }
.panel-head { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin-bottom: 14px; }
.panel-head p { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
  text-align: left; font: 600 10px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
  letter-spacing: .08em; text-transform: uppercase; color: var(--muted);
  border-bottom: 1px solid var(--line); padding: 0 10px 9px; white-space: nowrap;
}
td { border-bottom: 1px solid #f0eee8; padding: 11px 10px; vertical-align: top; }
tr:last-child td { border-bottom: 0; }
td.id { font: 600 11px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--accent); white-space: nowrap; }
td.req { max-width: 520px; }
td.req .section { color: var(--muted); font-size: 11px; margin-top: 2px; }
.pill {
  display: inline-block; border-radius: 999px; padding: 3px 9px;
  font-size: 10px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; white-space: nowrap;
}
.pill.ok { background: var(--ok-soft); color: var(--ok); }
.pill.warn { background: var(--warn-soft); color: var(--warn); }
.pill.bad { background: var(--bad-soft); color: var(--bad); }
.pill.info { background: var(--info-soft); color: var(--info); }
.pill.muted { background: #f0efeb; color: var(--muted); }
.findings { display: grid; gap: 9px; }
.finding { display: grid; grid-template-columns: 78px 1fr; gap: 14px; border-top: 1px solid #f0eee8; padding-top: 10px; }
.finding:first-child { border-top: 0; padding-top: 0; }
.finding .kind { font: 600 10px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.finding p { margin: 0; }
.finding .where { color: var(--muted); font-size: 12px; margin-top: 2px; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.empty { color: var(--muted); font-size: 13px; padding: 8px 0; }
.foot { color: var(--muted); font-size: 12px; margin-top: 30px; display: flex; justify-content: space-between; gap: 20px; }
code { font: 12px ui-monospace, SFMono-Regular, Menlo, monospace; background: #f1efe9; padding: 1px 5px; border-radius: 4px; }
@media (max-width: 880px) {
  .hero { grid-template-columns: 1fr; }
  .grid { grid-template-columns: repeat(3, 1fr); }
  .two { grid-template-columns: 1fr; }
}
@media print {
  body { background: #fff; }
  .wrap { padding: 0; }
  .panel, .hero, .kpi { box-shadow: none; break-inside: avoid; }
}
"""


def _e(value: object) -> str:
    return html.escape(str(value or ""))


def _pill(status: str) -> str:
    return f'<span class="pill {STATUS_CLASS.get(status, "muted")}">{_e(STATUS_LABEL.get(status, status))}</span>'


def build_report(matrix: Matrix, review: Review | None, evidence: list[Evidence], signoff: dict | None = None, signoff_status: str = "none") -> str:
    summary = matrix.summary
    total = max(summary["total_requirements"], 1)
    counts = summary["by_status"]
    score = review.score if review else int(summary["coverage_pct"])
    score_class = "ok" if score >= 80 else "warn" if score >= 55 else "bad"
    if signoff_status == "stale":
        verdict = "Signature invalid — evidence changed"
    elif signoff:
        verdict = f"Signed off by {signoff.get('signed_by')}"
    elif score >= 85 and counts["gap"] == 0:
        verdict = "Ready for human sign-off"
    elif score >= 55:
        verdict = "Close, but not submittable"
    else:
        verdict = "Not ready to submit"
    segments = [
        ("ok", counts["compliant"]),
        ("warn", counts["partial"]),
        ("info", counts["needs-approval"]),
        ("bad", counts["gap"]),
    ]
    bar = "".join(
        f'<span style="width:{count / total * 100:.2f}%;background:var(--{name})"></span>'
        for name, count in segments
    )
    legend = "".join(
        f'<span><i style="background:var(--{name})"></i>{label}: {count}</span>'
        for (name, count), label in zip(segments, ["Compliant", "Partial", "Needs approval", "Gap"])
    )
    kpis = [
        (summary["total_requirements"], "Requirements"),
        (counts["compliant"], "Compliant"),
        (counts["partial"], "Partial"),
        (counts["gap"], "Gaps"),
        (f'{summary["coverage_pct"]}%', "Coverage"),
        (summary["mandatory_gaps"], "Mandatory gaps"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="v">{_e(value)}</div><div class="l">{_e(label)}</div></div>'
        for value, label in kpis
    )

    gaps = [row for row in matrix.rows if row.status != "compliant"]
    gap_rows = "".join(
        f"<tr><td class='id'>{_e(row.requirement_id)}</td>"
        f"<td class='req'>{_e(truncate(row.text, 150))}<div class='section'>{_e(row.section)}</div></td>"
        f"<td>{_pill(row.status)}</td><td>{_e(row.owner)}</td><td>{_e(row.action)}</td></tr>"
        for row in gaps
    ) or "<tr><td colspan='5' class='empty'>No open actions.</td></tr>"

    requirement_rows = "".join(
        f"<tr><td class='id'>{_e(row.requirement_id)}</td>"
        f"<td class='req'>{_e(truncate(row.text, 170))}<div class='section'>{_e(row.section)} · {_e(row.category)} · {_e(row.kind)}</div></td>"
        f"<td>{_pill(row.status)}</td>"
        f"<td>{', '.join(_e(ref.id) for ref in row.evidence[:2]) or '—'}</td></tr>"
        for row in matrix.rows
    )

    finding_html = ""
    if review:
        for finding in review.findings:
            finding_html += (
                f"<div class='finding'><div class='kind'>{_e(finding.severity)}</div>"
                f"<div><p>{_e(finding.message)}</p>"
                f"<div class='where'>{_e(finding.id)} · {_e(finding.kind)}"
                + (f" · {_e(finding.requirement_id)}" if finding.requirement_id else "")
                + "</div></div></div>"
            )
    if not finding_html:
        finding_html = "<div class='empty'>No review has been run yet.</div>"

    evidence_total = summary.get("evidence", {}).get("total", len(evidence))
    evidence_approved = summary.get("evidence", {}).get("approved", sum(1 for e in evidence if e.approved))

    if signoff_status == "stale" and signoff:
        signoff_html = (
            "<div class='finding'><div class='kind'>Invalid</div><div>"
            f"<p>{_e(signoff.get('signed_by'))} signed this bid, but the evidence library changed afterwards.</p>"
            "<div class='where'>The recorded digest no longer matches. Review the change and sign again; "
            "the old signature does not cover the current evidence.</div></div></div>"
        )
    elif signoff:
        accepted = signoff.get("accepted_gap_ids") or []
        signoff_html = (
            f"<div class='finding'><div class='kind'>Signed</div><div>"
            f"<p><b>{_e(signoff.get('signed_by'))}</b> signed this bid on {_e(signoff.get('signed_at'))}.</p>"
            f"<div class='where'>{_e(signoff.get('decision'))} · readiness {_e(signoff.get('readiness_score'))}/100"
            + (f" · {len(accepted)} accepted gap(s)" if accepted else "")
            + f"</div></div></div>"
            f"<div class='finding'><div class='kind'>Evidence</div><div>"
            f"<p>The signature pins {_e(signoff.get('evidence', {}).get('approved'))} approved records.</p>"
            f"<div class='where'>sha256 {_e(str(signoff.get('evidence', {}).get('digest', ''))[:24])}…</div>"
            f"</div></div>"
        )
        if accepted:
            signoff_html += (
                "<div class='finding'><div class='kind'>Accepted</div><div><p>"
                + ", ".join(_e(gap) for gap in accepted)
                + "</p><div class='where'>Gaps the bid lead accepted in writing.</div></div></div>"
            )
        if signoff.get("note"):
            signoff_html += (
                f"<div class='finding'><div class='kind'>Note</div><div><p>{_e(signoff['note'])}</p></div></div>"
            )
    else:
        signoff_html = (
            "<div class='finding'><div class='kind'>Pending</div><div>"
            "<p>No human has signed this bid yet.</p>"
            "<div class='where'>Run <code>bidroom signoff --by &lt;name&gt;</code> after the red-team is clean.</div>"
            "</div></div>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BidRoom report — {_e(matrix.client or "RFP")}</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="eyebrow">BidRoom / compliance report</div>
  <h1>{_e(matrix.client or "RFP response")}</h1>
  <p class="sub">Evidence-backed bid readiness, generated from the room's requirement register.</p>
  <div class="meta">
    <span><b>Reference</b> {_e(matrix.reference or "not stated")}</span>
    <span><b>Due</b> {_e(human_date(matrix.due_date))}</span>
    <span><b>Generated</b> {_e(matrix.generated_at)}</span>
    <span><b>Evidence</b> {_e(evidence_approved)} approved of {_e(evidence_total)}</span>
  </div>

  <section class="hero">
    <div class="donut" style="--score:{score}"><div class="num">{score}</div><div class="den">/ 100</div></div>
    <div class="hero-copy">
      <h2>{_e(verdict)}</h2>
      <p>{_e(summary["total_requirements"])} requirements were extracted from the RFP. The matcher found approved evidence for {_e(counts["compliant"])} of them and a partial match for {_e(counts["partial"])}. {_e(counts["gap"])} still have no proof, including {_e(summary["mandatory_gaps"])} mandatory requirement(s).</p>
      <div class="verdict"><span class="dot" style="background:var(--{score_class})"></span>Numeric readiness {score}/100 · human sign-off still required</div>
    </div>
  </section>

  <div class="grid">{kpi_html}</div>

  <section class="panel">
    <div class="panel-head"><div><h2>Human sign-off</h2><p>The gate no agent can pass for you.</p></div></div>
    <div class="findings">{signoff_html}</div>
  </section>

  <section class="panel">
    <div class="panel-head"><div><h2>Coverage</h2><p>Compliant counts fully; partial counts half.</p></div></div>
    <div class="bar">{bar}</div>
    <div class="legend">{legend}</div>
  </section>

  <section class="panel">
    <div class="panel-head"><div><h2>What still needs a human</h2><p>{len(gaps)} open action(s), ordered as extracted from the RFP.</p></div></div>
    <table>
      <thead><tr><th>ID</th><th>Requirement</th><th>Status</th><th>Owner</th><th>Next action</th></tr></thead>
      <tbody>{gap_rows}</tbody>
    </table>
  </section>

  <div class="two">
    <section class="panel">
      <div class="panel-head"><div><h2>Red-team findings</h2><p>Generated by <code>bidroom review</code>.</p></div></div>
      <div class="findings">{finding_html}</div>
    </section>
    <section class="panel">
      <div class="panel-head"><div><h2>How to read this</h2><p>The rules the room enforces.</p></div></div>
      <div class="findings">
        <div class="finding"><div class="kind">Rule 1</div><div><p>A claim only counts when it cites an approved evidence record.</p></div></div>
        <div class="finding"><div class="kind">Rule 2</div><div><p>Unapproved evidence is a blocker, not a maybe.</p></div></div>
        <div class="finding"><div class="kind">Rule 3</div><div><p>Every gap has a named owner and a next action.</p></div></div>
        <div class="finding"><div class="kind">Rule 4</div><div><p>The red-team reviews the draft; the bid lead signs the submission.</p></div></div>
      </div>
    </section>
  </div>

  <section class="panel">
    <div class="panel-head"><div><h2>Requirement register</h2><p>All {summary["total_requirements"]} extracted requirements with their best evidence.</p></div></div>
    <table>
      <thead><tr><th>ID</th><th>Requirement</th><th>Status</th><th>Evidence</th></tr></thead>
      <tbody>{requirement_rows}</tbody>
    </table>
  </section>

  <div class="foot">
    <span>Generated by BidRoom · <code>github.com/&lt;you&gt;/bidroom</code></span>
    <span>Every claim has a receipt.</span>
  </div>
</div>
</body>
</html>
"""


def write_report(matrix: Matrix, review: Review | None, evidence: list[Evidence], workspace: Path) -> Path:
    from .signoff import signoff_state

    state = signoff_state(workspace, evidence)
    path = Path(workspace) / "report.html"
    path.write_text(
        build_report(matrix, review, evidence, state["record"], state["status"]),
        encoding="utf-8",
    )
    return path
