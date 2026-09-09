# LearnWithAvisha — Visual Pilot 001

A 27-second visual proof, not an episode. It answers one question: does this
feel like a story happening inside a living chemical plant?

## Deliverables

| | file |
|---|---|
| A — style frame | `output/visual_pilot_001/frame_a_style.png` |
| B — consistency frame | `output/visual_pilot_001/frame_b_consistency.png` |
| C — sequence | `output/visual_pilot_001/pilot001_v1.mp4` (27.000 s, 1920x1080p60, stereo) |

## Build

```
BIN=../.micromamba/root/envs/manim/bin
$BIN/python -m manim -s -qh frame_a.py FrameA          # style frame
$BIN/python -m manim -s -qh frame_b.py FrameB          # consistency frame
$BIN/python -m manim -qh    pilot001.py Pilot001       # sequence, 1620 frames
$BIN/python plant_sound.py ../output/visual_pilot_001/plant_bed.wav
./assemble.sh                                          # grade, pad, mux
```

`grade.sh` runs the finishing pass — bloom, vignette, grain — on a still or a
movie. Manim output is never delivered ungraded; the grain is what stops flat
vector fills reading as clipart.

## The world, as frozen by this pilot

Anything below can become canon. Nothing below should be changed casually,
because every later shot inherits it.

**Units and ground.** 1 world unit = 1 metre. The walkway grating top surface
is y = 0 and the operator walks on it. The distant plant stands on
`HORIZON_Y = 0.62`.

**Light.** One low morning sun, behind and left of the bay, sitting on the
horizon at roughly (-2.6, 1.2). Everything is contre-jour: cool steel bodies,
warm rims on top and left edges, the sky brighter than the plant. If a future
asset lights from the right, the world breaks.

**Depth.** Four layers — FAR, MID, NEAR, FORE. Distance is expressed only as
loss of contrast, loss of line weight and loss of detail. The haze sheets
between layers are tinted to the sky at each height; haze a warm dawn with a
cool grey and every silhouette turns blue and jumps forward.

**Colour.** Red is reserved. Nothing in this world is red unless it is a real
alarm, and in Pilot 001 nothing is. Hi-vis ochre on the operator is the only
saturated colour in frame, which is why the eye finds him.

**Perspective.** The equipment is drawn in near-elevation, which keeps E-101
canonical and readable. The FLOOR carries the depth, converging on a
vanishing point at (-2.0, 2.05). That split is deliberate: it buys a place you
could walk into without turning the hero asset into a projection problem.

### Asset 001 — E-101

A 1-2 shell-and-tube exchanger. Hot process on the tube side, cooling water on
the shell side. Geometry is fixed in `plant_world.E101` and imported by every
shot.

- Both tube nozzles land on the channel head (left). That is what makes it a
  two-tube-pass machine.
- Shell inlet at the far (right) end, shell outlet at the near (left) end, so
  the shell stream runs counter-current to the first tube pass.
- Shell inlet bottom, outlet top, so the shell runs liquid-full.
- Saddles under the shell, on a plinth, on the deck. Girth flanges with bolt
  rings at both tubesheet joints. Lifting lugs. A vent at the high point.

**Why the process is in the tubes and not the shell.** This is the choice the
whole story rests on, so it is deliberate rather than arbitrary. Cooling water
is often the tube-side stream precisely because tubes are the side you can
clean, but here the fouling stream is the process, not the water. Putting the
dirty stream where it can be rodded out is the same reasoning applied to a
different fluid. It also puts the drift on an instrument an operator actually
walks past: TI-1014 reads the process outlet, so as the tube-side film builds,
duty falls and that number climbs. Move the process to the shell side and the
story loses the instrument that carries it.

### Instruments

| tag | service | type |
|---|---|---|
| TI-1014 | E-101 process outlet | digital indicator on a thermowell — the hero |
| TI-1013 | E-101 process inlet | local dial |
| PI-1012 | cooling water inlet | local dial, needle stable |

### Lines

`6"-P-10103` process in · `6"-P-10104` process out ·
`8"-CWS-10121` cooling water supply · `8"-CWR-10122` cooling water return

### OPERATOR_01

Name not frozen. Rigged for small movements only: a walk cycle, a head that
pitches to read an instrument, a body that turns back. No facial animation. He
is backlit like everything else and carries a warm rim down his left side,
which is what separates him from the equipment he stands in front of.

## The three shots

| | time | what happens |
|---|---|---|
| 1 | 0.0 – 10.5 | Ordinary morning. Camera drifts 2%. He walks his route. |
| 2 | 10.5 – 19.0 | Patient push in. He glances at TI-1014 in passing, takes two more paces, stops, turns, looks again. |
| 3 | 19.0 – 27.0 | Cut to the reading. 87. The log sheet comes up: 87, 85, 83. It goes down. Hold. Fade. |

No fouling, no cutaway, no equation, no narration, no alarm, no red light. The
film ends on an unanswered observation.

## Sound

`plant_sound.py` synthesises the bed — nothing is sampled. Three rules:

1. The machine bed never changes. Same drone, same blade-pass, same level,
   start to finish. If the plant sounded wrong the story would be over.
2. Footsteps are locked to the animated gait and to his distance from camera,
   so they swell as he approaches and stop when he stops. The silence where the
   next footstep should have been is the loudest thing in the film.
3. At Shot 3 the world narrows — the top end drops about 8 dB and the stereo
   image closes — while the machine stays exactly where it was.

No music. No riser. No swell on the reveal.

## What this pilot does NOT establish

Deliberately out of scope until the test is approved: any second bay, any
interior, night or overcast lighting, a second character, equipment other than
E-101, and any teaching content whatsoever.
