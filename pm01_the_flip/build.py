"""
Build LWA_PM_01 — The Flip.

    title card (3.5 s)  →  main animation with voiceover  →  end card (learnwithavisha.ai)

The Avisha icon is overlaid on every frame: 60 × 60 px, bottom right, 20 px from
both edges, at 85 % opacity. The voiceover starts when the main animation does.

Run with the manim env's python:

    .micromamba/root/envs/manim/bin/python pm01_the_flip/build.py

Inputs (pm01_the_flip/assets/ unless overridden):
    title_card.svg    Isha's title card
    avisha_icon.png   the watermark
    ../voiceover.mp3  the narration (repo root)

Output: finals/LWA_PM_01_TheFlip.mp4
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BIN = Path(sys.executable).parent
RENDER = HERE / "_render"

TITLE_SECONDS = 3.5
TITLE_FADE = 0.4
WIDTH, HEIGHT, FPS = 1920, 1080, 60
BG = "0x0d0d1a"
WATERMARK_PX, WATERMARK_MARGIN, WATERMARK_OPACITY = 60, 20, 0.85


def run(cmd):
    print("→", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def duration(path):
    out = subprocess.run([BIN / "ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def render_scenes(quality):
    run([BIN / "manim", f"-q{quality}", "--disable_caching", "--media_dir", RENDER,
         HERE / "scene.py", "Ep01Main", "Ep01EndCard"])
    return scene_paths(quality)


def scene_paths(quality):
    folder = {"h": "1080p60", "l": "480p15"}[quality]
    videos = RENDER / "videos" / "scene" / folder
    return videos / "Ep01Main.mp4", videos / "Ep01EndCard.mp4"


def rasterise_title(svg):
    png = RENDER / "title_card.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    run([BIN / "ffmpeg", "-v", "error", "-c:v", "librsvg", "-width", WIDTH, "-height", HEIGHT,
         "-keep_ar", "1", "-i", svg, "-frames:v", "1", "-y", png])
    return png


def assemble(title_png, main, end, watermark, voiceover, out):
    total = TITLE_SECONDS + duration(main) + duration(end)
    delay_ms = int(TITLE_SECONDS * 1000)
    fade_out = TITLE_SECONDS - TITLE_FADE
    normalise = f"fps={FPS},scale={WIDTH}:{HEIGHT},format=yuv420p,setsar=1"
    graph = ";".join([
        # The title card sits on the episode background, so a transparent SVG
        # or one that isn't 16:9 still fills the frame cleanly.
        f"[1:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease[tc]",
        f"[0:v][tc]overlay=(W-w)/2:(H-h)/2,{normalise},"
        f"fade=t=in:st=0:d={TITLE_FADE},fade=t=out:st={fade_out}:d={TITLE_FADE}[title]",
        f"[2:v]{normalise}[main]",
        f"[3:v]{normalise}[end]",
        "[title][main][end]concat=n=3:v=1:a=0[film]",
        f"[4:v]scale={WATERMARK_PX}:{WATERMARK_PX}:flags=lanczos,format=rgba,"
        f"colorchannelmixer=aa={WATERMARK_OPACITY}[mark]",
        f"[film][mark]overlay=W-w-{WATERMARK_MARGIN}:H-h-{WATERMARK_MARGIN}:format=auto[v]",
        f"[5:a]adelay={delay_ms}:all=1,apad=whole_dur={total:.3f}[a]",
    ])
    out.parent.mkdir(parents=True, exist_ok=True)
    run([BIN / "ffmpeg", "-v", "error",
         "-f", "lavfi", "-t", TITLE_SECONDS, "-i", f"color=c={BG}:s={WIDTH}x{HEIGHT}:r={FPS}",
         "-loop", "1", "-framerate", FPS, "-t", TITLE_SECONDS, "-i", title_png,
         "-i", main, "-i", end,
         "-i", watermark,
         "-i", voiceover,
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", FPS,
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
         "-y", out])
    run([BIN / "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
         "-of", "compact", out])
    print(f"\nwrote {out}  ({total:.2f} s)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--title-card", type=Path, default=HERE / "assets" / "title_card.svg")
    parser.add_argument("--watermark", type=Path, default=HERE / "assets" / "avisha_icon.png")
    parser.add_argument("--voiceover", type=Path, default=REPO / "voiceover.mp3")
    parser.add_argument("--out", type=Path, default=REPO / "finals" / "LWA_PM_01_TheFlip.mp4")
    parser.add_argument("--draft", action="store_true",
                        help="render the scenes at 480p15 for a fast layout check")
    parser.add_argument("--skip-render", action="store_true",
                        help="reassemble from the scenes already in _render (e.g. after a new title card)")
    args = parser.parse_args()

    for name in ("title_card", "watermark", "voiceover"):
        path = getattr(args, name)
        if not path.exists():
            sys.exit(f"missing {name.replace('_', ' ')}: {path}")

    quality = "l" if args.draft else "h"
    main_mp4, end_mp4 = scene_paths(quality) if args.skip_render else render_scenes(quality)
    assemble(rasterise_title(args.title_card), main_mp4, end_mp4, args.watermark, args.voiceover, args.out)


if __name__ == "__main__":
    main()
