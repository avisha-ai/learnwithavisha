# LearnWithAvisha — Chemical Engineering Education Videos
## Pink Baby Session Briefing

---

## What We Are Building

A free, automated chemical engineering education YouTube channel under the Avisha brand.

**Platform:** learnwithavisha.ai + YouTube
**Format:** Faceless animated videos with AI voiceover
**Audience:** ChE students, teachers, working engineers
**Cadence:** 1–2 videos per week (once pipeline is proven)

---

## Current Mission — Pilot Video Only

**DO NOT build the full automation pipeline yet.**

Build ONE demonstration video only:
- Topic: Shell and Tube Heat Exchanger
- Goal: Prove the concept works before committing to full build
- Mrinal watches it, approves, then we show Mayur
- If approved — full pipeline gets built next session

---

## Tech Stack — Decided

| Job | Tool |
|---|---|
| Animation | Manim (Python) — free, open source |
| Voiceover | ElevenLabs API (free tier for pilot) |
| Script | Pre-written (provided below) |
| Video assembly | Manual for pilot — ffmpeg to combine audio + video |
| Upload | Manual for pilot — YouTube Studio |
| Future automation | Pure Python on Railway — NO n8n |
| Repository | GitHub under Avisha organisation |

---

## Pilot Video — Shell and Tube Heat Exchanger

### What the animation must show

A clean schematic Manim animation — textbook style, not photorealistic.

**Sequence — builds up on screen as voice explains:**

1. Shell outline draws itself — horizontal cylinder
2. Tube bundle appears inside the shell
3. Hot fluid arrow enters left side of tubes — RED — labelled "Hot Fluid In"
4. Hot fluid travels through tubes left to right
5. Hot fluid exits right side — ORANGE — labelled "Hot Fluid Out" — colour change shows cooling
6. Cooling water arrow enters shell side right — BLUE — labelled "CW In"
7. Cooling water flows left through shell — counter-current to tube fluid
8. Cooling water exits left — LIGHT BLUE — labelled "CW Out" — colour change shows warming
9. Temperature labels appear: Hot In 150°C → Hot Out 80°C / CW In 30°C → CW Out 55°C
10. Arrow appears showing heat transfer direction — from tubes to shell side
11. Title card: "Shell and Tube Heat Exchanger" appears at top

**Style:**
- Clean white or dark background — dark preferred (easier on eyes)
- Colour coding: Red/Orange = hot, Blue/Light Blue = cold
- Labels clean and readable — engineering drawing style
- No clutter — only what is needed to understand the concept
- Animations smooth — 1–2 seconds per element appearing

---

### Script for Voiceover

This script goes to ElevenLabs to generate the voiceover MP3.

Mrinal will select the voice on elevenlabs.io before this step.

---

**SCRIPT — Shell and Tube Heat Exchanger**
*(approximately 4 minutes — 550 words)*

---

Welcome to LearnWithAvisha. Today we look at one of the most common pieces of equipment in any chemical plant — the shell and tube heat exchanger.

A heat exchanger does one job. It transfers heat from a hot fluid to a cold fluid — without the two fluids mixing.

The shell and tube design is the most widely used type in industry. Let us understand why — and how it works.

The equipment has two main parts. The shell — which is the large outer cylinder. And the tubes — a bundle of smaller tubes that run through the inside of the shell.

Two fluids flow through this equipment — but they never touch each other.

The first fluid flows inside the tubes. In our example, this is a hot process fluid entering at 150 degrees Celsius. As it travels through the tubes, it gives up its heat. By the time it exits, it has cooled down to 80 degrees Celsius.

The second fluid flows on the shell side — in the space between the shell wall and the outside of the tubes. In our example, this is cooling water entering at 30 degrees Celsius. As it absorbs heat from the tubes, it warms up. It exits at 55 degrees Celsius.

Notice the flow directions. The hot fluid enters from the left. The cooling water enters from the right. They flow in opposite directions. This is called counter-current flow.

Counter-current flow is important. It allows the maximum temperature difference between the two fluids throughout the length of the exchanger. This makes heat transfer more efficient.

The driving force for heat transfer is always the temperature difference. The greater the difference — the faster the heat moves from the hot fluid to the cold fluid through the tube wall.

The tube wall itself must be thin enough to allow heat to pass through easily — but strong enough to handle the operating pressures of both fluids.

In a real plant, shell and tube heat exchangers come in many sizes. From small units the size of a table — to large exchangers several metres long and over a metre in diameter.

They are used everywhere. Cooling reactor effluents. Preheating feed streams. Condensing vapours. Heating cold fluids before a distillation column.

The design of a shell and tube heat exchanger involves calculating the required heat transfer area — which depends on the heat duty, the overall heat transfer coefficient, and the log mean temperature difference. We will cover each of these in detail in future videos.

For now — remember the key points.

Shell and tube heat exchangers transfer heat between two fluids through a tube wall. Hot fluid inside the tubes. Cold fluid on the shell side. Counter-current flow for maximum efficiency. Temperature difference is the driving force.

This is LearnWithAvisha — chemical engineering fundamentals, explained simply.

---

*Reference: Coulson and Richardson — Chemical Engineering Volume 1, Chapter 12*

---

## File Structure

```
learnwithavisha/
├── CLAUDE.md                  ← this file
├── pilot/
│   ├── shell_tube_animation.py    ← Manim animation script
│   ├── script.txt                 ← voiceover script
│   ├── voiceover.mp3              ← generated by ElevenLabs
│   ├── animation.mp4              ← rendered by Manim
│   └── final_video.mp4            ← combined by ffmpeg
├── curriculum/
│   └── topic_queue.csv            ← subject/topic list for future videos
└── README.md
```

---

## Build Instructions — Pilot Session

### Step 1 — Manim animation

```bash
pip install manim
python shell_tube_animation.py
```

Renders to `/media/videos/shell_tube_animation/1080p60/ShellTubeScene.mp4`

### Step 2 — Voiceover

Mrinal generates MP3 from ElevenLabs manually for pilot.
Save as `pilot/voiceover.mp3`

### Step 3 — Combine with ffmpeg

```bash
ffmpeg -i animation.mp4 -i voiceover.mp3 \
  -c:v copy -c:a aac -shortest final_video.mp4
```

### Step 4 — Review

Mrinal and Mayur watch `final_video.mp4`
If approved → proceed to full pipeline build next session
If changes needed → note them in CLAUDE.md and revise

---

## What Pink Baby Must NOT Do This Session

- Do not build the automation pipeline yet
- Do not build Railway deployment yet
- Do not build YouTube upload automation yet
- Do not build the topic queue system yet
- Do not build learnwithavisha.ai website yet

**One video. Prove it works. Everything else follows.**

---

## Future Pipeline — For Reference Only

Once pilot is approved, next session builds:

```
Scheduled Python script (Railway)
        ↓
Read next topic from Google Sheet queue
        ↓
Fetch textbook chapter from Google Drive
        ↓
Claude API Call 1 — Write script from textbook chapter
        ↓
Claude API Call 2 — Review script against textbook
        ↓
Save reviewed script to Google Drive
        ↓
WhatsApp/email notification to Mayur
        ↓
Mayur approves in Google Sheet (10 minutes)
        ↓
Generate Manim animation Python code via Claude API
        ↓
Run Manim — render animation MP4
        ↓
ElevenLabs API — generate voiceover MP3
        ↓
ffmpeg — combine animation + voiceover
        ↓
YouTube Data API — upload and schedule
        ↓
Google Sheet status updated to Published
```

---

## Curriculum Plan — For Reference Only

Subject 1 — Fluid Flow
Subject 2 — Heat Transfer (pilot video is from here)
Subject 3 — Mass Transfer
Subject 4 — Reaction Engineering
Subject 5 — Thermodynamics
Subject 6 — Separation Processes

Full topic breakdown to be built next session.

---

## Key Principles — Never Forget

1. Textbook faithful — every statement referenced to source
2. Generic — no opinions, no "in practice" claims
3. Simple language — analogy first, concept second, equation last
4. Two AI quality checks before any human sees the script
5. Mayur approves — 10 minutes maximum — before any video publishes
6. Free forever for students — no paywalls, no registration

---

## GitHub

Repository: github.com/avisha-ai/learnwithavisha
Branch: main
Commit after every working milestone — not after every file change

---

*Last updated: August 2026*
*Project owner: Mrinal | Avisha.AI*
*Technical lead: Pink Baby (Claude Code in VS Code)*
*Creative Director: Claude (claude.ai)*
