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

import llm_client
from config import (BANNED_WORDS, CHANNEL, CLOSING_LINE, OPEN_SOURCE_DOMAINS,
                    SCRIPT_MAX_WORDS, SCRIPT_MIN_WORDS)
from queue_manager import Topic

log = logging.getLogger(__name__)

SYSTEM = f"""You are a chemical engineering educator with 20 years of teaching \
experience, writing for the {CHANNEL} YouTube channel.

You write the spoken voiceover script for a single animated teaching video.
The script is read aloud by a narrator. It is never shown on screen.

GROUNDING — non-negotiable:
- Research the topic with web search. You may use ONLY these open licensed
  sources: {", ".join(OPEN_SOURCE_DOMAINS)}. Any other source is rejected.
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


def validate_sources(sources: list[str]) -> list[str]:
    """
    Every source the writer reports must sit on an open licensed domain.

    OpenRouter's include_domains is applied by the search engine rather than by
    the API, so a filter that silently degrades would let a copyrighted
    textbook into a script with nothing failing. This is the backstop: the
    allow-list is checked again here, in code, against what the model says it
    actually read.
    """
    problems = []
    if not sources:
        return ["reports no sources — it must research before writing"]
    for source in sources:
        lowered = source.lower()
        if not any(domain in lowered for domain in OPEN_SOURCE_DOMAINS):
            problems.append(
                f"cites '{source[:90]}', which is not an open licensed source"
            )
    return problems


def _prompt(topic: Topic, feedback: str | None,
            previous: str | None = None) -> str:
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
        # The draft itself has to travel with the feedback. Without it the
        # writer starts from a blank page every round, so it cannot "change
        # nothing else" as instructed — it re-researches, rewrites, and trades
        # the old defects for new ones instead of converging.
        if previous:
            parts += [
                "",
                "This is a REWRITE, not a new script.",
                "",
                "PREVIOUS DRAFT — edit this text directly:",
                "-------------------",
                previous,
                "-------------------",
                "",
                "Apply ONLY the corrections listed below. Keep every other "
                "sentence exactly as it already stands — same wording, same "
                "order, same structure. Do not re-research settled material "
                "and do not restyle anything that was not criticised. Verify "
                "any NEW claim you add against the open licensed sources.",
                feedback,
            ]
        else:
            parts += [
                "",
                "This is a REWRITE. The previous draft was rejected. Fix every "
                "point below and change nothing else that was already correct:",
                feedback,
            ]
    return "\n".join(parts)


def write(topic: Topic, feedback: str | None = None, attempts: int = 3,
          previous: str | None = None) -> dict:
    """
    Research and write the script. Retries in-process when a hard rule is
    broken, feeding the failure back to Claude rather than silently accepting.
    """
    problems: list[str] = []
    result: dict = {}
    last_draft = previous          # carries across in-process retries too

    for attempt in range(1, attempts + 1):
        note = feedback
        if problems:
            note = ((feedback + "\n") if feedback else "") + \
                   "The previous attempt broke these hard rules:\n" + \
                   "\n".join(f"  - The script {p}." for p in problems)

        log.info("  Claude call 1 — writing script (attempt %d/%d)", attempt, attempts)
        result = llm_client.call_json(
            SYSTEM, _prompt(topic, note, last_draft), SCHEMA, search=True,
        )

        script = result["script"].strip()
        result["script"] = script
        last_draft = script
        problems = validate(script) + validate_sources(result.get("sources_read", []))
        if not problems:
            log.info("  script ok — %d words, %d sources",
                     word_count(script), len(result.get("sources_read", [])))
            return result

        log.warning("  script rejected: %s", "; ".join(problems))

    raise RuntimeError(
        f"Script for {topic.key} still breaks hard rules after {attempts} "
        f"attempts: {'; '.join(problems)}"
    )
