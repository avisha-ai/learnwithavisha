"""
world/characters/operator_01/rig.py

OPERATOR_01. The name is not frozen.

He is experienced and this is his workplace, so the rig only does small
movements: a pace that never hurries, a head that pitches up to read an
instrument, a body that turns back for a second look. There is no facial
animation and there is no theatrical acting.

A single SVG cannot hold a gait, so this is a solver rather than a drawing.
poses.json names the parameter sets, engine/actions.py drives them over
time, and this file resolves them into limbs. He is backlit like everything
else and gets his warm left edge from one rim pass over the finished body.
"""

import json
import os

from engine.draw import *

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "character.json")) as _f:
    CHARACTER = json.load(_f)
with open(os.path.join(_HERE, "poses.json")) as _f:
    POSES = json.load(_f)

HIP_Y, KNEE_L, SHIN_L = 0.94, 0.47, 0.47
SHO_Y, UARM_L, FARM_L = 1.42, 0.31, 0.29
HEAD_Y, HEAD_R = 1.615, 0.105


def _quad(p0, p1, w0, w1, colour, opacity=1.0):
    d = p1 - p0
    n = np.array([-d[1], d[0], 0.0])
    ln = np.linalg.norm(n)
    if ln < 1e-9:
        n = np.array([0.0, 1.0, 0.0])
    else:
        n = n / ln
    return Polygon(p0 + n * w0 / 2, p1 + n * w1 / 2,
                   p1 - n * w1 / 2, p0 - n * w0 / 2
                   ).set_stroke(width=0).set_fill(colour, opacity)


def _limb(root, a_deg, length, facing):
    a = math.radians(a_deg)
    return root + np.array([math.sin(a) * facing * length,
                            -math.cos(a) * length, 0.0])


def _torso_poly(hip, lean, facing, scale, inset=0.0):
    """Torso with real shoulders. A slab reads as a box the moment he is
    bigger than a silhouette, which is exactly when the character has to
    start working."""
    pts = [(-0.158, 0.00), (0.158, 0.00), (0.190, 0.335), (0.152, 0.462),
           (0.078, 0.530), (-0.078, 0.530), (-0.152, 0.462), (-0.190, 0.335)]
    a = math.radians(lean) * facing
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for px, py in pts:
        px = (px - inset * (1 if px > 0 else -1)) * facing
        py = py + inset * 0.6
        out.append(np.array([hip[0] + (px * ca - py * sa) * scale,
                             hip[1] + (px * sa + py * ca) * scale, 0.0]))
    return out


def build(x, phase=0.0, facing=1, walking=True, head_pitch=0.0,
                   clipboard=0.0, y=0.0, scale=1.0):
    """OPERATOR_01.

    phase       walk cycle position in radians
    facing      +1 faces right, -1 faces left
    walking     False locks a relaxed stance
    head_pitch  degrees, positive = looking up at an instrument
    clipboard   0 = at his side, 1 = raised to compare against the gauge

    He is backlit like everything else, so the figure is built body-first and
    then given a warm rim along its left edge in one pass. That rim is what
    separates him from the equipment he is standing in front of.
    """
    p = phase
    if not walking:
        th_a, th_b, kf_a, kf_b = -5.0, 8.0, 6.0, 12.0
        bob, lean = 0.0, 3.0
        ar_a, ar_b = 7.0, -6.0
    else:
        th_a = 26.0 * math.sin(p)
        th_b = 26.0 * math.sin(p + math.pi)
        kf_a = 9.0 + 34.0 * max(0.0, math.sin(p + 1.95))
        kf_b = 9.0 + 34.0 * max(0.0, math.sin(p + 1.95 + math.pi))
        bob, lean = 0.022 * math.cos(2 * p), 5.0
        ar_a = -21.0 * math.sin(p)
        ar_b = -21.0 * math.sin(p + math.pi)

    body = VGroup()
    O = np.array([x, y + bob, 0.0])
    hip = O + np.array([0.0, HIP_Y * scale, 0.0])
    lean_r = math.radians(lean) * facing
    sho = hip + np.array([-math.sin(lean_r) * 0.505 * scale,
                          math.cos(lean_r) * 0.505 * scale, 0.0])

    # far leg first, then near leg — depth inside the figure itself
    for th, kf, col, w in ((th_b, kf_b, "#0c0f15", 0.90),
                           (th_a, kf_a, FIG_DARK, 1.0)):
        knee = _limb(hip, th, KNEE_L * scale, facing)
        ankle = _limb(knee, th - kf, SHIN_L * scale, facing)
        body.add(_quad(hip, knee, 0.150 * scale * w, 0.118 * scale * w, col))
        body.add(_quad(knee, ankle, 0.116 * scale * w, 0.088 * scale * w, col))
        boot = ankle + np.array([0.115 * facing * scale, -0.030 * scale, 0])
        body.add(_quad(ankle + np.array([-0.05 * facing * scale, -0.015, 0]),
                       boot, 0.098 * scale * w, 0.070 * scale * w, "#0a0d12"))

    # far arm behind the torso
    def arm(ang, col, near):
        if near and clipboard > 0.02:
            a0 = -20.0 - 44.0 * clipboard
            ef = 32.0 + 44.0 * clipboard
        else:
            a0 = ang
            ef = 16.0 + 13.0 * max(0.0, math.sin(p + 1.2))
        elb = _limb(sho, a0, UARM_L * scale, facing)
        wri = _limb(elb, a0 + ef, FARM_L * scale, facing)
        gg = VGroup()
        gg.add(_quad(sho, elb, 0.122 * scale, 0.100 * scale, col))
        gg.add(_quad(elb, wri, 0.098 * scale, 0.080 * scale, col))
        gg.add(Dot(wri, radius=0.046 * scale, color=SKIN))
        return gg, wri

    far_arm, _ = arm(ar_b, "#0c0f15", False)
    body.add(far_arm)

    # torso and hi-vis vest
    body.add(Polygon(*_torso_poly(hip, lean, facing, scale))
             .set_stroke(width=0).set_fill(FIG_DARK, 1))
    vest = Polygon(*_torso_poly(hip + np.array([0, 0.055 * scale, 0]),
                                lean, facing, scale, inset=0.020))
    body.add(vest.set_stroke(width=0).set_fill(VEST, 1))
    for fy in (0.30, 0.50):
        b0 = hip + (sho - hip) * fy
        b1 = hip + (sho - hip) * (fy + 0.070)
        body.add(_quad(b0, b1, 0.315 * scale, 0.325 * scale, BAND, 0.75))

    near_arm, wri = arm(ar_a, FIG_MID, True)
    body.add(near_arm)
    if clipboard > 0.02:
        body.add(_clipboard(wri, facing, scale, clipboard))

    # neck, head, hard hat — pitched as one piece about the base of the neck
    neck = sho + np.array([-math.sin(lean_r) * 0.045 * scale,
                           math.cos(lean_r) * 0.045 * scale, 0.0])
    hc = neck + np.array([0.052 * facing * scale, 0.145 * scale, 0.0])
    head = VGroup()
    head.add(_quad(neck, hc, 0.125 * scale, 0.105 * scale, SKIN))
    head.add(Dot(hc, radius=HEAD_R * scale, color=SKIN))
    head.add(Dot(hc + np.array([0.088 * facing * scale, -0.022 * scale, 0]),
                 radius=0.030 * scale, color=SKIN))              # nose line
    hat = AnnularSector(inner_radius=0.0, outer_radius=HEAD_R * 1.24 * scale,
                        angle=PI, start_angle=0.0)
    hat.set_stroke(width=0).set_fill(HAT, 1)
    hat.move_to(hc + np.array([0.006 * facing * scale, HEAD_R * 0.60 * scale,
                               0]))
    head.add(hat)
    # peak forward only, plus a short lip behind. Not a bar through the head.
    bb = hc[1] + HEAD_R * 0.30 * scale
    head.add(Polygon(
        np.array([hc[0] + 0.020 * facing * scale, bb + 0.030 * scale, 0]),
        np.array([hc[0] + 0.205 * facing * scale, bb + 0.006 * scale, 0]),
        np.array([hc[0] + 0.205 * facing * scale, bb - 0.030 * scale, 0]),
        np.array([hc[0] + 0.020 * facing * scale, bb - 0.026 * scale, 0]),
    ).set_stroke(width=0).set_fill(HAT, 1))
    head.add(_quad(np.array([hc[0] - 0.020 * facing * scale, bb, 0]),
                   np.array([hc[0] - 0.135 * facing * scale,
                             bb + 0.012 * scale, 0]),
                   0.052 * scale, 0.034 * scale, "#a7aeb8"))
    if abs(head_pitch) > 0.01:
        head.rotate(math.radians(head_pitch) * facing, about_point=neck)
    body.add(head)

    # one rim pass: a warm copy offset toward the sun, sitting behind him
    rim = body.copy()
    rim.set_color(STEEL_RIM)
    rim.set_opacity(0.42)
    rim.shift(np.array([-0.026 * scale, 0.016 * scale, 0.0]))
    return VGroup(rim, body)


def _clipboard(wrist, facing, scale, raised):
    g = VGroup()
    w, h = 0.24 * scale, 0.32 * scale
    cx = wrist[0] + 0.11 * facing * scale
    cy = wrist[1] + 0.10 * scale * raised
    g.add(band_rect(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, "#2f3640"))
    g.add(band_rect(cx - w / 2 + 0.012, cx + w / 2 - 0.012,
                    cy - h / 2 + 0.012, cy + h / 2 - 0.028, "#b9c2ce"))
    g.add(band_rect(cx - w * 0.18, cx + w * 0.18, cy + h / 2 - 0.036,
                    cy + h / 2 - 0.008, "#7d8797"))
    for i in range(5):
        ry = cy + h / 2 - 0.075 - i * 0.045 * scale
        g.add(band_rect(cx - w * 0.34, cx + w * 0.30, ry, ry + 0.010, "#6c7686",
                        0.75))
    return g
