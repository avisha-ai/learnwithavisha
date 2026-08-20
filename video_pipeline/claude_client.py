"""
Thin wrapper over the Anthropic Messages API for the three pipeline calls.

Two things every pipeline call needs and the raw SDK does not do for you:
  • a pause_turn loop — server-side web search pauses long turns and expects
    the conversation to be resumed, otherwise the answer comes back truncated;
  • the open-source allow-list — web search and web fetch are pinned to
    OPEN_SOURCE_DOMAINS, so a script physically cannot be grounded in a
    copyrighted textbook.
"""

from __future__ import annotations

import json
import logging

import anthropic

from config import (CLAUDE_EFFORT, CLAUDE_MODEL, OPEN_SOURCE_DOMAINS,
                    ANTHROPIC_API_KEY_ENV, require_env)

log = logging.getLogger(__name__)

MAX_PAUSE_RESUMES = 6


def client() -> anthropic.Anthropic:
    require_env(ANTHROPIC_API_KEY_ENV)      # fail early with a clear message
    return anthropic.Anthropic()


def open_source_tools(max_searches: int = 8, max_fetches: int = 8) -> list[dict]:
    """Web search + web fetch, restricted to open licensed sources only."""
    return [
        {
            "type": "web_search_20260209",
            "name": "web_search",
            "max_uses": max_searches,
            "allowed_domains": list(OPEN_SOURCE_DOMAINS),
        },
        {
            "type": "web_fetch_20260209",
            "name": "web_fetch",
            "max_uses": max_fetches,
            "allowed_domains": list(OPEN_SOURCE_DOMAINS),
            "max_content_tokens": 40000,
        },
    ]


def call(system: str,
         prompt: str,
         *,
         schema: dict | None = None,
         tools: list[dict] | None = None,
         max_tokens: int = 32000,
         effort: str = CLAUDE_EFFORT,
         model: str = CLAUDE_MODEL) -> tuple[str, list]:
    """
    Run one Messages request to completion, resuming across pause_turn.

    Returns (text, full_content_blocks). When `schema` is given the text is
    guaranteed-valid JSON for that schema.
    """
    api = client()
    messages: list[dict] = [{"role": "user", "content": prompt}]

    output_config: dict = {"effort": effort}
    if schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": schema}

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "thinking": {"type": "adaptive"},
        "output_config": output_config,
    }
    if tools:
        kwargs["tools"] = tools

    collected: list = []
    for attempt in range(MAX_PAUSE_RESUMES + 1):
        # Streaming: these turns are long (web search + a full script) and a
        # non-streaming request would sit at risk of an HTTP timeout.
        with api.messages.stream(messages=messages, **kwargs) as stream:
            response = stream.get_final_message()

        collected.extend(response.content)

        if response.stop_reason == "refusal":
            detail = getattr(response, "stop_details", None)
            category = getattr(detail, "category", None)
            raise RuntimeError(f"Claude declined this request (category={category}).")

        if response.stop_reason == "pause_turn":
            if attempt == MAX_PAUSE_RESUMES:
                raise RuntimeError("Claude paused too many times without finishing.")
            log.info("  ... turn paused, resuming (%d)", attempt + 1)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": "Continue."})
            continue

        if response.stop_reason == "max_tokens":
            raise RuntimeError(
                f"Response hit max_tokens ({max_tokens}). Raise max_tokens and retry."
            )
        break

    text = "".join(b.text for b in collected if b.type == "text").strip()
    if not text:
        raise RuntimeError("Claude returned no text content.")
    return text, collected


def call_json(system: str, prompt: str, schema: dict, **kwargs) -> dict:
    """Structured-output call — returns the parsed object."""
    text, _ = call(system, prompt, schema=schema, **kwargs)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:      # pragma: no cover — schema guarantees this
        raise RuntimeError(f"Claude returned invalid JSON: {exc}\n{text[:500]}") from exc
