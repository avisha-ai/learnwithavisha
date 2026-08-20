"""
topic_queue.csv is the single source of truth for pipeline state.

Status flow
-----------
    pending             nothing done yet
    awaiting_approval   script written + reviewed, waiting for Mayur
    changes_requested   Mayur wants edits — writer re-runs
    approved            Mayur approved — production may start
    produced            final_video.mp4 exists on disk
    uploaded            on YouTube as private, publishAt is set
    published           the scheduled time has passed
    failed              a stage raised — see the notes column

Mayur approves by editing one cell: status -> approved.
"""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass, field, fields
from pathlib import Path

from config import CURRICULUM_CSV, IST, topic_dir

PENDING = "pending"
AWAITING_APPROVAL = "awaiting_approval"
CHANGES_REQUESTED = "changes_requested"
APPROVED = "approved"
PRODUCED = "produced"
UPLOADED = "uploaded"
PUBLISHED = "published"
FAILED = "failed"

VALID_STATUSES = {
    PENDING, AWAITING_APPROVAL, CHANGES_REQUESTED, APPROVED,
    PRODUCED, UPLOADED, PUBLISHED, FAILED,
}


@dataclass
class Topic:
    subject_number: int
    subject: str
    subject_slug: str
    topic_number: int
    topic_name: str
    slug: str
    status: str
    ref_nptel: str
    ref_libretexts: str
    ref_mit_ocw: str
    youtube_id: str = ""
    scheduled_at_ist: str = ""
    updated_at: str = ""
    notes: str = ""

    # ── derived ──────────────────────────────────────────────────
    @property
    def key(self) -> str:
        return f"S{self.subject_number}T{self.topic_number}"

    @property
    def dir(self) -> Path:
        return topic_dir(self.subject_slug, self.subject_number, self.slug)

    @property
    def script_path(self) -> Path:
        return self.dir / "script.txt"

    @property
    def review_path(self) -> Path:
        return self.dir / "review.json"

    @property
    def animation_path(self) -> Path:
        return self.dir / "animation.py"

    @property
    def voiceover_path(self) -> Path:
        return self.dir / "voiceover.mp3"

    @property
    def rendered_path(self) -> Path:
        return self.dir / "animation.mp4"

    @property
    def video_path(self) -> Path:
        return self.dir / "final_video.mp4"

    @property
    def thumbnail_path(self) -> Path:
        return self.dir / "thumbnail.jpg"

    @property
    def scene_name(self) -> str:
        """Manim scene class name — derived, so generator and renderer agree."""
        words = [w for w in self.slug.split("_")[1:] if w]
        return "".join(w.capitalize() for w in words)[:40] + "Scene"

    def ensure_dir(self) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        return self.dir


_FIELDS = [f.name for f in fields(Topic)]
_INT_FIELDS = {"subject_number", "topic_number"}


def _row_to_topic(row: dict) -> Topic:
    data = {k: (row.get(k) or "") for k in _FIELDS}
    for k in _INT_FIELDS:
        data[k] = int(data[k])
    return Topic(**data)


def load(path: Path = CURRICULUM_CSV) -> list[Topic]:
    with path.open(newline="", encoding="utf-8") as f:
        return [_row_to_topic(r) for r in csv.DictReader(f)]


def save(topics: list[Topic], path: Path = CURRICULUM_CSV) -> None:
    """Rewrite the whole CSV atomically — never leave a half-written queue."""
    tmp = path.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS)
        w.writeheader()
        for t in topics:
            w.writerow({k: getattr(t, k) for k in _FIELDS})
    tmp.replace(path)


def find(key_or_name: str, path: Path = CURRICULUM_CSV) -> Topic:
    """Look a topic up by 'S1T1' key, by slug, or by exact topic name."""
    needle = key_or_name.strip()
    topics = load(path)
    for t in topics:
        if needle.upper() == t.key or needle == t.slug or needle == t.topic_name:
            return t
    lowered = needle.lower()
    matches = [t for t in topics if lowered in t.topic_name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(f"{t.key} {t.topic_name}" for t in matches)
        raise KeyError(f"'{needle}' is ambiguous — matches: {names}")
    raise KeyError(f"No topic matches '{needle}'")


def next_in_status(status: str, path: Path = CURRICULUM_CSV) -> Topic | None:
    """First topic in curriculum order with the given status."""
    for t in load(path):
        if t.status == status:
            return t
    return None


def update(topic: Topic, path: Path = CURRICULUM_CSV, **changes) -> Topic:
    """Apply changes to one topic and persist the whole queue."""
    status = changes.get("status")
    if status is not None and status not in VALID_STATUSES:
        raise ValueError(f"Unknown status '{status}'")

    topics = load(path)
    for t in topics:
        if t.key == topic.key:
            for k, v in changes.items():
                setattr(t, k, v)
            t.updated_at = dt.datetime.now(IST).isoformat(timespec="seconds")
            save(topics, path)
            return t
    raise KeyError(f"{topic.key} is not in {path}")


def scheduled_slots(path: Path = CURRICULUM_CSV) -> list[dt.datetime]:
    """Every publish slot already claimed, oldest first — drives alternation."""
    out = []
    for t in load(path):
        if t.scheduled_at_ist:
            out.append(dt.datetime.fromisoformat(t.scheduled_at_ist))
    return sorted(out)
