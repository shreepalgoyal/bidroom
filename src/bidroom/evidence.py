from __future__ import annotations

import hashlib
import math
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .models import Evidence
from .util import norm_ws, now_iso, parse_date, today_iso, tokenize, truncate

REQUIRED_FIELDS = ("id", "title")

# A requirement that names a product, standard or protocol should not be
# "answered" by evidence that never mentions it. These patterns catch tokens
# such as IDOX, ISO/IEC, IPv6, WCAG, SAML and AES-256.
QUALIFIER = re.compile(
    r"\b(?:[A-Z]{2,}(?:[/.-][A-Z0-9]+)*|[A-Za-z]+\d+[A-Za-z0-9]*)\b"
)

# Named commitments that need their own proof, not a nearby generic record.
DISTINCTIVE_PHRASES = (
    "open government licence",
    "open-data extract",
    "assisted-digital",
    "gainshare",
    "digital skills workshops",
    "e-tendering portal",
    "pricing schedule",
    "signed declaration",
    "executive summary",
    "iso/iec 27001",
    "idox",
    "internet protocol version 6",
    "public sector bodies accessibility regulations",
    "cyber essentials plus",
)


@dataclass
class EvidenceIssue:
    severity: str
    evidence_id: str
    message: str
    path: str = ""


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            end = index
            break
    if end is None:
        return {}, text
    raw = "\n".join(lines[1:end])
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a mapping")
    return data, "\n".join(lines[end + 1 :]).lstrip("\n")


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def load_evidence_file(path: Path) -> Evidence:
    path = Path(path)
    data, body = _split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        raise ValueError(f"{path}: missing frontmatter field(s): {', '.join(missing)}")
    approved = data.get("approved", False)
    if isinstance(approved, str):
        approved = approved.strip().lower() in {"true", "yes", "1", "approved"}
    paragraphs = [norm_ws(block) for block in re.split(r"\n\s*\n", body) if block.strip()]
    claim = norm_ws(str(data.get("claim", ""))) or (paragraphs[0] if paragraphs else "")
    return Evidence(
        id=str(data["id"]).strip(),
        title=str(data["title"]).strip(),
        claim=claim,
        body=body.strip(),
        tags=_as_list(data.get("tags")),
        categories=_as_list(data.get("categories")),
        approved=bool(approved),
        owner=str(data.get("owner", "")).strip(),
        last_verified=str(data.get("last_verified", "")).strip(),
        source=str(data.get("source", "")).strip(),
        path=str(path),
    )


def load_evidence(path: Path) -> list[Evidence]:
    path = Path(path)
    if not path.exists():
        return []
    files = sorted(path.rglob("*.md")) if path.is_dir() else [path]
    evidence: list[Evidence] = []
    seen: dict[str, str] = {}
    for file in files:
        item = load_evidence_file(file)
        if item.id in seen:
            raise ValueError(f"Duplicate evidence id {item.id}: {seen[item.id]} and {file}")
        seen[item.id] = str(file)
        evidence.append(item)
    return evidence


def _replace_frontmatter(text: str, data: dict) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Evidence file has no YAML frontmatter to update.")
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() in {"---", "..."}:
            end = index
            break
    if end is None:
        raise ValueError("Evidence frontmatter is not closed with ---.")
    body = "\n".join(lines[end + 1 :]).lstrip("\n").rstrip()
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{rendered}\n---\n\n{body}\n"


def find_evidence_path(path: Path, evidence_id: str) -> Path:
    """Find the file whose frontmatter id matches, case-insensitively."""
    path = Path(path)
    if path.is_file():
        candidates = [path]
    elif path.is_dir():
        candidates = sorted(path.rglob("*.md"))
    else:
        raise ValueError(f"No evidence directory at {path}")
    wanted = evidence_id.strip().lower()
    for file in candidates:
        data, _ = _split_frontmatter(file.read_text(encoding="utf-8", errors="replace"))
        if str(data.get("id", "")).strip().lower() == wanted:
            return file
    raise ValueError(f"No evidence record with id {evidence_id} under {path}")


def set_approval(
    path: Path,
    approved: bool,
    by: str,
    note: str = "",
    evidence_id: str | None = None,
) -> Evidence:
    """Approve or revoke one record. Approval requires a named human."""
    by = norm_ws(by)
    note = norm_ws(note)
    if not by:
        raise ValueError("Approval needs a named approver (--by). An agent cannot approve its own evidence.")
    file = find_evidence_path(path, evidence_id) if evidence_id else Path(path)
    text = file.read_text(encoding="utf-8", errors="replace")
    data, _ = _split_frontmatter(text)
    if not data:
        raise ValueError(f"{file} has no frontmatter to update.")
    data["approved"] = bool(approved)
    if approved:
        data["approved_by"] = by
        data["approved_at"] = today_iso()
        if note:
            data["approval_note"] = note
    else:
        data["approved_by"] = ""
        data["approved_at"] = ""
        data["approval_note"] = note or "Approval revoked."
    file.write_text(_replace_frontmatter(text, data), encoding="utf-8")
    return load_evidence_file(file)


def import_evidence(
    source: Path,
    destination: Path,
    approve: bool = False,
    force: bool = False,
) -> list[tuple[str, Path, bool]]:
    """Copy Markdown evidence into the library.

    Imported records land unapproved unless `approve` is set, so the evidence
    owner still has to read and approve each one before it can support a claim.
    """
    source = Path(source).expanduser()
    destination = Path(destination).expanduser()
    if not source.exists():
        raise ValueError(f"No such evidence source: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    files = sorted(source.rglob("*.md")) if source.is_dir() else [source]
    if not files:
        raise ValueError(f"No Markdown evidence files in {source}")
    existing = {
        item.id.lower(): item for item in load_evidence(destination)
    }
    imported: list[tuple[str, Path, bool]] = []
    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        data, _ = _split_frontmatter(text)
        if not data.get("id") or not data.get("title"):
            raise ValueError(f"{file}: missing id or title in frontmatter")
        evidence_id = str(data["id"]).strip()
        key = evidence_id.lower()
        if key in existing and not force:
            raise ValueError(
                f"{evidence_id} already exists at {existing[key].path}. "
                "Use --force to replace the record (approval resets to pending)."
            )
        if not approve:
            data["approved"] = False
            data.pop("approved_by", None)
            data.pop("approved_at", None)
            data.pop("approval_note", None)
        target = destination / f"{key}.md"
        target.write_text(_replace_frontmatter(text, data), encoding="utf-8")
        item = load_evidence_file(target)
        existing[key] = item
        imported.append((item.id, target, item.approved))
    return imported


def evidence_digest(evidence: list[Evidence]) -> str:
    """Stable fingerprint of the evidence library used for sign-off."""
    digest = hashlib.sha256()
    for item in sorted(evidence, key=lambda e: e.id):
        digest.update(item.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.title.encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.claim.encode("utf-8"))
        digest.update(b"\0")
        digest.update(b"approved" if item.approved else b"pending")
        digest.update(b"\0")
        digest.update(item.last_verified.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def lint_evidence(evidence: list[Evidence], stale_days: int = 365) -> list[EvidenceIssue]:
    issues: list[EvidenceIssue] = []
    today = date.today()
    for item in evidence:
        if not item.tags:
            issues.append(EvidenceIssue("medium", item.id, "No tags; matching will be weak.", item.path))
        if not item.claim:
            issues.append(EvidenceIssue("high", item.id, "No claim; the writer has nothing to cite.", item.path))
        if not item.source:
            issues.append(EvidenceIssue("medium", item.id, "No source; a reviewer cannot verify it.", item.path))
        if not item.last_verified:
            issues.append(EvidenceIssue("medium", item.id, "No last_verified date.", item.path))
        else:
            verified = parse_date(item.last_verified)
            if not verified:
                issues.append(EvidenceIssue("medium", item.id, f"Unparseable last_verified: {item.last_verified}", item.path))
            elif (today - verified).days > stale_days:
                issues.append(
                    EvidenceIssue(
                        "high",
                        item.id,
                        f"Evidence is {(today - verified).days} days old; re-verify before submission.",
                        item.path,
                    )
                )
        if not item.approved:
            issues.append(EvidenceIssue("info", item.id, "Not approved; it cannot support a compliance claim yet.", item.path))
    return issues


def _has_word(haystack: str, needle: str) -> bool:
    return re.search(
        rf"(?<![a-z0-9]){re.escape(needle.lower())}(?![a-z0-9])",
        haystack,
    ) is not None


def _missing_qualifiers(requirement_text: str, item: Evidence) -> list[str]:
    haystack = " ".join(
        [item.title, item.claim, item.body, " ".join(item.tags), " ".join(item.categories)]
    ).lower()
    missing: list[str] = []
    for match in QUALIFIER.finditer(requirement_text):
        token = match.group(0)
        if not _has_word(haystack, token):
            missing.append(token)
    lowered = requirement_text.lower()
    for phrase in DISTINCTIVE_PHRASES:
        if phrase in lowered and phrase not in haystack:
            missing.append(phrase)
    return missing


class EvidenceIndex:
    def __init__(self, evidence: list[Evidence]):
        self.evidence = evidence
        self._tokens: dict[str, set[str]] = {}
        self._tag_tokens: dict[str, set[str]] = {}
        document_frequency: Counter[str] = Counter()
        for item in evidence:
            tokens = set(tokenize(" ".join([item.title, item.claim, item.body])))
            tag_tokens = set(tokenize(" ".join(item.tags + item.categories)))
            self._tokens[item.id] = tokens
            self._tag_tokens[item.id] = tag_tokens
            for token in tokens | tag_tokens:
                document_frequency[token] += 1
        total = max(len(evidence), 1)
        self._weight = {
            token: math.log((total + 1) / (frequency + 1)) + 1.0
            for token, frequency in document_frequency.items()
        }
        self._default_weight = math.log(total + 1) + 1.0

    def _weight_for(self, token: str) -> float:
        return self._weight.get(token, self._default_weight)

    def score(self, requirement_text: str, category: str, item: Evidence) -> float:
        req_tokens = set(tokenize(requirement_text))
        if not req_tokens:
            return 0.0
        ev_tokens = self._tokens[item.id]
        tag_tokens = self._tag_tokens[item.id]
        denominator = sum(self._weight_for(token) for token in req_tokens) or 1.0
        overlap_tokens = req_tokens & ev_tokens
        tag_overlap_tokens = req_tokens & tag_tokens
        overlap = sum(self._weight_for(token) for token in overlap_tokens) / denominator
        tag_overlap = sum(self._weight_for(token) for token in tag_overlap_tokens) / denominator
        category_match = 1.0 if category in item.categories or category in item.tags else 0.0
        bonus = 0.0
        lowered = requirement_text.lower()
        for tag in item.tags:
            if " " in tag and tag.lower() in lowered:
                bonus = 0.08
                break
        score = 0.55 * overlap + 0.30 * tag_overlap + 0.15 * category_match + bonus
        if len(overlap_tokens) < 2:
            score *= 0.55
        if _missing_qualifiers(requirement_text, item):
            # A named standard or product is absent from this record. It may
            # still be a useful related record, but it is not proof.
            score *= 0.30
        return round(min(score, 1.0), 4)

    def search(self, requirement_text: str, category: str, limit: int = 3) -> list[tuple[Evidence, float]]:
        scored = [(item, self.score(requirement_text, category, item)) for item in self.evidence]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [(item, score) for item, score in scored[:limit] if score > 0.02]


def evidence_summary(evidence: list[Evidence]) -> dict[str, int]:
    return {
        "total": len(evidence),
        "approved": sum(1 for item in evidence if item.approved),
        "unapproved": sum(1 for item in evidence if not item.approved),
        "stale": sum(
            1
            for item in evidence
            if item.last_verified
            and (parsed := parse_date(item.last_verified))
            and (date.today() - parsed).days > 365
        ),
    }


def describe(item: Evidence, length: int = 120) -> str:
    return f"{item.id} — {item.title}: {truncate(item.claim, length)}"
