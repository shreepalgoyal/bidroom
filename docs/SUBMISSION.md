# Submission form — copy-paste answers

Fill this in on the Flip the Switch submission form. The video is at [`docs/bidroom-demo.mp4`](bidroom-demo.mp4); upload it to YouTube as **Unlisted** (or Loom) and paste the URL below. The repo is `https://github.com/shreepalgoyal/bidroom`.

## Upload checklist

1. Upload [`docs/bidroom-demo.mp4`](bidroom-demo.mp4) to YouTube as **Unlisted**. Title: `BidRoom — evidence-backed RFP responses with a human sign-off | Flip the Switch 2026`.
2. Use the description and chapters below. Copy the video URL into this file and the README.
3. Push the repo, then open the public URL in a private window to confirm it is visible without signing in.
4. Register / submit on the [Flip the Switch page](https://www.wemakedevs.org/hackathons/switch). Track: **Best Business Workflow**.
5. Optional: add the `#HowISwitch` post, blog post, or Wispr card in Track Details.

## Video metadata

**Title**

```
BidRoom — evidence-backed RFP responses with a human sign-off | Flip the Switch 2026
```

**Description**

```
BidRoom is a five-agent RFP workflow built on Switch, OpenCode and Mattermost for Flip the Switch 2026 (Track 01: Best Business Workflow).

Five agents — scout, matcher, evidence desk, writer and red team — share a Mattermost room with a human bid lead. Every compliance claim must cite an approved evidence record. Agents can propose evidence; only the bid lead can approve it or sign the submission. Sign-off pins the approved library with a SHA-256 digest.

On the bundled 77-requirement Northwind City Council RFP, the room moves from 50 compliant / 19 gaps (68.8%, score 55) to 57 compliant / 12 gaps (77.9%, score 70, zero blockers) after six records are reviewed and approved. Eight mandatory gaps remain visible with owners.

Repo: https://github.com/shreepalgoyal/bidroom
Template: switch/bidroom.template.yaml
Stack: Switch 0.40.1, OpenCode, Mattermost, Python

Chapters:
0:00 The problem
0:07 The rule
0:19 The bid room
0:31 Scout
0:47 Matcher
0:58 Evidence desk
1:05 The human gate
1:26 The writer
1:36 Red team
1:43 Sign-off
1:55 Report
2:00 End
```

---

## Project Details

**Project title**

```
BidRoom — evidence-backed RFP responses with a human sign-off
```

**Tracks you are submitting for**

```
Best Business Workflow
```

> Code with Wispr is automatic only if you upload the Wispr usage card in Track Details. The project does not depend on Wispr; upload the card only if you want to be considered for that track.

**Project description**

```
Public-sector bids are won or lost on evidence, not prose. A bid team has four weeks, hundreds of requirements and a library of case studies that may not prove what the sales team wants to say. The dangerous failure is not a missing answer; it is an answer that sounds true, cites the wrong proof, and is discovered after award. Generic AI writers make this worse because they optimise for fluent text, not for proof.

BidRoom is a working RFP workflow for bid teams, capture managers and subject-matter experts. Five Switch agents share a Mattermost room with a human bid lead. The scout ingests the RFP and names the riskiest mandatory items. The matcher builds a compliance matrix and gives every gap a named owner. The evidence desk turns a gap into a reviewable Markdown record. The writer drafts only from approved records and keeps citations. The red team attacks the draft and reports blockers and a readiness score.

The rule is enforced in code: every compliance claim must cite an approved evidence record. Agents can propose and import evidence, but only a named human can approve it, and only the bid lead can sign. Sign-off pins the approved library with a SHA-256 digest, so a later edit marks the signature stale. On the bundled 77-requirement Northwind City Council RFP, the room moves from 50 compliant / 19 gaps (68.8%, score 55) to 57 compliant / 12 gaps (77.9%, score 70, zero blockers) after six evidence records are reviewed and approved. Eight mandatory gaps remain visible with owners, and the sign-off records that they were accepted with a written reason.
```

**GitHub Repository or contribution**

```
https://github.com/shreepalgoyal/bidroom
```

**Demo video**

```
<PASTE_YOUTUBE_OR_LOOM_URL>
```

**Live demo or deployment**

```
```

---

## Track Details

**Pull requests**

```
```
(Not required for Best Business Workflow.)

**Blog post**

```
```
(Optional.)

**Wispr usage card**

```
```
(Optional; only if you want Code with Wispr.)

**#HowISwitch post**

```
```
(Optional.)

---

## How you used Switch

```
I built BidRoom as a five-agent bid team in one Switch group, bridged into Mattermost, with a human bid lead in the room.

Agents connected: five OpenCode agents — northwind-scout (RFP intake), northwind-matcher (compliance matrix and gap owners), northwind-evidence (evidence desk), northwind-writer (draft from approved evidence only) and northwind-redteam (independent review). All five run locally through OpenCode on a tool-capable model (opencode/deepseek-v4.1-flash-free) and share one checkout, so they share the same .bidroom/ workspace rather than passing files around.

Platform: the local Switch server's Mattermost bridge. The template creates two linked rooms — "Bid: Northwind City Council" (the war room, all five agents plus the bid lead) and "northwind-evidence-desk" (matcher and evidence desk). The template also declares roles (requirements owner, evidence owner, draft owner, exclusive red-team role), three room documents (BID-BRIEF.md, RUNBOOK.md, EVIDENCE-POLICY.md) and a kickoff that starts the scout, so the group begins working the moment it is created.

Real work it does: it runs a real 77-requirement UK local-government RFP (Northwind City Council, NCC-2026-114). The scout ingests the RFP and posts 65 mandatory / 12 scored requirements and the five hardest mandatory items. The matcher builds a 77-row compliance matrix and posts 50 compliant / 6 partial / 2 needs-approval / 19 gaps at 68.8%, grouped by owner. The evidence desk imports six gap-closing Markdown records, lints them, and posts the approval queue with what each record proves and what is still missing. I approve six records by name in the terminal (and reject two: the AI search pilot is still in sandbox, delegated access is in legal review). The matrix moves to 57 / 6 / 2 / 12 at 77.9%. The writer drafts only from approved records with citations, and the red team reports blockers first, then the readiness score. I sign off with an accepted-gap reason; the signature stores a SHA-256 digest of the approved library and the report shows the signature and the gap owners.

How teammates work with it: the room is the audit trail. A capture manager can watch the matrix and the gap queue without opening a terminal; a subject-matter expert is named as the owner of a gap and supplies the record; the bid lead is the only person who approves evidence and signs. The relay is visible: scout → matcher → human approval → writer → redteam → human sign-off. Agents never run the approval or sign-off commands — those are not in the MCP tool surface, and imported evidence always lands unapproved even if the source says approved: true.

The template is the distribution unit: one YAML file creates the agents, the rooms, the roles, the documents and the kickoff. That is the part I would reuse on the next bid.
```

## What you liked about Switch, and what you would improve

```
What worked: Switch made a multi-agent business workflow legible to a non-engineer. The room is the audit trail, the roles are explicit, and the template is a genuinely good distribution unit — one file creates five agents, two rooms, three documents and a kickoff. The relay between agents is visible in chat, and because every agent works in the same checkout, the hand-off is a real workspace state change, not a summary passed between prompts. The kickoff is a nice touch: the group starts itself instead of waiting for a human to prime it.

What got in the way: model selection for local OpenCode agents was the sharpest edge. A newly created agent can inherit a default model that cannot call tools, and the failure only appears on the first turn ("No endpoints found that support tool use"). I had to set Model and Utility model on each of the five agents, and an existing session keeps its original model even after the agent setting changes. A per-template model field plus a preflight check that the chosen model supports tool use would save that debugging loop. Second, the agents sometimes spent a turn looking for a "post message" tool instead of just replying in the room, which is a discoverability problem in the harness rather than the model. Third, the Mattermost bridge logs non-fatal "Invalid RootId parameter" errors for tool-activity posts, so a healthy room looks broken in the logs.

What I would want next: a first-class approval card in the room — the record, the source, the requirement and an Approve/Reject button — so the human gate is a button with context rather than a terminal command. A diff view when an approved record changes. And a per-template model + preflight in the template schema, so a group is known-good before the first turn.
```

---

## Short version (for a blog or social post)

```
BidRoom is an evidence-backed bid room built on Switch. Five OpenCode agents — scout, matcher, evidence desk, writer, red team — share a Mattermost room with a human bid lead. Every compliance claim must cite an approved evidence record; agents can propose evidence, but only the human approves it, and only the bid lead signs. Sign-off hashes the approved library, so later edits mark the signature stale. On a 77-requirement council RFP it moves from 50 compliant / 19 gaps (68.8%) to 57 compliant / 12 gaps (77.9%, zero blockers) after six records are reviewed. The matrix is the product; the human signs.
```
