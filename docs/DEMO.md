# Demo script

Target length: **2 minutes 45 seconds**. The recording must show the agents working in the real Switch room, not a slide deck.

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
| 0:12 | The problem: one RFP, 77 requirements, a library of claims that may not prove them | "One fluent paragraph that cites the wrong case study can lose the bid after award. Generic AI makes that worse." |
| 0:30 | Switch Console → room → the five agent names and the bid lead | "This is the bid room. Five OpenCode agents and me, in one Mattermost channel, created from a single Switch template." |
| 0:45 | Scroll to the scout's intake post: 77 requirements, 65 mandatory, 12 scored, five hardest items | "The scout reads the RFP, ingests the requirements and names the five hardest mandatory items." |
| 1:00 | Scroll to the matcher's matrix post: 50/6/2/19, 68.8%, gaps by owner | "The matcher builds the compliance matrix. Fifty compliant, nineteen gaps. Every gap has an owner. Nothing here is prose yet." |
| 1:20 | Terminal: `bidroom evidence approve ...` for one record; then `bidroom status` showing 57/6/2/12 | "This is the gate. Agents can propose evidence, but only I can approve it. I check the source, run the approval, and the matrix moves to 77.9%." |
| 1:40 | Room: the bid lead's approval post listing six approved records and two deliberately rejected ones | "I approved six and rejected two: the AI search pilot is still in sandbox, and the delegated-access consent wording is in legal review." |
| 1:55 | Room: writer's reply with draft path, counts, citations and deliberate gaps | "The writer drafts only from approved records. Every claim carries a citation. Gaps stay visible as gaps." |
| 2:10 | Room: red-team reply with blockers and the readiness score | "The red team re-reads the draft against the library. Unsupported claims are blockers, not style notes." |
| 2:25 | Terminal: `bidroom review --strict` exits 0; `bidroom signoff` with the reason | "The strict review is clean. I sign, and the signature pins the approved evidence with a SHA-256 digest." |
| 2:40 | `demo-output/report.html`: score 70/100, 0 blockers, 8 accepted gaps, signed panel | "The report shows what is proven, what is still a gap, and who owns it. That is the artifact I would take to a bid review." |
| 2:52 | End card: repo URL, track, "BidRoom" | "BidRoom. The matrix is the product. The human signs." |

## Recording

- macOS: `Cmd+Shift+5` → Record Selected Portion, or QuickTime → New Screen Recording.
- Record at 1920×1080 or 2560×1440. Do not record the whole desktop with personal tabs.
- Speak at a normal pace; the script is ~380 words, which is about 2:20 of speech, leaving room for pauses.
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
