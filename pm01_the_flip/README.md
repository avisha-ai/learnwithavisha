# LWA_PM_01 — The Flip

Shell and tube heat exchanger, built fresh from `voiceover.mp3` (repo root).

```
title card (3.5 s)  →  main animation + voiceover (195 s)  →  end card "learnwithavisha.ai" (5 s)
```

The Avisha icon is overlaid on every frame: 60 × 60 px, bottom right, 20 px from the edges, 85 % opacity.

## Files

| File | What it is |
|---|---|
| `scene.py` | Manim scenes: `Ep01Main` (timed to the voiceover) and `Ep01EndCard` |
| `build.py` | Renders both scenes, then assembles title card + main + end card, watermark and audio with ffmpeg |
| `voiceover_words.json` | Word-level timestamps of `voiceover.mp3` (faster-whisper `base.en`), the source of every cue in `scene.py` |
| `assets/title_card.svg` | Isha's title card — **drop it here** |
| `assets/avisha_icon.png` | Watermark, copied from `avisha-brand-assets/new assets/avisha-icon-1024.png` |

## Build

```bash
.micromamba/root/envs/manim/bin/python pm01_the_flip/build.py            # full 1080p60 → finals/LWA_PM_01_TheFlip.mp4
.micromamba/root/envs/manim/bin/python pm01_the_flip/build.py --draft    # 480p15 layout check, about a minute
.micromamba/root/envs/manim/bin/python pm01_the_flip/build.py --skip-render   # reassemble only, e.g. after a new title card
```

If the voiceover is regenerated, re-transcribe it and update `CUE` in `scene.py`: every cue is the
start time of a spoken word.
