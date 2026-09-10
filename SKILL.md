

## Episode Brief Format — Frozen September 2026

Every LearnWithAvisha episode — story or lesson — uses this exact format.
Claude writes both the story and the scene recipe.
Pink Baby builds directly from this. No translation step needed.

```
EPISODE: [Equipment/Topic] — [Episode Title]

CHARACTERS: [Which of Wade, Lyra, Ellis appear]
LOCATION: [exchanger_bay / pump_house / control_room / etc]
EQUIPMENT: [E-101 / P-201 / T-301 / etc]
NEW ASSETS: [None / list anything new needed]

SHOTS:

1. [Wide/Close/Medium] — [location] — [time of day]
   [What the character does]
   [What the plant is doing around them]

2. [Shot description]
   [Character action]
   [What earns attention]

3. [Shot description]
   [The reveal — number, sound, reading, anomaly]
   [Soundscape change if any]
   Hold. Fade.

WHAT THE VIEWER FEELS:
[One to three lines — emotional intention only]
[Not animation direction — just what the viewer should experience]

ENGINEERING TRUTH:
[The accurate principle behind the story]
[Referenced to open source — NPTEL / LibreTexts / MIT OCW]

UNRESOLVED QUESTION:
[The one question left hanging at the fade]
[This is what brings the viewer back]
```

---

## Story Universe — The World Grammar

Every episode follows this deeper structure:

World → Problem → Clue → Investigation → Engineering explanation → Payoff → New curiosity

Different episodes express this differently.
The structure is frozen. The choreography is never the same twice.

---

## The Three Characters — Canonical

**Wade** — The One Who Knows the Plant by Feel
Late 50s. Navy canvas coveralls. Silver beard. Brass pocket pressure gauge on leather lanyard.
Moves deliberately. Never rushes. The plant knows him.
Reference: world/characters/wade_reference.png

**Lyra** — The One Who Knows the Theory
Late 20s. Orange hi-vis field jacket. Round wireframe glasses. Dark curly hair messy bun.
Ruggedized tablet on left forearm — data glow on her jaw.
Forward leaning. Quick and precise. Always two steps ahead of everyone except the plant.
Reference: world/characters/lyra_reference.png

**Ellis** — The One Who Knows the Pattern
Early 40s. Olive field jacket. Dark crewneck. Utility gloves — chalk mark on right knuckle.
Still. Upright. Looks through things rather than at them.
His pause is an event.
Reference: world/characters/ellis_reference.png

---

## The Plant — Canonical Rules

- Equipment has history. Tags recur. What happened to E-101 in episode 1 matters in episode 6.
- Episodes never own assets. The world owns assets.
- New assets added only when a real episode requires them.
- AI may invent atmosphere. AI may never invent engineering.
- Equipment tags, piping, gauges, flow direction — always controlled and correct.

---

## Episode Writing Rule — Claude's Job

Claude writes:
- The story in plain language
- The scene recipe in the format above
- The engineering truth — accurately sourced
- The unresolved question

Claude does NOT write:
- Animation code
- Python functions
- Asset specifications
- Rendering instructions

That belongs to Pink Baby.

---

## Stories Already Written

Episode 1 — E-101 — The Eleven Day Creep
Characters: Wade
Engineering truth: Fouling reduces U silently. Pressure drop stays flat. Temperature drifts. No alarm until too late.
Unresolved question: Why did the pressure drop stay perfectly flat?
Status: Scene recipe complete. Assets in progress.


---

## Character Voices — Frozen September 2026

All voices generated via ElevenLabs API. Eleven v3 model. Stability 75%.

**Wade** — ElevenLabs voice: Daniel
Deep. Warm. Unhurried. Gravelly.
Speaks like someone who has seen everything and is never surprised.

**Lyra** — ElevenLabs voice: Leandra
Clear. Professional. Forward moving.
Already thinking about the next thing while saying this thing.

**Ellis** — ElevenLabs voice: Adam
Calm. Measured. Quiet.
Each word chosen carefully.

Rule: Never swap voices between characters. Ever.
The voice IS the character.


---

## ElevenLabs Voice IDs — Frozen September 2026

Use these exact IDs in the ElevenLabs API calls. Never look up by name — always use ID.

WADE_VOICE_ID = "9fHP3GqJWwJmIbYQwQ1V"    # Daniel — deep, warm, gravelly
LYRA_VOICE_ID = "9CeirP4ivY4Fg4JmYNWz"    # Leandra — clear, professional
ELLIS_VOICE_ID = "HdI8DDQNjJGf1UOh1gG0"   # Adam — calm, measured

Model: eleven_v3
Stability: 75%
Style Exaggeration: None
Speed: 1.00
