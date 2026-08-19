# LearnWithAvisha — Chemical Engineering Education

Free, automated chemical engineering education videos for students, teachers, and engineers worldwide.

**Website:** learnwithavisha.ai (coming soon)
**YouTube:** LearnWithAvisha (coming soon)
**By:** Avisha.AI

---

## What This Is

A fully automated pipeline that produces chemical engineering tutorial videos — faceless, animated, voiced by AI, published to YouTube — one to two videos per week.

Free forever. No registration. No paywall.

---

## Current Status

🟡 Pilot phase — Shell and Tube Heat Exchanger demonstration video

---

## Curriculum Plan

Videos follow standard ChE university syllabus in order:

1. **Fluid Flow** — Fluid properties → Pressure → Bernoulli → Reynolds number → Pipe flow → Pressure drop → Pumps
2. **Heat Transfer** — Conduction → Convection → LMTD → Heat exchangers → Condensers → Reboilers
3. **Mass Transfer** — Diffusion → Absorption → Distillation → Extraction → Evaporation → Drying
4. **Reaction Engineering** — Reaction types → Rate equations → Batch reactor → CSTR → PFR
5. **Thermodynamics** — Laws → Phase equilibrium → VLE → Equations of state
6. **Separation Processes** — Filtration → Centrifugation → Sedimentation → Membranes

---

## Tech Stack

| Component | Tool |
|---|---|
| Animations | Manim (Python) |
| Voiceover | ElevenLabs API |
| Video assembly | ffmpeg |
| Automation | Python on Railway |
| Quality check | Claude API (two-pass review) |
| Distribution | YouTube Data API |

---

## Pilot — How to Run

```bash
# Install Manim
pip install manim

# Render animation (low quality preview)
manim -pql shell_tube_animation.py ShellTubeScene

# Render animation (high quality final)
manim -pqh shell_tube_animation.py ShellTubeScene

# Combine with voiceover (after generating MP3 from ElevenLabs)
ffmpeg -i animation.mp4 -i voiceover.mp3 \
  -c:v copy -c:a aac -shortest final_video.mp4
```

---

## Quality Principles

- Every script is textbook-faithful — referenced to source chapter
- Two Claude API review passes before any human sees the script
- Human approval required before any video publishes
- Generic and accurate — no invented claims, no opinions

---

## Project Owner

Mrinal | Avisha.AI
github.com/avisha-ai/learnwithavisha
