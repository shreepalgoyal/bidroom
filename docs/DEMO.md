# Demo script

The recorded cut is **2:04** and lives at [`docs/bidroom-demo.mp4`](bidroom-demo.mp4). It is a narrated composition of real Switch room screenshots, the signed report and a terminal replay; the room and the workspace are the ones in this repo. The shot list below is the recording plan, with the times used in the final cut.

## Before you record

1. The room `Bid: Northwind City Council` already contains the scout intake and the matcher matrix.
2. The bid lead has approved the six gap-closing records; `.bidroom` reports **57 compliant · 6 partial · 2 needs-approval · 12 gap, 77.9%**.
3. Open these windows in this order:
   - Switch Console, room `Bid: Northwind City Council` (full screen)
   - Terminal at the repo root, font size 16+, with `.venv/bin/bidroom -w .bidroom status` already run once
   - `demo-output/report.html` in a browser tab
4. Close Slack, mail and notifications. Do not show API keys.
5. Check the microphone level and record a 10-second test.

## Shot list

| Time | Shot | Say |
| --- | --- | --- |
| 0:00 | Title card: **BidRoom — evidence-backed bids, with a human gate** | "A public-sector RFP is not a writing problem. It is an evidence problem." |
| 0:07 | The problem: one RFP, 77 requirements, a library of claims that may not prove them | "This one has seventy-seven requirements, sixty-five of them mandatory, and a library of case studies that may or may not prove what the sales team wants to say." |
| 0:18 | The rule: prose vs proof, the relay, "agents can propose, they cannot approve" | "One fluent paragraph that cites the wrong case study can lose the bid after award. Generic AI writers make that worse, because they optimise for prose, not proof." |
| 0:31 | Switch Console → room → the five agent names and the bid lead | "This is the bid room. Five OpenCode agents and me, in one Mattermost channel, created from a single Switch template." |
| 0:47 | Scroll to the scout's intake post: 77 requirements, 65 mandatory, 12 scored, five hardest items | "The scout reads the RFP and names the five hardest mandatory items." |
| 0:52 | Scroll to the matcher's matrix post: 50/6/2/19, 68.8%, gaps by owner | "The matcher builds the compliance matrix: fifty compliant, six partial, two waiting on approval, nineteen gaps, each with an owner." |
| 1:03 | Room: the evidence desk's approval queue and the six gap-closing records | "The evidence desk turns gaps into reviewable records and posts the approval queue." |
| 1:10 | Terminal: `bidroom evidence approve ...`; then `bidroom status` showing 57/6/2/12 | "This is the gate. Agents can propose evidence, but only I can approve it. I approved six records and rejected two." |
| 1:18 | Room: the bid lead's approval post listing six approved records and two deliberately rejected ones | "The matrix moves to fifty-seven compliant, seventy-seven point nine percent coverage." |
| 1:26 | Room: writer's reply with draft path, counts, citations and deliberate gaps | "The writer drafts only from approved records. Every claim carries a citation. A gap stays a gap, with an owner." |
| 1:35 | Room: red-team reply with blockers and the readiness score | "The red team re-reads the draft against the library and reports zero blockers, score seventy." |
| 1:42 | Room: the sign-off post with the digest and accepted gaps | "I sign, and the signature pins the approved evidence with a SHA-256 digest. If anyone edits an approved record afterwards, the report marks the signature stale." |
| 1:49 | `docs/sample-report.html`: score 70/100, 0 blockers, 8 accepted gaps, signed panel | "The report shows what is proven, what is still a gap, and who owns it. That is the artifact I would take to a bid review." |
| 1:57 | End card: repo URL, track, "BidRoom" | "BidRoom. The matrix is the product. The human signs." |

## Recording

- macOS: `Cmd+Shift+5` → Record Selected Portion, or QuickTime → New Screen Recording.
- Record at 1920×1080 or 2560×1440. Do not record the whole desktop with personal tabs.
- Speak at a normal pace; the narration is about 250 words and runs 1:39, with the full cut at 2:04 including pauses.
- If a turn stalls, cut the wait and keep the result: the room is asynchronous, and the video is allowed to show the posted outcome.
- Export MP4 (H.264) at 1080p, then upload to YouTube as **Unlisted** or Loom. Under 3:00.

## Voiceover script

> A public-sector RFP is not a writing problem. It is an evidence problem.
>
> This one has seventy-seven requirements, sixty-five of them mandatory, and a library of case studies that may or may not prove what the sales team wants to say. One fluent paragraph that cites the wrong case study can lose the bid after award. Generic AI writing tools make that worse, because they optimise for prose, not proof.
>
> This is the bid room. Five OpenCode agents and me, in one Mattermost channel, created from a single Switch template. Scout, matcher, evidence desk, writer and red team. Every one of them works in the same checkout.
>
> The scout reads the RFP, ingests the requirements and names the five hardest mandatory items. The matcher builds the compliance matrix: fifty compliant, six partial, two waiting on approval, nineteen gaps. Every gap has an owner. Nothing here is prose yet.
>
> This is the gate. Agents can propose evidence, but only I can approve it. I check each source, run the approval, and the matrix moves to fifty-seven compliant and seventy-seven point nine percent coverage. I approved six records and rejected two: the AI search pilot is still in sandbox, and the delegated-access consent wording is in legal review.
>
> The writer drafts only from approved records. Every claim carries a citation. A gap stays a gap, with an owner. The red team re-reads the draft against the library. An unsupported claim is a blocker, not a style note.
>
> The strict review is clean. I sign, and the signature pins the approved evidence with a SHA-256 digest. If anyone edits an approved record afterwards, the report marks the signature stale.
>
> The report shows what is proven, what is still a gap, and who owns it. That is the artifact I would take to a bid review.
>
> BidRoom. The matrix is the product. The human signs.
