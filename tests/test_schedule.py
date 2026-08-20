"""
Tests for the frozen Tuesday/Thursday 8pm IST publish schedule.

Run: python -m pytest tests/ -q      (or: python tests/test_schedule.py)
"""

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "video_pipeline"))

from config import IST                                    # noqa: E402
from youtube_upload import (build_tags, build_title,      # noqa: E402
                            next_publish_slot, to_rfc3339_utc)

TUE, THU = 1, 3


def ist(y, m, d, hh=0, mm=0):
    return dt.datetime(y, m, d, hh, mm, tzinfo=IST)


def check(label, condition):
    print(f"  {'PASS' if condition else 'FAIL'}  {label}")
    return condition


def test_only_tuesday_or_thursday_at_2000():
    print("only Tuesday/Thursday at 20:00 IST")
    ok = True
    taken = []
    for _ in range(40):
        slot = next_publish_slot(now=ist(2026, 8, 20, 9), taken=taken)
        ok &= slot.weekday() in (TUE, THU) and slot.hour == 20 and slot.minute == 0
        taken.append(slot)
    return check("40 consecutive slots are all Tue/Thu 20:00", ok)


def test_days_alternate():
    print("days alternate automatically")
    taken, days = [], []
    for _ in range(20):
        slot = next_publish_slot(now=ist(2026, 8, 20, 9), taken=taken)
        taken.append(slot)
        days.append(slot.weekday())
    alternating = all(a != b for a, b in zip(days, days[1:]))
    return check(f"20 slots alternate: {['Tue' if d==TUE else 'Thu' for d in days[:6]]}…",
                 alternating)


def test_slots_strictly_increase():
    print("no slot is ever reused")
    taken = []
    for _ in range(30):
        taken.append(next_publish_slot(now=ist(2026, 8, 20, 9), taken=taken))
    return check("30 slots strictly increasing and unique",
                 all(a < b for a, b in zip(taken, taken[1:])) and len(set(taken)) == 30)


def test_lead_time_respected():
    print("today's slot is skipped when it is too close")
    # Thursday 20 Aug 2026, 19:00 IST — only 1 h before the 20:00 slot.
    late = next_publish_slot(now=ist(2026, 8, 20, 19), taken=[])
    # Same Thursday but 09:00 — plenty of lead time, so today is fine.
    early = next_publish_slot(now=ist(2026, 8, 20, 9), taken=[])
    return (check("19:00 Thu -> next Tuesday", late == ist(2026, 8, 25, 20))
            and check("09:00 Thu -> tonight 20:00", early == ist(2026, 8, 20, 20)))


def test_resumes_after_existing_schedule():
    print("resumes after slots already claimed in the queue")
    taken = [ist(2026, 9, 1, 20)]           # a Tuesday well in the future
    slot = next_publish_slot(now=ist(2026, 8, 20, 9), taken=taken)
    return check("after Tue 1 Sep -> Thu 3 Sep", slot == ist(2026, 9, 3, 20))


def test_unsorted_and_past_slots():
    print("tolerates unsorted and already-past claimed slots")
    taken = [ist(2026, 9, 3, 20), ist(2026, 6, 2, 20), ist(2026, 9, 1, 20)]
    slot = next_publish_slot(now=ist(2026, 8, 20, 9), taken=taken)
    return check("latest claimed is Thu 3 Sep -> Tue 8 Sep", slot == ist(2026, 9, 8, 20))


def test_dst_free_utc_conversion():
    print("8pm IST is 14:30 UTC all year (India has no DST)")
    jan = to_rfc3339_utc(ist(2026, 1, 6, 20))
    jul = to_rfc3339_utc(ist(2026, 7, 7, 20))
    return check(f"Jan {jan} / Jul {jul}",
                 jan == "2026-01-06T14:30:00Z" and jul == "2026-07-07T14:30:00Z")


def test_metadata_limits():
    print("title and tags stay inside YouTube's limits")
    import queue_manager
    ok = True
    longest = ""
    for topic in queue_manager.load():
        title = build_title(topic)
        tags = build_tags(topic)
        ok &= len(title) <= 100
        ok &= sum(len(t) + 1 for t in tags) <= 500
        ok &= "free" not in title.lower()
        if len(title) > len(longest):
            longest = title
    return check(f"all 51 topics — longest title {len(longest)} chars: {longest}", ok)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    results = [t() for t in tests]
    print(f"\n{sum(results)}/{len(results)} tests passed")
    sys.exit(0 if all(results) else 1)
