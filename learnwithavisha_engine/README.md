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
│   ├── characters/operator_01/
│   │   ├── character.json     proportions, wardrobe, direction
│   │   ├── poses.json         named poses; the rig invents nothing
│   │   ├── rig.py             the solver
│   │   ├── log_sheet.py       his prop, because check_log() is his action
│   │   └── neutral/walking/inspecting.svg
│   ├── instruments/temperature_gauge.py/.json/.svg
│   └── sound/                 plant_ambience · steam · footsteps_grating
├── engine/
│   ├── draw.py       drawing kit; every asset shades from lighting.json
│   ├── loader.py     the world registry
│   ├── camera.py     wide_establishing · slow_push_in · instrument_closeup
│   ├── actions.py    walk_to · stop · look_at · second_glance · check_log
│   ├── sound.py      stem synthesis + episode mix
│   ├── scene.py      recipe → frames
│   └── export_svg.py builders → canonical SVG
└── episodes/ep001_the_drift/
    ├── episode.json  the recipe. This is the only file the story lives in.
    ├── style_frame.py
    ├── render.py
    └── finish.sh
```

## Build

```
BIN=../.micromamba/root/envs/manim/bin
cd episodes/ep001_the_drift
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
  "characters": ["operator_01"],
  "equipment": ["E-101"],
  "shots": [
    {"camera": "wide_establishing",  "target": "exchanger_bay"},
    {"camera": "slow_push_in",       "target": "operator_01"},
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

**Colour.** Red is reserved for real alarms. Nothing here is red. The hi-vis
ochre on the operator is the only saturated colour in frame, which is why the
eye finds him.

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

### Instruments and lines

`TI-1014` process outlet, digital · `TI-1013` process inlet, dial ·
`PI-1012` cooling water inlet, dial.
`6"-P-10103` · `6"-P-10104` · `8"-CWS-10121` · `8"-CWR-10122`

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
