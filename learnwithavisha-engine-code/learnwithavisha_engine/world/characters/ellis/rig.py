"""
world/characters/ellis/rig.py

ELLIS — The One Who Knows the Pattern. Early 40s.

Reference: world/characters/ellis_reference.png

What has to survive at distance:

    the stillness     he stands more upright than anyone else and his walk
                      barely swings. His pause is an event.
    the open jacket   olive, with a dark knit panel showing straight down the
                      middle — a vertical stripe no one else has
    the gloves        dark utility gloves, and a chalk mark on the right
                      knuckle that he has clearly not noticed

He looks through things rather than at them, so his head pitches less than
the others when he inspects: he does not lean in.
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


def _head(j, pitch):
    """Clean and unremarkable on purpose. He is the one you do not look at
    until he stops moving, so nothing on his head competes for attention."""
    R, f, hc = j["head_r"], j["facing"], j["head"]
    g = VGroup()
    g.add(Dot(hc + np.array([-0.54 * R * f, 0.16 * R, 0]),
              radius=0.76 * R, color=HAIR_BROWN))
    g.add(F.head_group(j, SKIN, neck_w=0.74))
    g.add(F.hair_cap(j, HAIR_BROWN, outer=1.02, flat=0.34, back=-0.05))
    g.add(F.quad(hc + np.array([-0.50 * R * f, 0.52 * R, 0]),
                 hc + np.array([-1.02 * R * f, 0.14 * R, 0]),
                 0.38 * R, 0.26 * R, HAIR_BROWN))              # swept back

    stub = Ellipse(width=0.96 * R, height=0.50 * R)
    stub.set_stroke(width=0).set_fill(mix(SKIN, "#241a20", 0.55), 0.26)
    stub.move_to(hc + np.array([0.20 * R * f, -0.58 * R, 0]))
    g.add(stub)
    g.add(F.face(j, SKIN, brow=HAIR_BROWN, nose=0.23, eye_x=0.38,
                 eye_y=0.16))
    return F.pitch_head(g, j, pitch)


def _pocket(j, s, frac, side, w=0.076, h=0.058):
    c = j["hip"] + (j["shoulder"] - j["hip"]) * frac
    c = c + np.array([side * 0.132 * j["facing"] * s, 0.0, 0.0])
    g = VGroup(Rectangle(width=w * s, height=h * s).set_stroke(width=0)
               .set_fill(OLIVE_DARK, 0.85).move_to(c))
    g.add(Rectangle(width=w * s, height=0.020 * s).set_stroke(width=0)
          .set_fill(OLIVE_LIGHT, 0.60)
          .move_to(c + np.array([0, h * 0.5 * s, 0])))
    return g


def build(x, phase=0.0, facing=1, walking=True, head_pitch=0.0,
          clipboard=0.0, y=0.0, scale=1.0):
    pose = POSES["walking"] if walking else POSES["neutral"]
    j = F.solve(x, y=y, phase=phase, facing=facing, walking=walking,
                height=HEIGHT * scale, stance=pose.get("stance", {}))
    s, f = j["scale"], j["facing"]
    body = VGroup()

    body.add(F.legs(j, s, "#3a3f2c", "#23271b", "#0d0f12", w=LIMB))

    far, _, _ = F.arm(j, "b", j["arm_angle_b"], j["arm_flex_b"], s,
                      OLIVE_DARK, w0=0.118 * LIMB, w1=0.096 * LIMB,
                      hand=GLOVE_DARK, hand_r=0.048)
    body.add(far)

    # dark knit first, then the olive jacket left open over it
    body.add(Polygon(*F.torso_poly(j, s, build=BUILD))
             .set_stroke(width=0).set_fill(OLIVE, 1))
    # The jacket hangs open. This dark panel straight down the middle is the
    # only vertical stripe in the cast, and it is how he reads at distance.
    body.add(F.quad(j["hip"] + (j["shoulder"] - j["hip"]) * 0.02,
                    j["shoulder"] + np.array([0.0, 0.034 * s, 0]),
                    0.118 * BUILD * s, 0.098 * BUILD * s, KNIT_CHARCOAL))
    for side in (-1, 1):
        edge = j["hip"] + (j["shoulder"] - j["hip"]) * 0.50
        body.add(F.quad(edge + np.array([side * 0.062 * f * s, -0.24 * s, 0]),
                        edge + np.array([side * 0.062 * f * s, 0.26 * s, 0]),
                        0.020 * s, 0.020 * s, OLIVE_LIGHT).set_opacity(0.45))
    body.add(F.band(j, s, 0.02, 0.055, OLIVE_DARK, build=BUILD, opacity=0.9))
    for frac, side in ((0.66, -1), (0.66, 1), (0.26, -1), (0.26, 1)):
        body.add(_pocket(j, s, frac, side))
    collar = j["shoulder"] + np.array([0.0, 0.018 * s, 0])
    body.add(F.quad(collar + np.array([-0.092 * f * s, 0, 0]),
                    collar + np.array([0.092 * f * s, 0.028 * s, 0]),
                    0.072 * s, 0.050 * s, OLIVE_LIGHT))

    ang, flex = j["arm_angle_a"], j["arm_flex_a"]
    if clipboard > 0.02:
        ang, flex = -20.0 - 44.0 * clipboard, 32.0 + 44.0 * clipboard
    elbow = F.limb_end(j["shoulder"], ang, F.UARM_L * s, f)
    wrist = F.limb_end(elbow, ang + flex, F.FARM_L * s, f)
    body.add(F.quad(j["shoulder"], elbow, 0.118 * LIMB * s, 0.098 * LIMB * s,
                    OLIVE))
    body.add(F.quad(elbow, wrist, 0.098 * LIMB * s, 0.080 * LIMB * s, OLIVE))
    body.add(F.quad(elbow + (wrist - elbow) * 0.78, wrist,
                    0.092 * LIMB * s, 0.084 * LIMB * s, OLIVE_LIGHT)
             .set_opacity(0.55))                                  # turned cuff
    body.add(Dot(wrist, radius=0.050 * s, color=GLOVE_DARK))
    # the chalk mark, on the right knuckle. He has not noticed it.
    body.add(Dot(wrist + np.array([0.034 * f * s, 0.014 * s, 0]),
                 radius=0.014 * s, color=CHALK).set_opacity(0.9))

    body.add(_head(j, head_pitch))
    return VGroup(F.rim_pass(body, s), body)
