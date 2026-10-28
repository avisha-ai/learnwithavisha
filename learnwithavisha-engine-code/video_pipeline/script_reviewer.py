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

import llm_client
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
have checked it. Use web search to re-read the open licensed sources yourself.
You may use ONLY these: {", ".join(OPEN_SOURCE_DOMAINS)}.

Check every one of these and report each failure separately:
1. Technical errors — anything factually wrong.
2. Wrong numbers — any value that the open sources do not support.
3. Wrong units, or a unit that is missing where it matters.
4. Wrong assumptions — a statement true only in a special case, told as general.
5. Unsourced factual claims — anything you cannot point to in the open
   sources. See SOURCING below. Being true is not enough. Analogies and
   illustrative comparisons are exempt.
6. Verbatim reproduction — any phrasing lifted from a source instead of explained.
7. Opinions, anecdotes, or invented "in practice" claims.
8. Language that is too advanced for a first year student.
9. Structure — hook, definition, how it works, key variables, applications,
   recap, then the exact closing sentence: "{CLOSING_LINE}"
10. Length — must be {SCRIPT_MIN_WORDS} to {SCRIPT_MAX_WORDS} words.
11. Forbidden words — the word "free" must not appear anywhere, in any sense.
12. No references, URLs, or source names read aloud in the script body.

SOURCING — absolute, and it overrides your own judgement:
Every FACTUAL claim in the script must rest on something you can actually point
to in the open licensed sources. If you cannot name the source page that
supports a factual claim, flag it and send it back. Analogies are the one
exception, defined below.

This applies EVEN WHEN THE CLAIM IS TRUE. Correctness is not the test —
traceability to an approved source is. A claim you know to be right from your
own knowledge, a textbook you have read elsewhere, or common engineering
understanding is still unsourced, and unsourced facts do not ship.

It covers every kind of FACTUAL claim, not just numbers: definitions,
mechanisms, material behaviour, molecular structure, and application or
equipment claims.

ANALOGIES — the one carve-out:
Analogies and illustrative comparisons are teaching devices, not claims about
the world, and they do NOT need a source. The brief requires them: analogy
first, concept second, equation last. Do not flag a comparison merely because
the source pages do not contain it.

Allowed unsourced — a figure of speech, or an appeal to something the viewer
has already felt or seen, used to illuminate a concept that IS sourced:
  - "stir honey and then stir water — the honey resists your spoon far more"
  - "it flexes slightly, then stays put, like a spring"
  - "picture a cup of water"

Still REQUIRED to be sourced — a technical assertion about how the world
actually works, however casually it is phrased:
  - molecular structure claims ("the molecules are locked into a fixed lattice")
  - mechanism claims ("heating loosens cohesion, so viscosity drops")
  - application and equipment claims ("sizing a pump needs density and viscosity")
  - any number, unit, property value, or named law

The test is what the sentence ASSERTS, not how it is dressed. "Honey is thicker
than water" is an everyday comparison. "Honey has a higher viscosity because its
molecules are larger" is a mechanism claim and needs a source. A factual claim
does not become exempt by being written as a comparison.

Where you cannot tell which side a sentence falls on, treat it as a factual
claim and require the source.

For each unsourced factual claim, quote the exact phrase, say which source you
expected to support it and what that source actually says instead, and require
either a rewrite that matches an approved source or removal of the claim.

Severity:
- "critical" — wrong, invented, an unsourced factual claim, or a forbidden
  word. Blocks the video.
- "major" — misleading, badly out of structure, or too advanced.
- "minor" — wording that could be clearer. Does not block on its own.

Never grade an unsourced FACTUAL claim as "minor" on the grounds that it is
harmless or accurate. An unsourced factual claim is critical, always. An
analogy needs no source and is not a finding at all.

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

    result = llm_client.call_json(SYSTEM, prompt, SCHEMA, search=True)

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
    previous = None
    for round_no in range(1, rounds + 1):
        log.info("Quality gate round %d/%d", round_no, rounds)
        draft = script_writer.write(topic, feedback=feedback, previous=previous)
        result = review(topic, draft["script"], draft.get("sources_read"))

        if result["verdict"] == APPROVED:
            return draft["script"], draft, result

        feedback = feedback_text(result)
        previous = draft["script"]
        log.warning("  rewrite requested:\n%s", feedback)

    raise RuntimeError(
        f"{topic.key}: reviewer did not approve after {rounds} rounds. "
        f"Last findings:\n{feedback}"
    )
