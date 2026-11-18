"""
LearnWithAvisha · widescreen side-by-side: 2D episode on the left, 3D exchanger on the right

Takes a finished vertical episode (1080x1920, captions burned in, with audio) and builds a
1920x1080 version: the 2D video sits slightly left of centre, and the 3D shell-and-tube
panel (hx3d.py, PyVista) fills the space on the right that used to be empty. Audio and
captions come from the 2D episode unchanged; the 3D panel is rendered to the same length.

Run from the learnwithavisha folder, after the episode pipeline:
    .venv/bin/python3 pipeline/side_by_side.py out/lwa_s1e02_the_fouling_problem_captioned.mp4 --fouling
    .venv/bin/python3 pipeline/side_by_side.py out/lwa_s1e01_the_flip_captioned.mp4 --flip-at 42.0
    .venv/bin/python3 pipeline/side_by_side.py <video> --draft      # quick layout check

Output: out/<episode>_wide.mp4  (1920x1080, 30 fps, H.264 + AAC)
Everything here is free and offline: PyVista + ffmpeg.
"""

import argparse, subprocess, sys
from pathlib import Path

import hx3d

FRAME_W, FRAME_H = 1920, 1080
LEFT_X = 88                         # 2D panel: 608 px wide at full height, moved left of centre
LEFT_W = 608
RIGHT_X = LEFT_X + LEFT_W + 32      # 3D panel fills the rest of the frame
RIGHT_W, RIGHT_H = hx3d.PANEL_W, hx3d.PANEL_H
BG_HEX = "0x%02x%02x%02x" % hx3d.BG

def duration_of(video):
    ffprobe = str(Path(hx3d.FFMPEG).with_name("ffprobe"))
    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(video)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  could not read the length of {video}:\n{r.stderr[-400:]}")
    return float(r.stdout.strip())

def compose(left, right, out, duration):
    vf = (f"color=c={BG_HEX}:s={FRAME_W}x{FRAME_H}:r={hx3d.FPS}:d={duration:.3f}[bg];"
          f"[0:v]scale={LEFT_W}:{FRAME_H}:flags=lanczos,setsar=1[l];"
          f"[1:v]scale={RIGHT_W}:{RIGHT_H},setsar=1[r];"
          f"[bg][l]overlay={LEFT_X}:0[t];"
          f"[t][r]overlay={RIGHT_X}:{(FRAME_H - RIGHT_H) // 2}:shortest=1,format=yuv420p[v]")
    cmd = [hx3d.FFMPEG, "-y", "-loglevel", "error", "-i", str(left), "-i", str(right),
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-crf", "20", "-preset", "medium",
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  side-by-side failed:\n{r.stderr[-800:]}")
    return Path(out)

def make_wide(video, fouling=False, mode="counter", flip_at=None, draft=False):
    video = Path(video)
    dur = duration_of(video)
    stem = video.stem.removesuffix("_captioned").removesuffix("_master")
    panel = video.with_name(f"{stem}_3d{'_draft' if draft else ''}.mp4")
    out = video.with_name(f"{stem}_wide{'_draft' if draft else ''}.mp4")
    print(f"  3D panel for {video.name} ({dur:.1f}s)…")
    size = (RIGHT_W // 2, RIGHT_H // 2) if draft else (RIGHT_W, RIGHT_H)
    hx3d.render_video(panel, dur, size, 15 if draft else hx3d.FPS, fouling, mode, flip_at)
    compose(video, panel, out, dur)
    print(f"  wide: {out}")
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", help="finished vertical episode (the _captioned.mp4)")
    ap.add_argument("--mode", choices=("counter", "parallel"), default="counter")
    ap.add_argument("--flip-at", type=float, help="3D starts parallel, flips to countercurrent at this time (s)")
    ap.add_argument("--fouling", action="store_true", help="show fouled (brown) tubes")
    ap.add_argument("--draft", action="store_true", help="half-size 3D at 15 fps — layout check")
    a = ap.parse_args()
    make_wide(a.video, a.fouling, a.mode, a.flip_at, a.draft)

if __name__ == "__main__":
    main()
