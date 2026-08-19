# SKILL: LearnWithAvisha Video Production
## Version 1.0 | August 2026

---

## What This Skill Is

This skill enables production of LearnWithAvisha chemical engineering education videos without repeating decisions already made. Read this before starting any new video.

---

## Brand Identity — Frozen

**Channel name:** LearnWithAvisha
**Tagline:** Chemical Engineering — Made Simple.
**Website:** learnwithavisha.ai (coming soon)
**YouTube:** LearnWithAvisha
**Owner:** Mrinal | Avisha.AI
**GitHub:** github.com/avisha-ai/learnwithavisha

---

## Logo / Watermark — Frozen

- A small monogram **"LWA"** styled in the Avisha brand
- Positioned: bottom right corner of every video frame
- Style: elegant, minimal, like a hallmark or watermark
- Colour: white with 40% opacity — subtle, never distracting
- Font: serif, slightly italic — feels like an engineering atelier mark
- Size: small enough to not distract, present enough to brand every frame
- DO NOT put LearnWithAvisha as a heading at the top of the video
- DO NOT mention the word "free" anywhere in any video

---

## Voice — Frozen

**Voice:** Leandra — Clear and Professional (ElevenLabs)
**Model:** Eleven v3
**Speed:** 1.00
**Stability:** 75% (Robust side)
**Style Exaggeration:** None (fully left)
**Output format:** MP3 44.1 kHz 128kbps

To generate voiceover:
1. Go to elevenlabs.io
2. Text to Speech
3. Select Leandra
4. Select Eleven v3 model
5. Paste full script
6. Generate and download as voiceover.mp3

---

## Animation Style — Frozen

**Tool:** Manim (Python) — Community Edition
**Resolution:** 1920x1080 @ 60fps
**Background:** Dark (#0d0d1a or similar deep dark)
**Colour coding:**
- Hot fluid / high temperature = RED (#ff4444) → ORANGE (#ff8c00)
- Cold fluid / low temperature = BLUE (#4488ff) → LIGHT BLUE (#90caf9)
- Heat transfer = YELLOW
- Equipment shell/structure = Steel grey (#b0bec5)
- Labels = WHITE
- Accent / highlight = YELLOW (#FFD700)
- Watermark LWA = WHITE at 40% opacity

**Animation principles:**
- Each element builds on screen one at a time — never dump everything at once
- After each major element appears — PAUSE 2.5 seconds — breathing room for viewer
- Total animation duration MUST match voiceover duration exactly
- Screen must NEVER go blank while voiceover is still playing
- Last frame holds until voiceover ends
- Smooth transitions — 1.0 to 1.5 seconds per element appearing

---

## Video Structure — Frozen

Every video follows this structure:

1. **Opening** — LWA watermark appears bottom right. Topic title appears. 3 second hold.
2. **Equipment build-up** — elements appear one by one in process flow order
3. **Flow animation** — fluids/streams animate through the equipment
4. **Labels appear** — temperatures, pressures, stream names — synced to voice
5. **Pause moments** — 2.5 second pauses after each major reveal
6. **Key points summary** — appears at end of animation, holds while voice summarises
7. **End** — topic title fades, LWA watermark pulses gently, fades out

---

## Script Writing Rules — Frozen

- Textbook faithful — every statement referenced to source textbook and chapter
- Generic — no opinions, no "in practice what happens is"
- Simple language — analogy first, concept second, equation last
- Length — 4 to 5 minutes (550 to 700 words)
- Tone — calm, clear, like a good professor explaining to a first year student
- Structure:
  1. Opening hook — one sentence on why this matters
  2. What it is — simple definition
  3. How it works — step by step, synced to animation
  4. Key variables — what affects performance
  5. Where it's used — real plant applications
  6. Key points recap — 3 to 4 bullet points spoken clearly
  7. Close — "This is LearnWithAvisha — chemical engineering fundamentals, explained simply."
- Always end with: Reference: [Textbook name], Chapter [X]
- NEVER mention "free"
- NEVER mention pricing or Avisha services

---

## Quality Check — Frozen

Before any video is produced:

**API Call 1 — Writer**
System prompt: "You are a chemical engineering educator with 20 years experience. Read the textbook chapter provided. Write a teaching script strictly inside what the textbook says. Reference the textbook by name and chapter for every key statement. Follow the LearnWithAvisha script structure exactly."

**API Call 2 — Reviewer**
System prompt: "You are a chemical engineering expert. Compare this script against the textbook chapter provided. Find any error, wrong number, wrong unit, wrong assumption, or statement not supported by the textbook. List every discrepancy. If clean, respond APPROVED."

**Human approval — Mayur**
Mayur reads the reviewed script. 10 minutes maximum. Approves or notes changes. No video is produced without approval.

---

## Curriculum — Subject Order

Videos are produced in this exact order. Never random. Never skip.

### Subject 1 — Fluid Flow
1. What is a fluid — properties and behaviour
2. Pressure in fluids — Pascal's law
3. Bernoulli's equation — the energy balance
4. Reynolds number — laminar vs turbulent flow
5. Pipe flow — velocity profiles
6. Pressure drop in pipes — Darcy-Weisbach
7. Centrifugal pumps — how they work
8. Pump curves and system curves
9. Valves — types and functions
10. Flow measurement — orifice, venturi, rotameter

### Subject 2 — Heat Transfer
1. Modes of heat transfer — conduction, convection, radiation
2. Fourier's law — conduction
3. Newton's law of cooling — convection
4. Overall heat transfer coefficient — U
5. Log mean temperature difference — LMTD
6. Shell and tube heat exchanger — basics ✅ DONE
7. Shell and tube — parallel vs counter-current flow
8. Shell and tube — baffles and their purpose
9. Shell and tube — multi-pass arrangements
10. Shell and tube — fouling and cleaning
11. Plate heat exchangers
12. Condensers
13. Reboilers
14. Jacketed vessels

### Subject 3 — Mass Transfer
1. Fick's law of diffusion
2. Gas absorption — principles
3. Packed columns
4. Distillation — vapour-liquid equilibrium
5. McCabe-Thiele method
6. Distillation column internals
7. Liquid-liquid extraction
8. Evaporation
9. Drying
10. Crystallisation

### Subject 4 — Reaction Engineering
1. Types of chemical reactions
2. Rate of reaction
3. Batch reactor
4. Continuous stirred tank reactor — CSTR
5. Plug flow reactor — PFR
6. Yield and selectivity
7. Temperature effects on reaction rate

### Subject 5 — Thermodynamics
1. First law of thermodynamics
2. Second law and entropy
3. Phase equilibrium
4. Vapour-liquid equilibrium — VLE
5. Equations of state
6. Refrigeration cycles

### Subject 6 — Separation Processes
1. Filtration
2. Centrifugation
3. Sedimentation
4. Membrane separation

---

## File Structure — Every Video

```
learnwithavisha/
├── CLAUDE.md
├── SKILL.md                        ← this file
├── pilot/                          ← shell and tube pilot (complete)
│   ├── shell_tube_animation.py
│   ├── script.txt
│   ├── voiceover.mp3
│   └── final_video.mp4
├── subject1_fluid_flow/
│   ├── 01_what_is_a_fluid/
│   │   ├── animation.py
│   │   ├── script.txt
│   │   ├── voiceover.mp3
│   │   └── final_video.mp4
│   └── ...
├── subject2_heat_transfer/
│   └── ...
└── curriculum/
    └── topic_queue.csv
```

---

## Pink Baby Build Instructions — Every Video

1. Read SKILL.md first — all decisions are already made
2. Read the script for the current topic
3. Write Manim animation Python file — follow animation style rules above
4. Ensure LWA watermark bottom right — white, 40% opacity, serif italic monogram
5. Ensure total animation duration matches voiceover duration exactly
6. Ensure 2.5 second pauses after each major element reveal
7. Render at 1080p60
8. Combine with voiceover.mp3 using ffmpeg
9. Output as final_video.mp4
10. Commit to GitHub

---

## What Is Coming Next After Pilot

Shell and tube series — in order:
- Video 2: Parallel vs counter-current flow comparison
- Video 3: What baffles do and why they matter
- Video 4: Single pass vs multi-pass arrangements
- Video 5: Fouling — what it is, how it affects U, how to clean

Then move to Subject 1 — Fluid Flow — from Topic 1.

---

## Key Principles — Never Forget

1. Textbook faithful — referenced to source
2. Generic — no invented claims
3. Simple language always
4. Two AI quality checks before human sees script
5. Mayur approves before any video publishes
6. LWA watermark only — no heading, no end card repeat
7. Never mention "free"
8. Animation synced to voiceover — never out of sync
9. Breathing pauses after every major reveal
10. Quality over quantity — one good video beats three rushed ones

---

*Skill created: August 2026*
*Project: LearnWithAvisha*
*By: Claude (Creative Director) | Avisha.AI*
