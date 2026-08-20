"""
Claude API Call 1 — write the voiceover script for one topic.

Grounding: the writer may only read nptel.ac.in, eng.libretexts.org,
chem.libretexts.org, openstax.org and ocw.mit.edu. The allow-list is enforced
by the web_search / web_fetch server tools, not by the prompt, so no
copyrighted textbook can reach the script.

Never reproduces source text verbatim — it points to the source instead.
"""

from __future__ import annotations

import logging
import re

import claude_client
from config import (BANNED_WORDS, CHANNEL, CLOSING_LINE, OPEN_SOURCE_DOMAINS,
                    SCRIPT_MAX_WORDS, SCRIPT_MIN_WORDS)
from queue_manager import Topic

log = logging.getLogger(__name__)

SYSTEM = f"""You are a chemical engineering educator with 20 years of teaching \
experience, writing for the {CHANNEL} YouTube channel.

You write the spoken voiceover script for a single animated teaching video.
The script is read aloud by a narrator. It is never shown on screen.

GROUNDING — non-negotiable:
- Research the topic using ONLY the web_search and web_fetch tools. They are
  restricted to open licensed sources: {", ".join(OPEN_SOURCE_DOMAINS)}.
- Every teaching statement must be supported by what you actually read there.
- NEVER reproduce source text verbatim. Explain it in your own plain words.
- NEVER invent a number. No pressure, temperature, flow rate, dimension,
  coefficient or safety limit unless the source you read states it. If a
  worked example needs numbers, use round illustrative values and say plainly
  that they are an example.
- If the sources do not support a statement, leave the statement out.

STRUCTURE — follow exactly, in this order:
1. Opening hook — one sentence on why this matters.
2. What it is — a simple definition.
3. How it works — step by step, in the order an animation would build it up.
4. Key variables — what affects behaviour or performance.
5. Where it is used — real plant applications, stated generically.
6. Key points recap — three or four points, spoken as sentences.
7. Close — the exact sentence: "{CLOSING_LINE}"

LANGUAGE RULES:
- Simple language. Explain to a first year student, not to a PhD.
- Analogy first, concept second, equation last.
- Calm and clear, like a good professor. Short sentences.
- Generic only. No opinions, no "in practice what happens is", no anecdotes.
- Spoken prose only. No headings, no bullet characters, no stage directions,
  no speaker labels, no markdown, no emoji.
- Write numbers and symbols as they are spoken: "150 degrees Celsius",
  "delta T", "the Reynolds number".
- {SCRIPT_MIN_WORDS} to {SCRIPT_MAX_WORDS} words. This is a hard requirement.

FORBIDDEN:
- The word "free" must never appear. Not once, in any sense.
- Never mention pricing, subscriptions, or Avisha's commercial services.
- Never say the channel name anywhere except the closing sentence.
- Never read out a reference or a URL. References live in the description box."""

SCHEMA = {
    "type": "object",
    "properties": {
        "script": {
            "type": "string",
            "description": "The full spoken script, plain prose, no markdown.",
        },
        "summary": {
            "type": "string",
            "description": "2-3 sentence plain English summary for the YouTube "
                           "description box. Does not repeat the script verbatim.",
        },
        "sources_read": {
            "type": "array",
            "description": "The open licensed pages actually read, in the form "
                           "'Source name — page or module title — url'.",
            "items": {"type": "string"},
        },
        "key_points": {
            "type": "array",
            "description": "The 3-4 recap points, each a short phrase. These "
                           "drive the summary panel in the animation.",
            "items": {"type": "string"},
        },
        "visual_beats": {
            "type": "array",
            "description": "The elements an animation must build up, in the "
                           "order the script introduces them. One short phrase each.",
            "items": {"type": "string"},
        },
    },
    "required": ["script", "summary", "sources_read", "key_points", "visual_beats"],
    "additionalProperties": False,
}


def word_count(script: str) -> int:
    return len(script.split())


def validate(script: str) -> list[str]:
    """Hard brand and format rules. Returns a list of problems — empty is good."""
    problems = []
    lowered = script.lower()

    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            problems.append(f"contains the forbidden word/phrase '{word}'")

    if CLOSING_LINE.lower() not in lowered:
        problems.append("does not end with the frozen closing line")
    elif not script.strip().endswith(CLOSING_LINE):
        problems.append("closing line is present but is not the last sentence")

    words = word_count(script)
    if not SCRIPT_MIN_WORDS <= words <= SCRIPT_MAX_WORDS:
        problems.append(
            f"is {words} words — must be {SCRIPT_MIN_WORDS}-{SCRIPT_MAX_WORDS}"
        )

    for marker in ("#", "*", "- ", "•", "```", "Narrator:", "VOICEOVER:"):
        if marker in script:
            problems.append(f"contains the formatting marker '{marker.strip()}'")

    return problems


def _prompt(topic: Topic, feedback: str | None) -> str:
    parts = [
        f"Write the voiceover script for this video.",
        "",
        f"Subject: {topic.subject} (Subject {topic.subject_number} of the "
        f"{CHANNEL} curriculum)",
        f"Topic {topic.topic_number}: {topic.topic_name}",
        "",
        "Start from these open licensed sources and search within them:",
        f"  - NPTEL — Chemical Engineering — {topic.ref_nptel}",
        f"  - LibreTexts — {topic.ref_libretexts}",
        f"  - MIT OpenCourseWare — {topic.ref_mit_ocw}",
        "",
        "Search first. Read the actual pages. Then write.",
    ]
    if feedback:
        parts += [
            "",
            "This is a REWRITE. The previous draft was rejected. Fix every point "
            "below and change nothing else that was already correct:",
            feedback,
        ]
    return "\n".join(parts)


def write(topic: Topic, feedback: str | None = None, attempts: int = 3) -> dict:
    """
    Research and write the script. Retries in-process when a hard rule is
    broken, feeding the failure back to Claude rather than silently accepting.
    """
    problems: list[str] = []
    result: dict = {}

    for attempt in range(1, attempts + 1):
        note = feedback
        if problems:
            note = ((feedback + "\n") if feedback else "") + \
                   "The previous attempt broke these hard rules:\n" + \
                   "\n".join(f"  - The script {p}." for p in problems)

        log.info("  Claude call 1 — writing script (attempt %d/%d)", attempt, attempts)
        result = claude_client.call_json(
            SYSTEM, _prompt(topic, note), SCHEMA,
            tools=claude_client.open_source_tools(),
        )

        script = result["script"].strip()
        result["script"] = script
        problems = validate(script)
        if not problems:
            log.info("  script ok — %d words, %d sources",
                     word_count(script), len(result.get("sources_read", [])))
            return result

        log.warning("  script rejected: %s", "; ".join(problems))

    raise RuntimeError(
        f"Script for {topic.key} still breaks hard rules after {attempts} "
        f"attempts: {'; '.join(problems)}"
    )
