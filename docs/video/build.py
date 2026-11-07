#!/usr/bin/env python3
"""Assemble the BidRoom demo video from the committed slides and narration.

Usage:
    python docs/video/build.py
    python docs/video/build.py --audio-dir /path/to/elevenlabs/wavs
    python docs/video/build.py --out /tmp/bidroom-demo.mp4

The narration files are p01.wav ... p12.wav. They may be any sample rate or
channel count; the build normalises them to 48 kHz stereo. The two split
chapters (the human gate and the sign-off) are split proportionally, so a
new voice track does not need manual timing.

Requires ffmpeg and ffprobe on PATH.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_SLIDES = HERE / "slides"
DEFAULT_AUDIO = HERE / "audio"
DEFAULT_OUT = REPO / "docs" / "bidroom-demo.mp4"
WORK = HERE / "build"

# (slide, narration, split fraction or None). A split fraction cuts one
# narration file across two slides.
PLAN = [
    ("01.png", "p01.wav", None),
    ("02.png", "p02.wav", None),
    ("03.png", "p03.wav", None),
    ("04.png", "p04.wav", None),
    ("05.png", "p05.wav", None),
    ("06.png", "p06.wav", None),
    ("07.png", "p07.wav", None),
    ("08a.png", "p08.wav", 0.55),
    ("08.png", "p08.wav", 0.55),
    ("09.png", "p09.wav", None),
    ("10.png", "p10.wav", None),
    ("11.png", "p11.wav", 0.48),
    ("11b.png", "p11.wav", 0.48),
    ("12.png", "p12.wav", None),
]


def run(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-4000:])
        raise SystemExit(f"command failed: {' '.join(args)}")
    return proc.stdout


def duration(path: Path) -> float:
    return float(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ]
        ).strip()
    )


def trim(src: Path, start: float, end: float, dst: Path) -> float:
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(src),
            "-ss",
            f"{start:.3f}",
            "-to",
            f"{end:.3f}",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dst),
        ]
    )
    return duration(dst)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slides", type=Path, default=DEFAULT_SLIDES)
    parser.add_argument("--audio-dir", type=Path, default=DEFAULT_AUDIO)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--keep-work", action="store_true", help="Keep the per-slide segments")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe are required on PATH.")
    missing = [name for _, name, _ in PLAN if not (args.audio_dir / name).exists()]
    if missing:
        raise SystemExit(f"Missing narration files in {args.audio_dir}: {', '.join(sorted(set(missing)))}")
    missing_slides = [name for name, _, _ in PLAN if not (args.slides / name).exists()]
    if missing_slides:
        raise SystemExit(f"Missing slides in {args.slides}: {', '.join(missing_slides)}")

    WORK.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []
    total = 0.0
    seen_split: dict[str, float] = {}

    for index, (slide, voice, split) in enumerate(PLAN, 1):
        source = args.audio_dir / voice
        full = duration(source)
        if split is not None:
            cut = full * split
            if voice in seen_split:
                start, end = seen_split[voice], full
            else:
                start, end = 0.0, cut
                seen_split[voice] = cut
            wav = WORK / f"a{index:02d}.wav"
            speech = trim(source, start, end, wav)
        else:
            wav = source
            speech = full

        lead = 0.7
        tail = 1.0
        if split is not None and split < 1.0 and index == 8:
            tail = 0.4
        if split is not None and split < 1.0 and index == 13:
            tail = 1.2
        if slide == "01.png":
            lead = 1.1
        if slide == "12.png":
            tail = 2.6

        length = round(lead + speech + tail, 3)
        total += length
        segment = WORK / f"seg{index:02d}.mp4"
        video_filter = (
            f"[0:v]scale=1920:1080,format=yuv420p,"
            f"fade=t=in:st=0:d=0.30,fade=t=out:st={length - 0.35:.3f}:d=0.35[v];"
            f"[1:a]adelay={int(lead * 1000)}|{int(lead * 1000)},apad,atrim=0:{length:.3f}[a]"
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-loop",
                "1",
                "-framerate",
                "30",
                "-i",
                str(args.slides / slide),
                "-i",
                str(wav),
                "-filter_complex",
                video_filter,
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-t",
                f"{length:.3f}",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-movflags",
                "+faststart",
                str(segment),
            ]
        )
        segments.append(segment)
        print(f"{index:02d} {slide:8s} {speech:6.2f}s + lead/tail = {length:6.2f}s  total {total:6.2f}s")

    listing = WORK / "list.txt"
    listing.write_text("".join(f"file '{segment}'\n" for segment in segments), encoding="utf-8")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(args.out),
        ]
    )
    final = duration(args.out)
    print(f"\nfinal: {args.out}  {final:.2f}s  {args.out.stat().st_size} bytes")
    if final >= 180:
        print("WARNING: the video is 3 minutes or longer.", file=sys.stderr)
        return 1
    if not args.keep_work:
        shutil.rmtree(WORK, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
