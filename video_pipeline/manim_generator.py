"""
Generate the Manim animation for a topic, then render it.

The narration already exists when this runs, so its exact duration is a hard
input: SKILL.md requires the animation to match the voiceover exactly and the
screen never to go blank while the voice is still speaking.

The approved pilot (shell_tube_animation.py) is passed to Claude as the
reference implementation — its absolute-timeline helpers (hold_until / at /
caption) are the pattern every generated scene reuses, so timing is expressed
in absolute seconds rather than accumulated run_times that drift.

Generated code is compiled and test-rendered at low quality before the real
render, and a failure is fed back to Claude for a repair attempt.
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import llm_client
from config import (BACKGROUND, BREATH_PAUSE, COLOURS, FPS, PILOT_ANIMATION,
                    RESOLUTION, WATERMARK_OPACITY)
from queue_manager import Topic

log = logging.getLogger(__name__)

RENDER_TIMEOUT = 3600
SYNC_TOLERANCE = 0.75           # seconds of drift allowed against the voiceover

SYSTEM = f"""You write Manim Community Edition scenes for the LearnWithAvisha \
chemical engineering channel. You output Python source code and nothing else.

FROZEN ANIMATION RULES — from SKILL.md. Breaking any of these fails the build.

Timing:
- You are given TOTAL_RUNTIME, the exact duration of the finished voiceover.
  The scene must last exactly that long. Not shorter. Not longer.
- Use an ABSOLUTE timeline. Copy the hold_until / at / caption helpers from the
  reference scene. Every cue is an absolute timestamp in seconds. Never chain
  relative waits — they drift and the video falls out of sync with the voice.
- Pause {BREATH_PAUSE} seconds after every major element reveal. The lower
  caption strip is exempt: it tracks the narration continuously.
- Elements appear one at a time in the order the narration introduces them.
  Never dump everything on screen at once.
- Transitions are 1.0 to 1.5 seconds.
- The screen must NEVER be blank while the voice is still speaking. The last
  frame holds until TOTAL_RUNTIME.

Brand:
- The LWA monogram watermark is added before the first animation and is never
  removed: white italic Georgia "LWA" inside a thin circle, opacity
  {WATERMARK_OPACITY}, bottom right, self.add() so it is on every frame.
- NEVER put "LearnWithAvisha" as a heading. The topic title only.
- No end card. No references on screen. No URLs. The word "free" never appears.

Look:
- Background {BACKGROUND}. Resolution {RESOLUTION[0]}x{RESOLUTION[1]} at {FPS} fps.
- Hot / high temperature: {COLOURS['hot_in']} into {COLOURS['hot_out']}.
- Cold / low temperature: {COLOURS['cold_in']} into {COLOURS['cold_out']}.
- Heat transfer {COLOURS['heat']}. Equipment {COLOURS['equipment']}.
  Labels {COLOURS['label']}. Accent {COLOURS['accent']}.
- Clean schematic, engineering drawing style. Only what is needed to understand.

Code rules:
- Manim Community Edition v0.20. `from manim import *`.
- One Scene subclass, named exactly as instructed. Nothing else at module level
  except imports, constants and that class.
- Keep everything inside the frame: x within -7.0..7.0, y within -3.9..3.9.
  The caption strip sits low, around y = -2.7; never overlap it with diagram
  elements.
- Use Text(), not Tex() or MathTex() — no LaTeX is installed. Write equations
  as plain text such as "Re = rho v D / mu".
- Do not use ImageMobject, SVGMobject, external assets, or network access.
- Do not call self.wait() with a negative or computed-negative duration.
- No comments explaining what Manim is. Comment the timeline cues only.

OUTPUT FORMAT — absolute:
Return ONLY Python source. No markdown fence, no prose, no explanation before
or after. The first line must be a docstring or an import."""


def _strip_fence(text: str) -> str:
    """Claude is told not to fence the code; strip one anyway if it appears."""
    fence = re.match(r"^\s*```(?:python)?\s*\n(.*?)\n```\s*$", text, re.S)
    return fence.group(1) if fence else text.strip()


def _prompt(topic: Topic, script: str, runtime: float,
            beats: list[str], key_points: list[str],
            repair: str | None) -> str:
    reference = PILOT_ANIMATION.read_text(encoding="utf-8")

    parts = [
        f"Topic: {topic.topic_name}",
        f"Subject: {topic.subject}",
        f"Scene class name: {topic.scene_name}",
        f"TOTAL_RUNTIME = {runtime:.3f}   # exact duration of voiceover.mp3",
        "",
        "THE NARRATION — the animation is built to this, sentence by sentence.",
        "Estimate when each sentence is spoken by its share of the total word",
        "count, and place the matching visual cue at that absolute timestamp.",
        "----------------",
        script,
        "----------------",
        "",
        "Elements to build up, in narration order:",
        *(f"  {i}. {b}" for i, b in enumerate(beats, 1)),
        "",
        "Recap points for the summary panel at the end:",
        *(f"  - {p}" for p in key_points),
        "",
        "REFERENCE IMPLEMENTATION — the approved pilot scene. Reuse its",
        "timeline helpers and its watermark block exactly. Match its style.",
        "----------------",
        reference,
        "----------------",
        "",
        f"Write the complete {topic.scene_name} scene now.",
    ]

    if repair:
        parts += [
            "",
            "THE PREVIOUS ATTEMPT FAILED. Fix this and return the whole file again:",
            textwrap.indent(repair[-4000:], "    "),
        ]
    return "\n".join(parts)


def _check_syntax(path: Path) -> str | None:
    result = subprocess.run(
        ["python", "-m", "py_compile", str(path)],
        capture_output=True, text=True,
    )
    return None if result.returncode == 0 else result.stderr.strip()


def _render(path: Path, scene: str, quality: str, destination: Path | None = None) -> tuple[bool, str]:
    """Render with manim. quality: 'l' for the dry run, 'h' for the real one."""
    media = path.parent / "media"
    cmd = ["manim", f"-q{quality}", "--media_dir", str(media),
           "--disable_caching", str(path), scene]
    if quality == "h":
        cmd += ["--fps", str(FPS), "-r", f"{RESOLUTION[0]},{RESOLUTION[1]}"]

    log.info("  manim -q%s %s", quality, scene)
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=path.parent, timeout=RENDER_TIMEOUT)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout)[-6000:]

    produced = sorted(media.rglob(f"{scene}.mp4"))
    if not produced:
        return False, "manim reported success but produced no MP4."
    if destination:
        shutil.copy2(produced[-1], destination)
    return True, str(produced[-1])


def generate(topic: Topic, script: str, runtime: float,
             beats: list[str], key_points: list[str],
             attempts: int = 3) -> Path:
    """Write animation.py for the topic, proving it compiles and renders."""
    path = topic.ensure_dir() / "animation.py"
    repair: str | None = None

    for attempt in range(1, attempts + 1):
        log.info("  Claude call 3 — generating Manim scene (attempt %d/%d)",
                 attempt, attempts)
        code, _ = llm_client.call(
            SYSTEM,
            _prompt(topic, script, runtime, beats, key_points, repair),
            max_tokens=64000,
        )
        path.write_text(_strip_fence(code) + "\n", encoding="utf-8")

        problem = _check_syntax(path)
        if problem:
            log.warning("  syntax error in generated scene")
            repair = f"The file does not compile:\n{problem}"
            continue

        if f"class {topic.scene_name}" not in path.read_text(encoding="utf-8"):
            repair = (f"The file must define a Scene subclass named exactly "
                      f"{topic.scene_name}.")
            continue

        ok, detail = _render(path, topic.scene_name, "l")
        if not ok:
            log.warning("  test render failed")
            repair = f"manim failed to render the scene:\n{detail}"
            continue

        drift = _drift(Path(detail), runtime)
        if drift is not None and abs(drift) > SYNC_TOLERANCE:
            log.warning("  scene is %.2f s out of sync with the voiceover", drift)
            repair = (
                f"The rendered scene is {abs(drift):.2f} s "
                f"{'longer' if drift > 0 else 'shorter'} than the voiceover. "
                f"It must be exactly {runtime:.3f} s. Adjust the final "
                f"hold_until({runtime:.3f}) and the cue timeline so the total "
                f"matches, and never let the screen go blank before the end."
            )
            continue

        log.info("  scene generated and verified (drift %.3f s)", drift or 0.0)
        return path

    raise RuntimeError(f"{topic.key}: could not generate a working Manim scene "
                       f"after {attempts} attempts. Last problem:\n{repair}")


def _drift(rendered: Path, runtime: float) -> float | None:
    from voiceover import duration_seconds
    try:
        return duration_seconds(rendered) - runtime
    except Exception:                       # pragma: no cover
        return None


def render(topic: Topic) -> Path:
    """Final 1080p60 render of an already-generated scene."""
    destination = topic.rendered_path
    ok, detail = _render(topic.animation_path, topic.scene_name, "h", destination)
    if not ok:
        raise RuntimeError(f"{topic.key}: final render failed:\n{detail}")
    log.info("  rendered %s", destination.name)
    return destination
