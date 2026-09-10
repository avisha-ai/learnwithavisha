# LearnWithAvisha — the world engine

A reusable asset library and a scene-recipe system. Episodes describe what
happens; the world supplies everything they happen to.

## The rule everything else serves

**Episodes never own assets. The world owns assets.**

`engine/loader.py` is where that is enforced. An episode names a location,
some equipment and some characters, and gets back the canonical ones. There
is no way for an episode to hand in its own drawing, which is what stops the
world drifting apart episode by episode. Improve E-101 once and every episode
that says `"equipment": ["E-101"]` inherits it.

## Layout

```
learnwithavisha_engine/
├── world/                     ← canonical. Everything lives here.
│   ├── lighting.json          one sun, one palette, for the whole world
│   ├── locations/exchanger_bay/
│   │   ├── location.json      layers, haze, framings, stand marks, tags
│   │   ├── background.py/.svg sky, sun, distant plant, steel frame
│   │   ├── pipework.py/.svg   lines that land on real nozzles
│   │   └── foreground.py/.svg grating deck, handrail, near framing
│   ├── equipment/E-101/
│   │   ├── metadata.json      what the machine IS
│   │   └── exterior.py/.svg
│   ├── characters/
│   │   ├── wade_reference.png · lyra_reference.png · ellis_reference.png
│   │   ├── character_sheet.py all three, all poses, one morning
│   │   └── wade/ lyra/ ellis/
│   │       ├── character.json proportions, wardrobe, direction
│   │       ├── poses.json     named poses; the rig invents nothing
│   │       ├── rig.py         what this person wears over the shared solver
│   │       └── neutral/walking/inspecting.svg
│   ├── instruments/
│   │   ├── temperature_gauge.py/.json/.svg
│   │   └── indicator_light.py/.json   running lamps and beacons
│   └── sound/                 plant_ambience · steam · footsteps_grating
├── engine/
│   ├── draw.py       drawing kit; every asset shades from lighting.json
│   ├── figure.py     the shared human solver — gait, lean, head, rim
│   ├── loader.py     the world registry
│   ├── camera.py     wide_establishing · slow_push_in · instrument_closeup
│   ├── actions.py    walk_to · stop · look_at · second_glance · check_log
│   ├── sound.py      stem synthesis + episode mix
│   ├── scene.py      recipe → frames
│   └── export_svg.py builders → canonical SVG
└── episodes/ep001_the_eleven_day_creep/
    ├── brief.md      the story, as written by the Creative Director
    ├── episode.json  the recipe derived from it — shots, blocking, sound
    ├── style_frame.py
    ├── render.py
    └── finish.sh
```

## Build

```
BIN=../.micromamba/root/envs/manim/bin
cd episodes/ep001_the_eleven_day_creep
$BIN/python -m manim -s -qh style_frame.py StyleFrameA   # style frame
$BIN/python -m manim -qh    render.py Ep001              # film, ~1620 frames
./finish.sh                                              # grade, pad, mix
```

`python -m engine.sound` regenerates the world stems.
`python -m engine.export_svg` regenerates the canonical SVGs.

## What an episode looks like

```json
{
  "location": "exchanger_bay",
  "characters": ["wade"],
  "equipment": ["E-101"],
  "shots": [
    {"camera": "wide_establishing",  "target": "exchanger_bay"},
    {"camera": "slow_push_in",       "target": "wade"},
    {"camera": "instrument_closeup", "target": "TI-1014"}
  ],
  "timeline": [
    {"action": "walk_to",       "mark": "at_TI-1014", "arrive": 15.4},
    {"action": "look_at",       "target": "TI-1014"},
    {"action": "stop"},
    {"action": "second_glance", "target": "TI-1014"},
    {"action": "check_log",     "target": "TI-1014", "until": 25.4}
  ]
}
```

Episode 2 changes the words, not the drawings.

## The world, as frozen

**Units and ground.** 1 world unit = 1 metre. The grating deck the operator
walks on is y = 0. The distant plant stands on y = 0.62.

**Light.** One low morning sun behind and left of the bay, on the horizon.
Everything is contre-jour: cool steel bodies, warm rims, the sky brighter
than the plant. `lighting.json` is the only place this is written down, and
`engine/draw.py` is the only thing that reads it, so an asset never gets to
light itself from somewhere else.

**Depth.** Four layers. Distance is loss of contrast, never a change in light
direction. Haze sheets are tinted to the sky at each height — haze a warm
dawn with a cool grey and every silhouette turns blue and jumps forward.

**Colour.** Red is reserved for real alarms. Nothing here is red. Hi-vis
ochre is the only saturated colour the world allows, which is why Lyra is the
one the eye goes to when she is in frame.

**Perspective.** The floor carries the depth and the equipment stays in
near-elevation. That keeps E-101 canonical and readable at any scale while
still giving a place you could walk into.

### E-101

A 1-2 shell-and-tube exchanger, hot process on the tube side. Both tube
nozzles land on the channel head, which is what makes it a two-tube-pass
machine. Shell inlet at the far end and outlet at the near end, so the shell
runs counter-current to the first tube pass; inlet bottom and outlet top, so
it runs liquid-full.

The process is on the **tube** side because the process is the fouling stream
here, and the tubes are the side you can rod out. That is also why the drift
shows up on TI-1014, which reads the process outlet on his walking route.

### The three canonical characters

Designed from the reference images in `world/characters/`, translated into
this world rather than copied from them. The references are rendered
three-dimensional characters; this world is flat, banded and backlit, so what
carries across is identity, not surface.

Each one has to be recognisable at forty pixels tall, so each was given a
silhouette job that no other character does:

| | identity at distance | build | direction |
|---|---|---|---|
| **Wade** | bulk, bib straps, silver beard, brass gauge on the chest | widest and shortest | moves deliberately, never rushes |
| **Lyra** | the bun above the skull line, brightest garment, tablet glow | slimmest, leans forward | quick and precise |
| **Ellis** | upright stillness, dark knit stripe down an open olive jacket, gloved hands | tallest, straightest | still; his pause is an event |

Three poses each — `neutral`, `walking`, `inspecting` — named in each
character's `poses.json` and exported to SVG beside their `rig.py`.

`engine/figure.py` holds the shared solver: gait, lean, head pitch, the turn,
and the single rim pass. Characters differ in what they wear and how they
carry themselves, not in how a leg works. Head parts are sized in multiples
of head radius, never in body scale — tuned against body scale they come out
several times too large, which is the difference between a face and a
snowman.

**Lyra's tablet is the world's one sanctioned second light source.** It is a
device she actually carries, so it may cast a small local glow on her forearm
and under her jaw. Nothing else in this world lights from anywhere but the
morning sun.

**None of the three wears a hard hat**, which matches the references. Flag it
if plant PPE should override the character design.

### Instruments and lines

`TI-1014` process outlet, digital · `TI-1013` process inlet, dial ·
`PI-1012` cooling water inlet, dial.
`6"-P-10103` · `6"-P-10104` · `8"-CWS-10121` · `8"-CWR-10122`

### Voiceover

An episode may carry spoken lines in `episode.json` under `voiceover`. Each
names the character, the line, the second it lands on, and the mp3 to use.
The mix drops it in if the file is there and says so plainly if it is not —
the beat then plays as a held silence rather than failing the render.

Generating them is manual for now. The ElevenLabs account is free tier, and
the API refuses library voices with `paid_plan_required`, which includes
Daniel. So the line comes off elevenlabs.io by hand and gets saved beside
`episode.json` under the filename the recipe names.

### Indicator lights

Running lamps and beacons, placed by the location in `indicators_placed`.
They matter more than their size suggests. A still plant is a drawing; a
plant with a few lamps breathing at different rates is a place that has been
running all night. Every lamp carries its own period and phase, because
lights that blink together read as decoration and lights that do not read as
independent machines.

They are also doing story work. Red is reserved, so these are green and
amber, and every one of them in Episode 1 says RUNNING NORMALLY — including
the lamp bolted to the exchanger that is quietly fouling shut. The plant is
not lying. Nobody has asked it the right question yet.

### Sound

Three world stems, placed per episode. The machine bed never changes level —
if the plant sounded wrong the story would be over. Footsteps are read off
the character's gait, so they swell as he approaches and stop when he stops.
In the last shot the air drops about 7 dB and the stereo image closes while
the machine stays exactly where it was. No music.

## About the SVGs

The Python builders are the source; the SVGs are exports. Both are shipped
because a canonical asset should be inspectable and diffable without running
Manim — open `exterior.svg` and you see exactly the E-101 every episode gets.

The source is not SVG because these assets are parametric. E-101 shades
itself from `lighting.json`, so moving the sun re-lights the machine. The
operator is a solver, not a drawing: a single SVG cannot hold a gait. If
hand-drawn art ever replaces a builder, `engine/loader.py` is where it
plugs in, and that is a real piece of work rather than a swap.

## What is deliberately NOT built

Pilot 001 does not need these, so guessing at them now would be guessing at
stories nobody has written:

- `equipment/E-101/cutaway` — this episode never goes inside the exchanger
- `follow_character`, `return_to_wide` — no shot here uses them
- `turn_away()` — he never turns away
- any second location, character, or piece of equipment
- fouling, heat-transfer theory, narration, alarms, music

## Supersedes

`../visual_pilot_001/` is the hand-built version of this same scene. Its
world has been ported into `world/` here. Keeping both means two copies of
E-101, which is exactly what this architecture exists to prevent — delete it
once you are happy with what the engine renders.

`world/characters/operator_01/` was the placeholder for the character Wade
now plays. SKILL.md names Wade for Episode 1, so `episode.json` casts Wade
and operator_01 is no longer referenced by anything. It can go too.
