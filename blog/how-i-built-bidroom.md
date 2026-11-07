# How I built BidRoom: five AI agents, one bid, and a human who has to sign

*A public-sector RFP is not a writing problem. It is an evidence problem.*

**Demo:** [2:04 walkthrough](https://youtu.be/0KTzrEUJdoU) · **Code:** [github.com/shreepalgoyal/bidroom](https://github.com/shreepalgoyal/bidroom) · **Signed report:** [sample-report.html](https://github.com/shreepalgoyal/bidroom/blob/main/docs/sample-report.html)

---

## The failure mode nobody demos

Every AI writing tool looks good on an RFP. Give it a 90-page tender and it will return fluent, confident prose in seconds. That is exactly the problem.

A bid team has four weeks, hundreds of requirements, and a library of case studies that may or may not prove what the sales team wants to say. The dangerous failure is not a missing answer. It is an answer that sounds true, cites the wrong proof, and gets discovered after award. The bid is lost, the contract is challenged, and the team cannot reconstruct why the claim was made.

Generic AI makes this worse because it optimises for prose. A language model will happily turn a SOC 2 report into an answer for an ISO/IEC 27001 requirement, because both are "security certifications". They are not the same thing.

So I built BidRoom around a different rule:

> Every compliance claim must cite an **approved** evidence record. Agents can propose evidence. Only a named human can approve it, and only the bid lead can sign the submission.

That single constraint changes the shape of the whole workflow. Gaps stop being embarrassing and become first-class objects with owners. Approval stops being a chat reaction and becomes an auditable act. And the final artifact is not a document — it is a compliance matrix you can defend in a bid review.

## The room

BidRoom is built on [Switch](https://www.switchagents.ai), with OpenCode as the agent runtime and the Mattermost rooms that Switch provisions as the shared workspace.

One Switch template (`switch/bidroom.template.yaml`) creates:

- **Five agents** — `scout`, `matcher`, `evidence`, `writer`, `redteam` — each with its own role prompt and tool access.
- **Two linked rooms** — `Bid: Northwind City Council` for the client workflow, and `northwind-evidence-desk` for evidence review.
- **The runbook, the relay rules, and a kickoff message**, so the room explains itself to a new member.

The agents share one checkout, so `.bidroom/` on disk is the only shared state. Switch provides the identities, the rooms and the relay. Without it there is no room, no agent identity, and no place for the human gate to live.

The relay is explicit and one-directional:

```
scout → matcher → human approval → writer → redteam → human sign-off
```

Agents never approve evidence and never sign. The runbook says so, and the CLI refuses to pretend otherwise.

## The pipeline

**Scout** reads the RFP and extracts the requirement register. On the bundled Northwind City Council tender (`NCC-2026-114`, a resident services portal) that is 77 requirements: 65 mandatory, 12 scored. It also names the five hardest mandatory items so the bid lead knows where to spend the week.

**Matcher** scores every requirement against the evidence library. Matching is token overlap over requirement text, tags and categories, with **qualifier penalties**. If a requirement names a standard or product — ISO/IEC 27001, IDOX, IPv6, WCAG, PSBAR, Open Government Licence — and the record does not name it, the score is penalised. That is what stops a SOC 2 record from answering an ISO/IEC 27001 question.

**Evidence** turns gaps into reviewable Markdown records with frontmatter: id, claim, tags, categories, owner, last verified, source, approval state. It posts the approval queue to the room. This is the only agent that touches the evidence library, and it can only add records in an unapproved state.

**Writer** drafts only from approved records. Every claim carries a citation. A gap stays a gap, with an owner and a next action. No record, no sentence.

**Redteam** re-reads the draft against the library. Unsupported claims become blockers, not style notes. It also reports the readiness score, so the bid lead sees the difference between "the prose is good" and "the bid is defensible".

## The human gate is code, not a prompt

This is the part I cared most about.

Approval is a CLI command with a required `--by` name:

```bash
bidroom evidence approve E-DEL-09 \
  --by "Priya Raman" \
  --note "Checked Delivery report v4 section 3: top-20 transactions complete end to end."
```

Sign-off is another:

```bash
bidroom signoff --by "Priya Raman" \
  --note "Reviewed the matrix, draft and red-team findings." \
  --accept-gaps
```

`--accept-gaps` is not a bypass. It requires a written reason, and the report lists every accepted gap by id. The signature pins the approved evidence library with a SHA-256 digest. If anyone edits an approved record afterwards, the report marks the signature **stale**. The MCP server deliberately exposes no approval or sign-off tool, so an agent cannot approve its own evidence even if it is talked into trying.

That is the whole product thesis: the interesting work is not generating text. It is deciding what counts as proof, and who is allowed to say so.

## The numbers

The bundled example is a synthetic but realistic UK local-government RFP. It ships with 54 evidence records.

| | Baseline | After six human approvals |
| --- | --- | --- |
| Compliant | 50 | **57** |
| Partial | 6 | 6 |
| Needs approval | 2 | 2 |
| Gap | 19 | **12** |
| Coverage | 68.8% | **77.9%** |
| Approved evidence | 46 | **52** |
| Readiness | 55/100 | **70/100** |
| Blockers | 19 | **0** |

The six records that closed gaps were real, reviewable files: the top-20 transactions journey, the single digital front door, the IDOX Uniform integration, a 60k-user load test, the assisted-digital route, and the open-data extract. They were imported **unapproved** on purpose, so the human step is visible.

Two records stayed unapproved on purpose too: the AI search pilot is still in sandbox, and the delegated-access consent wording is in legal review. A demo that approves everything is not a demo of a gate.

Eight mandatory gaps remain, each with an owner and a disclosed next step: ISO/IEC 27001 certification, UK GDPR/DPA/PSBAR evidence, IPv6, digital-skills workshops, gainshare, and the submission/commercial items the council has not answered yet. The report shows them. That is the point.

## What surprised me

**Qualifier penalties did more for trust than any prompt.** The first version of the matcher was generous. It matched "security certification" to "security certification" and produced a beautiful, wrong matrix. Adding named-standard penalties turned the matrix into something a bid lead would actually challenge.

**Gaps are a feature, not a failure state.** Once a gap had an owner and a next action, the room stopped arguing about prose and started closing evidence. The matrix became the product.

**The human gate needs a scripted replay.** Judges and reviewers should not have to approve six records by hand to see the signed result. `bidroom demo --full` replays the human's part — imports the six records, records the approvals by name, drafts, reviews, and signs — and lands on the same 57/6/2/12, 77.9%, 70/100, zero blockers. The gate is still the same CLI command. The demo just makes it reproducible in one command.

**The agents are most useful before the prose.** Scout and matcher did the work I would have spent two days on. Writer was fast but only trustworthy because the evidence layer existed first.

## Run it

```bash
git clone https://github.com/shreepalgoyal/bidroom.git
cd bidroom
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Full replay: baseline, six human approvals, draft, red team, sign-off
.venv/bin/bidroom demo --out demo-output --force --full

# Baseline only
.venv/bin/bidroom demo --out demo-baseline --force
```

To run the real room, import `switch/bidroom.template.yaml` in Switch Console → Templates, set `directory` to the shared checkout and `repo_url` to your fork, and create the group. The full setup, including the OpenCode version note and Mattermost troubleshooting, is in [`docs/SETUP.md`](https://github.com/shreepalgoyal/bidroom/blob/main/docs/SETUP.md).

There are 19 tests, including one end-to-end test that runs the full demo and asserts the signed result. No API key is needed for the example.

## What I would build next

- **Evidence expiry.** `last_verified` exists but nothing forces a re-check before a bid. A stale library should block sign-off, not just warn.
- **Per-claim provenance.** The report pins the library digest; the next step is a per-claim hash so a reviewer can trace one sentence to one record.
- **A real RFP ingest path.** The example is Markdown. Public-sector tenders arrive as PDFs, spreadsheets and portals, and that ingestion is where the next week of work goes.
- **Team roles.** One bid lead is enough for a demo. Real bids have a security reviewer, a commercial reviewer and a delivery lead, and the gate should know the difference.

---

BidRoom was built for **Flip the Switch — Track 01: Best Business Workflow**. Five agents in a real room, a real compliance matrix, a real signature, and a human who has to mean it.

*If you want to see the room instead of the prose: [2:04 demo](https://youtu.be/0KTzrEUJdoU).*
