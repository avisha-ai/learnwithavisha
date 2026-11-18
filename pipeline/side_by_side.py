"""
LearnWithAvisha · widescreen side-by-side: 2D episode on the left, 3D exchanger on the right

Takes a finished vertical episode (1080x1920, captions burned in, with audio) and builds a
1920x1080 version split into two equal halves with a thin partition between them:
  left  (960x1080)  "ON PAPER" — the 2D episode at full height (608x1080), centred
  right (960x1080)  "IN THE PLANT" — the 3D shell-and-tube panel (hx3d.py, PyVista)
Audio and captions come from the 2D episode unchanged; the 3D panel is rendered to the
same length.

Run from the learnwithavisha folder, after the episode pipeline:
    .venv/bin/python3 pipeline/side_by_side.py out/lwa_s1e02_the_fouling_problem_captioned.mp4 --foul-at 17.7 --title-from 7.1
    .venv/bin/python3 pipeline/side_by_side.py out/lwa_s1e01_the_flip_captioned.mp4 --flip-at 42.0
    .venv/bin/python3 pipeline/side_by_side.py <video> --draft      # quick layout check

Output: out/<episode>_wide.mp4  (1920x1080, 30 fps, H.264 + AAC)
Everything here is free and offline: PyVista + ffmpeg.
"""

import argparse, subprocess, sys
from pathlib import Path

import hx3d

FRAME_W, FRAME_H = 1920, 1080
HALF_W = FRAME_W // 2               # two equal halves
LEFT_W = 608                        # 2D episode at full height (1080x1920 scaled to 608x1080)
LEFT_X = (HALF_W - LEFT_W) // 2     # centred in the left half
LEFT_BG = "0x%02x%02x%02x" % hx3d.BG   # same dark as the 3D side and the 2D episode itself
RIGHT_X = HALF_W
RIGHT_W, RIGHT_H = hx3d.PANEL_W, hx3d.PANEL_H
assert (RIGHT_W, RIGHT_H) == (HALF_W, FRAME_H), "hx3d.PANEL_W/H must fill the right half"
DIVIDER_W, DIVIDER_COLOUR = 3, "0x3A4050"   # vertical partition centred on x = 960
TITLE_FADE = 0.5                            # ON PAPER fades in over this long (s)

def duration_of(video):
    ffprobe = str(Path(hx3d.FFMPEG).with_name("ffprobe"))
    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(video)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  could not read the length of {video}:\n{r.stderr[-400:]}")
    return float(r.stdout.strip())

def compose(left, right, title, out, duration, title_from=0.0):
    """left: 2D episode, right: 3D panel, title: transparent ON PAPER png for the left half,
    shown from title_from (s) — after the 2D's own title scene, so the two never overlap."""
    vf = (f"color=c={LEFT_BG}:s={FRAME_W}x{FRAME_H}:r={hx3d.FPS}:d={duration:.3f}[bg];"
          f"[0:v]scale={LEFT_W}:{FRAME_H}:flags=lanczos,setsar=1[l];"
          f"[1:v]scale={RIGHT_W}:{RIGHT_H},setsar=1[r];"
          f"[2:v]format=rgba,fade=t=in:st={title_from:.3f}:d={TITLE_FADE}:alpha=1[title];"
          f"[bg][l]overlay={LEFT_X}:0[t1];"
          f"[t1][r]overlay={RIGHT_X}:0:shortest=1[t2];"
          f"[t2][title]overlay=0:0[t3];"     # on top of the 2D, same place as IN THE PLANT
          f"[t3]drawbox=x={HALF_W - DIVIDER_W // 2}:y=0:w={DIVIDER_W}:h={FRAME_H}"
          f":color={DIVIDER_COLOUR}:t=fill,format=yuv420p[v]")
    cmd = [hx3d.FFMPEG, "-y", "-loglevel", "error", "-i", str(left), "-i", str(right),
           "-loop", "1", "-t", f"{duration:.3f}", "-i", str(title),
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-crf", "20", "-preset", "medium",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  side-by-side failed:\n{r.stderr[-800:]}")
    return Path(out)

def make_wide(video, fouling=False, mode="counter", flip_at=None, draft=False, foul_at=None,
              title_from=0.0):
    """foul_at: 3D tubes start clean and fade to fouled from this time (s); implies fouling.
    title_from: when ON PAPER appears (the end of the 2D's title scene)."""
    video = Path(video)
    dur = duration_of(video)
    stem = video.stem.removesuffix("_captioned").removesuffix("_master")
    panel = video.with_name(f"{stem}_3d{'_draft' if draft else ''}.mp4")
    out = video.with_name(f"{stem}_wide{'_draft' if draft else ''}.mp4")
    title = video.with_name(f"{stem}_on_paper_title.png")
    print(f"  3D panel for {video.name} ({dur:.1f}s)…")
    size = (RIGHT_W // 2, RIGHT_H // 2) if draft else (RIGHT_W, RIGHT_H)
    hx3d.render_video(panel, dur, size, 15 if draft else hx3d.FPS, fouling, mode, flip_at, foul_at)
    hx3d.render_title_png("ON PAPER", title, (HALF_W, FRAME_H))
    compose(video, panel, title, out, dur, title_from)
    print(f"  wide: {out}")
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", help="finished vertical episode (the _captioned.mp4)")
    ap.add_argument("--mode", choices=("counter", "parallel"), default="counter")
    ap.add_argument("--flip-at", type=float, help="3D starts parallel, flips to countercurrent at this time (s)")
    ap.add_argument("--fouling", action="store_true", help="show fouled (brown) tubes")
    ap.add_argument("--foul-at", type=float,
                    help="3D tubes clean until this time (s), then fade to fouled over hx3d.FOUL_FADE s")
    ap.add_argument("--title-from", type=float, default=0.0,
                    help="show ON PAPER from this time (s): the end of the 2D's title scene")
    ap.add_argument("--draft", action="store_true", help="half-size 3D at 15 fps — layout check")
    a = ap.parse_args()
    make_wide(a.video, a.fouling, a.mode, a.flip_at, a.draft, a.foul_at, a.title_from)

if __name__ == "__main__":
    main()
