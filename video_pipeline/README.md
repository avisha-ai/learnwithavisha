# Video Pipeline — Session 2

Automated production for LearnWithAvisha videos: topic queue → script → human
approval → voiceover → animation → assembly → scheduled YouTube upload.

```
topic_queue.csv
      │
      ▼
  script_writer.py ──► script_reviewer.py ──┐   Claude call 1 + call 2
      ▲                                     │   (rewrite loop, max 3 rounds)
      └──────── discrepancies ──────────────┘
      │
      ▼
  ┌─────────────────────────────┐
  │  MAYUR APPROVES  (10 min)   │   status: awaiting_approval → approved
  └─────────────────────────────┘   nothing is produced before this
      │
      ▼
  voiceover.py      ElevenLabs — Leandra, Eleven v3 → voiceover.mp3
      │             its exact duration is the animation's TOTAL_RUNTIME
      ▼
  manim_generator.py  Claude call 3 → animation.py → 1080p60 animation.mp4
      │
      ▼
  assembler.py      ffmpeg mux + thumbnail → final_video.mp4
      │
      ▼
  youtube_upload.py  private + publishAt = next Tue/Thu 8:00 PM IST
```

## Why voiceover runs before the animation

SKILL.md freezes it: the animation must match the voiceover exactly and the
screen must never go blank while the voice is still speaking. That is only
achievable if the narration's exact length is known before the scene is
written, so the MP3 is generated first and its duration is a hard input to the
Manim generator. The approved pilot was built the same way
(`TOTAL_RUNTIME = 194.351`).

## Open sources only

`script_writer.py` and `script_reviewer.py` research through OpenRouter's web
plugin with `include_domains` pinned to `nptel.ac.in`, `eng.libretexts.org`,
`chem.libretexts.org`, `openstax.org` and `ocw.mit.edu`.

That filter is applied by the search engine, not by the API, so it is backed up
in code: `script_writer.validate_sources` re-checks every source the writer
reports against the same allow-list and rejects the draft if anything else
appears. A search filter that silently degraded would otherwise let a
copyrighted textbook into a script with nothing failing. Sources are pointed
to, never reproduced.

## Provider

Requests go to OpenRouter (`https://openrouter.ai/api/v1`) running
`anthropic/claude-sonnet-5`. OpenRouter serves only an OpenAI-compatible
`/chat/completions` endpoint, so the pipeline uses the `openai` SDK; the model
underneath is still Claude. Provider settings live in `config.py`.

## Setup

```bash
cp .env.example .env          # then fill in the two keys
```

| Credential | Used by | How to get it |
|---|---|---|
| `OPENROUTER_API_KEY` | script writer, reviewer, Manim generator | openrouter.ai → Keys |
| `ELEVENLABS_API_KEY` | voiceover | elevenlabs.io → profile → API key |
| `.credentials/youtube_client_secrets.json` | uploader | Google Cloud console → enable YouTube Data API v3 → OAuth client ID → Desktop app |

The uploader opens a browser once and caches the token in
`.credentials/youtube_token.json`. Both files are gitignored.

## Usage

```bash
cd video_pipeline

python main.py --status                                  # queue overview + next slot
python main.py --topic S1T1 --stages script              # write + review, then stop
python main.py --topic S1T1 --approve                    # record Mayur's approval
python main.py --topic S1T1 --stages voiceover,animate,assemble
python main.py --topic S1T1 --stages upload --dry-run    # metadata + slot, no upload
python main.py                                           # next topic, all stages

python youtube_upload.py -n 10                           # preview the schedule
```

`--force` redoes a stage whose artifacts already exist. `--auto-approve` skips
the human gate and is for pipeline testing only.

## The approval gate

`voiceover`, `animate`, `assemble` and `upload` refuse to run while a topic is
`pending`, `awaiting_approval` or `changes_requested`. The pipeline exits with
code 2 and prints the path to the script. Mayur approves by setting `status` to
`approved` in `curriculum/topic_queue.csv`, or by running `--approve`.

## Publish schedule

Every video uploads **private** with a `publishAt` timestamp, so YouTube itself
makes it public — nothing has to be running at 8pm.

The slot is the next Tuesday-or-Thursday 20:00 IST that is at least
`MIN_LEAD_HOURS` away and strictly later than every slot already claimed in
`topic_queue.csv`. Tuesday/Thursday alternation falls out of that rule rather
than being tracked: consecutive Tue/Thu slots alternate by construction.
8pm IST is 14:30 UTC year round — India has no daylight saving.

Per CLAUDE_MASTER.md the first 5–6 videos are uploaded by hand; this module
takes over from video 7.

## Queue status values

| Status | Meaning |
|---|---|
| `pending` | nothing done |
| `awaiting_approval` | script written and reviewed, waiting for Mayur |
| `changes_requested` | Mayur wants edits — the writer re-runs with feedback |
| `approved` | production may start |
| `produced` | `final_video.mp4` exists |
| `uploaded` | on YouTube, private, `publishAt` set |
| `published` | the scheduled time has passed |
| `failed` | a stage raised — see the `notes` column |

## Tests

```bash
python tests/test_schedule.py       # 8 checks — Tue/Thu 8pm IST scheduling
python tests/test_pipeline_e2e.py   # 23 checks — every stage, Claude+ElevenLabs stubbed
```

The end-to-end test runs the real Manim render, the real ffmpeg assembly and
the real queue transitions in a sandbox; only the two paid network calls are
stubbed.

## Files

| File | Role |
|---|---|
| `config.py` | every frozen constant from SKILL.md and CLAUDE_MASTER.md |
| `queue_manager.py` | `topic_queue.csv` state machine |
| `llm_client.py` | OpenRouter client — streaming, strict JSON schema, domain-filtered web search |
| `script_writer.py` | Claude call 1 + the hard brand rules |
| `script_reviewer.py` | Claude call 2 + the write/review/rewrite loop |
| `manim_generator.py` | Claude call 3, compile check, test render, sync check |
| `voiceover.py` | ElevenLabs, voice lookup by name, duration measurement |
| `assembler.py` | ffmpeg mux, sync verification, thumbnail |
| `youtube_upload.py` | metadata, schedule, OAuth, resumable upload, playlists |
| `main.py` | orchestrator, approval gate, resumable stages |
