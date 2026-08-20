# LearnWithAvisha — Complete Ecosystem
## Pink Baby Master Brief | August 2026

---

## What We Are Building

A complete free chemical engineering education ecosystem consisting of three connected parts:

**Part 1 — YouTube Channel** (learnwithavisha on YouTube)
Automated faceless animated videos. One to two per week. Manim animations synced to AI voiceover. Textbook faithful. Simple language.

**Part 2 — Website** (learnwithavisha.ai)
The organised curriculum home. Videos embedded by subject and topic. Students find the full learning path here. Clean. Simple. Avisha branded.

**Part 3 — AI Assistant** (ask.learnwithavisha.ai)
A dedicated chemical engineering AI professor. Available 24/7. Answers any ChE question — whether the video exists or not. Grounded in open licensed sources. Simple language. Never generic. Never lazy.

---

## The Mission — One Sentence

**Give every chemical engineering student in the world a free, always-available, textbook-faithful professor — and show them what the equipment actually looks like.**

---

## Part 1 — Video Pipeline

### Status
Pilot video complete — Shell and Tube Heat Exchanger V1 ✅
Session 1 fixes complete ✅

### Video Format — V1 (Current)
- Tool: Manim Python
- Resolution: 1920x1080 @ 60fps
- Background: Dark (#0d0d1a)
- Voice: Leandra — ElevenLabs Eleven v3
- Style: 2D schematic — textbook diagram style animated

### Video Format — V2 (Next Target)
Side by side split screen:
- Left panel (960x1080): Manim 2D schematic — what the textbook shows
- Right panel (960x1080): PyVista Python — 3D equipment render — what it looks like in a real plant
- Voice bridges both: "On the left — how engineers draw it. On the right — what you see in the plant."
- Assembly: ffmpeg splits screen, combines both panels, adds voiceover
- This is the Avisha knockout format — nobody in ChE education does this
- Basic 3D shapes only: horizontal cylinder, vertical cylinder, rectangle, cube, cone, sphere, arrows

### Branding Rules — Frozen
- LWA monogram watermark bottom right — always visible
- White italic serif Georgia font, thin circle border, 85% opacity
- Never put LearnWithAvisha as a heading at the top
- Never mention "free" anywhere in any video
- Never repeat branding — watermark only, no end card duplication
- Every video ends: "This is LearnWithAvisha — chemical engineering fundamentals, explained simply."

### References — Description Box Only
References go in the YouTube description box — NEVER inside the video itself.

Reasons:
- References inside video interrupt learning flow
- Description box is standard practice for all serious educational channels
- Clean, professional, always accessible without cluttering the animation

**Description template — Pink Baby auto-generates this for every video:**

```
Topic: [Topic Name]
Subject: [Subject Name] — LearnWithAvisha Curriculum

[2-3 sentence plain English summary of what the video covers]

📚 References:
• NPTEL — Chemical Engineering — [relevant module]
  nptel.ac.in
• LibreTexts Engineering — [relevant chapter]
  eng.libretexts.org
• MIT OpenCourseWare — Chemical Engineering
  ocw.mit.edu

🔗 Full curriculum: learnwithavisha.ai
❓ Ask anything: ask.learnwithavisha.ai

By Avisha.AI | Engineering Made Intelligent
```

Pink Baby generates this description automatically for every video
and passes it to the YouTube Data API during upload.
No manual description writing ever needed.

### Upload Plan — Frozen

**First 5-6 videos — manual upload by Mrinal**
Automation takes over from Video 7 onwards.

Reasons:
- Gives Mrinal and Mayur full control over the launch
- Allows quality check of each video before it goes public
- Ensures the channel looks established from day one

Manual upload checklist for each of the first videos:
1. Watch the full video — approve it
2. Go to YouTube Studio
3. Upload the MP4
4. Paste the auto-generated description from Pink Baby
5. Add to correct subject playlist
6. Set thumbnail — first frame of animation
7. Schedule for Tuesday or Thursday 8pm IST
8. Publish

From Video 7 onwards — fully automatic.
Pink Baby handles everything via YouTube Data API.
Tuesday and Thursday. 8pm IST. No human involvement needed.

### Launch Plan
Do not launch with one video. Launch with 5-6 videos already uploaded.
A channel with 5-6 videos from day one looks established.
A channel with 1 video looks like an experiment.
Build the library first. Then open the channel. Then share.

### YouTube Upload Schedule — Frozen
- Upload day: Tuesday and Thursday
- Upload time: 8:00 PM IST
- Method: Fully automatic via YouTube Data API
- Pink Baby bakes this schedule into youtube_upload.py
- No manual uploading after the first 5-6 launch videos

### YouTube Uploader — youtube_upload.py must:
- Schedule every video for Tuesday OR Thursday at 8pm IST
- Alternate between the two days automatically
- Auto-generate title from topic name
- Auto-generate description from template above
- Auto-assign to correct subject playlist
- Auto-add tags from topic and subject
- Set thumbnail — auto-generated from first animation frame
- Upload as private first — publish at scheduled time

---

## Curriculum — Full Subject Order
Videos produced strictly in this order. Never random. Never skip.

**Subject 1 — Fluid Flow**
01 What is a fluid — properties and behaviour
02 Pressure in fluids — Pascal's law
03 Bernoulli's equation — the energy balance
04 Reynolds number — laminar vs turbulent flow
05 Pipe flow — velocity profiles
06 Pressure drop in pipes — Darcy-Weisbach
07 Centrifugal pumps — how they work
08 Pump curves and system curves
09 Valves — types and functions
10 Flow measurement — orifice, venturi, rotameter

**Subject 2 — Heat Transfer**
01 Modes of heat transfer — conduction, convection, radiation
02 Fourier's law — conduction
03 Newton's law of cooling — convection
04 Overall heat transfer coefficient — U
05 Log mean temperature difference — LMTD
06 Shell and tube heat exchanger — basics ✅ PILOT DONE
07 Shell and tube — parallel vs counter-current flow
08 Shell and tube — baffles and their purpose
09 Shell and tube — multi-pass arrangements
10 Shell and tube — fouling and cleaning
11 Plate heat exchangers
12 Condensers
13 Reboilers
14 Jacketed vessels

**Subject 3 — Mass Transfer**
01 Fick's law of diffusion
02 Gas absorption — principles
03 Packed columns
04 Distillation — vapour liquid equilibrium
05 McCabe-Thiele method
06 Distillation column internals
07 Liquid liquid extraction
08 Evaporation
09 Drying
10 Crystallisation

**Subject 4 — Reaction Engineering**
01 Types of chemical reactions
02 Rate of reaction
03 Batch reactor
04 Continuous stirred tank reactor CSTR
05 Plug flow reactor PFR
06 Yield and selectivity
07 Temperature effects on reaction rate

**Subject 5 — Thermodynamics**
01 First law of thermodynamics
02 Second law and entropy
03 Phase equilibrium
04 Vapour liquid equilibrium VLE
05 Equations of state
06 Refrigeration cycles

**Subject 6 — Separation Processes**
01 Filtration
02 Centrifugation
03 Sedimentation
04 Membrane separation

---

## Script Quality Rules
- Textbook faithful — every statement referenced to open source
- Generic — no opinions, no invented claims
- Simple language — analogy first, concept second, equation last
- Two Claude API review passes before human sees script
- Mayur approves in 10 minutes before any video is produced
- Never mention "free"

---

## Video Production Pipeline — Automated Python on Railway

```
Scheduled Python script
        ↓
Read next topic from Google Sheet queue
        ↓
Fetch open source reference from NPTEL/LibreTexts/MIT OCW
        ↓
Claude API Call 1 — Write script from reference material
        ↓
Claude API Call 2 — Review script against reference
        ↓
Save reviewed script to Google Drive
        ↓
WhatsApp notification to Mayur — "Script ready"
        ↓
Mayur approves in Google Sheet
        ↓
Generate Manim Python code via Claude API
        ↓
Run Manim — render animation MP4
        ↓
ElevenLabs API — generate voiceover MP3 (Leandra, v3)
        ↓
ffmpeg — combine animation + voiceover → final_video.mp4
        ↓
Auto-generate description from template
        ↓
YouTube Data API — upload, set metadata, schedule publish
        ↓
Google Sheet status updated to Published
        ↓
Supabase — add topic to Q&A database as "video available"
```

---

## 3D Animation Tool — Frozen

**PyVista — chosen tool for 3D**
- Pure Python — Pink Baby writes it exactly like Manim
- Designed specifically for engineering and scientific visualisation
- Clean 3D renders — perfect for educational equipment diagrams
- No separate software — installs via pip
- Exports directly to MP4
- Same pipeline as Manim — no new tools needed

```bash
pip install pyvista
pip install pyvista[all]
```

**Basic shapes for ChE equipment:**
- Horizontal cylinder — shell and tube heat exchanger, pipes
- Vertical cylinder — distillation column, absorption column, reactor vessel
- Rectangle/cube — tank, reactor body
- Cone — vessel heads, nozzles
- Sphere — storage vessels
- Arrows — fluid flow direction, inlet/outlet streams

**Manim 3D — backup option**
If PyVista proves difficult for a specific shape — Manim has built-in 3D capability (ThreeDScene). Use as fallback only.

**Blender — shelved**
Too complex. Revisit only if PyVista cannot produce sufficient quality.

**Three.js — web only**
Use only if ask.learnwithavisha.ai needs interactive 3D the student can rotate in browser.

---

## Part 2 — Website (learnwithavisha.ai)

### Purpose
Organised curriculum home. Students find the full learning path here. Videos embedded by subject and topic. Avisha branded.

### Structure
```
learnwithavisha.ai/
├── Home — what this is, who it's for
├── Curriculum — all 6 subjects listed
│   ├── /fluid-flow
│   ├── /heat-transfer
│   ├── /mass-transfer
│   ├── /reaction-engineering
│   ├── /thermodynamics
│   └── /separation-processes
├── Ask — link to ask.learnwithavisha.ai
└── About — Avisha.AI, Mrinal, the mission
```

### Design Principles
- Clean. Minimal. No clutter.
- Dark theme — consistent with video aesthetic
- LWA monogram prominent but not aggressive
- Mobile first — students use phones
- Fast — no heavy frameworks
- Each topic page: video embedded + text summary + link to Ask

### Tech Stack
- Next.js 14
- Tailwind CSS
- Vercel hosting
- Hostinger DNS — learnwithavisha.ai pointing to Vercel
- YouTube API — auto-fetches new videos when uploaded
- Supabase — topic database, video status tracking

---

## Part 3 — AI Assistant (ask.learnwithavisha.ai)

### What This Is
A dedicated chemical engineering AI professor. Not a generic chatbot. A specialist.
Available 24 hours. 7 days. Never tired. Answers any ChE question.
Grounded in open licensed sources. Simple language always.

**One sentence: A chemical engineering professor that lives inside ask.learnwithavisha.ai — available to every student in the world, for free, forever.**

### What It Does
- Answers any chemical engineering question in simple language
- References open licensed sources for every answer
- Links to the relevant LearnWithAvisha video if it exists
- If video does not exist — says "Video coming soon — subscribe to be notified"
- Stays strictly within chemical engineering — does not answer unrelated questions
- Honest about limits — if something is too advanced it says so and gives the foundation first

### What It Does NOT Do
- Does not give opinions
- Does not invent answers or numbers
- Does not answer outside ChE scope
- Does not replace the videos — it complements them
- Does not pretend to know what it does not know

### Knowledge Base — Open Licensed Sources Only

**Sources used — all free, all open licensed, zero legal risk:**
- NPTEL — nptel.ac.in — IIT lecture notes and videos
- LibreTexts Engineering — eng.libretexts.org
- OpenStax — openstax.org
- MIT OpenCourseWare — ocw.mit.edu

**How RAG works:**
1. Open source content chunked into sections stored in Supabase with pgvector
2. Student asks a question
3. System finds most relevant chunks via vector similarity search
4. Chunks fed to Claude API along with the question
5. Claude answers using the actual source text
6. Answer includes source name and module as reference

### Answer Format — Every Response

```
[Simple 2-3 sentence answer in plain English]

[Explanation — analogy first, concept second, equation if needed]

[Source reference — "According to NPTEL Chemical Engineering, Module X..."]

[Related video — embedded or linked if available]

[Related questions — 3 suggestions]
```

### System Prompt — The AI Professor Persona

```
You are a dedicated chemical engineering professor and teaching assistant
for LearnWithAvisha. You have deep expertise across all areas of chemical
engineering — fluid flow, heat transfer, mass transfer, reaction engineering,
thermodynamics, and separation processes.

Your rules:
1. Answer ONLY chemical engineering questions. Politely decline anything else.
2. Always use simple language. Explain to a first year student, not a PhD.
3. Always use analogy first, concept second, equation last.
4. Always reference the open source provided to you.
5. Never invent an answer. If unsure, say so and point to the relevant source.
6. If a question is too advanced, give the foundation first.
7. Keep answers concise — 150 to 300 words maximum.
8. End every answer with the source reference.
9. Suggest 3 related questions the student might also want to know.
10. If a LearnWithAvisha video covers this topic, mention it.

HARD RULES — never break these:
1. If you are not certain — say so explicitly. Always.
2. Never invent numbers — not pressures, temperatures, flow rates,
   equipment sizes, safety limits, or any specific values.
3. If the answer requires a specific value you cannot verify —
   say: "I cannot confirm this value with certainty.
   Please refer directly to [source]."
4. Never guess at safety-related information. Ever.
5. Refuse to answer rather than invent.
   A refused answer is safer than a confident wrong one.

You represent Avisha.AI — engineering made intelligent.
Be precise. Be clear. Be helpful. Never be generic.
```

### Tech Stack
- Next.js 14 frontend — clean single page, one search box
- Claude API — claude-sonnet-4-6 — the AI brain
- Supabase — pgvector — source chunk storage and retrieval
- Python — content chunking and embedding pipeline
- Vercel hosting
- Hostinger DNS — ask.learnwithavisha.ai

### Website Design — ask.learnwithavisha.ai

```
[LWA monogram — top left]

[Heading — centred]
"Ask anything about chemical engineering."

[Subheading]
"Grounded in NPTEL, LibreTexts, MIT OCW and more."

[Search box — large, centred]
"What would you like to know?"

[Example questions]
• How does a distillation column work?
• What is the difference between laminar and turbulent flow?
• Why does fouling reduce heat exchanger performance?
• What is NPSH and why does it matter for pumps?

[Answer appears below — clean, readable, referenced]
[Related video embedded if available]
[Related questions — clickable]

[Footer]
"LearnWithAvisha — Chemical Engineering Made Simple | By Avisha.AI"
```

---

## File Structure — Full Ecosystem

```
GitHub: avisha-ai/learnwithavisha
├── CLAUDE.md                    ← pilot brief
├── CLAUDE_MASTER.md             ← this file — master brief
├── SKILL.md                     ← video production bible
├── README.md
├── pilot/                       ← shell and tube pilot
├── curriculum/
│   └── topic_queue.csv
├── video_pipeline/
│   ├── main.py
│   ├── script_writer.py
│   ├── script_reviewer.py
│   ├── manim_generator.py
│   ├── voiceover.py
│   ├── assembler.py
│   └── youtube_upload.py
├── website/
│   ├── pages/
│   ├── components/
│   └── styles/
└── ask/
    ├── pages/
    ├── components/
    ├── api/
    │   ├── ask.py
    │   └── search.py
    ├── scripts/
    │   ├── chunk_sources.py
    │   └── embed_chunks.py
    └── prompts/
        └── professor.txt
```

---

## Supabase Database Schema

```sql
CREATE TABLE videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject TEXT NOT NULL,
  topic_number INTEGER NOT NULL,
  topic_name TEXT NOT NULL,
  youtube_url TEXT,
  status TEXT DEFAULT 'pending',
  published_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name TEXT NOT NULL,
  module TEXT NOT NULL,
  topic_tags TEXT[],
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE questions_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  source_reference TEXT,
  video_id UUID REFERENCES videos(id),
  asked_at TIMESTAMP DEFAULT NOW()
);
```

---

## Build Order — Six Sessions

### Session 1 — Pilot Video Fixes ✅ COMPLETE
1. Remove header title from shell tube animation ✅
2. Add LWA watermark bottom right ✅
3. Add 2.5 second pauses after each element ✅
4. Verify sync — animation matches voiceover exactly ✅
5. Render final_video_v2.mp4 ✅

### Session 2 — Video Pipeline Automation
1. topic_queue.csv — full curriculum list
2. script_writer.py — Claude API script generation
3. script_reviewer.py — Claude API quality check
4. voiceover.py — ElevenLabs API (Leandra, v3)
5. assembler.py — ffmpeg combination
6. youtube_upload.py — YouTube Data API — Tuesday Thursday 8pm IST
7. main.py — scheduler orchestrating all steps
8. Test end to end with Subject 1 Topic 1

### Session 3 — Knowledge Base Setup
1. chunk_sources.py — NPTEL/LibreTexts/MIT OCW content chunking
2. embed_chunks.py — embedding pipeline to Supabase
3. Supabase schema — knowledge_chunks table with pgvector
4. Test retrieval — does a question return relevant chunks?

### Session 4 — ask.learnwithavisha.ai
BEFORE writing any code — verify both guardrails are implemented:
- Open sources only in RAG pipeline — no copyrighted textbooks
- Hard rules in system prompt — no invented numbers, refuse when unsure

Then build:
1. Next.js frontend — single clean page
2. Search box and answer display
3. API route — question → vector search → Claude → answer
4. Video lookup — embed video if available
5. Related questions — suggested follow-ups
6. Deploy to Vercel
7. DNS — ask.learnwithavisha.ai on Hostinger

### Session 5 — learnwithavisha.ai Website
1. Next.js frontend — curriculum organised by subject
2. Subject pages — videos listed in order
3. Topic pages — video embedded + text summary + Ask link
4. Mobile optimised
5. Deploy to Vercel
6. DNS — learnwithavisha.ai on Hostinger

### Session 6 — V2 Video Format
1. PyVista Python script — 3D equipment render (basic shapes only)
2. Split screen assembly — Manim left + PyVista right
3. ffmpeg split screen pipeline
4. Test with shell and tube V2

---

## Key Principles — Never Forget

1. Open sources only — NPTEL, LibreTexts, OpenStax, MIT OCW
2. Never reproduce source text verbatim — point to it instead
3. Simple language always — first year student level
4. Two AI quality checks before any human sees a script
5. Mayur approves scripts — 10 minutes maximum
6. LWA watermark only — never heading, never twice
7. Never mention "free" in any video or answer
8. Animation synced to voiceover — never out of sync
9. Breathing pauses — 2.5 seconds after every major reveal
10. AI assistant answers ChE only — never wanders outside scope
11. AI never invents numbers — refuses rather than guesses
12. References in description box only — never inside the video
13. Launch with 5-6 videos — not one
14. First 5-6 uploads manual — automation from Video 7 onwards
15. Videos and Ask are connected — one ecosystem, not two

---

## DNS Setup — Hostinger

```
learnwithavisha.ai      A        75.2.60.5  (Vercel)
www.learnwithavisha.ai  CNAME    cname.vercel-dns.com
ask.learnwithavisha.ai  CNAME    cname.vercel-dns.com
```

---

## The Vision — Said Simply

A student anywhere in the world — Mumbai, Lagos, Manila, São Paulo — opens their phone. Types a question about distillation. Gets a clear, simple, accurate answer in seconds. Referenced to NPTEL or LibreTexts. With a link to a beautifully animated video showing exactly how it works — in 2D and in 3D.

For free. Forever.

That is LearnWithAvisha. That is Avisha.AI.

---

*Master brief written: August 2026*
*Project owner: Mrinal | Avisha.AI*
*Technical lead: Pink Baby (Claude Code in VS Code)*
*Creative Director: Claude (claude.ai)*
*Chief Architect: ChatGPT*
