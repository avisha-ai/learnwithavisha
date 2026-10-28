"""
ffmpeg assembly — animation.mp4 + voiceover.mp3 -> final_video.mp4.

Also extracts the thumbnail. SKILL.md sets the thumbnail as the first frame of
the animation; frame zero is a near-empty stage, so the frame is taken a little
way in, once the first element has been drawn.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from queue_manager import Topic
from voiceover import duration_seconds

log = logging.getLogger(__name__)

SYNC_TOLERANCE = 0.75       # seconds — video vs. narration
THUMBNAIL_AT = 6.0          # seconds into the animation


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{result.stderr[-3000:]}")


def check_sync(video: Path, audio: Path, tolerance: float = SYNC_TOLERANCE) -> float:
    """
    Verify the animation matches the narration before they are combined.

    -shortest would otherwise quietly truncate whichever is longer: a short
    animation cuts the voice off mid-sentence, a long one ends on silence.
    """
    v, a = duration_seconds(video), duration_seconds(audio)
    drift = v - a
    if abs(drift) > tolerance:
        raise RuntimeError(
            f"Animation is {v:.3f} s but the narration is {a:.3f} s "
            f"({drift:+.3f} s drift, tolerance {tolerance:.2f} s). "
            f"SKILL.md requires them to match — regenerate the animation."
        )
    log.info("  sync ok — video %.3f s, audio %.3f s (%+.3f s)", v, a, drift)
    return drift


def thumbnail(video: Path, destination: Path, at: float = THUMBNAIL_AT) -> Path:
    at = min(at, max(0.0, duration_seconds(video) - 0.5))
    _run(["ffmpeg", "-y", "-ss", f"{at:.2f}", "-i", str(video),
          "-frames:v", "1", "-q:v", "2", str(destination)])
    log.info("  thumbnail from t=%.1fs -> %s", at, destination.name)
    return destination


def combine(video: Path, audio: Path, destination: Path) -> Path:
    """Mux the rendered animation with the narration. Video is copied, not re-encoded."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-i", str(video), "-i", str(audio),
          "-map", "0:v:0", "-map", "1:a:0",
          "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
          "-movflags", "+faststart", "-shortest", str(destination)])
    log.info("  assembled %s — %.3f s", destination.name, duration_seconds(destination))
    return destination


def assemble(topic: Topic) -> Path:
    """Full assembly stage for one topic: verify sync, mux, extract thumbnail."""
    for required in (topic.rendered_path, topic.voiceover_path):
        if not required.exists():
            raise FileNotFoundError(f"{topic.key}: missing {required}")

    check_sync(topic.rendered_path, topic.voiceover_path)
    combine(topic.rendered_path, topic.voiceover_path, topic.video_path)
    thumbnail(topic.rendered_path, topic.thumbnail_path)
    return topic.video_path
