# Judging notes

A short map from the submission to the things a judge is likely to check.

## The one-sentence version

BidRoom is a working RFP-response pipeline where five Switch agents share a Mattermost room with a human bid lead, every compliance claim must cite an **approved** evidence record, and the human gate is enforced by code rather than by a prompt.

## What is live, not mocked

- A real Switch group: five agents (`scout`, `matcher`, `evidence`, `writer`, `redteam`) created from one template, bridged into two Mattermost rooms.
- Real agent turns in the room: intake (77 requirements), matrix (50/6/2/19, 68.8%), evidence queue, draft, and red-team review.
- A real workspace on disk: 54 Markdown evidence records, 77 requirements, `matrix.json`, `draft.md`, `review.json`, `report.html`, `signoff.json`.
- A signed sample report at [`docs/sample-report.html`](sample-report.html); `bidroom demo --full` reproduces the same 70/100 result in one command.
- A real CLI and MCP server, with **19 passing tests**.

## Track 01 — Best Business Workflow

| What the track asks for | Where it is |
| --- | --- |
| Agents in a real chat with teammates | Mattermost rooms `Bid: Northwind City Council` and `northwind-evidence-desk`; screenshots in `docs/screenshots/`; the demo video shows the room |
| Real work, not a toy | A 77-requirement council RFP, a 54-record evidence library, a compliance matrix, a draft with citations, a red-team review and a signed report |
| A workflow a team would actually use | The relay is explicit: scout → matcher → **human approval** → writer → redteam → **human sign-off** |
| Human-in-the-loop | Approvals and sign-off are CLI-only; the MCP surface has no approval or sign-off tool |
| Reproducible | `bidroom demo --out demo-output --force --full` rebuilds the signed 70/100 example; 19 tests; README + setup + architecture docs |

## The distinct idea

Most "AI bid writer" demos optimise the prose. BidRoom optimises the **evidence boundary**:

- The matrix is the primary artifact; the draft is downstream.
- A gap is a first-class result with a named owner, not a prompt failure.
- Approval is a named, dated, noted human act.
- Sign-off hashes the approved library; later edits mark the signature **stale**.
- An unsupported claim is a blocker, and `review --strict` exits non-zero.

That is the difference between a demo that writes well and a workflow a bid team can defend in an audit.

## Numbers to check

```text
Baseline   50 compliant · 6 partial · 2 needs-approval · 19 gap · 68.8% · score 55
After      57 compliant · 6 partial · 2 needs-approval · 12 gap · 77.9% · score 70
Evidence   54 total · 52 approved · 2 unapproved · 0 stale
Blockers   0
Sign-off   approved-with-accepted-gaps, 12 accepted gaps, evidence digest recorded
```

The two unapproved records are deliberate: `E-DEL-07` (AI search pilot, evaluation incomplete) and `E-DEL-08` (delegated access, legal review pending). A demo that approves everything would be less credible, not more.

## Engineering quality

- **Deterministic engine.** No LLM in the scoring path; the same inputs produce the same matrix and score.
- **Conservative claim splitter.** A citation covers its own sentence, not the paragraph. This is tested.
- **Import cannot smuggle approval.** A source file with `approved: true` lands unapproved.
- **Signature is scoped.** SHA-256 over the approved records; stale detection is tested.
- **CLI exit codes.** `review --strict` and `signoff` fail loudly, which is what an agent or CI needs.
- **No secrets in the repo.** `.bidroom/`, `.venv/`, `demo-output/` are gitignored; the example uses `.example` domains.

## What to read first

1. `README.md` — problem, rule, Switch setup, commands, results.
2. `docs/ARCHITECTURE.md` — data model, trust boundaries, failure modes.
3. `docs/SETUP.md` — template import, model preflight, troubleshooting.
4. `switch/bidroom.template.yaml` — the five agents, two rooms, roles, documents, kickoff.
5. `src/bidroom/signoff.py` and `src/bidroom/review.py` — the two places the invariants live.

## Honest limitations

- Matching is lexical with qualifier penalties, not semantic. It is a triage tool, not a judge.
- The example evidence is fictional but realistic; the engine does not verify that a source is genuine. It makes approval named, dated and visible instead.
- The Mattermost bridge logs non-fatal `Invalid RootId` errors for tool-activity posts. The main room is unaffected.
- A newly created OpenCode agent can inherit a model that cannot call tools. `docs/SETUP.md` documents the preflight; a template-level model field would remove the footgun.
