from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

from .draft import write_draft
from .evidence import EvidenceIndex, evidence_summary, load_evidence
from .ingest import ingest
from .matrix import build_matrix, write_matrix
from .models import Matrix, RFP, Review
from .report import write_report
from .review import review_draft, write_review
from .util import days_until, human_date, load_json, now_iso, write_json

SERVER_INFO = {"name": "bidroom", "version": "0.1.0"}
PROTOCOL_VERSION = "2024-11-05"


def _text(value: str, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": value}], "isError": is_error}


def _paths(workspace: Path) -> dict[str, Path]:
    return {
        "rfp": workspace / "rfp.json",
        "matrix": workspace / "matrix.json",
        "draft": workspace / "draft.md",
        "review": workspace / "review.json",
        "report": workspace / "report.html",
        "evidence": workspace / "evidence",
    }


def _rfp(workspace: Path) -> RFP:
    path = _paths(workspace)["rfp"]
    if not path.exists():
        raise ValueError("No RFP ingested yet. Call bidroom_ingest first.")
    return RFP.from_dict(load_json(path))


def _matrix(workspace: Path) -> Matrix:
    path = _paths(workspace)["matrix"]
    if not path.exists():
        raise ValueError("No matrix yet. Call bidroom_matrix first.")
    return Matrix.from_dict(load_json(path))


def _evidence(workspace: Path, override: str | None = None):
    directory = Path(override).expanduser() if override else _paths(workspace)["evidence"]
    return load_evidence(directory)


TOOLS: list[dict[str, Any]] = [
    {
        "name": "bidroom_status",
        "description": "Show the current BidRoom workspace state: RFP, matrix, draft, review and report.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "bidroom_ingest",
        "description": "Extract requirements, client, reference and deadline from an RFP document.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "Path to the RFP (.md, .txt, .pdf, .docx)."},
            },
            "required": ["file"],
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_matrix",
        "description": "Match every requirement to approved evidence and write the compliance matrix.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "evidence": {"type": "string", "description": "Optional evidence directory override."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_draft",
        "description": "Draft responses from approved evidence only, with [E-xxx] citations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "evidence": {"type": "string", "description": "Optional evidence directory override."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_review",
        "description": "Red-team the draft against the matrix and evidence library.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "evidence": {"type": "string", "description": "Optional evidence directory override."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_report",
        "description": "Build the single-file HTML readiness report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "evidence": {"type": "string", "description": "Optional evidence directory override."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_requirements",
        "description": "List requirements from the matrix, optionally filtered by status, category or kind.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "compliant, partial, needs-approval or gap; comma-separated."},
                "category": {"type": "string"},
                "kind": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_gaps",
        "description": "List every requirement that is not yet compliant, with owner and next action.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Optional owner filter."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_evidence_search",
        "description": "Search the evidence library for proof relevant to a requirement or topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "bidroom_evidence_add",
        "description": "Add one evidence record to the library. Unapproved records cannot support a claim.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "claim": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "categories": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "source": {"type": "string"},
                "approved": {"type": "boolean"},
                "last_verified": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["id", "title", "claim"],
            "additionalProperties": False,
        },
    },
]


def _status(workspace: Path) -> str:
    paths = _paths(workspace)
    lines = [f"Workspace: {workspace}"]
    if paths["rfp"].exists():
        rfp = _rfp(workspace)
        lines.append(f"RFP: {rfp.title} — {len(rfp.requirements)} requirements, due {human_date(rfp.due_date)} ({days_until(rfp.due_date)} days)")
    else:
        lines.append("RFP: not ingested")
    if paths["matrix"].exists():
        matrix = _matrix(workspace)
        summary = matrix.summary
        counts = summary["by_status"]
        lines.append(
            f"Matrix: {summary['total_requirements']} requirements; "
            f"{counts['compliant']} compliant, {counts['partial']} partial, "
            f"{counts['needs-approval']} needs approval, {counts['gap']} gap; "
            f"coverage {summary['coverage_pct']}%, mandatory gaps {summary['mandatory_gaps']}"
        )
        evidence = summary.get("evidence", {})
        lines.append(
            f"Evidence: {evidence.get('approved', 0)} approved, "
            f"{evidence.get('unapproved', 0)} unapproved, {evidence.get('stale', 0)} stale"
        )
    else:
        lines.append("Matrix: not built")
    lines.append(f"Draft: {'yes' if paths['draft'].exists() else 'no'}")
    if paths["review"].exists():
        review = load_json(paths["review"])
        lines.append(f"Review: score {review.get('score')}/100, {review.get('summary', {}).get('blockers', 0)} blockers")
    else:
        lines.append("Review: not run")
    lines.append(f"Report: {'yes' if paths['report'].exists() else 'no'} ({paths['report']})")
    return "\n".join(lines)


def _requirements(workspace: Path, arguments: dict[str, Any]) -> str:
    matrix = _matrix(workspace)
    rows = matrix.rows
    status = arguments.get("status")
    if status:
        wanted = {value.strip() for value in str(status).split(",")}
        rows = [row for row in rows if row.status in wanted]
    if arguments.get("category"):
        rows = [row for row in rows if row.category == arguments["category"]]
    if arguments.get("kind"):
        rows = [row for row in rows if row.kind == arguments["kind"]]
    if arguments.get("limit"):
        rows = rows[: int(arguments["limit"])]
    lines = []
    for row in rows:
        lines.append(f"{row.requirement_id} | {row.status} | {row.category} | {row.kind} | {row.text}")
        if row.evidence:
            lines.append("  evidence: " + ", ".join(ref.id for ref in row.evidence))
    lines.append(f"\n{len(rows)} requirement(s)")
    return "\n".join(lines)


def _gaps(workspace: Path, arguments: dict[str, Any]) -> str:
    matrix = _matrix(workspace)
    rows = [row for row in matrix.rows if row.status != "compliant"]
    if arguments.get("owner"):
        rows = [row for row in rows if row.owner.lower() == str(arguments["owner"]).lower()]
    if arguments.get("limit"):
        rows = rows[: int(arguments["limit"])]
    if not rows:
        return "No open actions. Ready for human sign-off."
    lines = [f"{len(rows)} open action(s):"]
    for row in rows:
        lines.append(f"{row.requirement_id} | {row.status} | {row.owner} | {row.text}")
        lines.append(f"  action: {row.action}")
    return "\n".join(lines)


def _evidence_add(workspace: Path, arguments: dict[str, Any]) -> str:
    directory = _paths(workspace)["evidence"]
    directory.mkdir(parents=True, exist_ok=True)
    evidence_id = str(arguments["id"])
    path = directory / f"{evidence_id.lower()}.md"
    frontmatter = {
        "id": evidence_id,
        "title": arguments["title"],
        "claim": arguments["claim"],
        "tags": arguments.get("tags", []),
        "categories": arguments.get("categories", []),
        "approved": bool(arguments.get("approved", False)),
        "owner": arguments.get("owner", ""),
        "last_verified": arguments.get("last_verified") or now_iso()[:10],
        "source": arguments.get("source", ""),
    }
    body = arguments.get("body") or arguments["claim"]
    text = "---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n" + body.strip() + "\n"
    path.write_text(text, encoding="utf-8")
    state = "approved" if frontmatter["approved"] else "NOT approved"
    return f"Wrote {path} ({state})."


def dispatch(workspace: Path, name: str, arguments: dict[str, Any]) -> str:
    paths = _paths(workspace)
    if name == "bidroom_status":
        return _status(workspace)
    if name == "bidroom_ingest":
        source = Path(str(arguments["file"])).expanduser()
        if not source.exists():
            raise ValueError(f"No such file: {source}")
        rfp = ingest(source)
        if not rfp.requirements:
            raise ValueError("No requirements found in that document.")
        write_json(paths["rfp"], rfp.to_dict())
        by_category: dict[str, int] = {}
        for requirement in rfp.requirements:
            by_category[requirement.category] = by_category.get(requirement.category, 0) + 1
        top = ", ".join(f"{key} {value}" for key, value in sorted(by_category.items(), key=lambda x: -x[1]))
        return (
            f"Ingested {source}\nTitle: {rfp.title}\nClient: {rfp.client or 'not stated'}\n"
            f"Reference: {rfp.reference or 'not stated'}\nDue: {human_date(rfp.due_date)}\n"
            f"Requirements: {len(rfp.requirements)}\nBy category: {top}"
        )
    if name == "bidroom_matrix":
        rfp = _rfp(workspace)
        evidence = _evidence(workspace, arguments.get("evidence"))
        matrix = build_matrix(rfp, evidence)
        write_json(paths["matrix"], matrix.to_dict())
        write_matrix(matrix, workspace)
        summary = matrix.summary
        counts = summary["by_status"]
        return (
            f"Matrix built: {summary['total_requirements']} requirements, "
            f"{counts['compliant']} compliant, {counts['partial']} partial, "
            f"{counts['needs-approval']} needs approval, {counts['gap']} gap, "
            f"coverage {summary['coverage_pct']}%, mandatory gaps {summary['mandatory_gaps']}.\n"
            f"Saved {paths['matrix']}, matrix.md and matrix.csv."
        )
    if name == "bidroom_draft":
        matrix = _matrix(workspace)
        evidence = _evidence(workspace, arguments.get("evidence"))
        write_draft(matrix, evidence, workspace)
        return f"Draft written to {paths['draft']}. Keep every [E-xxx] citation; never invent a claim."
    if name == "bidroom_review":
        matrix = _matrix(workspace)
        evidence = _evidence(workspace, arguments.get("evidence"))
        if not paths["draft"].exists():
            raise ValueError("No draft yet. Call bidroom_draft first.")
        review = review_draft(paths["draft"].read_text(encoding="utf-8"), matrix, evidence)
        write_json(paths["review"], review.to_dict())
        write_review(review, matrix, workspace)
        blockers = [finding for finding in review.findings if finding.severity == "blocker"]
        lines = [
            f"Readiness score: {review.score}/100",
            f"Blockers: {review.summary['findings'].get('blocker', 0)} | "
            f"High: {review.summary['findings'].get('high', 0)} | "
            f"Medium: {review.summary['findings'].get('medium', 0)}",
        ]
        for finding in blockers[:10]:
            lines.append(f"{finding.id} {finding.requirement_id or '—'} {finding.message}")
        lines.append(f"Saved {paths['review']} and review.md.")
        return "\n".join(lines)
    if name == "bidroom_report":
        matrix = _matrix(workspace)
        evidence = _evidence(workspace, arguments.get("evidence"))
        review = None
        if paths["review"].exists():
            review = Review.from_dict(load_json(paths["review"]))
        path = write_report(matrix, review, evidence, workspace)
        return f"Report written to {path}"
    if name == "bidroom_requirements":
        return _requirements(workspace, arguments)
    if name == "bidroom_gaps":
        return _gaps(workspace, arguments)
    if name == "bidroom_evidence_search":
        evidence = _evidence(workspace, arguments.get("evidence"))
        index = EvidenceIndex(evidence)
        results = index.search(
            str(arguments["query"]),
            str(arguments.get("category") or "other"),
            limit=int(arguments.get("limit") or 5),
        )
        if not results:
            return "No matching evidence."
        lines = []
        for item, score in results:
            lines.append(f"{score:.2f} | {item.id} | {item.title} | {'approved' if item.approved else 'unapproved'}")
            lines.append(f"  {item.claim}")
        return "\n".join(lines)
    if name == "bidroom_evidence_add":
        return _evidence_add(workspace, arguments)
    raise ValueError(f"Unknown tool: {name}")


def _respond(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def serve(workspace: Path) -> int:
    workspace = Path(workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            _respond({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            continue
        method = message.get("method")
        request_id = message.get("id")
        if method is None:
            continue
        if request_id is None:
            # Notification: initialized, cancelled, etc. No response is allowed.
            continue
        try:
            if method == "initialize":
                _respond({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": SERVER_INFO,
                    },
                })
            elif method == "ping":
                _respond({"jsonrpc": "2.0", "id": request_id, "result": {}})
            elif method == "tools/list":
                _respond({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
            elif method == "tools/call":
                params = message.get("params") or {}
                name = params.get("name")
                arguments = params.get("arguments") or {}
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be an object.")
                result = dispatch(workspace, str(name), arguments)
                _respond({"jsonrpc": "2.0", "id": request_id, "result": _text(result)})
            elif method in {"resources/list", "prompts/list"}:
                key = method.split("/")[0]
                _respond({"jsonrpc": "2.0", "id": request_id, "result": {key: []}})
            else:
                _respond({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                })
        except Exception as exc:  # noqa: BLE001 - report tool errors to the client
            _respond({"jsonrpc": "2.0", "id": request_id, "result": _text(f"Error: {exc}", is_error=True)})
    return 0
