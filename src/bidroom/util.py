from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "between", "both",
    "but", "by", "can", "could", "did", "do", "does", "doing", "done", "during",
    "each", "either", "else", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "may",
    "me", "might", "more", "most", "must", "my", "myself", "no", "nor", "not",
    "now", "of", "off", "on", "once", "only", "or", "other", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "will", "with", "would", "you",
    "your", "yours", "yourself", "yourselves", "shall", "required", "require",
    "requires", "including", "include", "includes", "provide", "provided",
    "provides", "supplier", "suppliers", "solution", "solutions", "organisation",
    "organization", "contracting", "authority", "bidder", "bid", "tender",
    "tenderer", "applicant", "proposal", "response", "responses", "contract",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def slugify(text: str) -> str:
    text = norm_ws(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def tokenize(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9][a-z0-9+#.%/-]*", (text or "").lower())
    out: list[str] = []
    for token in raw:
        token = token.strip(".-/")
        if len(token) < 2 or token in STOPWORDS:
            continue
        # Light plural folding keeps matching forgiving without a stemmer.
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("es") and token[:-2].endswith(("s", "x", "z", "ch", "sh")):
            token = token[:-2]
        elif len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        out.append(token)
    return out


def token_set(text: str) -> set[str]:
    return set(tokenize(text))


def split_sentences(text: str) -> list[str]:
    text = norm_ws(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9@])", text)
    return [p.strip() for p in parts if p.strip()]


def read_text(path: Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt", ".rst"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Reading PDFs needs the extra: pip install 'bidroom[pdf]'") from exc
        reader = PdfReader(str(path))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if suffix == ".docx":
        try:
            import docx  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Reading DOCX needs the extra: pip install 'bidroom[docx]'") from exc
        document = docx.Document(str(path))
        chunks: list[str] = []
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                chunks.append(paragraph.text)
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                chunks.append(" | ".join(cells))
        return "\n".join(chunks)
    raise RuntimeError(f"Unsupported document type: {suffix or '(none)'}")


def write_json(path: Path, data: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_json(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_date(value: str) -> date | None:
    if not value:
        return None
    value = norm_ws(value)
    value = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", value, flags=re.I)
    for fmt in (
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y",
        "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
    ):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    match = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})", value)
    if match:
        return parse_date(f"{match.group(1)} {match.group(2)} {match.group(3)}")
    return None


def days_until(value: str | date | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = parse_date(value)
    if value is None:
        return None
    return (value - date.today()).days


def human_date(value: str | date | None) -> str:
    if value is None:
        return "not stated"
    if isinstance(value, str):
        parsed = parse_date(value)
        if parsed:
            value = parsed
    if isinstance(value, date):
        return value.strftime("%d %b %Y")
    return str(value)


def truncate(text: str, length: int = 160) -> str:
    text = norm_ws(text)
    if len(text) <= length:
        return text
    return text[: length - 1].rsplit(" ", 1)[0] + "…"


def escape_md_cell(text: str) -> str:
    return norm_ws(text).replace("|", "\\|")
