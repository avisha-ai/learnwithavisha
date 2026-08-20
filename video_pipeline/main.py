#!/usr/bin/env python
"""
LearnWithAvisha — video production pipeline.

    script  ->  [Mayur approves]  ->  voiceover  ->  animate  ->  assemble  ->  upload

Why voiceover runs before the animation
---------------------------------------
SKILL.md freezes one rule above the others: the animation must match the
voiceover exactly and the screen must never go blank while the voice is still
speaking. That only holds if the narration's exact duration is known before the
scene is written, so the MP3 is generated first and its length is an input to
the Manim generator. The pilot was built the same way.

Each stage writes its artifacts into output/subjectN_<subject>/<slug>/ and
records progress in curriculum/topic_queue.csv. Stages are resumable: a stage
whose artifact already exists is skipped unless --force is given.

Examples
--------
    python main.py --status
    python main.py --topic S1T1 --stages script
    python main.py --topic S1T1 --approve
    python main.py --topic S1T1 --stages voiceover,animate,assemble
    python main.py --topic S1T1 --stages upload --dry-run
    python main.py                     # next approved topic, all the way through
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import sys
import traceback
from pathlib import Path

import assembler
import manim_generator
import queue_manager as q
import script_reviewer
import voiceover as vo
import youtube_upload as yt
from config import IST, OUTPUT_DIR

log = logging.getLogger("pipeline")

STAGES = ("script", "voiceover", "animate", "assemble", "upload")


# ── per-topic state ──────────────────────────────────────────────
def state_path(topic: q.Topic) -> Path:
    return topic.dir / "state.json"


def load_state(topic: q.Topic) -> dict:
    path = state_path(topic)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_state(topic: q.Topic, **changes) -> dict:
    topic.ensure_dir()
    state = {**load_state(topic), **changes}
    state_path(topic).write_text(json.dumps(state, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    return state


# ── stages ───────────────────────────────────────────────────────
def stage_script(topic: q.Topic, force: bool = False, **_) -> q.Topic:
    """Claude call 1 + Claude call 2. Ends at the human approval gate."""
    if topic.script_path.exists() and not force:
        log.info("script.txt already exists — skipping (use --force to rewrite)")
        return topic

    script, draft, review = script_reviewer.write_and_review(topic)

    topic.ensure_dir()
    topic.script_path.write_text(script + "\n", encoding="utf-8")
    topic.review_path.write_text(json.dumps(review, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    save_state(topic,
               summary=draft["summary"],
               key_points=draft.get("key_points", []),
               visual_beats=draft.get("visual_beats", []),
               sources_read=draft.get("sources_read", []),
               word_count=len(script.split()))

    topic = q.update(topic, status=q.AWAITING_APPROVAL,
                     notes=review.get("notes_for_mayur", "")[:200])

    log.info("")
    log.info("  Script ready for approval:  %s", topic.script_path)
    log.info("  Review:                     %s", topic.review_path)
    log.info("  Mayur: read it, then set status to 'approved' in "
             "curriculum/topic_queue.csv")
    log.info("  (or run: python main.py --topic %s --approve)", topic.key)
    return topic


def stage_voiceover(topic: q.Topic, force: bool = False, **_) -> q.Topic:
    """ElevenLabs — Leandra, Eleven v3. Its duration drives the animation."""
    if topic.voiceover_path.exists() and not force:
        seconds = vo.duration_seconds(topic.voiceover_path)
        log.info("voiceover.mp3 already exists — %.3f s", seconds)
    else:
        script = topic.script_path.read_text(encoding="utf-8").strip()
        seconds = vo.generate(script, topic.voiceover_path)
    save_state(topic, runtime_seconds=round(seconds, 3))
    return topic


def stage_animate(topic: q.Topic, force: bool = False, **_) -> q.Topic:
    """Claude call 3 writes the Manim scene, then it renders at 1080p60."""
    state = load_state(topic)
    runtime = state.get("runtime_seconds")
    if not runtime:
        raise RuntimeError(f"{topic.key}: run the voiceover stage first — the "
                           f"animation is timed to the narration.")

    if not topic.animation_path.exists() or force:
        manim_generator.generate(
            topic,
            topic.script_path.read_text(encoding="utf-8").strip(),
            runtime,
            state.get("visual_beats", []),
            state.get("key_points", []),
        )
    else:
        log.info("animation.py already exists — skipping generation")

    if not topic.rendered_path.exists() or force:
        manim_generator.render(topic)
    else:
        log.info("animation.mp4 already exists — skipping render")
    return topic


def stage_assemble(topic: q.Topic, force: bool = False, **_) -> q.Topic:
    """ffmpeg — mux animation and narration, extract the thumbnail."""
    if topic.video_path.exists() and not force:
        log.info("final_video.mp4 already exists — skipping")
    else:
        assembler.assemble(topic)
    return q.update(topic, status=q.PRODUCED)


def stage_upload(topic: q.Topic, dry_run: bool = False, **_) -> q.Topic:
    """YouTube — private now, public at the next Tuesday/Thursday 8pm IST."""
    state = load_state(topic)
    summary = state.get("summary")
    if not summary:
        raise RuntimeError(f"{topic.key}: no summary in state.json — rerun the "
                           f"script stage to regenerate the description text.")

    slot = yt.next_publish_slot(taken=q.scheduled_slots())
    result = yt.upload(topic, summary, slot, dry_run=dry_run)

    if dry_run:
        return topic
    return q.update(topic, status=q.UPLOADED,
                    youtube_id=result["video_id"],
                    scheduled_at_ist=result["scheduled_at_ist"])


STAGE_FUNCS = {
    "script": stage_script,
    "voiceover": stage_voiceover,
    "animate": stage_animate,
    "assemble": stage_assemble,
    "upload": stage_upload,
}

# Stages that must not run until a human has approved the script.
GATED = ("voiceover", "animate", "assemble", "upload")


# ── reporting ────────────────────────────────────────────────────
def show_status() -> None:
    topics = q.load()
    counts: dict[str, int] = {}
    for t in topics:
        counts[t.status] = counts.get(t.status, 0) + 1

    print(f"\ntopic_queue.csv — {len(topics)} topics\n")
    for status in (q.PENDING, q.AWAITING_APPROVAL, q.CHANGES_REQUESTED, q.APPROVED,
                   q.PRODUCED, q.UPLOADED, q.PUBLISHED, q.FAILED):
        if counts.get(status):
            print(f"  {status:<20} {counts[status]}")

    active = [t for t in topics if t.status not in (q.PENDING,)]
    if active:
        print("\n  key    status              topic")
        print("  " + "-" * 68)
        for t in active:
            print(f"  {t.key:<6} {t.status:<19} {t.topic_name[:44]}")

    upcoming = q.scheduled_slots()
    nxt = yt.next_publish_slot(taken=upcoming)
    print(f"\n  next publish slot: {yt.describe_slot(nxt)}\n")


def approve(topic: q.Topic) -> q.Topic:
    if topic.status not in (q.AWAITING_APPROVAL, q.CHANGES_REQUESTED):
        log.warning("%s is '%s', not awaiting approval", topic.key, topic.status)
    review = json.loads(topic.review_path.read_text(encoding="utf-8")) \
        if topic.review_path.exists() else {}
    stamp = dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    log.info("%s approved at %s", topic.key, stamp)
    return q.update(topic, status=q.APPROVED,
                    notes=f"approved {stamp}; "
                          f"{len(review.get('discrepancies', []))} review notes")


# ── CLI ──────────────────────────────────────────────────────────
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="LearnWithAvisha video production pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples")[-1],
    )
    p.add_argument("--topic", help="S1T1, a slug, or part of the topic name. "
                                   "Default: the next topic ready to move.")
    p.add_argument("--stages", default=",".join(STAGES),
                   help=f"comma separated subset of: {', '.join(STAGES)}")
    p.add_argument("--force", action="store_true",
                   help="redo stages whose artifacts already exist")
    p.add_argument("--dry-run", action="store_true",
                   help="build the YouTube request but do not upload")
    p.add_argument("--approve", action="store_true",
                   help="record Mayur's approval and exit")
    p.add_argument("--auto-approve", action="store_true",
                   help="skip the human gate — pipeline testing only")
    p.add_argument("--status", action="store_true", help="show the queue and exit")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def pick_topic(explicit: str | None) -> q.Topic:
    if explicit:
        return q.find(explicit)
    for status in (q.APPROVED, q.CHANGES_REQUESTED, q.PRODUCED, q.PENDING):
        topic = q.next_in_status(status)
        if topic:
            return topic
    raise SystemExit("Nothing left in the queue to work on.")


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.status:
        show_status()
        return 0

    topic = pick_topic(args.topic)

    if args.approve:
        approve(topic)
        return 0

    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    unknown = [s for s in stages if s not in STAGE_FUNCS]
    if unknown:
        raise SystemExit(f"Unknown stage(s): {', '.join(unknown)}. "
                         f"Valid: {', '.join(STAGES)}")

    log.info("=" * 72)
    log.info("%s  %s", topic.key, topic.topic_name)
    log.info("Subject %d — %s", topic.subject_number, topic.subject)
    log.info("Status: %s   Stages: %s", topic.status, " -> ".join(stages))
    log.info("=" * 72)

    for stage in stages:
        # The human gate. Nothing is produced from an unapproved script.
        if stage in GATED and topic.status in (q.PENDING, q.AWAITING_APPROVAL,
                                               q.CHANGES_REQUESTED):
            if args.auto_approve:
                log.warning("\n--auto-approve: skipping the human gate "
                            "(pipeline testing only)")
                topic = approve(topic)
            else:
                log.info("")
                log.info("STOPPED at the approval gate.")
                log.info("  %s is '%s'. Mayur must approve the script before "
                         "production.", topic.key, topic.status)
                log.info("  Read:    %s", topic.script_path)
                log.info("  Approve: python main.py --topic %s --approve", topic.key)
                return 2

        log.info("\n--- %s ---", stage)
        try:
            topic = STAGE_FUNCS[stage](topic, force=args.force, dry_run=args.dry_run)
        except Exception as exc:
            log.error("\nStage '%s' failed for %s: %s", stage, topic.key, exc)
            if args.verbose:
                traceback.print_exc()
            q.update(topic, status=q.FAILED,
                     notes=f"{stage} failed: {str(exc)[:180]}")
            return 1

    log.info("\n" + "=" * 72)
    log.info("%s — done. Status: %s", topic.key, q.find(topic.key).status)
    if topic.video_path.exists():
        log.info("Video: %s", topic.video_path)
    log.info("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
