"""
engine/figure.py — the shared human solver.

Characters differ in what they wear and how they carry themselves, not in
how a leg works. So the mechanics live here once, and each character's
rig.py only decides what is drawn over the skeleton this file solves.

That split is the reason three people can share one walk and still be
recognisable at forty pixels tall: the SILHOUETTE work is per character
(Wade's bulk and beard, Lyra's bun, Ellis's upright stillness), while the
gait, the lean, the head pitch and the turn are common.

Everything here is backlit like the rest of the world. rim_pass() is the
one place that is decided, so no character can light itself differently.
"""

import math

from engine.draw import *

# Reference skeleton, in metres, for a 1.78 m figure. A character scales
# these by its own height and widens or narrows them by its build.
REF_HEIGHT = 1.78
HIP_Y, KNEE_L, SHIN_L = 0.94, 0.47, 0.47
SHO_RISE, UARM_L, FARM_L = 0.505, 0.31, 0.29
NECK_RISE, HEAD_RISE, HEAD_R = 0.045, 0.145, 0.105


def limb_end(root, a_deg, length, facing):
    a = math.radians(a_deg)
    return root + np.array([math.sin(a) * facing * length,
                            -math.cos(a) * length, 0.0])


def quad(p0, p1, w0, w1, colour, opacity=1.0):
    d = p1 - p0
    n = np.array([-d[1], d[0], 0.0])
    ln = np.linalg.norm(n)
    n = np.array([0.0, 1.0, 0.0]) if ln < 1e-9 else n / ln
    return Polygon(p0 + n * w0 / 2, p1 + n * w1 / 2,
                   p1 - n * w1 / 2, p0 - n * w0 / 2
                   ).set_stroke(width=0).set_fill(colour, opacity)


def solve(x, y=0.0, phase=0.0, facing=1, walking=True, height=REF_HEIGHT,
          stance=None):
    """Joint positions for one figure at one instant.

    Returns a dict the rigs read. `a` is the near side of the body, `b` the
    far side — drawing order matters, so the naming is not cosmetic.
    """
    s = height / REF_HEIGHT
    p = phase
    st = stance or {}
    if not walking:
        th_a, th_b = st.get("thigh_a", -5.0), st.get("thigh_b", 8.0)
        kf_a, kf_b = st.get("knee_a", 6.0), st.get("knee_b", 12.0)
        ar_a, ar_b = st.get("arm_a", 7.0), st.get("arm_b", -6.0)
        bob, lean = 0.0, st.get("lean", 3.0)
    else:
        sw = st.get("swing", 26.0)
        th_a, th_b = sw * math.sin(p), sw * math.sin(p + math.pi)
        kf_a = 9.0 + 34.0 * max(0.0, math.sin(p + 1.95))
        kf_b = 9.0 + 34.0 * max(0.0, math.sin(p + 1.95 + math.pi))
        ar_a = -st.get("arm_swing", 21.0) * math.sin(p)
        ar_b = -st.get("arm_swing", 21.0) * math.sin(p + math.pi)
        bob, lean = 0.022 * math.cos(2 * p) * s, st.get("lean", 5.0)

    O = np.array([x, y + bob, 0.0])
    hip = O + np.array([0.0, HIP_Y * s, 0.0])
    lean_r = math.radians(lean) * facing
    sho = hip + np.array([-math.sin(lean_r) * SHO_RISE * s,
                          math.cos(lean_r) * SHO_RISE * s, 0.0])
    neck = sho + np.array([-math.sin(lean_r) * NECK_RISE * s,
                           math.cos(lean_r) * NECK_RISE * s, 0.0])
    head = neck + np.array([0.052 * facing * s, HEAD_RISE * s, 0.0])

    j = {"scale": s, "facing": facing, "hip": hip, "shoulder": sho,
         "neck": neck, "head": head, "head_r": HEAD_R * s,
         "lean": lean, "phase": p, "walking": walking}
    for side, th, kf, ar in (("a", th_a, kf_a, ar_a), ("b", th_b, kf_b, ar_b)):
        knee = limb_end(hip, th, KNEE_L * s, facing)
        ankle = limb_end(knee, th - kf, SHIN_L * s, facing)
        elb_a = ar
        flex = 16.0 + 13.0 * max(0.0, math.sin(p + 1.2))
        elbow = limb_end(sho, elb_a, UARM_L * s, facing)
        wrist = limb_end(elbow, elb_a + flex, FARM_L * s, facing)
        j["knee_" + side], j["ankle_" + side] = knee, ankle
        j["elbow_" + side], j["wrist_" + side] = elbow, wrist
        j["arm_angle_" + side], j["arm_flex_" + side] = elb_a, flex
    return j


def arm(j, side, angle, flex, scale, colour, w0=0.122, w1=0.098,
        hand=None, hand_r=0.046):
    """Redraw one arm at an explicit angle — for a raised tablet or a hand
    resting on a rail, where the gait's own swing is not what is wanted."""
    elbow = limb_end(j["shoulder"], angle, UARM_L * scale, j["facing"])
    wrist = limb_end(elbow, angle + flex, FARM_L * scale, j["facing"])
    g = VGroup(quad(j["shoulder"], elbow, w0 * scale, w1 * scale, colour),
               quad(elbow, wrist, w1 * scale, (w1 - 0.018) * scale, colour))
    if hand is not None:
        g.add(Dot(wrist, radius=hand_r * scale, color=hand))
    return g, elbow, wrist


def legs(j, scale, near, far, boot, w=1.0):
    """Far leg first, then near. Depth inside the figure itself."""
    g = VGroup()
    for side, col in (("b", far), ("a", near)):
        k = 0.90 if side == "b" else 1.0
        hip, knee, ankle = j["hip"], j["knee_" + side], j["ankle_" + side]
        g.add(quad(hip, knee, 0.150 * scale * k * w, 0.118 * scale * k * w, col))
        g.add(quad(knee, ankle, 0.116 * scale * k * w, 0.088 * scale * k * w,
                   col))
        toe = ankle + np.array([0.115 * j["facing"] * scale, -0.030 * scale, 0])
        g.add(quad(ankle + np.array([-0.05 * j["facing"] * scale, -0.015, 0]),
                   toe, 0.098 * scale * k, 0.070 * scale * k, boot))
    return g


def torso_poly(j, scale, build=1.0, inset=0.0, lift=0.0):
    """Torso with real shoulders. A slab reads as a box the moment a figure
    is bigger than a silhouette, which is when a character starts working."""
    pts = [(-0.158, 0.00), (0.158, 0.00), (0.190, 0.335), (0.152, 0.462),
           (0.078, 0.530), (-0.078, 0.530), (-0.152, 0.462), (-0.190, 0.335)]
    a = math.radians(j["lean"]) * j["facing"]
    ca, sa = math.cos(a), math.sin(a)
    hip = j["hip"] + np.array([0.0, lift * scale, 0.0])
    out = []
    for px, py in pts:
        px = (px * build - inset * (1 if px > 0 else -1)) * j["facing"]
        py = py + inset * 0.6
        out.append(np.array([hip[0] + (px * ca - py * sa) * scale,
                             hip[1] + (px * sa + py * ca) * scale, 0.0]))
    return out


def band(j, scale, frac, thick, colour, build=1.0, opacity=0.78):
    """A horizontal band across the torso — reflective tape, a belt, a hem."""
    b0 = j["hip"] + (j["shoulder"] - j["hip"]) * frac
    b1 = j["hip"] + (j["shoulder"] - j["hip"]) * (frac + thick)
    return quad(b0, b1, 0.315 * build * scale, 0.325 * build * scale,
                colour, opacity)


def head_group(j, skin, neck_w=0.78, ear=True):
    """Bare head, neck and ear.

    Everything a character draws on a head — hair, beard, glasses — is sized
    in multiples of head_r, never in body scale. Head parts tuned against
    body scale end up several times too large, which is the difference
    between a face and a snowman.
    """
    R, f, hc = j["head_r"], j["facing"], j["head"]
    g = VGroup()
    g.add(quad(j["neck"], hc, neck_w * R, (neck_w - 0.12) * R, skin))
    g.add(Dot(hc, radius=R, color=skin))
    if ear:
        g.add(Dot(hc + np.array([-0.34 * R * f, -0.06 * R, 0]),
                  radius=0.26 * R, color=mix(skin, "#2a1d18", 0.30)))
    return g


def face(j, skin, eye="#241a14", brow=None, nose=0.22, eye_x=0.44,
         eye_y=0.20):
    """One eye and a brow. Static — this world does no facial animation —
    but without them a head reads as a mannequin at close range."""
    R, f, hc = j["head_r"], j["facing"], j["head"]
    g = VGroup()
    g.add(Dot(hc + np.array([0.90 * R * f, -0.12 * R, 0]),
              radius=nose * R, color=skin))
    g.add(Dot(hc + np.array([eye_x * R * f, eye_y * R, 0]),
              radius=0.095 * R, color=eye))
    if brow:
        a = hc + np.array([(eye_x - 0.20) * R * f, (eye_y + 0.28) * R, 0])
        b = hc + np.array([(eye_x + 0.24) * R * f, (eye_y + 0.34) * R, 0])
        g.add(quad(a, b, 0.13 * R, 0.10 * R, brow))
    return g


def hair_cap(j, colour, outer=1.06, flat=0.22, back=0.0):
    """A cap over the top of the skull. It must not reach below the eyes."""
    R, f, hc = j["head_r"], j["facing"], j["head"]
    cap = AnnularSector(inner_radius=0.0, outer_radius=outer * R,
                        angle=PI, start_angle=0.0)
    cap.set_stroke(width=0).set_fill(colour, 1)
    cap.move_to(hc + np.array([back * R * f, flat * R, 0]))
    return cap


def pitch_head(head, j, degrees):
    if abs(degrees) > 0.01:
        head.rotate(math.radians(degrees) * j["facing"], about_point=j["neck"])
    return head


def rim_pass(body, scale, opacity=0.30, dx=-0.014, dy=0.010):
    """One warm copy offset toward the sun, sitting behind the figure.

    This is the only place a character's rim light is decided, which is what
    keeps three people lit by the same morning.
    """
    rim = body.copy()
    rim.set_color(STEEL_RIM)
    rim.set_opacity(opacity)
    rim.shift(np.array([dx * scale, dy * scale, 0.0]))
    return rim
