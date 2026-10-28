"""
Generate the animation for a topic with Veo, then conform it to the narration.

This replaces manim_generator.py. The shape of the stage is unchanged — the
pipeline still calls generate() then render(), and still ends up with an
animation.mp4 the exact length of voiceover.mp3 — but nothing between those
two points is the same.

    manim_generator          gemini_generator
    ---------------          ----------------
    LLM writes Python        LLM writes scene prompts (or a human does)
    py_compile proves it     nothing to compile — prompts cannot be checked
    manim renders it         Veo generates one clip per prompt
    timing is exact          timing is imposed afterwards, by cutting

What that trade costs, stated plainly because the code cannot recover it:

  * Determinism. The same prompt returns different pixels every run. Wade's
    beard, the paint on the shell, the camera height — none of it is stable
    between clips, let alone between episodes.
  * The frozen colour code. COLOURS in config.py used to be literal hex passed
    to Manim. Here they are words in a prompt, and Veo approximates them.
  * The compile/repair loop. A bad Manim scene raised a traceback that could be
    fed back for repair. A bad Veo clip is a valid MP4 of the wrong thing, and
    only a person watching it can tell.

What is still guaranteed, and enforced below rather than hoped for:

  * Exact runtime. Clips are generated to overshoot, then cut to the
    voiceover's duration to the millisecond, so assembler.check_sync passes.
  * 1920x1080 at 60 fps, whatever Veo hands back.
  * The LWA monogram on every frame, composited with ffmpeg.
  * Silence. Veo scores every clip it makes; that audio is discarded, because
    the ElevenLabs narration is the only voice this channel ships.
"""

from __future__ import annotations

import json
import logging
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import llm_client
from config import (BACKGROUND, CLIPS_DIRNAME, COLOURS, FPS,
                    GEMINI_API_KEY_ENV, RESOLUTION, SCENE_PROMPTS_FILE,
                    VEO_ASPECT_RATIO, VEO_CLIP_SECONDS, VEO_MAX_CLIPS,
                    VEO_MODEL, VEO_POLL_SECONDS, VEO_POLL_TIMEOUT,
                    VEO_RESOLUTION, WATERMARK_FONT, WATERMARK_OPACITY,
                    WATERMARK_TEXT, require_env)
from queue_manager import Topic

log = logging.getLogger(__name__)

FFMPEG_TIMEOUT = 3600


# ═══ paths ═══════════════════════════════════════════════════════
def prompts_path(topic: Topic) -> Path:
    """Where this topic's scene prompts live. Hand-written or derived."""
    return topic.dir / SCENE_PROMPTS_FILE


def clips_dir(topic: Topic) -> Path:
    return topic.dir / CLIPS_DIRNAME


def clip_path(topic: Topic, index: int) -> Path:
    return clips_dir(topic) / f"scene_{index:03d}.mp4"


# ═══ planning ════════════════════════════════════════════════════
def clip_count(runtime: float) -> int:
    """
    How many Veo clips cover the narration.

    Veo offers 4, 6 or 8 second clips and 1080p is only offered at 8, so every
    clip is VEO_CLIP_SECONDS long and the last one overshoots. The overshoot is
    cut in conform(), never padded, so the video can only ever be trimmed down
    to the voice — it cannot run out early.
    """
    return max(1, math.ceil(runtime / VEO_CLIP_SECONDS))


def _check_budget(count: int) -> None:
    if count > VEO_MAX_CLIPS:
        raise RuntimeError(
            f"This narration needs {count} Veo clips at {VEO_CLIP_SECONDS} s "
            f"each, over the VEO_MAX_CLIPS guard of {VEO_MAX_CLIPS}. Every "
            f"clip is a separate billed generation. Raise VEO_MAX_CLIPS in "
            f"config.py only if you mean to spend that."
        )


# ═══ scene prompts ═══════════════════════════════════════════════
SYSTEM = f"""You write shot prompts for Veo, Google's text-to-video model, for \
the LearnWithAvisha chemical engineering channel. You return JSON and nothing else.

You are given a narration script and the visual beats it introduces. Split the
narration into consecutive shots of exactly {VEO_CLIP_SECONDS} seconds and
write one Veo prompt per shot.

WHAT EACH PROMPT MUST CARRY. Veo holds no memory between clips, so every prompt
repeats the look from scratch. A prompt that says "the same exchanger as before"
produces a different exchanger.

- Subject: the equipment or detail on screen for those {VEO_CLIP_SECONDS} seconds.
- Camera: one move only. Slow push, slow orbit, locked off. Never a cut.
- Light: the plant look — dim industrial interior, deep shadow, the near-black
  {BACKGROUND} cast of the channel's background, hard practical light sources.
- Palette, repeated in words every single time: hot fluid runs red into orange,
  cold fluid runs blue into pale blue, heat glows yellow, steel is cool grey.
- Finish: "cinematic industrial footage, shallow depth of field, no text,
  no captions, no lettering, no watermark, no people speaking".

HARD RULES.
- NEVER ask for text, numbers, labels, captions, titles or UI in the frame.
  Veo renders lettering as unreadable garbage. Temperature values and labels are
  added later in post, not generated.
- NEVER name a real company, plant or trademark.
- NEVER ask for a face in close-up or a person talking to camera.
- One continuous action per shot. No "then", no scene changes inside a clip.
- Describe only what a camera could see. No narration, no explanation.

Return JSON matching the schema exactly. `shots` must have exactly the number of
entries you are told to produce, in narration order."""

PROMPT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["shots"],
    "properties": {
        "shots": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["index", "covers", "prompt"],
                "properties": {
                    "index": {"type": "integer"},
                    "covers": {
                        "type": "string",
                        "description": "the sentence(s) of narration this shot sits under",
                    },
                    "prompt": {"type": "string"},
                },
            },
        }
    },
}


def derive_prompts(topic: Topic, script: str, runtime: float,
                   beats: list[str], key_points: list[str]) -> list[dict]:
    """Turn the narration and its visual beats into one Veo prompt per shot."""
    count = clip_count(runtime)
    _check_budget(count)

    request = "\n".join([
        f"Topic: {topic.topic_name}",
        f"Subject: {topic.subject}",
        f"Narration runtime: {runtime:.3f} s",
        f"Produce EXACTLY {count} shots of {VEO_CLIP_SECONDS} s each.",
        "",
        "THE NARRATION — split it across the shots by word count, so shot N",
        "sits under the sentences actually being spoken at that moment.",
        "----------------",
        script,
        "----------------",
        "",
        "Visual beats, in narration order:",
        *(f"  {i}. {b}" for i, b in enumerate(beats, 1)),
        "",
        "Recap points, for the closing shots:",
        *(f"  - {p}" for p in key_points),
    ])

    log.info("  deriving %d scene prompts from the narration", count)
    data = llm_client.call_json(SYSTEM, request, PROMPT_SCHEMA, max_tokens=32000)
    shots = data.get("shots", [])

    if len(shots) != count:
        log.warning("  model returned %d shots, expected %d — fitting to %d",
                    len(shots), count, count)
        shots = _fit(shots, count)

    for i, shot in enumerate(shots):
        shot["index"] = i
    return shots


def _fit(shots: list[dict], count: int) -> list[dict]:
    """Trim a long shot list, or repeat the last shot to cover a short one."""
    if not shots:
        raise RuntimeError("the model returned no shots at all")
    shots = shots[:count]
    while len(shots) < count:
        shots.append(dict(shots[-1]))
    return shots


def load_prompts(topic: Topic) -> list[dict]:
    """Read scene_prompts.json. Hand-written files win over derived ones."""
    data = json.loads(prompts_path(topic).read_text(encoding="utf-8"))
    shots = data["shots"] if isinstance(data, dict) else data
    if not shots:
        raise RuntimeError(f"{prompts_path(topic)} contains no shots")
    return shots


def save_prompts(topic: Topic, shots: list[dict]) -> Path:
    path = prompts_path(topic)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"model": VEO_MODEL,
                    "clip_seconds": VEO_CLIP_SECONDS,
                    "shots": shots}, indent=2) + "\n",
        encoding="utf-8")
    log.info("  wrote %d scene prompts -> %s", len(shots), path.name)
    return path


# ═══ Veo ═════════════════════════════════════════════════════════
def _client():
    """The google-genai client. Imported lazily so the rest of the pipeline
    runs without the SDK installed."""
    try:
        from google import genai
    except ImportError as exc:            # pragma: no cover
        raise RuntimeError(
            "google-genai is not installed. `pip install google-genai` — it is "
            "the SDK for the Veo generation calls."
        ) from exc
    return genai.Client(api_key=require_env(GEMINI_API_KEY_ENV))


def _video_config():
    from google.genai import types
    return types.GenerateVideosConfig(
        aspect_ratio=VEO_ASPECT_RATIO,
        resolution=VEO_RESOLUTION,
        duration_seconds=str(VEO_CLIP_SECONDS),
    )


def _download(client, generated, destination: Path) -> None:
    """
    Save the finished clip.

    The SDK has moved this around between releases: older builds return a file
    handle you call .save() on, newer ones take a destination straight on
    files.download(). Try the documented path first and fall back rather than
    pinning the pipeline to one SDK minor version.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        client.files.download(file=generated.video, destination=str(destination))
        if destination.exists() and destination.stat().st_size > 0:
            return
    except TypeError:
        pass
    client.files.download(file=generated.video)
    generated.video.save(str(destination))


class QuotaError(RuntimeError):
    """Veo refused on billing or permission grounds. Retrying cannot help."""


def _classify(exc: Exception) -> Exception:
    """
    Turn an SDK exception into something the retry loop can reason about.

    A 429 from Veo is not a transient blip — the free tier carries no video
    quota at all, so the same call will fail identically forever. Retrying it
    three times just triples the wait before the operator sees the real cause.
    """
    text = str(exc)
    if "RESOURCE_EXHAUSTED" in text or "429" in text:
        return QuotaError(
            "Veo returned 429 RESOURCE_EXHAUSTED. Video generation is a paid "
            "feature and this key has no video quota — text calls on the same "
            "key still succeed. Enable billing on the Google Cloud project "
            "behind this key, then rerun; finished clips are reused. "
            "https://ai.google.dev/gemini-api/docs/rate-limits"
        )
    if "PERMISSION_DENIED" in text or "403" in text:
        return QuotaError(
            "Veo returned 403 PERMISSION_DENIED. The key is valid but not "
            "entitled to video generation on this project."
        )
    return exc


def generate_clip(client, prompt: str, destination: Path) -> Path:
    """One Veo generation, start to saved MP4. Blocks until the clip is done."""
    from google.genai import types

    try:
        operation = client.models.generate_videos(
            model=VEO_MODEL,
            source=types.GenerateVideosSource(prompt=prompt),
            config=_video_config(),
        )
    except Exception as exc:                                # noqa: BLE001
        raise _classify(exc) from exc

    waited = 0.0
    while not operation.done:
        if waited > VEO_POLL_TIMEOUT:
            raise RuntimeError(
                f"Veo did not finish {destination.name} within "
                f"{VEO_POLL_TIMEOUT:.0f} s. The operation may still complete — "
                f"rerun the stage and the finished clips are reused."
            )
        time.sleep(VEO_POLL_SECONDS)
        waited += VEO_POLL_SECONDS
        operation = client.operations.get(operation)

    error = getattr(operation, "error", None)
    if error:
        raise RuntimeError(f"Veo refused {destination.name}: {error}")

    videos = getattr(operation.response, "generated_videos", None) or []
    if not videos:
        raise RuntimeError(
            f"Veo returned no video for {destination.name}. This is usually a "
            f"safety filter on the prompt rather than a fault — reword the shot."
        )

    _download(client, videos[0], destination)
    log.info("  clip %s — %.1f s, %.1f MB", destination.name,
             _duration(destination), destination.stat().st_size / 1e6)
    return destination


# ═══ ffmpeg ══════════════════════════════════════════════════════
def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True,
                            timeout=FFMPEG_TIMEOUT)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{result.stderr[-3000:]}")


def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def _watermark_filter() -> str:
    """
    The LWA monogram, bottom right, on every frame.

    Manim used to draw this into the scene. Veo cannot be trusted with
    lettering, so it is burned on afterwards — which is strictly more reliable
    than the old path, since it no longer depends on the model complying.
    """
    if not WATERMARK_FONT.exists():
        log.warning("  watermark font missing at %s — shipping without the "
                    "monogram, which breaks the brand rule in SKILL.md",
                    WATERMARK_FONT)
        return ""
    return (
        f",drawtext=fontfile='{WATERMARK_FONT}':text='{WATERMARK_TEXT}'"
        f":fontcolor=white@{WATERMARK_OPACITY}:fontsize=44"
        f":x=w-tw-56:y=h-th-48"
    )


def conform(clips: list[Path], runtime: float, destination: Path) -> Path:
    """
    Join the clips, cut to the narration, and force the frozen output format.

    Everything the old renderer got for free from Manim is imposed here:
    resolution, frame rate, the watermark, and a duration that matches the
    voiceover exactly. Veo's own audio track is dropped with -an.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    listing = destination.parent / "_concat.txt"
    listing.write_text(
        "".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")

    width, height = RESOLUTION
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={BACKGROUND},"
        f"fps={FPS}"
        f"{_watermark_filter()}"
    )

    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
        "-t", f"{runtime:.3f}",
        "-vf", video_filter,
        "-an",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(destination),
    ])
    listing.unlink(missing_ok=True)

    actual = _duration(destination)
    log.info("  conformed %s — %.3f s against a %.3f s narration (%+.3f s)",
             destination.name, actual, runtime, actual - runtime)
    return destination


# ═══ stage entry points ══════════════════════════════════════════
def generate(topic: Topic, script: str, runtime: float,
             beats: list[str], key_points: list[str],
             attempts: int = 3) -> Path:
    """
    Produce every Veo clip for the topic.

    `attempts` is per clip, not per episode. A failed clip is retried on its
    own; the clips that already succeeded are never regenerated, because each
    one costs money. Rerunning the stage resumes where it stopped.
    """
    topic.ensure_dir()

    if prompts_path(topic).exists():
        shots = load_prompts(topic)
        log.info("  %s already exists — using its %d shots",
                 SCENE_PROMPTS_FILE, len(shots))
    else:
        shots = derive_prompts(topic, script, runtime, beats, key_points)
        save_prompts(topic, shots)

    _check_budget(len(shots))
    clips_dir(topic).mkdir(parents=True, exist_ok=True)

    total = len(shots)
    log.info("  Veo — %d clips of %d s (%s, %s)",
             total, VEO_CLIP_SECONDS, VEO_MODEL, VEO_RESOLUTION)

    client = None
    for shot in shots:
        index = int(shot["index"])
        destination = clip_path(topic, index)
        if destination.exists() and destination.stat().st_size > 0:
            log.info("  clip %03d/%03d already generated — skipping",
                     index + 1, total)
            continue

        client = client or _client()
        last: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                log.info("  clip %03d/%03d — generating (attempt %d/%d)",
                         index + 1, total, attempt, attempts)
                generate_clip(client, shot["prompt"], destination)
                break
            except QuotaError:
                # Not transient. Fail the whole stage now rather than burning
                # two more identical refusals per clip.
                destination.unlink(missing_ok=True)
                raise
            except Exception as exc:                        # noqa: BLE001
                last = exc
                log.warning("  clip %03d failed: %s", index + 1, exc)
                destination.unlink(missing_ok=True)
        else:
            raise RuntimeError(
                f"{topic.key}: clip {index + 1} failed {attempts} times. "
                f"Last problem:\n{last}"
            )

    return prompts_path(topic)


def render(topic: Topic) -> Path:
    """Join this topic's clips into animation.mp4, cut to the narration."""
    from voiceover import duration_seconds

    clips = sorted(clips_dir(topic).glob("scene_*.mp4"))
    if not clips:
        raise RuntimeError(f"{topic.key}: no clips in {clips_dir(topic)} — run "
                           f"the generate step first.")

    runtime = duration_seconds(topic.voiceover_path)
    covered = sum(_duration(c) for c in clips)
    if covered + 0.05 < runtime:
        raise RuntimeError(
            f"{topic.key}: the clips total {covered:.3f} s but the narration is "
            f"{runtime:.3f} s. The screen would go blank while the voice is "
            f"still speaking, which SKILL.md forbids. Generate "
            f"{clip_count(runtime) - len(clips)} more clip(s)."
        )

    return conform(clips, runtime, topic.rendered_path)
