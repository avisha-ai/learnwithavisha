"""
YouTube Data API upload — title, description, tags, playlist, thumbnail and
the frozen Tuesday/Thursday 8:00 PM IST publish schedule.

How the schedule works
----------------------
Every video is uploaded PRIVATE with a publishAt timestamp, so YouTube itself
flips it public at the scheduled moment and nothing has to run at 8pm.

The slot is always the next Tuesday-or-Thursday 20:00 IST that is both far
enough away (MIN_LEAD_HOURS) and strictly after every slot already claimed in
topic_queue.csv. Alternation falls out of that rule: consecutive Tue/Thu slots
alternate by construction, so video N+1 lands on the other day from video N
without anything tracking whose turn it is.

CLAUDE_MASTER.md: the first 5-6 videos are uploaded by hand. This module runs
from video 7 onwards.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
from pathlib import Path

from config import (BASE_TAGS, CHANNEL, DESCRIPTION_TEMPLATE, IST,
                    MIN_LEAD_HOURS, PUBLISH_HOUR_IST, PUBLISH_MINUTE_IST,
                    PUBLISH_WEEKDAYS, YOUTUBE_CATEGORY_ID, YOUTUBE_CLIENT_SECRETS,
                    YOUTUBE_SCOPES, YOUTUBE_TOKEN)
from queue_manager import Topic

log = logging.getLogger(__name__)

TITLE_LIMIT = 100
DESCRIPTION_LIMIT = 5000
TAGS_CHAR_LIMIT = 450       # YouTube's limit is 500 across all tags


# ══ scheduling ═══════════════════════════════════════════════════
def next_publish_slot(now: dt.datetime | None = None,
                      taken: list[dt.datetime] | None = None) -> dt.datetime:
    """
    The next free Tuesday-or-Thursday 20:00 IST slot.

    `taken` is every slot already claimed. The returned slot is strictly later
    than all of them, which is what makes the Tue/Thu days alternate.
    """
    now = (now or dt.datetime.now(IST)).astimezone(IST)
    cursor = now + dt.timedelta(hours=MIN_LEAD_HOURS)

    claimed = sorted(s.astimezone(IST) for s in (taken or []))
    if claimed and claimed[-1] >= cursor:
        cursor = claimed[-1]

    claimed_set = set(claimed)
    day = cursor.date()
    for offset in range(0, 60):
        candidate_day = day + dt.timedelta(days=offset)
        if candidate_day.weekday() not in PUBLISH_WEEKDAYS:
            continue
        slot = dt.datetime.combine(
            candidate_day,
            dt.time(PUBLISH_HOUR_IST, PUBLISH_MINUTE_IST),
            tzinfo=IST,
        )
        if slot > cursor and slot not in claimed_set:
            return slot

    raise RuntimeError("No Tuesday/Thursday slot found in the next 60 days.")


def to_rfc3339_utc(slot: dt.datetime) -> str:
    """publishAt must be UTC RFC3339 — e.g. 2026-08-25T14:30:00Z."""
    return slot.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def describe_slot(slot: dt.datetime) -> str:
    return slot.strftime("%A %d %B %Y, %I:%M %p IST").replace(" 0", " ")


# ══ metadata ═════════════════════════════════════════════════════
def build_title(topic: Topic) -> str:
    suffix = f" | {topic.subject} | {CHANNEL}"
    name = topic.topic_name
    if len(name) + len(suffix) > TITLE_LIMIT:
        suffix = f" | {CHANNEL}"
    if len(name) + len(suffix) > TITLE_LIMIT:
        name = name[:TITLE_LIMIT - len(suffix) - 1].rstrip(" —-") + "…"
    return f"{name}{suffix}"


def build_description(topic: Topic, summary: str) -> str:
    text = DESCRIPTION_TEMPLATE.format(
        topic_name=topic.topic_name,
        subject=topic.subject,
        summary=summary.strip(),
        ref_nptel=topic.ref_nptel,
        ref_libretexts=topic.ref_libretexts,
    )
    if "free" in text.lower().replace("freedom", ""):
        raise ValueError("Description contains the forbidden word 'free'.")
    return text[:DESCRIPTION_LIMIT]


def build_tags(topic: Topic) -> list[str]:
    words = [w for w in re.split(r"[^a-zA-Z0-9]+", topic.topic_name.lower())
             if len(w) > 3]
    candidates = [
        topic.topic_name.lower(),
        topic.subject.lower(),
        f"{topic.subject.lower()} chemical engineering",
        *words,
        *BASE_TAGS,
    ]

    tags, seen, budget = [], set(), 0
    for tag in candidates:
        tag = tag.strip()
        if not tag or tag in seen:
            continue
        if budget + len(tag) + 1 > TAGS_CHAR_LIMIT:
            continue
        seen.add(tag)
        tags.append(tag)
        budget += len(tag) + 1
    return tags


def playlist_title(topic: Topic) -> str:
    return f"{topic.subject} — {CHANNEL}"


def build_request_body(topic: Topic, summary: str, slot: dt.datetime) -> dict:
    return {
        "snippet": {
            "title": build_title(topic),
            "description": build_description(topic, summary),
            "tags": build_tags(topic),
            "categoryId": YOUTUBE_CATEGORY_ID,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": "private",       # flips public at publishAt
            "publishAt": to_rfc3339_utc(slot),
            "selfDeclaredMadeForKids": False,
            "license": "youtube",
            "embeddable": True,
        },
    }


# ══ API ══════════════════════════════════════════════════════════
def service():
    """Authenticated YouTube Data API client. Opens a browser on first run."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if YOUTUBE_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(YOUTUBE_TOKEN),
                                                      YOUTUBE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not YOUTUBE_CLIENT_SECRETS.exists():
                raise FileNotFoundError(
                    f"Missing {YOUTUBE_CLIENT_SECRETS}.\n"
                    f"Google Cloud console -> APIs & Services -> Credentials -> "
                    f"OAuth client ID -> Desktop app -> download the JSON and "
                    f"save it there. Enable the YouTube Data API v3 first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(YOUTUBE_CLIENT_SECRETS), YOUTUBE_SCOPES)
            creds = flow.run_local_server(port=0)
        YOUTUBE_TOKEN.parent.mkdir(parents=True, exist_ok=True)
        YOUTUBE_TOKEN.write_text(creds.to_json(), encoding="utf-8")
        YOUTUBE_TOKEN.chmod(0o600)

    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def _upload_video(yt, path: Path, body: dict) -> str:
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(path), chunksize=8 * 1024 * 1024,
                            resumable=True, mimetype="video/mp4")
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response, last = None, -1
    while response is None:
        status, response = request.next_chunk()
        if status:
            percent = int(status.progress() * 100)
            if percent >= last + 10:
                log.info("  uploading… %d%%", percent)
                last = percent
    return response["id"]


def _ensure_playlist(yt, title: str) -> str:
    """Find the subject playlist, creating it the first time."""
    page = None
    while True:
        resp = yt.playlists().list(part="snippet", mine=True,
                                   maxResults=50, pageToken=page).execute()
        for item in resp.get("items", []):
            if item["snippet"]["title"] == title:
                return item["id"]
        page = resp.get("nextPageToken")
        if not page:
            break

    log.info("  creating playlist '%s'", title)
    created = yt.playlists().insert(
        part="snippet,status",
        body={"snippet": {"title": title,
                          "description": f"{title} — curriculum order."},
              "status": {"privacyStatus": "public"}},
    ).execute()
    return created["id"]


def upload(topic: Topic, summary: str, slot: dt.datetime,
           dry_run: bool = False) -> dict:
    """Upload one produced video. Returns a record for the queue."""
    body = build_request_body(topic, summary, slot)

    log.info("  title:     %s", body["snippet"]["title"])
    log.info("  publishAt: %s  (%s)", body["status"]["publishAt"], describe_slot(slot))
    log.info("  playlist:  %s", playlist_title(topic))
    log.info("  tags:      %d", len(body["snippet"]["tags"]))

    if dry_run:
        log.info("  DRY RUN — nothing sent to YouTube")
        return {"video_id": None, "url": None, "scheduled_at_ist": slot.isoformat(),
                "dry_run": True, "body": body}

    if not topic.video_path.exists():
        raise FileNotFoundError(f"{topic.key}: {topic.video_path} does not exist")

    yt = service()
    video_id = _upload_video(yt, topic.video_path, body)
    log.info("  uploaded — video id %s", video_id)

    if topic.thumbnail_path.exists():
        from googleapiclient.http import MediaFileUpload
        yt.thumbnails().set(videoId=video_id,
                            media_body=MediaFileUpload(str(topic.thumbnail_path))
                            ).execute()
        log.info("  thumbnail set")

    playlist_id = _ensure_playlist(yt, playlist_title(topic))
    yt.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id,
                          "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
    ).execute()
    log.info("  added to playlist")

    return {"video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "scheduled_at_ist": slot.isoformat(),
            "dry_run": False}


# ══ CLI — schedule preview ═══════════════════════════════════════
def main(argv=None) -> int:
    import queue_manager

    parser = argparse.ArgumentParser(
        description="Preview the Tuesday/Thursday 8pm IST publish schedule.")
    parser.add_argument("-n", "--count", type=int, default=8,
                        help="how many upcoming slots to show")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    taken = queue_manager.scheduled_slots()
    if taken:
        print("Already claimed:")
        for slot in taken:
            print(f"  {describe_slot(slot)}")
        print()

    print(f"Next {args.count} slots:")
    for _ in range(args.count):
        slot = next_publish_slot(taken=taken)
        print(f"  {describe_slot(slot)}   ->  publishAt {to_rfc3339_utc(slot)}")
        taken.append(slot)
    return 0


if __name__ == "__main__":
    sys.exit(main())
