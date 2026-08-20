"""
ElevenLabs voiceover generation — Leandra, Eleven v3.

The animation is built to the voiceover, never the other way round, so this
stage runs BEFORE the Manim code is generated: the exact duration of the MP3
is what the animation is timed against. SKILL.md requires them to match.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

import requests

from config import (AUDIO_FORMAT, ELEVENLABS_API_KEY_ENV, ELEVENLABS_BASE,
                    ELEVENLABS_MODEL, VOICE_ID_ENV, VOICE_NAME, VOICE_SETTINGS,
                    require_env)

log = logging.getLogger(__name__)

TIMEOUT = 300


def _headers() -> dict:
    return {"xi-api-key": require_env(ELEVENLABS_API_KEY_ENV)}


def resolve_voice_id(name: str = VOICE_NAME) -> str:
    """
    Look the voice up by name so no ID is hard-coded or guessed.
    ELEVENLABS_VOICE_ID short-circuits this once the ID is known.
    """
    cached = os.environ.get(VOICE_ID_ENV, "").strip()
    if cached:
        return cached

    resp = requests.get(f"{ELEVENLABS_BASE}/voices", headers=_headers(),
                        timeout=TIMEOUT)
    resp.raise_for_status()
    voices = resp.json().get("voices", [])

    for voice in voices:
        if voice.get("name", "").strip().lower() == name.lower():
            log.info("  voice '%s' -> %s", name, voice["voice_id"])
            return voice["voice_id"]

    available = ", ".join(sorted(v.get("name", "?") for v in voices)) or "(none)"
    raise RuntimeError(
        f"Voice '{name}' is not in this ElevenLabs account. Available: {available}. "
        f"Add it from the Voice Library, or set {VOICE_ID_ENV} to its ID."
    )


def duration_seconds(path: Path) -> float:
    """Exact media duration via ffprobe — the number the animation is timed to."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def generate(script: str, destination: Path, voice_id: str | None = None) -> float:
    """Synthesise the script to MP3. Returns the duration in seconds."""
    voice_id = voice_id or resolve_voice_id()
    destination.parent.mkdir(parents=True, exist_ok=True)

    log.info("  ElevenLabs — %s / %s, %d characters",
             VOICE_NAME, ELEVENLABS_MODEL, len(script))

    resp = requests.post(
        f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}",
        headers={**_headers(), "Content-Type": "application/json",
                 "Accept": "audio/mpeg"},
        params={"output_format": AUDIO_FORMAT},
        json={
            "text": script,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": VOICE_SETTINGS,
        },
        timeout=TIMEOUT,
    )

    if resp.status_code != 200:
        detail = resp.text[:600]
        raise RuntimeError(f"ElevenLabs returned {resp.status_code}: {detail}")

    destination.write_bytes(resp.content)
    seconds = duration_seconds(destination)
    log.info("  wrote %s — %.3f s (%.1f min)", destination.name, seconds, seconds / 60)

    # The narration length drives the animation, so record it next to the audio.
    (destination.parent / "voiceover.json").write_text(
        json.dumps({
            "voice": VOICE_NAME,
            "voice_id": voice_id,
            "model": ELEVENLABS_MODEL,
            "settings": VOICE_SETTINGS,
            "format": AUDIO_FORMAT,
            "duration_seconds": round(seconds, 3),
            "characters": len(script),
        }, indent=2),
        encoding="utf-8",
    )
    return seconds
