from __future__ import annotations

import re
from pathlib import Path

from .models import RFP, Requirement
from .util import norm_ws, now_iso, parse_date, read_text, split_sentences, token_set

STRONG_MODAL = re.compile(
    r"\b(shall|must|is required to|are required to|is expected to|are expected to|"
    r"will be required|mandatory|needs? to)\b",
    re.I,
)
WEAK_MODAL = re.compile(r"\b(should|will|may|preferred|desirable|advantageous)\b", re.I)
REQUIREMENT_SECTION = re.compile(
    r"requirement|scope|objective|functional|technical|security|compliance|accessib|"
    r"support|service|implementation|social value|commercial|submission|evaluation|"
    r"deliverable|data|integration|performance|hosting|training|exit|safeguard|"
    r"insurance|pricing|cost|staffing|experience",
    re.I,
)
ACTION_VERBS = re.compile(
    r"\b(provide|support|comply|meet|ensure|deliver|integrate|migrate|train|maintain|"
    r"achieve|demonstrate|hold|implement|supply|offer|enable|allow|report|retain|"
    r"protect|test|document|include|operate|host|manage|respond|resolve|escalate|"
    r"publish|expose|adhere|align|certify|replace|reduce|increase|improve|measure|"
    r"monitor|audit|backup|recover|scale|secure|encrypt|authenticate|authorise|"
    r"authorize|register|notify|schedule|track|route|search|translate|personalise|"
    r"personalize)\b",
    re.I,
)

CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("security", [
        "security", "cyber", "iso 27001", "iso27001", "iso/iec", "27001", "soc 2",
        "soc2", "penetration", "vulnerability", "encryption", "encrypt", "encrypted",
        "breach", "gdpr", "data protection", "mfa", "multi-factor", "access control",
        "cyber essentials", "confidentiality", "incident reporting", "threat", "malware",
        "firewall", "siem", "least privilege", "data processing agreement",
        "processing activities", "subject access", "role-based", "roles", "administrator",
        "administrative",
    ]),
    ("accessibility", [
        "accessibility", "accessible", "wcag", "screen reader", "assistive", "disability",
        "inclusive", "aria", "keyboard", "contrast", "translation", "translated",
        "multilingual", "welsh", "polish", "urdu", "romanian", "easy read",
        "neurodiverse", "caption", "switch access", "plain english", "reading age",
        "assisted digital", "assisted-digital", "vpat",
    ]),
    ("hosting", [
        "cloud", "hosting", "hosted", "availability", "uptime", "disaster recovery",
        "backup", "rto", "rpo", "data centre", "data center", "data residency",
        "resilience", "resilient", "infrastructure", "scalable", "scalability", "scale",
        "performance", "latency", "load", "capacity", "redundan", "business continuity",
        "99.", "sla", "status page", "concurrent", "traffic", "united kingdom",
    ]),
    ("integration", [
        "integrate", "integration", "integrated", "api", "sso", "single sign-on", "saml",
        "oidc", "payment", "gov.uk pay", "stripe", "crm", "erp", "webhook", "data feed",
        "interoperable", "interoperability", "open standard", "idox", "socitm",
        "nhs login", "one login", "one-time passcode", "otp", "delegated access",
        "ipv6", "internet protocol version 6", "identity",
    ]),
    ("data", [
        "reporting", "analytics", "dashboard", "migration", "retention", "anonymise",
        "anonymised", "anonymize", "anonymized", "dataset", "warehouse", "etl",
        "quality", "open data", "audit trail", "audit log", "logs", "extract",
        "history", "archive",
    ]),
    ("support", [
        "service desk", "service level", "24/7", "24x7", "response time",
        "resolution", "escalation", "maintenance", "training", "onboarding", "exit",
        "transition", "hypercare", "runbook", "knowledge base", "p1", "severity",
        "service report",
    ]),
    ("experience", [
        "experience", "case study", "reference", "similar", "track record",
        "public sector", "local authority", "testimonial", "portfolio",
        "past performance", "previous",
    ]),
    ("delivery", [
        "implementation", "mobilisation", "mobilization", "project plan", "timeline",
        "governance", "agile", "team", "staffing", "cv", "resource", "milestone",
        "workstream", "programme", "program", "delivery", "kick-off", "kickoff",
        "go live", "go-live", "forms", "form builder", "publish", "named",
        "case management", "notification", "notifications", "sms", "email",
        "catalogue", "search", "ai-assisted", "transactions", "digital front door",
        "front door",
    ]),
    ("social", [
        "social value", "apprenticeship", "apprenticeships", "local", "carbon",
        "sustainable", "sustainability", "equality", "diversity", "community",
        "environment", "net zero", "living wage", "sme",
    ]),
    ("commercial", [
        "price", "priced", "pricing", "cost", "fixed", "insurance", "liability",
        "payment terms", "indemnity", "warrant", "bond", "discount", "rate card",
        "budget", "value for money", "invoice", "tax", "breakdown",
    ]),
    ("submission", [
        "submission", "format", "page limit", "portal", "deadline", "clarification",
        "signature", "certificate", "annex", "appendix", "question", "declaration",
        "tender return", "upload", "executive summary", "mandatory requirement",
        "compliant", "pages",
    ]),
]

SKIP_SECTIONS = re.compile(
    r"\b(introduction|background|context|questions and clarifications|"
    r"evaluation criteria|about us)\b",
    re.I,
)


def _keyword_hit(keyword: str, lowered: str) -> bool:
    """Match a keyword as a word, not as a fragment of a longer word."""
    if re.search(r"[^a-z0-9]", keyword):
        return keyword in lowered
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", lowered) is not None

OWNER_BY_CATEGORY = {
    "security": "Security lead",
    "accessibility": "Design lead",
    "hosting": "Platform lead",
    "integration": "Engineering lead",
    "data": "Data lead",
    "support": "Service lead",
    "experience": "Delivery lead",
    "delivery": "Programme lead",
    "social": "ESG lead",
    "commercial": "Commercial lead",
    "submission": "Bid lead",
    "other": "Bid lead",
}

ACTION_BY_CATEGORY = {
    "security": "Attach the certificate or report, or state the subcontractor and their evidence.",
    "accessibility": "Attach the audit or user-testing report, including the date and standard tested.",
    "hosting": "Provide the architecture, availability figure and DR test result.",
    "integration": "Name the endpoint, standard and a reference deployment.",
    "data": "Provide the data flow, retention schedule and a sample report.",
    "support": "Provide the SLA table and a sample monthly service report.",
    "experience": "Supply a comparable reference with contactable details and outcomes.",
    "delivery": "Supply the mobilisation plan, named roles and dates.",
    "social": "Quantify the commitment and name the measurement method.",
    "commercial": "Confirm the commercial position and attach the policy or certificate.",
    "submission": "Check the submission instructions and assign an owner.",
    "other": "Decide whether to comply, partially comply or bid no-bid, and record why.",
}


def _strip_markdown(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`>#]+", "", text)
    text = norm_ws(text)
    return text


def _headings(text: str) -> list[tuple[int, str, int]]:
    found: list[tuple[int, str, int]] = []
    for index, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if match:
            found.append((len(match.group(1)), _strip_markdown(match.group(2)), index))
    return found


def _section_paths(text: str) -> dict[int, tuple[str, str]]:
    """Map a line number to (leaf heading, full path)."""
    headings = _headings(text)
    stack: list[tuple[int, str]] = []
    mapping: dict[int, tuple[str, str]] = {}
    for level, title, line_no in headings:
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        path = " > ".join(title for _, title in stack)
        mapping[line_no] = (title, path)
    # Fill gaps: every line inherits the most recent heading.
    result: dict[int, tuple[str, str]] = {}
    current = ("", "")
    ordered = sorted(mapping)
    heading_index = 0
    total_lines = len(text.splitlines())
    for line_no in range(1, total_lines + 1):
        while heading_index < len(ordered) and ordered[heading_index] <= line_no:
            current = mapping[ordered[heading_index]]
            heading_index += 1
        result[line_no] = current
    return result


def _classify_category(text: str) -> str:
    lowered = text.lower()
    scores: list[tuple[int, int, str]] = []
    for order, (category, keywords) in enumerate(CATEGORY_RULES):
        score = sum(1 for keyword in keywords if _keyword_hit(keyword, lowered))
        if score:
            scores.append((score, -order, category))
    if not scores:
        return "other"
    scores.sort(reverse=True)
    return scores[0][2]


def _classify_kind(text: str) -> str:
    if STRONG_MODAL.search(text):
        return "mandatory"
    if re.search(r"\b(should|preferred|desirable|advantageous|scored|evaluated)\b", text, re.I):
        return "scored"
    if re.search(r"\b(may|optional|nice to have)\b", text, re.I):
        return "optional"
    return "informational"


def _clean_requirement(text: str) -> str:
    text = _strip_markdown(text)
    text = re.sub(r"^\s*(?:[-*•]|\d+(?:\.\d+)*[.)]?|[a-zA-Z][.)])\s+", "", text)
    if not re.match(
        r"^(?:the\s+)?(?:supplier|bidder|tenderer|contractor)\s+(?:shall|must|will|should|may)\b",
        text,
        re.I,
    ):
        text = re.sub(
            r"^(?:the\s+)?(?:supplier|bidder|tenderer|contractor)\s+",
            "",
            text,
            flags=re.I,
        )
        if text:
            text = text[0].upper() + text[1:]
    text = norm_ws(text)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def _looks_like_requirement(text: str, section: str) -> tuple[bool, float]:
    clean = _clean_requirement(text)
    if len(clean) < 22 or len(clean) > 700:
        return False, 0.0
    if re.match(r"^(note|background|example|figure|table|source|see)\b", clean, re.I):
        return False, 0.0
    in_requirement_section = bool(REQUIREMENT_SECTION.search(section))
    strong = bool(STRONG_MODAL.search(clean))
    weak = bool(WEAK_MODAL.search(clean))
    action = bool(ACTION_VERBS.search(clean))
    if strong:
        return True, 0.95
    if weak and in_requirement_section:
        return True, 0.82
    if in_requirement_section and action and len(clean.split()) >= 5:
        return True, 0.64
    return False, 0.0


def _blocks(text: str) -> list[tuple[int, str]]:
    """Split into bullet, table-row and paragraph blocks with their line numbers."""
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if re.match(r"^#{1,6}\s+", stripped):
            index += 1
            continue
        bullet = re.match(r"^(\s*)(?:[-*•]|\d+(?:\.\d+)*[.)])\s+(.*)$", line)
        if bullet:
            start = index + 1
            parts = [bullet.group(2).strip()]
            index += 1
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip():
                    break
                if re.match(r"^\s*(?:[-*•]|\d+(?:\.\d+)*[.)])\s+", nxt):
                    break
                if re.match(r"^#{1,6}\s+", nxt.strip()):
                    break
                if nxt.startswith(("    ", "\t")):
                    parts.append(nxt.strip())
                    index += 1
                    continue
                break
            blocks.append((start, " ".join(parts)))
            continue
        if stripped.startswith("|"):
            start = index + 1
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            index += 1
            if all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
                continue
            blocks.append((start, " | ".join(cells)))
            continue
        start = index + 1
        parts = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not re.match(
            r"^\s*(?:[-*•]|\d+(?:\.\d+)*[.)])\s+", lines[index]
        ) and not re.match(r"^#{1,6}\s+", lines[index].strip()):
            parts.append(lines[index].strip())
            index += 1
        blocks.append((start, " ".join(parts)))
    return blocks


def _dedupe(requirements: list[Requirement]) -> list[Requirement]:
    kept: list[Requirement] = []
    seen: list[set[str]] = []
    for requirement in requirements:
        tokens = token_set(requirement.text)
        if not tokens:
            continue
        duplicate = False
        for other in seen:
            union = tokens | other
            if union and len(tokens & other) / len(union) >= 0.82:
                duplicate = True
                break
        if duplicate:
            continue
        seen.append(tokens)
        kept.append(requirement)
    return kept


def _extract_metadata(text: str, source: str) -> tuple[str, str, str, str]:
    lines = [_strip_markdown(line) for line in text.splitlines() if line.strip()]
    title = ""
    for line in text.splitlines():
        match = re.match(r"^#\s+(.*\S)\s*$", line)
        if match:
            title = _strip_markdown(match.group(1))
            break
    if not title and lines:
        title = lines[0]

    client = ""
    for line in lines[:40]:
        match = re.search(r"(?:issued by|buyer|client|contracting authority)\s*[:\-]\s*(.+)", line, re.I)
        if match:
            client = norm_ws(match.group(1)).strip(" .")
            break

    reference = ""
    for line in lines[:40]:
        match = re.search(r"(?:rfp|itt|rfq|tender|reference)\s*(?:reference|ref)?\s*[:\-]?\s*([A-Z0-9][A-Z0-9][A-Z0-9/\-]{3,})", line)
        if match:
            reference = match.group(1).strip(" .,-")
            break
    if not reference:
        match = re.search(r"\b([A-Z]{2,6}[-/]\d{4}[-/]\d{2,6})\b", text)
        if match:
            reference = match.group(1)

    due_date = ""
    for line in lines:
        if re.search(r"deadline|closing date|responses? due|submission date|due date", line, re.I):
            match = re.search(
                r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}"
                r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+20\d{2}"
                r"|20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/20\d{2})",
                line,
                re.I,
            )
            if match:
                parsed = parse_date(match.group(1))
                due_date = parsed.isoformat() if parsed else match.group(1)
                break
    if not due_date:
        match = re.search(
            r"(?:due|deadline)[^\n]{0,60}?(\d{1,2}\s+\w+\s+20\d{2}|\d{4}-\d{2}-\d{2})",
            text,
            re.I,
        )
        if match:
            parsed = parse_date(match.group(1))
            due_date = parsed.isoformat() if parsed else match.group(1)
    return title, client, reference, due_date


def parse_rfp(text: str, source: str = "pasted") -> RFP:
    title, client, reference, due_date = _extract_metadata(text, source)
    paths = _section_paths(text)
    requirements: list[Requirement] = []
    for line_no, block in _blocks(text):
        section, section_path = paths.get(line_no, ("", ""))
        if SKIP_SECTIONS.search(section):
            continue
        candidates: list[str] = []
        if re.match(r"^\S+\s*\|\s*", block) and "|" in block:
            cells = [cell.strip() for cell in block.split("|") if cell.strip()]
            # A compliance table's meaningful cell is usually the longest one.
            if cells:
                candidates.append(max(cells, key=len))
        else:
            sentences = split_sentences(block)
            if len(sentences) > 1 and any(STRONG_MODAL.search(s) for s in sentences):
                candidates.extend(s for s in sentences if STRONG_MODAL.search(s) or WEAK_MODAL.search(s))
            else:
                candidates.append(block)
        for candidate in candidates:
            ok, confidence = _looks_like_requirement(candidate, section_path)
            if not ok:
                continue
            clean = _clean_requirement(candidate)
            requirements.append(
                Requirement(
                    id="",
                    text=clean,
                    section=section,
                    section_path=section_path,
                    kind=_classify_kind(clean),
                    category=_classify_category(clean),
                    source_line=line_no,
                    confidence=confidence,
                )
            )
    requirements = _dedupe(requirements)
    for index, requirement in enumerate(requirements, start=1):
        requirement.id = f"R-{index:03d}"
    return RFP(
        title=title,
        client=client,
        reference=reference,
        due_date=due_date,
        source=str(source),
        ingested_at=now_iso(),
        text=text,
        requirements=requirements,
    )


def ingest(path: Path) -> RFP:
    path = Path(path)
    return parse_rfp(read_text(path), source=str(path))
