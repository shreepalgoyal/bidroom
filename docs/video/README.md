# Video build

The submitted cut is [`../bidroom-demo.mp4`](../bidroom-demo.mp4) — 2:04, 1920×1080, H.264/AAC.

This folder contains everything needed to rebuild it with a different voice track:

```
slides/        the 14 rendered slides (committed)
narration/     the narration text for p01–p12 (committed)
audio/         drop p01.wav … p12.wav here (not committed)
build.py       trims, pads, muxes and concatenates the segments
```

## Rebuild with a new voice

1. Generate twelve WAV files from `narration/p01.txt` … `p12.txt`. Any sample rate or channel count is fine.
2. Put them in `audio/` as `p01.wav` … `p12.wav`.
3. Run:

   ```bash
   python docs/video/build.py
   ```

   The output replaces `docs/bidroom-demo.mp4`. The build refuses to finish if the cut is 3:00 or longer.

`p08.wav` is split across the terminal slide and the bid-lead post; `p11.wav` is split across the sign-off post and the report. The splits are proportional (55% / 48%), so a new voice does not need manual timing.

## Requirements

- `ffmpeg` and `ffprobe` on `PATH`
- Python 3.10+

The slides are already rendered; no Pillow or macOS fonts are needed to rebuild the video. If you change a screenshot or the report, replace the matching PNG in `slides/` and rebuild.

## Upload

Upload the MP4 to YouTube as **Unlisted** (or Loom), then put the URL in the README and the submission form. The video must stay under 3:00.

### Title

```
BidRoom — evidence-backed RFP responses with a human sign-off | Flip the Switch 2026
```

### Description

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
