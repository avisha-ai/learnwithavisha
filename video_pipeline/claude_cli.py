"""
Claude CLI transport — the same three pipeline calls, routed through the local
`claude` binary so they bill against the Max subscription instead of a metered
API key.

Signature-compatible with llm_client.call / llm_client.call_json, so callers
(script_writer, script_reviewer, manim_generator) need no changes.

Three things do NOT map cleanly from the OpenRouter path, and all of them
matter:

  * No strict JSON schema. The CLI has no response_format, so the schema is
    injected into the prompt and the reply is parsed and checked here. A
    malformed reply is retried with the parse error fed back to the model.

  * No engine level domain allow-list. OpenRouter pinned exa's
    include_domains; the CLI's WebSearch accepts no such filter from the
    command line. Grounding is therefore prompt-directed and enforced AFTER
    the fact, in code, by script_writer.validate_sources — which already
    existed as the backstop for exactly this weakness. The guarantee is
    genuinely weaker here: a wrong source is caught after it is read, not
    prevented from being read.

  * No max_tokens. Accepted and ignored, for signature compatibility.

ANTHROPIC_API_KEY is stripped from the subprocess environment deliberately: if
it is set, the CLI bills the metered API instead of the subscription, which is
the opposite of the point.

Write tools are denied and the subprocess runs in a scratch cwd, so a pipeline
call can never edit the repository it was launched from.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile

from config import CLAUDE_CLI_BIN, CLAUDE_CLI_MODEL, CLAUDE_EFFORT

log = logging.getLogger(__name__)

TIMEOUT = 1800          # research + a 700 word script is a long single turn
ATTEMPTS = 3            # JSON repair attempts

# Read-only. Everything that could touch the filesystem is denied outright.
SEARCH_TOOLS = ["WebSearch", "WebFetch"]
DENIED_TOOLS = ["Edit", "Write", "NotebookEdit", "Bash", "Task", "TodoWrite"]

_JSON_INSTRUCTION = """

OUTPUT FORMAT — this overrides any default brevity:
Return ONE JSON object and nothing else. No preamble, no explanation, no
markdown code fences. It must validate against this JSON Schema:

{schema}

Every field marked required must be present. Long string fields must contain
the full text — never truncate, never summarise, never write a placeholder."""


def _extract_json(text: str) -> dict:
    """Parse the model's reply as JSON, tolerating fences and stray prose."""
    cleaned = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.S)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise json.JSONDecodeError("no JSON object in reply", cleaned or " ", 0)
    return json.loads(cleaned[start:end + 1])


def _run(system: str, prompt: str, *, search: bool, effort: str,
         model: str) -> str:
    """One `claude -p` invocation. Returns the result text."""
    cmd = [
        CLAUDE_CLI_BIN, "-p", prompt,
        "--system-prompt", system,       # replace, not append: the Claude Code
                                         # default prompt pushes terse coding
                                         # answers, which fights a 700 word script
        "--output-format", "json",
        "--model", model,
        "--effort", effort,
        "--disallowedTools", *DENIED_TOOLS,
    ]
    if search:
        cmd += ["--allowedTools", *SEARCH_TOOLS]

    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

    with tempfile.TemporaryDirectory() as cwd:      # never the repo
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=TIMEOUT, env=env, cwd=cwd)

    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI exited {proc.returncode}.\n"
            f"stderr: {proc.stderr.strip()[:800]}"
        )

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"claude CLI did not return a JSON envelope: {exc}\n"
            f"{proc.stdout[:500]}"
        ) from exc

    if envelope.get("is_error"):
        raise RuntimeError(
            f"claude CLI reported an error: {str(envelope.get('result'))[:500]}"
        )

    text = (envelope.get("result") or "").strip()
    if not text:
        raise RuntimeError("claude CLI returned an empty result.")

    usage = envelope.get("modelUsage") or {}
    log.debug("  cli: %d turns, models=%s", envelope.get("num_turns", 0),
              ",".join(usage))
    return text


def call(system: str,
         prompt: str,
         *,
         schema: dict | None = None,
         search: bool = False,
         max_tokens: int = 32000,        # noqa: ARG001 - compatibility only
         effort: str = CLAUDE_EFFORT,
         model: str = CLAUDE_CLI_MODEL) -> tuple[str, list]:
    """One CLI turn. Returns (text, []) to match the llm_client shape."""
    if schema is not None:
        system = system + _JSON_INSTRUCTION.format(
            schema=json.dumps(schema, indent=2))
    return _run(system, prompt, search=search, effort=effort, model=model), []


def call_json(system: str, prompt: str, schema: dict, **kwargs) -> dict:
    """
    Structured-output call. The CLI cannot enforce a schema, so a bad reply is
    re-asked with the parse error attached rather than crashing the run.
    """
    required = schema.get("required", [])
    attempt_prompt = prompt
    last_error = ""

    for attempt in range(1, ATTEMPTS + 1):
        text, _ = call(system, attempt_prompt, schema=schema, **kwargs)
        try:
            data = _extract_json(text)
            missing = [k for k in required if k not in data]
            if missing:
                raise ValueError(f"missing required field(s): {', '.join(missing)}")
            return data
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = str(exc)
            log.warning("  cli returned unusable JSON (attempt %d/%d): %s",
                        attempt, ATTEMPTS, last_error)
            attempt_prompt = (
                f"{prompt}\n\n"
                f"Your previous reply could not be used: {last_error}\n"
                f"Return ONLY the JSON object, complete and valid, nothing else."
            )

    raise RuntimeError(
        f"claude CLI did not return valid JSON after {ATTEMPTS} attempts. "
        f"Last error: {last_error}"
    )
