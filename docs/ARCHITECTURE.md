# Architecture

BidRoom is a small pipeline with hard boundaries. The interesting part is not the matching algorithm; it is where the human gates sit.

```
RFP ──ingest──▶ requirements ──matrix──▶ compliance matrix ──draft──▶ draft.md
                                              │                         │
                                              │                         ▼
                                        evidence library          review.py
                                        (approved only)          blockers + score
                                              ▲                         │
                                              │                         ▼
                                     human approval             report.html
                                              │                         │
                                              └─────────────── signoff + digest
```

## Data model

### Requirement

Extracted from the RFP by `ingest.py`. Each requirement has:

- `id` (`R-001` …), `text`, `kind` (`mandatory` / `scored`), `category`
- `action` and `owner` (delivery, security, data, commercial, …)
- `source` (the section and line it came from)

The Northwind RFP produces **77 requirements: 65 mandatory, 12 scored**, across 12 categories.

### Evidence record

A Markdown file with YAML frontmatter. The fields that matter to the engine:

- `id`, `title`, `claim`
- `tags`, `categories`
- `approved` (boolean — **must be set by a human**)
- `owner`, `last_verified`, `source`
- `approved_by`, `approved_at`, `approval_note` (written by `evidence approve`)

### Matrix

`matrix.py` writes one row per requirement:

- `status`: `compliant` / `partial` / `needs-approval` / `gap`
- `evidence`: the best record and score, plus alternates
- `owner`: who must act
- `refs`: the citations the writer is allowed to use

Thresholds: **0.52** for `compliant`, **0.27** for `partial`. A record that scores below `0.27` is not proof.

Matching uses token overlap over the requirement text, tags and categories, with **qualifier penalties**. If the requirement names a standard or product (`ISO/IEC 27001`, `IDOX`, `IPv6`, `WCAG`, `PSBAR`, `Open Government Licence`) and the record does not name it, the score is penalised. This is what stops a SOC 2 record from answering an ISO/IEC 27001 requirement.

### Draft

`draft.py` writes `draft.md` from the matrix. It only cites records whose `approved` flag is true. A gap is written as `[[GAP: R-036 — ISO/IEC 27001 certification — owner: security]]`, not as prose.

### Review

`review.py` re-reads the draft **and the evidence library** and produces findings:

- `blocker`: a claim with no citation, a citation to an unapproved record, or a citation that does not prove the sentence
- `high` / `medium`: partial proof, stale evidence, weak owner coverage
- readiness score, anchored to coverage and blockers

The claim splitter is deliberately conservative. A sentence that follows a citation is a **new claim**, not part of the cited one. This prevents the classic failure where one citation appears to cover a whole paragraph.

`--strict` exits 1 on any blocker. That is what the red-team agent runs.

### Sign-off

`signoff.py` stores a signature record:

```json
{
  "decision": "approved-with-accepted-gaps",
  "client": "Northwind City Council",
  "reference": "NCC-2026-114",
  "signed_by": "Shreepal Goyal",
  "signed_at": "2026-11-06T...",
  "note": "Reviewed the matrix and draft.",
  "readiness_score": 70,
  "coverage_pct": 77.9,
  "accepted_gap_ids": ["R-036", "R-042"],
  "evidence": {
    "total": 54,
    "approved": 52,
    "unapproved": 2,
    "stale": 0,
    "digest": "sha256:..."
  }
}
```

Refusal rules:

1. Any blocker → refuse.
2. Open gaps without `--accept-gaps` → refuse.
3. `--accept-gaps` without a note of at least 20 characters → refuse.
4. Missing signer name → refuse.

`evidence_digest()` hashes the canonical bytes of every **approved** record (id, claim, source, body). `signoff_state()` recomputes it. If it differs, the signature is **stale** — the report says so and `status` says so.

## Module map

| Module | Responsibility | Key invariant |
| --- | --- | --- |
| `util.py` | paths, frontmatter, atomic writes, digest helpers | one workspace, one source of truth |
| `models.py` | `RFP`, `Requirement`, `Evidence`, `MatrixRow` | serialisable to JSON |
| `ingest.py` | RFP parsing and categorisation | every requirement has an id and an owner |
| `evidence.py` | load/lint/search/approve/import/digest | import always lands unapproved |
| `matrix.py` | match and classify | no unapproved record is "compliant" |
| `draft.py` | write the response | citations only from approved records |
| `review.py` | claim split, findings, score | unsupported claim → blocker |
| `signoff.py` | signature, refusal, staleness | digest covers the approved library |
| `report.py` | HTML report | every gap has an owner |
| `cli.py` | command surface | approval/sign-off are human commands |
| `mcp_server.py` | stdio MCP tools | no approval or sign-off tool |

## Trust boundaries

- **The agent is untrusted.** It can read the workspace and run the CLI, but the CLI's approval and sign-off commands require a human-supplied `--by` and are not exposed over MCP.
- **The source file is untrusted.** Importing evidence from a folder strips any `approved: true` in the source and writes `approved: false`.
- **The draft is untrusted.** The review re-derives citations from the evidence library rather than trusting the draft's own claim of approval.
- **The signature is scoped.** It covers the approved library at the moment of signing. Any later change makes it stale rather than silently valid.

## Failure modes the design accepts

- **A human can still approve bad evidence.** The engine cannot tell whether a source is genuine. It can make the approval named, dated, noted and visible.
- **A human can accept gaps.** The engine requires an explicit flag and a written reason; it does not pretend the gaps are closed.
- **Matching is lexical, not semantic.** Qualifier penalties reduce false positives but do not eliminate them. The matrix is a triage tool, not a judge.
- **The report is a snapshot.** It is regenerated; the signed record and digest are the durable artifacts.

## Extension points

- Add a parser for another RFP format in `ingest.py`.
- Add a scoring strategy in `matrix.py` (embeddings, BM25) behind the same `status` contract.
- Add an approval UI on top of `evidence approve` — the CLI contract is already there.
- Add a connector that publishes the report to a bid portal; keep sign-off out of it.
