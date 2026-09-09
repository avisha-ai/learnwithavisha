"""
engine/draw.py — the shared drawing kit.

Every asset in world/ is built from these primitives, and every one of them
shades from world/lighting.json. That is the mechanism behind the rule that
matters most here: there is exactly ONE light in this world, and an asset
cannot accidentally light itself from somewhere else because it never gets
to choose.

Palette names are re-exported as module globals so an asset file reads as a
drawing rather than as dictionary lookups.
"""

import json
import math
import os

from manim import *

_HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.normpath(os.path.join(_HERE, "..", "world"))

with open(os.path.join(WORLD, "lighting.json")) as _f:
    LIGHTING = json.load(_f)

_P = LIGHTING["palette"]
for _k, _v in _P.items():
    globals()[_k.upper()] = _v

M = LIGHTING["units"]["world_unit_metres"]
HORIZON_Y = LIGHTING["units"]["horizon_y"]
SUN_POS = tuple(LIGHTING["sun"]["position"])
_SH = LIGHTING["shading"]

def _c(x):
    return ManimColor(x)


def mix(a, b, t):
    return interpolate_color(_c(a), _c(b), max(0.0, min(1.0, t)))


# ── shading profiles — one light direction, applied everywhere ───


def _round_h(v):
    """Tone across a HORIZONTAL cylinder. v = 0 bottom, 1 top."""
    c = _SH["horizontal_cylinder"]
    key = math.exp(-((v - c["peak_v"]) / c["spread"]) ** 2)
    bounce = c["bounce"] * math.exp(-((v - c["bounce_v"]) / 0.13) ** 2)
    return c["floor"] + c["gain"] * key + bounce


def _round_v(u):
    """Tone across a VERTICAL cylinder. u = 0 left, 1 right."""
    c = _SH["vertical_cylinder"]
    key = math.exp(-((u - c["peak_u"]) / c["spread"]) ** 2)
    return c["floor"] + c["gain"] * key


def band_rect(x0, x1, y0, y1, colour, opacity=1.0):
    r = Rectangle(width=max(x1 - x0, 1e-4), height=max(y1 - y0, 1e-4))
    r.set_stroke(width=0)
    r.set_fill(colour, opacity=opacity)
    r.move_to(np.array([(x0 + x1) / 2, (y0 + y1) / 2, 0.0]))
    return r


def vgradient(x0, x1, y0, y1, top, bottom, bands=64):
    g = VGroup()
    for i in range(bands):
        t0 = y0 + (y1 - y0) * i / bands
        t1 = y0 + (y1 - y0) * (i + 1) / bands
        f = (i + 0.5) / bands
        g.add(band_rect(x0, x1, t0, t1, mix(bottom, top, f)))
    return g


def cyl_h(x0, x1, ycl, od, dark, light, bands=16, rim=True, rim_col=STEEL_RIM):
    """Horizontal cylinder seen side-on. The workhorse: shells, pipes."""
    g = VGroup()
    y0, y1 = ycl - od / 2, ycl + od / 2
    for i in range(bands):
        a = y0 + od * i / bands
        b = y0 + od * (i + 1) / bands
        v = (i + 0.5) / bands
        g.add(band_rect(x0, x1, a, b, mix(dark, light, _round_h(v))))
    if rim:
        g.add(band_rect(x0, x1, y1 - od * 0.035, y1, rim_col, 0.55))
    return g


def cyl_v(y0, y1, xcl, od, dark, light, bands=14, rim=True, rim_col=STEEL_RIM):
    """Vertical cylinder. Risers, columns, structural legs."""
    g = VGroup()
    x0, x1 = xcl - od / 2, xcl + od / 2
    for i in range(bands):
        a = x0 + od * i / bands
        b = x0 + od * (i + 1) / bands
        u = (i + 0.5) / bands
        g.add(band_rect(a, b, y0, y1, mix(dark, light, _round_v(u))))
    if rim:
        g.add(band_rect(x0, x0 + od * 0.07, y0, y1, rim_col, 0.42))
    return g


def dome(x_base, direction, ycl, od, depth, dark, light, bands=26,
         smooth=True):
    """Torispherical head. direction = +1 bulges right, -1 bulges left.

    The shading is banded, but a banded curve staircases badly the moment
    the camera pushes in: near the equator each band is only a few pixels
    tall while its width jumps twenty, so the silhouette reads as steps.
    So the outline is drawn once as a smooth polygon and the bands are
    inset behind it. The curve you see is the polygon; the bands only tint.
    """
    g = VGroup()
    if smooth and depth > 1e-4:
        pts = []
        n = 96
        for k in range(n + 1):
            th = -math.pi / 2 + math.pi * k / n
            pts.append(np.array([x_base + direction * depth * math.cos(th),
                                 ycl + od / 2 * math.sin(th), 0.0]))
        pts.append(np.array([x_base, ycl + od / 2, 0.0]))
        pts.append(np.array([x_base, ycl - od / 2, 0.0]))
        g.add(Polygon(*pts).set_stroke(width=0)
              .set_fill(mix(dark, light, _round_h(0.55)), 1))
    inset = 0.80 if smooth else 1.0
    for i in range(bands):
        v = (i + 0.5) / bands
        y = ycl - od / 2 + od * v
        a = ycl - od / 2 + od * i / bands
        b = ycl - od / 2 + od * (i + 1) / bands
        k = 1.0 - (2.0 * (y - ycl) / od) ** 2
        w = depth * inset * math.sqrt(max(k, 0.0))
        if w < 1e-3:
            continue
        xa, xb = (x_base, x_base + direction * w)
        g.add(band_rect(min(xa, xb), max(xa, xb), a, b,
                        mix(dark, light, _round_h(v))))
    return g


def flange(xc, ycl, od, thick, dark=STEEL_DARK, light=STEEL_LIGHT):
    """Girth or nozzle flange — the detail that reads as 'pressure vessel'."""
    fo = od * 1.16
    g = cyl_h(xc - thick / 2, xc + thick / 2, ycl, fo, dark, light,
              bands=12, rim=True)
    g.add(band_rect(xc - thick / 2, xc - thick / 2 + thick * 0.18,
                    ycl - fo / 2, ycl + fo / 2, STEEL_RIM, 0.30))
    return g


def flange_v(yc, xcl, od, thick, dark=STEEL_DARK, light=STEEL_LIGHT):
    fo = od * 1.20
    return cyl_v(yc - thick / 2, yc + thick / 2, xcl, fo, dark, light,
                 bands=10, rim=False)


def bolt_ring(xc, ycl, od, n=8, r=0.018, colour=STEEL_DARK):
    g = VGroup()
    for i in range(n):
        y = ycl - od * 0.52 + od * 1.04 * (i + 0.5) / n
        d = Dot(np.array([xc, y, 0.0]), radius=r, color=colour)
        g.add(d)
    return g


def elbow(xc, yc, od, quad, dark, light):
    """90 degree bend. quad picks which corner the bend turns through."""
    g = cyl_h(xc - od / 2, xc + od / 2, yc, od, dark, light, bands=10,
              rim=False)
    g.add(cyl_v(yc - od / 2, yc + od / 2, xc, od, dark, light, bands=10,
                rim=False))
    g.add(band_rect(xc - od / 2, xc - od / 2 + od * 0.10,
                    yc - od / 2, yc + od / 2, STEEL_RIM, 0.30))
    return g


def label(txt, pos, size=11, colour=TAG_TEXT, opacity=1.0, font=None):
    kw = {"font_size": size, "color": colour}
    if font:
        kw["font"] = font
    t = Text(txt, **kw)
    t.move_to(np.array([pos[0], pos[1], 0.0]))
    t.set_opacity(opacity)
    return t


def tag_plate(txt, x, y, w=0.62, h=0.20, size=12):
    """Stamped stainless tag plate, bolted to the equipment."""
    g = VGroup()
    g.add(band_rect(x - w / 2, x + w / 2, y - h / 2, y + h / 2, "#3f4653"))
    g.add(band_rect(x - w / 2, x + w / 2, y + h / 2 - h * 0.16,
                    y + h / 2, "#6a7484"))
    t = label(txt, (x, y), size=size, colour="#0f1319")
    t.set_width(min(w * 0.78, t.width))
    t.move_to(np.array([x, y, 0.0]))
    g.add(t)
    return g


def light_shaft(x_top, spread=4.6, width=1.25, opacity=0.030, y_top=11.0,
                y_bot=-3.10):
    """Sun through the structure. Three soft edges, never a hard beam."""
    g = VGroup()
    for k, o in ((1.00, opacity), (0.62, opacity * 1.5), (0.30, opacity * 1.9)):
        wt, wb = width * k, width * k * 1.75
        g.add(Polygon(
            np.array([x_top - wt / 2, y_top, 0]),
            np.array([x_top + wt / 2, y_top, 0]),
            np.array([x_top + spread + wb / 2, y_bot, 0]),
            np.array([x_top + spread - wb / 2, y_bot, 0]),
        ).set_stroke(width=0).set_fill(SUN_CORE, o))
    return g


def haze_sheet(opacity, x0=-34, x1=44, y0=-6.0, y1=12.0, bands=22):
    """Atmospheric perspective — the only thing separating the depth layers.

    The sheet is tinted to the SKY at each height. Haze a warm dawn with a
    cool grey and every distant silhouette turns blue and jumps forward.
    """
    g = VGroup()
    stops = ((y1, SKY_TOP), (5.0, SKY_UPPER), (1.85, SKY_BAND),
             (HORIZON_Y, SKY_HORIZON), (y0, "#413434"))
    for k in range(len(stops) - 1):
        ya, ca = stops[k]
        yb, cb = stops[k + 1]
        n = max(2, int(bands * abs(ya - yb) / (y1 - y0)))
        for i in range(n):
            t0 = yb + (ya - yb) * i / n
            t1 = yb + (ya - yb) * (i + 1) / n
            g.add(band_rect(x0, x1, t0, t1,
                            mix(cb, ca, (i + 0.5) / n), opacity))
    return g


def steam_puff(x, y, r, op, squash=0.72):
    e = Ellipse(width=r * 2, height=r * 2 * squash)
    e.set_stroke(width=0)
    e.set_fill("#c9d4e2", op)
    e.move_to(np.array([x, y, 0]))
    return e


def steam_column(x, y0, t, n=7, rise=2.6, spread=0.55, size=0.30,
                 peak=0.15, drift=0.9, seed=0.0):
    """One drifting plume. t is absolute seconds — deterministic, loopable.

    Each puff is three offset ellipses at a third of the opacity, which
    breaks the circle silhouette and reads as vapour rather than as bubbles.
    """
    g = VGroup()
    for i in range(n):
        ph = ((t * 0.15) + (i / n) + seed) % 1.0
        yy = y0 + rise * ph
        xx = x + drift * ph * ph + spread * math.sin(6.0 * ph + i * 1.7 + seed)
        rr = size * (0.45 + 2.1 * ph)
        op = peak * math.sin(math.pi * min(ph * 1.12, 1.0)) ** 1.9
        # Every puff is emitted every frame, faded to zero rather than
        # dropped. A group whose submobject count changes forces Manim to
        # realign the whole family on each redraw, and that alone was the
        # difference between a two minute render and a forty minute one.
        for k, (ox, oy, sc) in enumerate((( 0.00, 0.00, 1.00),
                                          (-0.42, 0.18, 0.74),
                                          ( 0.46, 0.10, 0.66))):
            g.add(steam_puff(xx + ox * rr, yy + oy * rr, max(rr * sc, 1e-3),
                             max(op * 0.34, 0.0), squash=0.40 + 0.09 * k))
    return g
