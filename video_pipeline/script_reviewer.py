"""
Claude API Call 2 — review the script against the open licensed sources.

This is an adversarial pass, not a second opinion. The reviewer re-reads the
sources itself (same open-source allow-list) and hunts for anything the writer
got wrong or could not support. It approves only when the script is clean.

Verdict is APPROVED or CHANGES_REQUIRED. CHANGES_REQUIRED sends the script
back to script_writer with the discrepancy list as feedback. A human never
sees a script that has not passed this gate.
"""

from __future__ import annotations

import logging

import claude_client
import script_writer
from config import (BANNED_WORDS, CLOSING_LINE, OPEN_SOURCE_DOMAINS,
                    SCRIPT_MAX_WORDS, SCRIPT_MIN_WORDS)
from queue_manager import Topic

log = logging.getLogger(__name__)

APPROVED = "APPROVED"
CHANGES_REQUIRED = "CHANGES_REQUIRED"

SYSTEM = f"""You are a chemical engineering expert reviewing a teaching script \
before it is turned into a video watched by students.

Your job is to find errors, not to praise. Assume the script is wrong until you
have checked it. Use web_search and web_fetch to re-read the open licensed
sources yourself: {", ".join(OPEN_SOURCE_DOMAINS)}.

Check every one of these and report each failure separately:
1. Technical errors — anything factually wrong.
2. Wrong numbers — any value that the open sources do not support.
3. Wrong units, or a unit that is missing where it matters.
4. Wrong assumptions — a statement true only in a special case, told as general.
5. Unsupported statements — anything you cannot verify in the open sources.
6. Verbatim reproduction — any phrasing lifted from a source instead of explained.
7. Opinions, anecdotes, or invented "in practice" claims.
8. Language that is too advanced for a first year student.
9. Structure — hook, definition, how it works, key variables, applications,
   recap, then the exact closing sentence: "{CLOSING_LINE}"
10. Length — must be {SCRIPT_MIN_WORDS} to {SCRIPT_MAX_WORDS} words.
11. Forbidden words — the word "free" must not appear anywhere, in any sense.
12. No references, URLs, or source names read aloud in the script body.

Severity:
- "critical" — wrong, unsupported, invented, or a forbidden word. Blocks the video.
- "major" — misleading, badly out of structure, or too advanced.
- "minor" — wording that could be clearer. Does not block on its own.

Set verdict to APPROVED only when there is no critical and no major finding.
Otherwise CHANGES_REQUIRED. Never approve something you did not verify."""

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": [APPROVED, CHANGES_REQUIRED]},
        "discrepancies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string",
                                 "enum": ["critical", "major", "minor"]},
                    "quote": {"type": "string",
                              "description": "The exact phrase from the script."},
                    "problem": {"type": "string"},
                    "fix": {"type": "string",
                            "description": "What the writer should do instead."},
                },
                "required": ["severity", "quote", "problem", "fix"],
                "additionalProperties": False,
            },
        },
        "sources_checked": {"type": "array", "items": {"type": "string"}},
        "notes_for_mayur": {
            "type": "string",
            "description": "Two sentences maximum. What a human approver should "
                           "look at. Empty string if nothing needs attention.",
        },
    },
    "required": ["verdict", "discrepancies", "sources_checked", "notes_for_mayur"],
    "additionalProperties": False,
}


def blocking(review: dict) -> list[dict]:
    return [d for d in review.get("discrepancies", [])
            if d.get("severity") in ("critical", "major")]


def feedback_text(review: dict) -> str:
    """Render the blocking findings as instructions for the writer."""
    lines = []
    for d in blocking(review):
        lines.append(f"  - [{d['severity']}] \"{d['quote']}\" — {d['problem']} "
                     f"Fix: {d['fix']}")
    return "\n".join(lines)


def review(topic: Topic, script: str, sources_read: list[str] | None = None) -> dict:
    log.info("  Claude call 2 — reviewing script")

    prompt = "\n".join([
        f"Subject: {topic.subject}",
        f"Topic {topic.topic_number}: {topic.topic_name}",
        "",
        "Open licensed sources this script is supposed to rest on:",
        f"  - NPTEL — Chemical Engineering — {topic.ref_nptel}",
        f"  - LibreTexts — {topic.ref_libretexts}",
        f"  - MIT OpenCourseWare — {topic.ref_mit_ocw}",
        "",
        "The writer says it read these pages:",
        *(f"  - {s}" for s in (sources_read or ["(none reported)"])),
        "",
        "Verify the sources yourself before you judge the script.",
        "",
        "SCRIPT UNDER REVIEW",
        "-------------------",
        script,
        "-------------------",
        f"(word count: {script_writer.word_count(script)})",
    ])

    result = claude_client.call_json(
        SYSTEM, prompt, SCHEMA, tools=claude_client.open_source_tools(),
    )

    # Deterministic rules are checked in code as well — the reviewer is a model
    # and can miss a banned word. Code wins.
    hard = script_writer.validate(script)
    if hard:
        result["verdict"] = CHANGES_REQUIRED
        for problem in hard:
            result.setdefault("discrepancies", []).insert(0, {
                "severity": "critical",
                "quote": "(whole script)",
                "problem": f"Automated brand check: the script {problem}.",
                "fix": "Rewrite so the frozen rule in SKILL.md is satisfied.",
            })

    blockers = blocking(result)
    log.info("  verdict: %s (%d blocking, %d total findings)",
             result["verdict"], len(blockers), len(result.get("discrepancies", [])))
    return result


def write_and_review(topic: Topic, rounds: int = 3) -> tuple[str, dict, dict]:
    """
    The full two-call quality gate. Writes, reviews, and rewrites against the
    reviewer's findings until the reviewer approves.

    Returns (script, draft, review).
    """
    feedback = None
    for round_no in range(1, rounds + 1):
        log.info("Quality gate round %d/%d", round_no, rounds)
        draft = script_writer.write(topic, feedback=feedback)
        result = review(topic, draft["script"], draft.get("sources_read"))

        if result["verdict"] == APPROVED:
            return draft["script"], draft, result

        feedback = feedback_text(result)
        log.warning("  rewrite requested:\n%s", feedback)

    raise RuntimeError(
        f"{topic.key}: reviewer did not approve after {rounds} rounds. "
        f"Last findings:\n{feedback}"
    )
