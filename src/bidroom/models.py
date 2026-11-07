from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Requirement:
    id: str
    text: str
    section: str
    section_path: str
    kind: str
    category: str
    source_line: int
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Requirement":
        return cls(**data)


@dataclass
class Evidence:
    id: str
    title: str
    claim: str
    body: str
    tags: list[str]
    categories: list[str]
    approved: bool
    owner: str
    last_verified: str
    source: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(**data)


@dataclass
class RFP:
    title: str
    client: str
    reference: str
    due_date: str
    source: str
    ingested_at: str
    text: str
    requirements: list[Requirement] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RFP":
        data = dict(data)
        data["requirements"] = [Requirement.from_dict(r) for r in data.get("requirements", [])]
        return cls(**data)


@dataclass
class EvidenceRef:
    id: str
    title: str
    score: float
    approved: bool


@dataclass
class MatrixRow:
    requirement_id: str
    text: str
    section: str
    kind: str
    category: str
    status: str
    score: float
    evidence: list[EvidenceRef]
    owner: str
    action: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = [asdict(e) for e in self.evidence]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MatrixRow":
        data = dict(data)
        data["evidence"] = [EvidenceRef(**e) for e in data.get("evidence", [])]
        return cls(**data)


@dataclass
class Matrix:
    client: str
    reference: str
    due_date: str
    generated_at: str
    rows: list[MatrixRow]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "client": self.client,
            "reference": self.reference,
            "due_date": self.due_date,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "rows": [r.to_dict() for r in self.rows],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Matrix":
        rows = [MatrixRow.from_dict(r) for r in data.get("rows", [])]
        return cls(
            client=data.get("client", ""),
            reference=data.get("reference", ""),
            due_date=data.get("due_date", ""),
            generated_at=data.get("generated_at", ""),
            rows=rows,
            summary=data.get("summary", {}),
        )


@dataclass
class Finding:
    id: str
    severity: str
    kind: str
    message: str
    requirement_id: str = ""
    location: str = ""
    evidence_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Finding":
        return cls(**data)


@dataclass
class Review:
    generated_at: str
    score: int
    findings: list[Finding]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "score": self.score,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Review":
        return cls(
            generated_at=data.get("generated_at", ""),
            score=int(data.get("score", 0)),
            findings=[Finding.from_dict(f) for f in data.get("findings", [])],
            summary=data.get("summary", {}),
        )
