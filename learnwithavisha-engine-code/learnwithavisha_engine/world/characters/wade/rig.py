"""
world/characters/wade/rig.py

WADE — The One Who Knows the Plant by Feel. Late 50s.

Reference: world/characters/wade_reference.png

Translated, not copied. The reference is a rendered three-dimensional
character; this world is flat, banded and backlit, so what carries across is
IDENTITY, not surface. Four things have to survive at forty pixels tall:

    the bulk          he is the widest silhouette in the world
    the bib           navy coveralls, straps and brass buckles on the shoulders
    the beard         a silver mass that breaks the head's outline
    the brass gauge   on its leather lanyard, dead centre of his chest

Everything else is allowed to disappear at distance. He moves deliberately
and never rushes, so his walk swings less than anyone else's and his stance
is planted wide.
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
    """Skull, then the beard on the jaw, then a cap of grey.

    Everything is in multiples of head_r. The beard is the shape that
    identifies him, so it is broad — but it starts BELOW the nose, or he
    reads as a snowman rather than as a man with a beard.
    """
    R, f, hc = j["head_r"], j["facing"], j["head"]
    g = VGroup()
    g.add(Dot(hc + np.array([-0.60 * R * f, 0.14 * R, 0]),
              radius=0.74 * R, color=HAIR_GREY))               # back of head
    g.add(F.head_group(j, SKIN, neck_w=0.92))
    g.add(F.hair_cap(j, HAIR_GREY, outer=1.05, flat=0.30, back=-0.06))
    g.add(F.quad(hc + np.array([-0.55 * R * f, 0.44 * R, 0]),
                 hc + np.array([-1.06 * R * f, 0.02 * R, 0]),
                 0.44 * R, 0.30 * R, HAIR_GREY))               # swept back

    beard = Ellipse(width=1.16 * R, height=1.04 * R)
    beard.set_stroke(width=0).set_fill(BEARD_SILVER, 1)
    beard.rotate(-0.12 * f).move_to(hc + np.array([0.12 * R * f,
                                                   -0.80 * R, 0]))
    g.add(beard)
    g.add(F.quad(hc + np.array([-0.30 * R * f, -0.44 * R, 0]),
                 hc + np.array([0.34 * R * f, -0.50 * R, 0]),
                 0.56 * R, 0.44 * R, BEARD_SILVER))            # jaw line
    g.add(F.face(j, SKIN, brow=HAIR_GREY, nose=0.26, eye_x=0.40,
                 eye_y=0.16))
    tache = Ellipse(width=0.62 * R, height=0.26 * R)
    tache.set_stroke(width=0).set_fill(BEARD_SILVER, 1)
    tache.rotate(-0.10 * f).move_to(hc + np.array([0.44 * R * f,
                                                   -0.30 * R, 0]))
    g.add(tache)                                               # moustache
    return F.pitch_head(g, j, pitch)


def build(x, phase=0.0, facing=1, walking=True, head_pitch=0.0,
          clipboard=0.0, y=0.0, scale=1.0):
    pose = POSES["walking"] if walking else POSES["neutral"]
    j = F.solve(x, y=y, phase=phase, facing=facing, walking=walking,
                height=HEIGHT * scale, stance=pose.get("stance", {}))
    s, f = j["scale"], j["facing"]
    body = VGroup()

    body.add(F.legs(j, s, COVERALL_NAVY, COVERALL_NAVY_DARK, "#0a0d12",
                    w=LIMB))

    # far arm, behind the bib
    far, _, _ = F.arm(j, "b", j["arm_angle_b"], j["arm_flex_b"], s,
                      COVERALL_NAVY_DARK, w0=0.128 * LIMB, w1=0.104 * LIMB)
    body.add(far)

    # coveralls: torso, then the bib panel, then the straps over it
    body.add(Polygon(*F.torso_poly(j, s, build=BUILD))
             .set_stroke(width=0).set_fill(COVERALL_NAVY, 1))
    body.add(Polygon(*F.torso_poly(j, s, build=BUILD * 0.92, inset=0.030,
                                   lift=0.040))
             .set_stroke(width=0).set_fill(HENLEY_DARK, 1))       # undershirt
    bib = Polygon(*F.torso_poly(j, s, build=BUILD * 0.86, inset=0.050,
                                lift=-0.020))
    body.add(bib.set_stroke(width=0).set_fill(COVERALL_NAVY, 1))
    body.add(F.band(j, s, 0.44, 0.030, mix(COVERALL_NAVY, "#000000", 0.35),
                    build=BUILD * 0.84, opacity=0.85))            # bib seam
    for side in (-1, 1):
        a = j["hip"] + (j["shoulder"] - j["hip"]) * 0.62
        b = j["shoulder"] + np.array([0.052 * side * f * s, 0.012 * s, 0])
        body.add(F.quad(a + np.array([0.070 * side * f * s, 0, 0]), b,
                        0.052 * s, 0.048 * s, COVERALL_NAVY_DARK))
        body.add(Dot(a + np.array([0.070 * side * f * s, 0.012 * s, 0]),
                     radius=0.019 * s, color=BRASS))              # buckle

    # near arm — coveralls to the elbow, rolled light sleeve below it
    ang, flex = j["arm_angle_a"], j["arm_flex_a"]
    if clipboard > 0.02:
        ang, flex = -20.0 - 44.0 * clipboard, 32.0 + 44.0 * clipboard
    elbow = F.limb_end(j["shoulder"], ang, F.UARM_L * s, f)
    wrist = F.limb_end(elbow, ang + flex, F.FARM_L * s, f)
    body.add(F.quad(j["shoulder"], elbow, 0.128 * LIMB * s, 0.106 * LIMB * s,
                    COVERALL_NAVY))
    body.add(F.quad(elbow, wrist, 0.106 * LIMB * s, 0.086 * LIMB * s,
                    SLEEVE_BLUE))
    body.add(Dot(wrist, radius=0.050 * s, color=SKIN))

    # the lanyard, and the brass pocket gauge it carries
    chest = j["hip"] + (j["shoulder"] - j["hip"]) * 0.74
    fob = chest + np.array([0.020 * f * s, -0.075 * s, 0])
    for side in (-1, 1):
        body.add(F.quad(j["neck"] + np.array([0.030 * side * f * s, 0, 0]),
                        fob, 0.014 * s, 0.011 * s, LEATHER))
    body.add(Rectangle(width=0.062 * s, height=0.078 * s)
             .set_stroke(width=0).set_fill(LEATHER, 1).move_to(fob))
    gx = chest + np.array([0.148 * f * s, 0.028 * s, 0])
    body.add(Dot(gx, radius=0.060 * s, color=BRASS))
    body.add(Dot(gx, radius=0.044 * s, color=GAUGE_FACE))
    body.add(F.quad(gx, gx + np.array([-0.020 * f * s, -0.028 * s, 0]),
                    0.012 * s, 0.008 * s, "#20252e"))             # needle

    body.add(_head(j, head_pitch))
    return VGroup(F.rim_pass(body, s), body)
