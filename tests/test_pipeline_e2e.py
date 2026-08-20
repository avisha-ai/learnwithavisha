"""
Offline end-to-end test of the video pipeline.

Runs every stage of main.py for real — manim render, ffmpeg mux, thumbnail
extraction, queue transitions, the approval gate, YouTube metadata and the
Tuesday/Thursday schedule — with only the two paid network calls stubbed:

  • claude_client  -> a canned script, review and Manim scene
  • ElevenLabs     -> a silent MP3 of a known duration, made with ffmpeg

A short runtime and a low-quality render keep it to about a minute. The real
run with live keys is the same code path at 1080p60.

Run: python tests/test_pipeline_e2e.py
"""

import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "video_pipeline"))

import config                                              # noqa: E402

SANDBOX = Path(tempfile.mkdtemp(prefix="lwa_e2e_"))
config.OUTPUT_DIR = SANDBOX / "output"
config.CURRICULUM_CSV = SANDBOX / "topic_queue.csv"
shutil.copy2(ROOT / "curriculum" / "topic_queue.csv", config.CURRICULUM_CSV)

import claude_client                                       # noqa: E402
import main                                                # noqa: E402
import queue_manager as q                                  # noqa: E402
import voiceover as vo                                     # noqa: E402
import youtube_upload as yt                                # noqa: E402

q.CURRICULUM_CSV = config.CURRICULUM_CSV
for module in (q, main):
    for name in dir(module):
        pass

RUNTIME = 24.0          # seconds — a short stand-in for the 4 minute narration

_BODY = (
    "Every process plant moves material from one place to another, and almost all "
    "of that material moves as a fluid. Understanding what a fluid is, and how it "
    "behaves, is where chemical engineering begins. A fluid is any substance that "
    "cannot resist a shearing force. Push sideways on a solid block and it deforms "
    "a little, then stops. Push sideways on water and it keeps moving for as long "
    "as you keep pushing. That continuous deformation under shear is the definition "
    "of a fluid, and it covers both liquids and gases. "
)

# Repeated to reach the 550-700 word band the writer must hit. Real scripts are
# written by Claude; this only has to satisfy the same validator.
STUB_SCRIPT = ((_BODY * 6).strip() + " This is LearnWithAvisha — chemical "
               "engineering fundamentals, explained simply.")

STUB_SCENE = '''"""Stub scene — stands in for the Claude-generated animation."""
from manim import *

TOTAL_RUNTIME = {runtime}


class {scene}(Scene):
    def hold_until(self, t):
        dt = t - self.clock
        if dt > 1e-3:
            self.wait(dt)
            self.clock = t

    def at(self, t, *anims, run_time=1.0):
        self.hold_until(t)
        self.play(*anims, run_time=run_time)
        self.clock += run_time

    def construct(self):
        self.clock = 0.0
        self.camera.background_color = "{bg}"

        ring = Circle(radius=0.42, fill_opacity=0)
        ring.set_stroke(WHITE, width=1.2, opacity=0.85)
        mono = Text("LWA", font="Georgia", slant=ITALIC, font_size=17, color=WHITE)
        mono.move_to(ring.get_center()).set_opacity(0.85)
        self.add(VGroup(ring, mono).to_corner(DR, buff=0.35))

        title = Text("{title}", font_size=30, color=WHITE).to_edge(UP, buff=0.6)
        self.at(0.5, FadeIn(title))

        vessel = Rectangle(width=6.0, height=2.4, color="{equip}").shift(DOWN * 0.2)
        self.at(4.0, Create(vessel))

        arrow = Arrow(LEFT * 3.4, RIGHT * 3.4, color="{cold}").shift(DOWN * 0.2)
        self.at(10.0, GrowArrow(arrow))

        label = Text("A fluid deforms continuously under shear",
                     font_size=22, color=WHITE).move_to(DOWN * 2.7)
        self.at(15.0, FadeIn(label))

        self.hold_until(TOTAL_RUNTIME)
'''


# ── stubs ────────────────────────────────────────────────────────
def stub_call(system, prompt, *, schema=None, tools=None, **kwargs):
    """Stands in for every Claude call, chosen by what the prompt asks for."""
    if "Scene class name" in prompt:
        scene = next(line.split(": ", 1)[1].strip()
                     for line in prompt.splitlines() if line.startswith("Scene class name"))
        return STUB_SCENE.format(runtime=RUNTIME, scene=scene,
                                 title="What is a Fluid",
                                 bg=config.BACKGROUND,
                                 equip=config.COLOURS["equipment"],
                                 cold=config.COLOURS["cold_in"]), []
    raise AssertionError("unexpected plain Claude call")


def stub_call_json(system, prompt, schema, **kwargs):
    if "SCRIPT UNDER REVIEW" in prompt:                 # reviewer
        return {"verdict": "APPROVED", "discrepancies": [],
                "sources_checked": ["LibreTexts Engineering — Fluid Mechanics"],
                "notes_for_mayur": "Clean draft."}
    return {                                            # writer
        "script": STUB_SCRIPT,
        "summary": "A plain English introduction to what makes something a fluid, "
                   "the properties that describe it, and how it behaves under force.",
        "sources_read": ["LibreTexts Engineering — Fluid Mechanics — "
                         "https://eng.libretexts.org/"],
        "key_points": ["A fluid cannot resist shear",
                       "Density and viscosity describe it",
                       "Viscosity changes with temperature"],
        "visual_beats": ["solid vs fluid under shear", "a vessel of fluid",
                         "flow through the vessel"],
    }


def stub_voiceover(script, destination, voice_id=None):
    """Silent MP3 of exactly RUNTIME seconds — stands in for ElevenLabs."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", str(RUNTIME), "-b:a", "128k", str(destination)],
        capture_output=True, check=True,
    )
    return vo.duration_seconds(destination)


# ── harness ──────────────────────────────────────────────────────
def check(label, condition, detail=""):
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{'  — ' + detail if detail else ''}")
    return bool(condition)


def run():
    claude_client.call = stub_call
    claude_client.call_json = stub_call_json
    vo.generate = stub_voiceover

    # script_writer/reviewer/manim_generator imported claude_client as a module,
    # so patching the module attributes above is enough.
    import manim_generator
    manim_generator.SYNC_TOLERANCE = 1.5     # low-quality render rounds to the frame

    results = []
    print(f"\nsandbox: {SANDBOX}\n")

    # 1 — script stage stops at the approval gate
    print("stage: script")
    rc = main.main(["--topic", "S1T1", "--stages", "script"])
    topic = q.find("S1T1", config.CURRICULUM_CSV)
    results.append(check("script stage exits 0", rc == 0))
    results.append(check("status -> awaiting_approval",
                         topic.status == q.AWAITING_APPROVAL, topic.status))
    results.append(check("script.txt written", topic.script_path.exists()))
    results.append(check("review.json written", topic.review_path.exists()))
    state = json.loads((topic.dir / "state.json").read_text())
    results.append(check("summary captured for the description",
                         bool(state.get("summary"))))

    # 2 — the gate actually blocks production
    print("\ngate: production blocked before approval")
    rc = main.main(["--topic", "S1T1", "--stages", "voiceover"])
    results.append(check("blocked with exit code 2", rc == 2))
    results.append(check("voiceover.mp3 not created",
                         not topic.voiceover_path.exists()))

    # 3 — approval
    print("\ngate: Mayur approves")
    main.main(["--topic", "S1T1", "--approve"])
    topic = q.find("S1T1", config.CURRICULUM_CSV)
    results.append(check("status -> approved", topic.status == q.APPROVED,
                         topic.status))

    # 4 — production stages, for real
    print("\nstages: voiceover -> animate -> assemble")
    rc = main.main(["--topic", "S1T1", "--stages", "voiceover,animate,assemble"])
    topic = q.find("S1T1", config.CURRICULUM_CSV)
    results.append(check("production stages exit 0", rc == 0))
    results.append(check("animation.py generated", topic.animation_path.exists()))
    results.append(check("animation.mp4 rendered", topic.rendered_path.exists()))
    results.append(check("final_video.mp4 assembled", topic.video_path.exists()))
    results.append(check("thumbnail.jpg extracted", topic.thumbnail_path.exists()))
    results.append(check("status -> produced", topic.status == q.PRODUCED,
                         topic.status))

    if topic.video_path.exists():
        v = vo.duration_seconds(topic.video_path)
        results.append(check(f"video length matches narration ({v:.2f}s vs {RUNTIME}s)",
                             abs(v - RUNTIME) < 1.5))
        has_audio = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
             "stream=codec_name", "-of", "csv=p=0", str(topic.video_path)],
            capture_output=True, text=True).stdout.strip()
        results.append(check("final video carries an audio track", bool(has_audio),
                             has_audio))

    # 5 — upload, dry run
    print("\nstage: upload (dry run)")
    rc = main.main(["--topic", "S1T1", "--stages", "upload", "--dry-run"])
    results.append(check("upload dry run exits 0", rc == 0))

    slot = yt.next_publish_slot(taken=q.scheduled_slots(config.CURRICULUM_CSV))
    body = yt.build_request_body(topic, state["summary"], slot)
    results.append(check("scheduled on a Tuesday or Thursday",
                         slot.weekday() in (1, 3), slot.strftime("%A")))
    results.append(check("scheduled at 8:00 PM IST",
                         (slot.hour, slot.minute) == (20, 0)))
    results.append(check("uploaded private with publishAt",
                         body["status"]["privacyStatus"] == "private"
                         and body["status"]["publishAt"].endswith("Z")))
    desc = body["snippet"]["description"]
    results.append(check("description carries all three open sources",
                         all(s in desc for s in ("NPTEL", "LibreTexts",
                                                 "MIT OpenCourseWare"))))
    results.append(check("description mentions neither 'free' nor a textbook",
                         "free" not in desc.lower()
                         and "coulson" not in desc.lower()))
    results.append(check("title within YouTube's 100 chars",
                         len(body["snippet"]["title"]) <= 100,
                         body["snippet"]["title"]))

    print("\n--- generated description ---")
    print(desc)
    print("-----------------------------")

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    code = run()
    shutil.rmtree(SANDBOX, ignore_errors=True)
    sys.exit(code)
