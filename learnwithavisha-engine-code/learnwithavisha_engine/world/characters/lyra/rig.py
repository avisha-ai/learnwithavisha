"""
world/characters/lyra/rig.py

LYRA — The One Who Knows the Theory. Late 20s.

Reference: world/characters/lyra_reference.png

What has to survive at distance:

    the bun           a dark mass ABOVE the skull line — no one else has a
                      silhouette that goes up
    the hi-vis        the brightest garment in the world, with two reflective
                      bands across it
    the tablet glow   a cool light on her forearm and under her jaw

The tablet is the world's ONE sanctioned second light source. It is a device
she actually carries, so it is allowed to cast; nothing else in this world
lights from anywhere but the morning sun.

She leans forward slightly even when standing still — quick and precise,
always two steps ahead of everyone except the plant.
"""

import json
import os

from engine.draw import *
import engine.figure as F

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "character.json")) as _f:
    CHARACTER = json.load(_f)
with open(os.path.join(_HERE, "poses.json")) as _f:
    POSES = json.load(_f)

HEIGHT = CHARACTER["height_m"]
BUILD = CHARACTER["build"]["torso"]
LIMB = CHARACTER["build"]["limb"]


def _head(j, pitch, glow):
    """The bun is the identifying shape, so it sits clear ABOVE the skull.
    The fringe covers the top of the head only — a helmet of hair loses the
    face, and the glasses then have nothing to sit on."""
    R, f, hc = j["head_r"], j["facing"], j["head"]
    g = VGroup()
    g.add(Dot(hc + np.array([-0.52 * R * f, 0.12 * R, 0]),
              radius=0.80 * R, color=HAIR_DARK))               # back of head
    g.add(F.head_group(j, SKIN, neck_w=0.70))
    g.add(F.hair_cap(j, HAIR_DARK, outer=1.02, flat=0.38, back=-0.04))

    bun = hc + np.array([-0.44 * R * f, 1.16 * R, 0])
    g.add(Dot(bun, radius=0.64 * R, color=HAIR_DARK))
    g.add(Dot(bun + np.array([0.22 * R * f, 0.22 * R, 0]),
              radius=0.34 * R, color=mix(HAIR_DARK, STEEL_RIM, 0.22)))
    for dx, dy, ln in ((-0.90, 0.06, 0.78), (-0.66, -0.26, 0.52)):
        a = hc + np.array([dx * R * f, dy * R, 0])
        g.add(F.quad(a, a + np.array([-0.16 * R * f, -ln * R, 0]),
                     0.20 * R, 0.11 * R, HAIR_DARK))           # loose strand

    g.add(F.face(j, SKIN, brow=HAIR_DARK, nose=0.20, eye_x=0.36,
                 eye_y=0.15))

    lens = hc + np.array([0.36 * R * f, 0.15 * R, 0])
    ring = Circle(radius=0.30 * R).set_fill("#0d1218", 0.16)
    ring.set_stroke("#c2ccd8", 1.35).move_to(lens)
    g.add(ring)
    g.add(F.quad(lens + np.array([-0.30 * R * f, 0.03 * R, 0]),
                 hc + np.array([-0.58 * R * f, 0.20 * R, 0]),
                 0.055 * R, 0.055 * R, "#aeb9c6"))             # temple arm

    if glow > 0.01:
        for w, h, o in ((1.60, 0.44, 0.040), (1.10, 0.32, 0.052),
                        (0.68, 0.22, 0.062)):
            d = Ellipse(width=w * R, height=h * R)
            d.set_stroke(width=0).set_fill(TABLET_GLOW, o * glow)
            d.move_to(hc + np.array([0.34 * R * f, -0.86 * R, 0]))
            g.add(d)
    return F.pitch_head(g, j, pitch)


def _tablet(j, wrist, elbow, glow):
    """Ruggedized tablet strapped to the left forearm. It sits ALONG the
    forearm, which is why her hands stay free."""
    s, f = j["scale"], j["facing"]
    mid = (wrist + elbow) / 2.0
    g = VGroup()
    g.add(F.quad(elbow, wrist, 0.130 * s, 0.118 * s, TABLET_BODY))
    g.add(F.quad(elbow + (wrist - elbow) * 0.16,
                 elbow + (wrist - elbow) * 0.88,
                 0.098 * s, 0.090 * s, "#0b1a1f"))
    face = F.quad(elbow + (wrist - elbow) * 0.20,
                  elbow + (wrist - elbow) * 0.84,
                  0.082 * s, 0.076 * s, TABLET_GLOW)
    face.set_opacity(0.55 + 0.35 * glow)
    g.add(face)
    for k in (0.34, 0.50, 0.66):
        g.add(F.quad(elbow + (wrist - elbow) * k,
                     elbow + (wrist - elbow) * (k + 0.05),
                     0.062 * s, 0.062 * s, "#0e2a2c").set_opacity(0.5))
    if glow > 0.01:
        for r, o in ((0.108, 0.055), (0.070, 0.075)):
            d = Ellipse(width=r * 2.6 * s, height=r * 1.5 * s)
            d.set_stroke(width=0).set_fill(TABLET_GLOW, o * glow)
            d.move_to(mid)
            g.add(d)
    return g


def build(x, phase=0.0, facing=1, walking=True, head_pitch=0.0,
          clipboard=0.0, y=0.0, scale=1.0, glow=1.0):
    pose = POSES["walking"] if walking else POSES["neutral"]
    j = F.solve(x, y=y, phase=phase, facing=facing, walking=walking,
                height=HEIGHT * scale, stance=pose.get("stance", {}))
    s, f = j["scale"], j["facing"]
    body = VGroup()

    body.add(F.legs(j, s, "#2b303a", "#1b1f26", "#0a0d12", w=LIMB))

    far, _, _ = F.arm(j, "b", j["arm_angle_b"], j["arm_flex_b"], s,
                      VEST_DARK, w0=0.116 * LIMB, w1=0.094 * LIMB)
    body.add(far)

    # hi-vis field jacket over a dark knit
    body.add(Polygon(*F.torso_poly(j, s, build=BUILD))
             .set_stroke(width=0).set_fill(KNIT_CHARCOAL, 1))
    body.add(Polygon(*F.torso_poly(j, s, build=BUILD, inset=0.014))
             .set_stroke(width=0).set_fill(VEST, 1))
    body.add(F.quad(j["hip"] + (j["shoulder"] - j["hip"]) * 0.52,
                    j["neck"], 0.074 * BUILD * s, 0.062 * BUILD * s,
                    KNIT_CHARCOAL))                        # open collar gap
    for fr in (0.30, 0.52):
        body.add(F.band(j, s, fr, 0.062, BAND, build=BUILD, opacity=0.80))
    collar = j["shoulder"] + np.array([0.0, 0.020 * s, 0])
    body.add(F.quad(collar + np.array([-0.058 * f * s, 0, 0]),
                    collar + np.array([0.058 * f * s, 0.020 * s, 0]),
                    0.046 * s, 0.034 * s, "#525a68"))

    # near arm, and the tablet strapped along its forearm
    ang, flex = j["arm_angle_a"], j["arm_flex_a"]
    if clipboard > 0.02:
        ang, flex = -34.0 - 30.0 * clipboard, 46.0 + 34.0 * clipboard
    elbow = F.limb_end(j["shoulder"], ang, F.UARM_L * s, f)
    wrist = F.limb_end(elbow, ang + flex, F.FARM_L * s, f)
    body.add(F.quad(j["shoulder"], elbow, 0.116 * LIMB * s, 0.096 * LIMB * s,
                    VEST))
    body.add(F.quad(elbow, wrist, 0.096 * LIMB * s, 0.078 * LIMB * s, VEST))
    body.add(F.quad(elbow + (wrist - elbow) * 0.72, wrist,
                    0.086 * LIMB * s, 0.078 * LIMB * s, BAND).set_opacity(0.7))
    body.add(Dot(wrist, radius=0.044 * s, color=SKIN))
    body.add(_tablet(j, wrist, elbow, glow))

    body.add(_head(j, head_pitch, glow))
    return VGroup(F.rim_pass(body, s), body)
