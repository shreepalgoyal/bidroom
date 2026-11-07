from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

import yaml

from .draft import write_draft
from .evidence import (
    evidence_summary,
    import_evidence,
    lint_evidence,
    load_evidence,
    set_approval,
)
from .ingest import ingest
from .matrix import build_matrix, write_matrix
from .models import Matrix, RFP
from .report import write_report
from .review import review_draft, write_review
from .signoff import SignoffRefused, create_signoff, load_signoff
from .util import human_date, days_until, load_json, now_iso, write_json

DEFAULT_WORKSPACE = ".bidroom"


def _workspace(args: argparse.Namespace) -> Path:
    value = args.workspace or os.environ.get("BIDROOM_WORKSPACE") or DEFAULT_WORKSPACE
    path = Path(value).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _paths(workspace: Path) -> dict[str, Path]:
    return {
        "rfp": workspace / "rfp.json",
        "matrix": workspace / "matrix.json",
        "draft": workspace / "draft.md",
        "review": workspace / "review.json",
        "review_md": workspace / "review.md",
        "report": workspace / "report.html",
        "evidence": workspace / "evidence",
        "inbox": workspace / "inbox",
        "signoff": workspace / "signoff.json",
        "signoff_md": workspace / "signoff.md",
    }


def _require(path: Path, hint: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {path}. {hint}")


def _load_rfp(workspace: Path) -> RFP:
    path = _paths(workspace)["rfp"]
    _require(path, "Run `bidroom ingest <rfp-file>` first.")
    return RFP.from_dict(load_json(path))


def _load_matrix(workspace: Path) -> Matrix:
    path = _paths(workspace)["matrix"]
    _require(path, "Run `bidroom matrix` first.")
    return Matrix.from_dict(load_json(path))


def _load_evidence(workspace: Path, override: str | None = None) -> list:
    directory = Path(override).expanduser().resolve() if override else _paths(workspace)["evidence"]
    return load_evidence(directory)


def _print_summary(matrix: Matrix) -> None:
    summary = matrix.summary
    counts = summary["by_status"]
    print(f"Client:       {matrix.client or 'not stated'}")
    print(f"Reference:    {matrix.reference or 'not stated'}")
    print(f"Due:          {human_date(matrix.due_date)} ({days_until(matrix.due_date)} days)")
    print(f"Requirements: {summary['total_requirements']}")
    print(
        "Statuses:     "
        f"{counts['compliant']} compliant, {counts['partial']} partial, "
        f"{counts['needs-approval']} needs approval, {counts['gap']} gap"
    )
    print(f"Coverage:     {summary['coverage_pct']}%")
    print(f"Mandatory gaps: {summary['mandatory_gaps']}")
    evidence = summary.get("evidence", {})
    print(
        f"Evidence:     {evidence.get('approved', 0)} approved, "
        f"{evidence.get('unapproved', 0)} unapproved, {evidence.get('stale', 0)} stale"
    )


def _print_gaps(matrix: Matrix, limit: int = 10) -> None:
    rows = [row for row in matrix.rows if row.status != "compliant"]
    if not rows:
        print("\nNo open actions. Ready for human sign-off.")
        return
    print(f"\nTop {min(limit, len(rows))} open actions:")
    for row in rows[:limit]:
        print(f"  {row.requirement_id}  {row.status:<15} {row.owner:<16} {row.action}")


def _cmd_init(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    for key in ("evidence", "inbox"):
        paths[key].mkdir(parents=True, exist_ok=True)
    print(f"Workspace ready: {workspace}")
    print(f"  evidence/  put one Markdown file per approved claim")
    print(f"  inbox/     drop the RFP here")
    if args.rfp:
        target = paths["inbox"] / Path(args.rfp).name
        shutil.copy2(Path(args.rfp), target)
        print(f"  copied {args.rfp} -> {target}")
    if args.evidence:
        source = Path(args.evidence)
        if not source.is_dir():
            raise SystemExit(f"No such evidence directory: {source}")
        files = sorted(source.glob("*.md"))
        for file in files:
            shutil.copy2(file, paths["evidence"] / file.name)
        print(f"  copied {len(files)} evidence file(s) from {source}")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    source = Path(args.file)
    if not source.exists():
        raise SystemExit(f"No such file: {source}")
    rfp = ingest(source)
    if not rfp.requirements:
        raise SystemExit("No requirements found. Check the document or use a text/Markdown version.")
    write_json(paths["rfp"], rfp.to_dict())
    print(f"Ingested {source}")
    print(f"  Title:        {rfp.title}")
    print(f"  Client:       {rfp.client or 'not stated'}")
    print(f"  Reference:    {rfp.reference or 'not stated'}")
    print(f"  Due:          {human_date(rfp.due_date)}")
    print(f"  Requirements: {len(rfp.requirements)}")
    by_kind: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for requirement in rfp.requirements:
        by_kind[requirement.kind] = by_kind.get(requirement.kind, 0) + 1
        by_category[requirement.category] = by_category.get(requirement.category, 0) + 1
    print("  By kind:      " + ", ".join(f"{k} {v}" for k, v in sorted(by_kind.items())))
    print("  By category:  " + ", ".join(f"{k} {v}" for k, v in sorted(by_category.items(), key=lambda x: -x[1])))
    print(f"\nSaved {paths['rfp']}")
    return 0


def _cmd_matrix(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    rfp = _load_rfp(workspace)
    evidence = _load_evidence(workspace, args.evidence)
    if not evidence:
        print("Warning: no evidence files found. Every requirement will be a gap.")
        print(f"Add Markdown files under {paths['evidence']} or pass --evidence.")
    matrix = build_matrix(rfp, evidence)
    write_json(paths["matrix"], matrix.to_dict())
    write_matrix(matrix, workspace)
    _print_summary(matrix)
    _print_gaps(matrix)
    print(f"\nSaved {paths['matrix']}, matrix.md, matrix.csv")
    return 0


def _cmd_draft(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    matrix = _load_matrix(workspace)
    evidence = _load_evidence(workspace, args.evidence)
    write_draft(matrix, evidence, workspace)
    print(f"Draft written: {paths['draft']}")
    print(f"  {matrix.summary['total_requirements']} sections, citations taken from approved evidence only.")
    print("  Edit the prose, keep the citations. Run `bidroom review` before anyone submits.")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    matrix = _load_matrix(workspace)
    evidence = _load_evidence(workspace, args.evidence)
    _require(paths["draft"], "Run `bidroom draft` first.")
    draft = paths["draft"].read_text(encoding="utf-8")
    review = review_draft(draft, matrix, evidence)
    write_json(paths["review"], review.to_dict())
    write_review(review, matrix, workspace)
    print(f"Readiness score: {review.score}/100")
    for key in ("blocker", "high", "medium", "low"):
        print(f"  {key:<8} {review.summary['findings'].get(key, 0)}")
    blockers = [finding for finding in review.findings if finding.severity == "blocker"]
    if blockers:
        print("\nBlockers:")
        for finding in blockers[:10]:
            print(f"  {finding.id} {finding.requirement_id or '—':<8} {finding.message}")
    print(f"\nSaved {paths['review']} and review.md")
    if args.strict and blockers:
        return 1
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    matrix = _load_matrix(workspace)
    evidence = _load_evidence(workspace, args.evidence)
    review = None
    if paths["review"].exists():
        from .models import Review

        review = Review.from_dict(load_json(paths["review"]))
    path = write_report(matrix, review, evidence, workspace)
    print(f"Report written: {path}")
    if args.open:
        import webbrowser

        webbrowser.open(path.as_uri())
    return 0


def _cmd_all(args: argparse.Namespace) -> int:
    _cmd_ingest(args)
    print()
    _cmd_matrix(args)
    print()
    _cmd_draft(args)
    print()
    _cmd_review(args)
    print()
    _cmd_report(args)
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    print(f"Workspace: {workspace}\n")
    if paths["rfp"].exists():
        rfp = RFP.from_dict(load_json(paths["rfp"]))
        print(f"RFP:     {rfp.title} — {len(rfp.requirements)} requirements, due {human_date(rfp.due_date)}")
    else:
        print("RFP:     not ingested")
    if paths["matrix"].exists():
        matrix = Matrix.from_dict(load_json(paths["matrix"]))
        _print_summary(matrix)
    else:
        print("Matrix:  not built")
    print(f"Draft:   {'yes' if paths['draft'].exists() else 'no'} ({paths['draft']})")
    if paths["review"].exists():
        review_data = load_json(paths["review"])
        print(
            f"Review:  score {review_data.get('score')} · "
            f"{review_data.get('summary', {}).get('blockers', 0)} blockers"
        )
    else:
        print("Review:  not run")
    signoff = load_signoff(workspace)
    if signoff:
        from .signoff import signoff_state

        state = signoff_state(workspace, load_evidence(paths["evidence"]))
        suffix = " (STALE: evidence changed)" if state["status"] == "stale" else ""
        print(
            f"Sign-off: {signoff.get('decision')} by {signoff.get('signed_by')} "
            f"at {signoff.get('signed_at')}{suffix}"
        )
    else:
        print("Sign-off: not signed")
    print(f"Report:  {'yes' if paths['report'].exists() else 'no'} ({paths['report']})")
    return 0


def _cmd_requirements(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    matrix = _load_matrix(workspace)
    rows = matrix.rows
    if args.status:
        wanted = {value.strip() for value in args.status.split(",")}
        rows = [row for row in rows if row.status in wanted]
    if args.category:
        rows = [row for row in rows if row.category == args.category]
    if args.kind:
        rows = [row for row in rows if row.kind == args.kind]
    if args.limit:
        rows = rows[: args.limit]
    if args.json:
        print(json.dumps([row.to_dict() for row in rows], indent=2))
        return 0
    for row in rows:
        print(f"{row.requirement_id}  {row.status:<15} {row.category:<14} {row.kind:<12} {row.text}")
        if row.evidence:
            print(f"        evidence: {', '.join(ref.id for ref in row.evidence)}")
    print(f"\n{len(rows)} requirement(s)")
    return 0


def _cmd_evidence(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    if args.action == "add":
        directory = _paths(workspace)["evidence"]
        directory.mkdir(parents=True, exist_ok=True)
        frontmatter = {
            "id": args.id,
            "title": args.title,
            "claim": args.claim,
            "tags": [tag.strip() for tag in args.tags.split(",") if tag.strip()],
            "categories": [value.strip() for value in args.categories.split(",") if value.strip()],
            "approved": bool(args.approved),
            "owner": args.owner,
            "last_verified": args.last_verified or now_iso()[:10],
            "source": args.source,
        }
        path = directory / f"{args.id.lower()}.md"
        if path.exists() and not args.force:
            raise SystemExit(f"{path} already exists. Use --force to replace it.")
        body = args.body or args.claim
        text = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n" + body.strip() + "\n"
        path.write_text(text, encoding="utf-8")
        print(f"Evidence written: {path}")
        if not args.approved:
            print("  Not approved yet: it will not support a claim until someone approves it.")
        return 0
    evidence = _load_evidence(workspace, args.evidence)
    if args.action in {"approve", "unapprove"}:
        directory = Path(args.evidence).expanduser().resolve() if args.evidence else _paths(workspace)["evidence"]
        approved = args.action == "approve"
        item = set_approval(
            directory,
            approved,
            by=args.by,
            note=args.note or "",
            evidence_id=args.id,
        )
        state = "approved" if item.approved else "unapproved"
        print(f"{item.id} is now {state}.")
        print(f"  {item.title}")
        print(f"  Approved by: {args.by}")
        if args.note:
            print(f"  Note: {args.note}")
        print("\nRerun `bidroom matrix` and `bidroom draft` so the change flows through.")
        return 0
    if args.action == "import":
        if not args.directory:
            raise SystemExit("evidence import needs a source directory.")
        target = Path(args.evidence).expanduser().resolve() if args.evidence else _paths(workspace)["evidence"]
        imported = import_evidence(
            Path(args.directory),
            target,
            approve=args.approve,
            force=args.force,
        )
        for evidence_id, path, approved in imported:
            print(f"{evidence_id:<12} {'approved' if approved else 'PENDING':9} {path.name}")
        pending = sum(1 for _, _, approved in imported if not approved)
        print(f"\n{len(imported)} record(s) imported into {target}")
        if pending:
            print(f"{pending} need approval: run `bidroom evidence approve <id> --by <name>`.")
        return 0
    if args.action == "lint":
        issues = lint_evidence(evidence)
        for issue in issues:
            print(f"{issue.severity:<7} {issue.evidence_id:<12} {issue.message}")
        print(f"\n{evidence_summary(evidence)}")
        return 1 if any(issue.severity == "blocker" for issue in issues) else 0
    if args.action == "search":
        from .evidence import EvidenceIndex

        index = EvidenceIndex(evidence)
        results = index.search(args.query, args.category or "other", limit=args.limit)
        if not results:
            print("No matches.")
            return 0
        for item, score in results:
            print(f"{score:.2f}  {item.id:<12} {item.title}  ({'approved' if item.approved else 'unapproved'})")
            print(f"      {item.claim[:180]}")
        return 0
    if args.action == "list":
        for item in evidence:
            print(f"{item.id:<12} {'approved' if item.approved else 'pending ':9} {item.title}")
        print(f"\n{evidence_summary(evidence)}")
        return 0
    raise SystemExit(f"Unknown evidence action: {args.action}")


def _cmd_signoff(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    paths = _paths(workspace)
    matrix = _load_matrix(workspace)
    evidence = _load_evidence(workspace, args.evidence)
    review = None
    if paths["review"].exists():
        from .models import Review

        review = Review.from_dict(load_json(paths["review"]))
    try:
        record = create_signoff(
            matrix,
            review,
            evidence,
            workspace,
            by=args.by,
            note=args.note or "",
            accept_gaps=args.accept_gaps,
        )
    except SignoffRefused as exc:
        print(f"Sign-off refused: {exc}", file=sys.stderr)
        return 1
    print(f"Signed off: {record['decision']}")
    print(f"  Bid lead:      {record['signed_by']}")
    print(f"  Readiness:     {record['readiness_score']}/100")
    print(f"  Accepted gaps: {len(record['accepted_gap_ids'])}")
    print(f"  Evidence hash: {record['evidence']['digest'][:16]}…")
    print(f"\nSaved {paths['signoff']} and {paths['signoff_md']}")
    print("Regenerate the report with `bidroom report` to show the signature.")
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if out.exists():
        if not args.force:
            raise SystemExit(f"{out} exists. Use --force to replace it.")
        shutil.rmtree(out)
    (out / "inbox").mkdir(parents=True)
    (out / "evidence").mkdir(parents=True)
    rfp_source = source / "rfp.md"
    if not rfp_source.exists():
        raise SystemExit(f"Missing example RFP: {rfp_source}")
    shutil.copy2(rfp_source, out / "inbox" / "rfp.md")
    evidence_source = source / "evidence"
    if evidence_source.exists():
        for file in evidence_source.glob("*.md"):
            shutil.copy2(file, out / "evidence" / file.name)
    print(f"BidRoom demo — seeding {out}\n")
    args.workspace = str(out)
    _cmd_ingest(argparse.Namespace(workspace=str(out), file=str(out / "inbox" / "rfp.md")))
    print()
    _cmd_matrix(argparse.Namespace(workspace=str(out), evidence=None))

    if args.full:
        extras = source / "evidence-extra"
        if not extras.exists():
            raise SystemExit(f"Missing gap-closing evidence pack: {extras}")
        print("\n--- replaying the human gate ---\n")
        imported = import_evidence(extras, out / "evidence")
        for evidence_id, path, approved in imported:
            print(f"{evidence_id:<12} {'approved' if approved else 'PENDING':9} {path.name}")
        approvals = [
            ("E-DEL-09", "Checked Delivery report v4 section 3: top-20 transactions complete end to end."),
            ("E-DEL-10", "Checked the architecture note and service catalogue: single digital front door."),
            ("E-DEL-11", "Checked the connector test pack and two live references: IDOX Uniform sync."),
            ("E-CLOUD-05", "Checked the October load-test annex: 60k users and 2k concurrent sessions."),
            ("E-A11Y-06", "Checked the journey map and adviser training record: assisted-digital route."),
            ("E-DATA-06", "Checked the schema, OGL notice and stable URL: monthly open-data extract."),
        ]
        for evidence_id, note in approvals:
            item = set_approval(
                out / "evidence", True, by="Demo bid lead", note=note, evidence_id=evidence_id
            )
            print(f"{item.id:<12} approved by Demo bid lead")
        print("\nE-DEL-07 and E-DEL-08 stay unapproved on purpose.")
        print()
        _cmd_matrix(argparse.Namespace(workspace=str(out), evidence=None))
        print()
        _cmd_draft(argparse.Namespace(workspace=str(out), evidence=None))
        print()
        _cmd_review(argparse.Namespace(workspace=str(out), evidence=None, strict=False))
        print()
        _cmd_signoff(
            argparse.Namespace(
                workspace=str(out),
                by="Demo bid lead",
                note=(
                    "Scripted demo: reviewed the matrix, draft and red-team findings. "
                    "Eight mandatory gaps accepted with named owners and disclosed to the council."
                ),
                accept_gaps=True,
                evidence=None,
            )
        )
    else:
        print()
        _cmd_draft(argparse.Namespace(workspace=str(out), evidence=None))
        print()
        _cmd_review(argparse.Namespace(workspace=str(out), evidence=None, strict=False))

    print()
    _cmd_report(argparse.Namespace(workspace=str(out), evidence=None, open=False))
    print(f"\nOpen the report: {out / 'report.html'}")
    return 0


def _cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import serve

    workspace = _workspace(args)
    return serve(workspace)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bidroom",
        description="Evidence-backed RFP responses for human + agent teams.",
    )
    parser.add_argument(
        "--workspace",
        "-w",
        help="Workspace directory (default: .bidroom or $BIDROOM_WORKSPACE)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a workspace")
    init.add_argument("--rfp", help="Copy an RFP into the inbox")
    init.add_argument("--evidence", help="Copy Markdown evidence into the library")
    init.set_defaults(func=_cmd_init)

    ingest_parser = subparsers.add_parser("ingest", help="Extract requirements from an RFP")
    ingest_parser.add_argument("file")
    ingest_parser.set_defaults(func=_cmd_ingest)

    matrix = subparsers.add_parser("matrix", help="Match requirements to evidence")
    matrix.add_argument("--evidence", help="Evidence directory (default: <workspace>/evidence)")
    matrix.set_defaults(func=_cmd_matrix)

    draft = subparsers.add_parser("draft", help="Draft responses from approved evidence")
    draft.add_argument("--evidence", help="Evidence directory (default: <workspace>/evidence)")
    draft.set_defaults(func=_cmd_draft)

    review = subparsers.add_parser("review", help="Red-team the draft against the matrix")
    review.add_argument("--evidence", help="Evidence directory (default: <workspace>/evidence)")
    review.add_argument("--strict", action="store_true", help="Exit 1 if any blockers are found")
    review.set_defaults(func=_cmd_review)

    report = subparsers.add_parser("report", help="Build the HTML readiness report")
    report.add_argument("--evidence", help="Evidence directory (default: <workspace>/evidence)")
    report.add_argument("--open", action="store_true", help="Open the report in a browser")
    report.set_defaults(func=_cmd_report)

    all_parser = subparsers.add_parser("all", help="Run ingest, matrix, draft, review and report")
    all_parser.add_argument("file")
    all_parser.add_argument("--evidence", help="Evidence directory (default: <workspace>/evidence)")
    all_parser.add_argument("--open", action="store_true")
    all_parser.set_defaults(func=_cmd_all)

    status = subparsers.add_parser("status", help="Show the current state of the workspace")
    status.set_defaults(func=_cmd_status)

    requirements = subparsers.add_parser("requirements", help="List requirements from the matrix")
    requirements.add_argument("--status", help="Filter by status (comma-separated)")
    requirements.add_argument("--category")
    requirements.add_argument("--kind")
    requirements.add_argument("--limit", type=int)
    requirements.add_argument("--json", action="store_true")
    requirements.set_defaults(func=_cmd_requirements)

    evidence = subparsers.add_parser("evidence", help="Manage the evidence library")
    evidence_sub = evidence.add_subparsers(dest="action", required=True)
    add = evidence_sub.add_parser("add", help="Add an evidence record")
    add.add_argument("--id", required=True)
    add.add_argument("--title", required=True)
    add.add_argument("--claim", required=True)
    add.add_argument("--tags", default="")
    add.add_argument("--categories", default="")
    add.add_argument("--owner", default="")
    add.add_argument("--source", default="")
    add.add_argument("--last-verified", default="")
    add.add_argument("--body", default="")
    add.add_argument("--approved", action="store_true")
    add.add_argument("--force", action="store_true")
    lint = evidence_sub.add_parser("lint", help="Check evidence quality")
    lint.add_argument("--evidence")
    approve = evidence_sub.add_parser("approve", help="Approve one evidence record (human only)")
    approve.add_argument("id")
    approve.add_argument("--by", required=True, help="Name of the evidence owner approving it")
    approve.add_argument("--note", help="Why it is approved or what changed")
    approve.add_argument("--evidence")
    unapprove = evidence_sub.add_parser("unapprove", help="Revoke approval for one record")
    unapprove.add_argument("id")
    unapprove.add_argument("--by", required=True)
    unapprove.add_argument("--note")
    unapprove.add_argument("--evidence")
    import_parser = evidence_sub.add_parser("import", help="Import Markdown evidence; records land unapproved")
    import_parser.add_argument("directory", help="Directory of Markdown evidence files")
    import_parser.add_argument("--evidence", help="Target evidence library (default: <workspace>/evidence)")
    import_parser.add_argument("--approve", action="store_true", help="Import as already approved (not recommended)")
    import_parser.add_argument("--force", action="store_true", help="Replace existing records; approval resets")
    search = evidence_sub.add_parser("search", help="Search the evidence library")
    search.add_argument("query")
    search.add_argument("--category")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--evidence")
    listing = evidence_sub.add_parser("list", help="List evidence")
    listing.add_argument("--evidence")
    evidence.set_defaults(func=_cmd_evidence)

    demo = subparsers.add_parser("demo", help="Run the Northwind example end to end")
    demo.add_argument("--source", default="examples/northwind")
    demo.add_argument("--out", default="demo-output")
    demo.add_argument("--force", action="store_true")
    demo.add_argument(
        "--full",
        action="store_true",
        help="Also replay the six human approvals and the sign-off, producing the 77.9%% / 70 signed example",
    )
    demo.set_defaults(func=_cmd_demo)

    signoff = subparsers.add_parser("signoff", help="Record the bid lead's sign-off")
    signoff.add_argument("--by", required=True, help="Bid lead's name")
    signoff.add_argument("--note", help="What was reviewed, or why gaps are accepted")
    signoff.add_argument("--accept-gaps", action="store_true", help="Sign despite open gaps; needs a written reason")
    signoff.add_argument("--evidence", help="Evidence directory (default: <workspace>/evidence)")
    signoff.set_defaults(func=_cmd_signoff)

    mcp = subparsers.add_parser("mcp", help="Run the MCP server over stdio")
    mcp.set_defaults(func=_cmd_mcp)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
