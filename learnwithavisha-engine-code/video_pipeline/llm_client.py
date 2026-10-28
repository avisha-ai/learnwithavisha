"""
OpenRouter client for the three pipeline calls.

OpenRouter exposes only an OpenAI-compatible /chat/completions endpoint — there
is no Anthropic Messages endpoint behind it — so requests go through the openai
SDK even though the model underneath is Claude.

Mapping from the Anthropic-native shapes this pipeline used before:

    system + prompt          -> messages[system, user]
    output_config.format     -> response_format.json_schema (strict)
    output_config.effort     -> reasoning.effort            (extra_body)
    web_search allowed_domains -> plugins[web].include_domains (extra_body)

The open-source restriction is the one that does not map cleanly. Anthropic's
server tool enforced allowed_domains itself; OpenRouter's include_domains is
honoured by the search engine, which is a weaker guarantee. So the allow-list
is enforced a second time in code, after the answer comes back — see
script_writer.validate_sources.
"""

from __future__ import annotations

import json
import logging

import claude_cli
from config import (CLAUDE_EFFORT, CLAUDE_MODEL, LLM_PROVIDER,
                    OPENROUTER_API_KEY_ENV,
                    OPENROUTER_BASE_URL, OPENROUTER_HEADERS,
                    OPENROUTER_SEARCH_ENGINE, OPENROUTER_SEARCH_MAX_RESULTS,
                    OPEN_SOURCE_DOMAINS, require_env)

log = logging.getLogger(__name__)

REQUEST_TIMEOUT = 900.0     # Manim generation is a long single turn


def client():
    import openai          # lazy: OpenRouter path only
    return openai.OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=require_env(OPENROUTER_API_KEY_ENV),
        timeout=REQUEST_TIMEOUT,
        max_retries=3,
        default_headers=OPENROUTER_HEADERS,
    )


def open_source_plugins() -> list[dict]:
    """
    The web plugin, restricted to open licensed sources.

    Wildcards cover the subdomains the courseware actually lives on
    (ocw.mit.edu serves PDFs from a few hosts).
    """
    domains: list[str] = []
    for domain in OPEN_SOURCE_DOMAINS:
        domains += [domain, f"*.{domain}"]
    return [{
        "id": "web",
        "engine": OPENROUTER_SEARCH_ENGINE,
        "max_results": OPENROUTER_SEARCH_MAX_RESULTS,
        "include_domains": domains,
        "search_prompt": (
            "These are the only sources you may use. They are open licensed "
            "courseware. Explain what they say in your own words — never "
            "reproduce their wording, and never state a number they do not give."
        ),
    }]


def call(system: str,
         prompt: str,
         *,
         schema: dict | None = None,
         search: bool = False,
         max_tokens: int = 32000,
         effort: str = CLAUDE_EFFORT,
         model: str = CLAUDE_MODEL) -> tuple[str, list]:
    """
    One chat completion, streamed. Returns (text, []).

    The second element is a compatibility shim: the Anthropic version returned
    content blocks and callers unpack a 2-tuple.
    """
    if LLM_PROVIDER == "claude_cli":
        return claude_cli.call(system, prompt, schema=schema, search=search,
                               max_tokens=max_tokens, effort=effort)

    api = client()

    extra_body: dict = {"reasoning": {"effort": effort}}
    if search:
        extra_body["plugins"] = open_source_plugins()

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "extra_body": extra_body,
    }

    if schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "pipeline_output",
                "strict": True,
                "schema": schema,
            },
        }

    chunks: list[str] = []
    finish_reason = None
    # Streamed: a 64k-token Manim generation would otherwise risk an HTTP timeout.
    stream = api.chat.completions.create(stream=True, **kwargs)
    for event in stream:
        if not event.choices:
            continue
        choice = event.choices[0]
        if choice.delta and choice.delta.content:
            chunks.append(choice.delta.content)
        if choice.finish_reason:
            finish_reason = choice.finish_reason

    text = "".join(chunks).strip()

    if finish_reason == "length":
        raise RuntimeError(
            f"Response hit max_tokens ({max_tokens}). Raise max_tokens and retry."
        )
    if finish_reason == "content_filter":
        raise RuntimeError("OpenRouter refused this request (content filter).")
    if not text:
        raise RuntimeError(
            f"OpenRouter returned no text (finish_reason={finish_reason}). "
            f"Check that '{model}' is available and that the account has credit."
        )
    return text, []


def call_json(system: str, prompt: str, schema: dict, **kwargs) -> dict:
    """Structured-output call — returns the parsed object."""
    if LLM_PROVIDER == "claude_cli":
        return claude_cli.call_json(system, prompt, schema, **kwargs)

    text, _ = call(system, prompt, schema=schema, **kwargs)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"OpenRouter returned invalid JSON despite a strict schema: {exc}\n"
            f"{text[:500]}"
        ) from exc
