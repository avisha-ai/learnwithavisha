"""
ChemE Factory — narration + looped B-roll -> finished MP4.

Local and free: edge-tts does the voice, MoviePy does the timeline, and the
ffmpeg binary that ships inside imageio-ffmpeg does the encode. Nothing here
needs a system ffmpeg on PATH and nothing calls a paid API.

Run it from anywhere:

    /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 make_video.py

That interpreter matters. Several Pythons on this Mac answer to `python3` and
only the 3.14 framework build has edge-tts and moviepy installed, so launching
with the wrong one raises ModuleNotFoundError before any real work starts.
Every path below is resolved against this file's own folder rather than the
shell's working directory, so the script cannot be broken by where it is
called from.

MoviePy 2.x note: `moviepy.editor` no longer exists, and the 1.x methods were
renamed — `subclip` -> `subclipped`, `set_audio` -> `with_audio`, and `loop`
moved into the effects system as `vfx.Loop`. The code below targets 2.x.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import edge_tts
from moviepy import AudioFileClip, VideoFileClip, vfx

# ── settings ─────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent

SOURCE_VIDEO = HERE / "simulation.mp4"
NARRATION = HERE / "narration.mp3"
OUTPUT = HERE / "the_microscopic_choke_final.mp4"

VOICE = "en-US-AndrewNeural"
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"

# How the B-roll repeats once it runs out.
#
#   "seamless"  crossfade the clip's tail back over its own head before
#               looping, so the repeat is a soft dissolve. simulation.mp4
#               ends nowhere near where it starts — the raw jump measures
#               about 29x a normal frame-to-frame change — so a plain loop
#               reads as a hard cut every time it comes round.
#   "cut"       plain repeat. Exact frames, visible seam.
LOOP_MODE = "seamless"
LOOP_OVERLAP = 0.8          # seconds of dissolve, "seamless" only

SCRIPT_TEXT = (
   [
  {
    "episode_id": "sorcery_ep1_fouling",
    "schedule": "Week 1 - Tuesday Launch",
    "title": "The Calcified Veil",
    "scenes": [
      {
        "scene_no": 1,
        "voiceover": "Deep within the clockwork heart of the Foundry, the elemental balance is breaking. The Solar Torrent, carrying the raw, burning kinetic energy of the furnace, is roaring wildly through the outer chamber. Inside the inner crystal pathways, the Deep Frost Currents sweep forward to draw out the chaos.",
        "prompt": "A breathtaking 3D cinematic render inside a colossal clockwork cathedral. A massive, roaring river of liquid-gold and glowing crimson particles (the shell-side fluid) cascades violently through a dark, ornate steel vault. Inside transparent crystal pipelines, an elegant, luminous stream of starlight-blue plasma weaves forward smoothly. Magical realism, global illumination, 8k."
      },
      {
        "scene_no": 2,
        "voiceover": "But a silent corruption is awake. Under the intense thermal stress, invisible impurities in the torrent undergo a sudden metamorphosis, crystallizing directly onto the outer walls of the frost channels. A heavy, jagged matrix of pale, glowing calcified stone locks onto the boundaries like a dense mineral curse.",
        "prompt": "An extreme close-up macro-render of a single solid metallic barrier separating the two magical currents. Luminous blue plasma surges left; liquid gold cascades right. At the outer interface, a jagged, sharp, crystalline crust of white-purple calcified mineral scale is aggressively growing and wrapping around the wall, blocking the ambient light. Ghibli cinematic beauty, highly detailed."
      },
      {
        "scene_no": 3,
        "voiceover": "This calcified veil forms an impenetrable insulation blanket, choking the thermal bridge. The kinetic driving force collapses, causing the solar line to swell under massive pressure. If the resistance isn't broken within the hour, the core will implode. The keepers execute a desperate, high-stakes gamble: they are flipping the vectors into reverse... but will the reverse currents save the vault?",
        "prompt": "A wide cinematic shot inside a dark, pulsating mechanical vault. A thick, cracked, glowing mineral scale crust completely smothers a matrix of copper pipes. Fading golden energy wavelets reflect backward off the choked barrier instead of passing through. High-pressure runic dials vibrating wildly in the foreground, suspenseful magical lighting, dark fantasy aesthetic."
      }
    ]
  }
]

)


# ── 1. narration ─────────────────────────────────────────────────
async def _synthesise() -> None:
    await edge_tts.Communicate(SCRIPT_TEXT, VOICE).save(str(NARRATION))


def generate_voice(force: bool = False) -> Path:
    """Render the script to MP3 with edge-tts. Needs network; nothing else does."""
    if NARRATION.exists() and NARRATION.stat().st_size > 0 and not force:
        print(f"{NARRATION.name} already present "
              f"({NARRATION.stat().st_size / 1e3:.0f} kB) — pass --force to redo")
        return NARRATION

    print(f"synthesising narration with {VOICE} ...")
    asyncio.run(_synthesise())

    if not NARRATION.exists() or NARRATION.stat().st_size == 0:
        raise RuntimeError(
            "edge-tts produced no audio. It streams from Microsoft's endpoint, "
            "so this is almost always a network or proxy problem."
        )
    print(f"  wrote {NARRATION.name} — {NARRATION.stat().st_size / 1e3:.0f} kB")
    return NARRATION


# ── 2. assembly ──────────────────────────────────────────────────
def assemble_video() -> Path:
    """Loop the B-roll to the narration's exact length and mux the two."""
    if not SOURCE_VIDEO.exists():
        raise FileNotFoundError(
            f"{SOURCE_VIDEO.name} is not in {HERE}. Put the clip there under "
            f"that exact name and rerun."
        )
    if not NARRATION.exists():
        raise FileNotFoundError(
            f"{NARRATION.name} is missing — run the voice step first.")

    with AudioFileClip(str(NARRATION)) as narration, \
            VideoFileClip(str(SOURCE_VIDEO)) as source:

        target = narration.duration
        print(f"narration {target:.3f} s | source {source.duration:.3f} s "
              f"| {source.size[0]}x{source.size[1]} @ {source.fps:g} fps")

        if source.duration < target:
            if LOOP_MODE == "seamless":
                # MakeLoopable dissolves the tail back over the head and hands
                # back a slightly shorter clip whose ends now match, so Loop
                # can repeat it without a visible join.
                loopable = source.with_effects([vfx.MakeLoopable(LOOP_OVERLAP)])
                print(f"  looping {target / loopable.duration:.2f}x with a "
                      f"{LOOP_OVERLAP:g} s dissolve at each repeat")
                video = loopable.with_effects([vfx.Loop(duration=target)])
            else:
                print(f"  looping source {target / source.duration:.2f}x "
                      f"(hard cut at each repeat)")
                video = source.with_effects([vfx.Loop(duration=target)])
        else:
            print("  source is long enough — trimming to the narration")
            video = source

        # Cut to the narration exactly, then hand it the only audio that
        # ships. with_audio replaces the source clip's own track rather than
        # mixing with it, which is what we want here.
        video = video.subclipped(0, target).with_audio(narration)

        print(f"encoding {OUTPUT.name} ({VIDEO_CODEC} / {AUDIO_CODEC}) ...")
        video.write_videofile(
            str(OUTPUT),
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            fps=source.fps,
        )

    print(f"done — {OUTPUT}")
    return OUTPUT


def main() -> int:
    print(f"python  {sys.executable}")
    print(f"folder  {HERE}\n")
    generate_voice(force="--force" in sys.argv)
    assemble_video()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
