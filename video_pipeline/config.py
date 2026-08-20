"""
LearnWithAvisha — pipeline configuration.

Everything in this file is FROZEN by SKILL.md and CLAUDE_MASTER.md.
Do not change a value here without changing the brief first.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

try:                                    # optional — .env is convenience only
    from dotenv import load_dotenv
except ImportError:                     # pragma: no cover
    def load_dotenv(*_a, **_kw):
        return False

# ── paths ────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_CSV = ROOT / "curriculum" / "topic_queue.csv"
OUTPUT_DIR = ROOT / "output"
PILOT_ANIMATION = ROOT / "shell_tube_animation.py"   # reference example for Manim generation
SKILL_MD = ROOT / "SKILL.md"
CREDENTIALS_DIR = ROOT / ".credentials"
YOUTUBE_CLIENT_SECRETS = CREDENTIALS_DIR / "youtube_client_secrets.json"
YOUTUBE_TOKEN = CREDENTIALS_DIR / "youtube_token.json"

load_dotenv(ROOT / ".env")

# manim, ffmpeg and ffprobe all live in the same environment as the interpreter
# running this pipeline, but that bin directory is not on the shell PATH. Put it
# there so subprocess calls to ffmpeg/ffprobe resolve without a wrapper script.
_BIN = str(Path(sys.executable).parent)
if _BIN not in os.environ.get("PATH", "").split(os.pathsep):
    os.environ["PATH"] = _BIN + os.pathsep + os.environ.get("PATH", "")

# ── brand — frozen ───────────────────────────────────────────────
CHANNEL = "LearnWithAvisha"
TAGLINE = "Chemical Engineering — Made Simple."
CLOSING_LINE = ("This is LearnWithAvisha — chemical engineering fundamentals, "
                "explained simply.")
# Words that must never appear in a script or a description.
BANNED_WORDS = ("free", "pricing", "subscription fee")

# ── LLM provider — OpenRouter ────────────────────────────────────
# OpenRouter speaks the OpenAI chat-completions wire format, not Anthropic's
# Messages API, so the pipeline talks to it through the openai SDK.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
CLAUDE_MODEL = "anthropic/claude-sonnet-4-6"
CLAUDE_EFFORT = "high"

# Sent on every request so the traffic is attributable in the OpenRouter
# dashboard. Optional for the API, useful for cost tracking per project.
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://learnwithavisha.ai",
    "X-Title": "LearnWithAvisha Video Pipeline",
}

# Web search plugin. Domain filtering is engine dependent, so the exa engine is
# pinned — it honours include_domains. The allow-list is ALSO re-checked in
# code after the model answers (script_writer.validate_sources), because a
# search engine that quietly ignores the filter would otherwise let a
# copyrighted textbook into a script without anything failing.
OPENROUTER_SEARCH_ENGINE = "exa"
OPENROUTER_SEARCH_MAX_RESULTS = 8

# Open licensed sources ONLY. This tuple is the allow-list handed to the
# web_search / web_fetch server tools, so the writer physically cannot ground
# a script in a copyrighted textbook.
OPEN_SOURCE_DOMAINS = (
    "nptel.ac.in",
    "eng.libretexts.org",
    "chem.libretexts.org",
    "openstax.org",
    "ocw.mit.edu",
)

# ── script rules — frozen (SKILL.md) ─────────────────────────────
SCRIPT_MIN_WORDS = 550
SCRIPT_MAX_WORDS = 700

# ── animation — frozen (SKILL.md) ────────────────────────────────
RESOLUTION = (1920, 1080)
FPS = 60
BACKGROUND = "#0d0d1a"
BREATH_PAUSE = 2.5          # seconds after every major reveal
COLOURS = {
    "hot_in": "#ff4444",
    "hot_out": "#ff8c00",
    "cold_in": "#4488ff",
    "cold_out": "#90caf9",
    "heat": "#ffff00",
    "equipment": "#b0bec5",
    "label": "#ffffff",
    "accent": "#FFD700",
}
WATERMARK_OPACITY = 0.85    # as rendered in the approved pilot

# ── voiceover — frozen (SKILL.md) ────────────────────────────────
ELEVENLABS_API_KEY_ENV = "ELEVENLABS_API_KEY"
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
VOICE_NAME = "Leandra"
VOICE_ID_ENV = "ELEVENLABS_VOICE_ID"        # optional override / cache
ELEVENLABS_MODEL = "eleven_v3"
VOICE_SETTINGS = {
    "stability": 0.75,          # SKILL.md: 75%, robust side
    "similarity_boost": 0.75,
    "style": 0.0,               # SKILL.md: style exaggeration fully left
    "use_speaker_boost": True,
    "speed": 1.0,
}
AUDIO_FORMAT = "mp3_44100_128"

# ── YouTube — frozen (CLAUDE_MASTER.md) ──────────────────────────
IST = ZoneInfo("Asia/Kolkata")
PUBLISH_WEEKDAYS = (1, 3)       # Monday=0 -> Tuesday=1, Thursday=3
PUBLISH_HOUR_IST = 20           # 8:00 PM IST
PUBLISH_MINUTE_IST = 0
MIN_LEAD_HOURS = 2              # never schedule a slot less than this away
YOUTUBE_CATEGORY_ID = "27"      # Education
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube"]

BASE_TAGS = (
    "chemical engineering", "chemical engineering basics", "process engineering",
    "engineering education", "learnwithavisha", "avisha", "chemical engineering lecture",
)

DESCRIPTION_TEMPLATE = """Topic: {topic_name}
Subject: {subject} — LearnWithAvisha Curriculum

{summary}

📚 References:
• NPTEL — Chemical Engineering — {ref_nptel}
  nptel.ac.in
• LibreTexts Engineering — {ref_libretexts}
  eng.libretexts.org
• MIT OpenCourseWare — Chemical Engineering
  ocw.mit.edu

🔗 Full curriculum: learnwithavisha.ai
❓ Ask anything: ask.learnwithavisha.ai

By Avisha.AI | Engineering Made Intelligent"""


# ── helpers ──────────────────────────────────────────────────────
def require_env(name: str) -> str:
    """Return an environment variable or fail with an actionable message."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Add it to {ROOT / '.env'} or export it "
            f"before running the pipeline."
        )
    return value


def topic_dir(subject_slug: str, subject_number: int, slug: str) -> Path:
    """Deterministic per-topic working directory. No path columns in the CSV."""
    return OUTPUT_DIR / f"subject{subject_number}_{subject_slug.replace('-', '_')}" / slug
