"""
LearnWithAvisha — Visual Pilot 001
plant_world.py — the canonical world kit.

Scope discipline: this is ONE exchanger bay, not a plant. It holds only the
assets Pilot 001 needs, built so that anything here can become canon later
without being redrawn.

WORLD CONVENTIONS — freeze these, everything downstream depends on them.

  Units      1 world unit = 1 metre.
  Ground     Walkway grating top surface is y = 0. The operator walks on it.
  Light      Low morning sun from the upper LEFT. Warm key (#c9a077),
             cool sky fill, cool bounce up off the grating. Every shaded
             primitive in this file obeys that one direction. If a later
             asset lights from the right, the world breaks.
  Depth      Four layers, far to near: FAR, MID, NEAR, FORE. Distance is
             expressed as loss of contrast (haze), loss of line weight and
             loss of detail — never as a change in light direction.
  Colour     Cool steel body, warm rim. Red is reserved. Nothing in this
             world is red unless it is a genuine alarm, and in Pilot 001
             nothing is.

ENGINEERING — deliberate, not decorative. AI may invent atmosphere here,
it may not invent engineering.

  E-101 is a 1-2 shell-and-tube exchanger. Hot process on the tube side,
  cooling water on the shell side.
    • Both tube nozzles land on the channel head (left) — that is what
      makes it a two-tube-pass machine.
    • Shell inlet sits at the far (right) end, shell outlet at the near
      (left) end, so the shell stream runs counter-current to the first
      tube pass.
    • Shell inlet is bottom, outlet is top, so the shell runs liquid-full.
    • Saddle supports sit under the shell, on a plinth, on the deck.
  Instruments
    • TI-1014  process outlet, digital indicator. The hero. Reads 87 °C.
    • TI-1013  process inlet, local dial.
    • PI-1012  cooling water inlet, local dial. Needle is stable and stays
               stable — the machine never sounds or looks wrong.
"""

import math
from manim import *

M = 1.0                       # one world unit is one metre

# ── palette ──────────────────────────────────────────────────────
BRAND_DEEP = "#0d0d1a"

SKY_TOP = "#0e1424"
SKY_UPPER = "#161d2f"
SKY_BAND = "#28293c"
SKY_HORIZON = "#7a5747"                   # dawn, low and warm
SUN_CORE = "#e0a06a"

# The plant is DARKER than the sky. Everything silhouettes against morning.
# This is the whole value structure — break it and the world goes flat.
FAR_DARK, FAR_LIGHT = "#1e2637", "#333e54"
MID_DARK, MID_LIGHT = "#151a24", "#28313f"

STEEL_DARK, STEEL_MID, STEEL_LIGHT = "#11161e", "#28313c", "#454f5c"
STEEL_RIM = "#e0a978"                     # the warm morning key
CONCRETE_DARK, CONCRETE_LIGHT = "#171920", "#3a3d45"

GRATE_DARK, GRATE_LIGHT = "#141922", "#3b4655"

GAUGE_FACE, GAUGE_CASE = "#b6bfcb", "#171b22"
LCD_BACK, LCD_LIT = "#0e2a19", "#6fd490"   # loop-powered digital indicator

VEST, VEST_DARK = "#c8823c", "#7d4e21"
BAND = "#d5dce4"
FIG_DARK, FIG_MID = "#10141b", "#1f2530"
SKIN = "#7a5947"
HAT = "#c3c9d2"

HORIZON_Y = 0.62          # distant plant stands here. Frozen.
HAZE = "#4a5064"
TAG_TEXT = "#7d8b9d"
FORE_BLACK = "#070910"

def _c(x):
    return ManimColor(x)


def mix(a, b, t):
    return interpolate_color(_c(a), _c(b), max(0.0, min(1.0, t)))


# ── shading profiles — one light direction, applied everywhere ───
def _round_h(v):
    """Tone across a HORIZONTAL cylinder. v = 0 bottom, 1 top."""
    key = math.exp(-((v - 0.72) / 0.27) ** 2)          # sun from above-left
    bounce = 0.18 * math.exp(-((v - 0.05) / 0.13) ** 2)  # off the grating
    return 0.09 + 0.80 * key + bounce


def _round_v(u):
    """Tone across a VERTICAL cylinder. u = 0 left, 1 right."""
    key = math.exp(-((u - 0.29) / 0.29) ** 2)
    return 0.11 + 0.78 * key


# ── primitives ───────────────────────────────────────────────────
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


# ═════════════════════════════════════════════════════════════════
# ASSET 001 — E-101
# ═════════════════════════════════════════════════════════════════
# Geometry is fixed here and nowhere else. Every shot imports these.
E101 = dict(
    ycl=1.45,            # shell centreline, metres above the grating
    od=0.95,             # shell outside diameter
    shell_x0=2.00,       # girth flange, channel end
    shell_x1=6.20,       # girth flange, rear end
    head_x0=1.30,        # channel head face
    bonnet_x1=6.86,      # rear bonnet extremity
    plinth_x0=2.55, plinth_x1=5.95, plinth_h=0.35,
    saddle_a=3.05, saddle_b=5.35, saddle_w=0.52,
    n_tube_in=1.90,      # tube-side inlet  — channel head, BOTTOM
    n_tube_out=1.62,     # tube-side outlet — channel head, TOP
    n_shell_in=5.55,     # shell inlet  — bottom, far end (counter-current)
    n_shell_out=2.55,    # shell outlet — top, near end (runs liquid-full)
    noz_od=0.20,
)


def build_e101(detail=1.0):
    """The hero asset. detail scales how much fine hardware is drawn."""
    E = E101
    ycl, od = E["ycl"], E["od"]
    top, bot = ycl + od / 2, ycl - od / 2
    g = VGroup()

    # plinth and saddles — it is bolted to something
    g.add(band_rect(E["plinth_x0"], E["plinth_x1"], 0.0, E["plinth_h"],
                    CONCRETE_DARK))
    g.add(band_rect(E["plinth_x0"], E["plinth_x1"],
                    E["plinth_h"] - 0.05, E["plinth_h"],
                    mix(CONCRETE_DARK, CONCRETE_LIGHT, 0.70)))
    g.add(band_rect(E["plinth_x0"], E["plinth_x1"],
                    E["plinth_h"] - 0.012, E["plinth_h"], STEEL_RIM, 0.22))
    for sx in (E["saddle_a"], E["saddle_b"]):
        w = E["saddle_w"]
        g.add(Polygon(
            np.array([sx - w, E["plinth_h"], 0]),
            np.array([sx + w, E["plinth_h"], 0]),
            np.array([sx + w * 0.62, bot + 0.02, 0]),
            np.array([sx - w * 0.62, bot + 0.02, 0]),
        ).set_stroke(width=0).set_fill(mix(STEEL_DARK, STEEL_MID, 0.45), 1))
        g.add(band_rect(sx - w, sx - w + 0.030, E["plinth_h"], bot,
                        STEEL_RIM, 0.34))

    # shell, heads, girth flanges
    g.add(cyl_h(E["shell_x0"], E["shell_x1"], ycl, od, STEEL_DARK,
                STEEL_LIGHT, bands=44))
    g.add(dome(E["shell_x1"], +1, ycl, od, E["bonnet_x1"] - E["shell_x1"],
               STEEL_DARK, STEEL_LIGHT, bands=40))
    g.add(cyl_h(E["head_x0"], E["shell_x0"], ycl, od,
                STEEL_DARK, STEEL_LIGHT, bands=44))   # channel barrel
    g.add(dome(E["head_x0"], -1, ycl, od, 0.26, STEEL_DARK, STEEL_LIGHT,
               bands=40))
    for fx in (E["shell_x0"], E["shell_x1"]):
        g.add(flange(fx, ycl, od, 0.13))
        if detail > 0.5:
            g.add(bolt_ring(fx, ycl, od * 1.16, n=9, r=0.017))

    # longitudinal shading break so the shell does not read as a flat bar
    g.add(band_rect(E["head_x0"], E["bonnet_x1"], ycl - od * 0.06,
                    ycl - od * 0.02, STEEL_DARK, 0.22))

    # nozzles — placement is the engineering, so it is explicit
    nod = E["noz_od"]
    # tube-side OUT, top of channel head, riser to the rack
    g.add(cyl_v(top - 0.02, top + 0.42, E["n_tube_out"], nod,
                STEEL_DARK, STEEL_LIGHT, bands=8))
    g.add(flange_v(top + 0.42, E["n_tube_out"], nod, 0.07))
    # tube-side IN, bottom of channel head
    g.add(cyl_v(bot - 0.40, bot + 0.02, E["n_tube_in"], nod,
                STEEL_DARK, STEEL_LIGHT, bands=8))
    g.add(flange_v(bot - 0.40, E["n_tube_in"], nod, 0.07))
    # shell OUT, top near end
    g.add(cyl_v(top - 0.02, top + 0.36, E["n_shell_out"], nod * 1.15,
                STEEL_DARK, STEEL_LIGHT, bands=8))
    g.add(flange_v(top + 0.36, E["n_shell_out"], nod * 1.15, 0.07))
    # shell IN, bottom far end
    g.add(cyl_v(bot - 0.34, bot + 0.02, E["n_shell_in"], nod * 1.15,
                STEEL_DARK, STEEL_LIGHT, bands=8))
    g.add(flange_v(bot - 0.34, E["n_shell_in"], nod * 1.15, 0.07))

    if detail > 0.5:
        # lifting lugs and a vent — small true details, not decoration
        for lx in (2.35, 5.80):
            g.add(band_rect(lx - 0.05, lx + 0.05, top - 0.01, top + 0.13,
                            mix(STEEL_DARK, STEEL_MID, 0.6)))
        g.add(cyl_v(top - 0.01, top + 0.16, 4.30, 0.07,
                    STEEL_DARK, STEEL_MID, bands=5, rim=False))

    g.add(tag_plate("E-101", 4.22, ycl - 0.02, w=0.74, h=0.235, size=13))
    return g


# ═════════════════════════════════════════════════════════════════
# PIPEWORK — every line lands on a real nozzle and goes somewhere
# ═════════════════════════════════════════════════════════════════
RACK_Y = 3.55


def build_pipework():
    E = E101
    ycl, od, nod = E["ycl"], E["od"], E["noz_od"]
    top, bot = ycl + od / 2, ycl - od / 2
    g = VGroup()
    d, l = STEEL_DARK, mix(STEEL_MID, STEEL_LIGHT, 0.35)

    # 6" process OUT: channel head top -> riser -> rack, running left
    x = E["n_tube_out"]
    g.add(cyl_v(top + 0.42, RACK_Y, x, nod, d, l, bands=8))
    g.add(elbow(x, RACK_Y, nod, 0, d, l))
    g.add(cyl_h(-9.0, x, RACK_Y, nod, d, l, bands=8))
    g.add(label('6"-P-10104', (0.30, RACK_Y + 0.20), size=10, opacity=0.75))

    # 6" process IN: from the rack, down, along, up into the bottom nozzle
    xi = E["n_tube_in"]
    g.add(cyl_h(-9.0, 0.42, RACK_Y - 0.34, nod, d, l, bands=8))
    g.add(elbow(0.42, RACK_Y - 0.34, nod, 0, d, l))
    g.add(cyl_v(0.62, RACK_Y - 0.34, 0.42, nod, d, l, bands=8))
    g.add(elbow(0.42, 0.62, nod, 0, d, l))
    g.add(cyl_h(0.42, xi, 0.62, nod, d, l, bands=8))
    g.add(elbow(xi, 0.62, nod, 0, d, l))
    g.add(cyl_v(0.62, bot - 0.40, xi, nod, d, l, bands=8))
    g.add(label('6"-P-10103', (-1.10, RACK_Y - 0.58), size=10, opacity=0.72))

    # 8" cooling water IN: rack right -> down -> bottom far nozzle
    xs = E["n_shell_in"]
    cod = nod * 1.15
    g.add(cyl_h(xs, 12.5, 0.55, cod, d, l, bands=8))
    g.add(elbow(xs, 0.55, cod, 0, d, l))
    g.add(cyl_v(0.55, bot - 0.34, xs, cod, d, l, bands=8))
    g.add(label('8"-CWS-10121', (8.30, 0.80), size=10, opacity=0.68))

    # 8" cooling water OUT: top near nozzle -> up -> rack, running right
    xo = E["n_shell_out"]
    g.add(cyl_v(top + 0.36, RACK_Y - 0.68, xo, cod, d, l, bands=8))
    g.add(elbow(xo, RACK_Y - 0.68, cod, 0, d, l))
    g.add(cyl_h(xo, 12.5, RACK_Y - 0.68, cod, d, l, bands=8))
    g.add(label('8"-CWR-10122', (7.60, RACK_Y - 0.48), size=10, opacity=0.68))

    # hand valve on the CW inlet, with a handwheel — operable, reachable
    g.add(flange_v(1.05, xs, cod, 0.07))
    g.add(band_rect(xs - 0.14, xs + 0.14, 1.10, 1.42,
                    mix(STEEL_DARK, STEEL_MID, 0.5)))
    g.add(Circle(radius=0.20).set_stroke(STEEL_LIGHT, 3.2).move_to(
        np.array([xs + 0.30, 1.26, 0])))
    g.add(band_rect(xs, xs + 0.30, 1.24, 1.28, STEEL_MID))
    return g


# ═════════════════════════════════════════════════════════════════
# INSTRUMENTS
# ═════════════════════════════════════════════════════════════════
def build_ti1014(value="87", x=None, y=2.15, scale=1.0):
    """Process outlet temperature indicator — the hero instrument.

    A loop-powered digital head on a thermowell in the outlet riser, rotated
    to face the walkway so it can be read from the normal route. It carries a
    close-up in Shot 3, so the hardware is real: gland, conduit, bracket,
    bezel, tag. Nothing here is decoration.
    """
    E = E101
    rx = E["n_tube_out"] if x is None else x
    s_ = scale
    g = VGroup()
    bx = rx - 0.44 * s_

    # thermowell boss into the line, then the transmitter neck
    g.add(band_rect(bx + 0.06 * s_, rx, y - 0.050 * s_, y + 0.050 * s_,
                    mix(STEEL_DARK, STEEL_MID, 0.62)))
    g.add(band_rect(rx - 0.10 * s_, rx - 0.05 * s_, y - 0.082 * s_,
                    y + 0.082 * s_, mix(STEEL_DARK, STEEL_MID, 0.75)))
    g.add(band_rect(bx + 0.02 * s_, bx + 0.09 * s_, y - 0.072 * s_,
                    y + 0.072 * s_, mix(STEEL_DARK, STEEL_MID, 0.70)))

    # housing, lit from the left like everything else in this world
    hx0, hx1 = bx - 0.32 * s_, bx + 0.04 * s_
    g.add(band_rect(hx0, hx1, y - 0.25 * s_, y + 0.25 * s_,
                    mix(STEEL_DARK, STEEL_MID, 0.42)))
    g.add(band_rect(hx0, hx0 + 0.030 * s_, y - 0.25 * s_, y + 0.25 * s_,
                    STEEL_RIM, 0.42))
    g.add(band_rect(hx0, hx1, y + 0.235 * s_, y + 0.25 * s_, STEEL_RIM, 0.26))
    # conduit gland underneath — the signal has to leave somehow
    g.add(band_rect(bx - 0.20 * s_, bx - 0.12 * s_, y - 0.34 * s_,
                    y - 0.24 * s_, mix(STEEL_DARK, STEEL_MID, 0.55)))
    g.add(cyl_v(y - 0.62 * s_, y - 0.32 * s_, bx - 0.16 * s_, 0.045 * s_,
                STEEL_DARK, STEEL_MID, bands=5, rim=False))

    # bezel and display glass
    g.add(band_rect(hx0 + 0.030 * s_, hx1 - 0.022 * s_, y - 0.115 * s_,
                    y + 0.185 * s_, "#0a0d12"))
    g.add(band_rect(hx0 + 0.048 * s_, hx1 - 0.040 * s_, y - 0.098 * s_,
                    y + 0.168 * s_, LCD_BACK))
    cx = (hx0 + 0.048 * s_ + hx1 - 0.040 * s_) / 2
    v = label(value, (cx, y + 0.040 * s_), size=40, colour=LCD_LIT)
    v.set_width(0.150 * s_)
    v.move_to(np.array([cx - 0.030 * s_, y + 0.040 * s_, 0]))
    g.add(v)
    u = label("°C", (cx, y + 0.035 * s_), size=20, colour=LCD_LIT)
    u.set_width(0.052 * s_)
    u.move_to(np.array([cx + 0.082 * s_, y + 0.030 * s_, 0]))
    g.add(u)
    g.add(tag_plate("TI-1014", cx, y - 0.055 * s_, w=0.185 * s_,
                    h=0.055 * s_, size=14))
    sub = label("E-101  PROCESS OUT", (cx, y - 0.205 * s_), size=12,
                colour="#5f6a79")
    sub.set_width(0.235 * s_)
    sub.move_to(np.array([cx, y - 0.205 * s_, 0]))
    g.add(sub)
    return g


def build_logsheet(x, y, scale=1.0, rows=(("09 SEP", "87"), ("08 SEP", "85"),
                                          ("07 SEP", "83"))):
    """His log sheet, held up beside the instrument.

    Deliberately not an infographic: no highlight, no arrow, no colour on the
    numbers. Three handwritten readings and the reader does the arithmetic.
    """
    g = VGroup()
    s_ = scale
    bw, bh = 1.05 * s_, 1.42 * s_
    g.add(band_rect(x - bw / 2, x + bw / 2, y - bh / 2, y + bh / 2, "#20252d"))
    g.add(band_rect(x - bw / 2, x - bw / 2 + 0.028 * s_, y - bh / 2,
                    y + bh / 2, STEEL_RIM, 0.40))
    pw, ph = bw - 0.10 * s_, bh - 0.16 * s_
    g.add(band_rect(x - pw / 2, x + pw / 2, y - ph / 2 - 0.02 * s_,
                    y + ph / 2 - 0.02 * s_, "#9aa3ae"))
    g.add(band_rect(x - pw / 2, x - pw / 2 + 0.022 * s_,
                    y - ph / 2 - 0.02 * s_, y + ph / 2 - 0.02 * s_,
                    "#c6ccd4"))
    g.add(band_rect(x - bw * 0.20, x + bw * 0.20, y + bh / 2 - 0.13 * s_,
                    y + bh / 2 - 0.02 * s_, "#4d5563"))

    hd = label("E-101   TI-1014", (x, y + ph / 2 - 0.20 * s_), size=20,
               colour="#2b313a")
    hd.set_width(pw * 0.66)
    hd.move_to(np.array([x - pw * 0.04, y + ph / 2 - 0.21 * s_, 0]))
    g.add(hd)
    g.add(band_rect(x - pw * 0.40, x + pw * 0.40, y + ph / 2 - 0.28 * s_,
                    y + ph / 2 - 0.272 * s_, "#6b7382"))
    for i2, (day, val) in enumerate(rows):
        ry = y + ph / 2 - 0.42 * s_ - i2 * 0.245 * s_
        d_ = label(day, (0, 0), size=18, colour="#3a414c")
        d_.set_width(pw * 0.34)
        d_.move_to(np.array([x - pw * 0.21, ry, 0]))
        g.add(d_)
        v_ = label(val, (0, 0), size=22, colour="#22272f")
        v_.set_width(pw * 0.155)
        v_.move_to(np.array([x + pw * 0.26, ry, 0]))
        g.add(v_)
    # his thumb on the board
    th = Ellipse(width=0.20 * s_, height=0.34 * s_)
    th.set_stroke(width=0).set_fill(SKIN, 1)
    th.rotate(-0.30).move_to(np.array([x - bw / 2 + 0.05 * s_,
                                       y - bh * 0.16, 0]))
    g.add(th)
    return g


def build_dial(tag, x, y, r=0.13, frac=0.62, face=GAUGE_FACE):
    """Local dial gauge. The needle is stable and stays stable."""
    g = VGroup()
    g.add(Circle(radius=r * 1.18).set_stroke(width=0).set_fill(GAUGE_CASE, 1)
          .move_to(np.array([x, y, 0])))
    g.add(Circle(radius=r).set_stroke(width=0).set_fill(face, 1)
          .move_to(np.array([x, y, 0])))
    g.add(Arc(radius=r * 1.12, start_angle=PI * 0.62, angle=PI * 0.5)
          .set_stroke(STEEL_RIM, 1.6, opacity=0.55).move_to(
              np.array([x, y, 0]) + np.array([-r * 0.06, r * 0.06, 0])))
    for i in range(9):
        a = PI * 1.25 - PI * 1.5 * i / 8
        p0 = np.array([x + r * 0.78 * math.cos(a), y + r * 0.78 * math.sin(a), 0])
        p1 = np.array([x + r * 0.96 * math.cos(a), y + r * 0.96 * math.sin(a), 0])
        g.add(Line(p0, p1).set_stroke(GAUGE_CASE, 1.4))
    a = PI * 1.25 - PI * 1.5 * frac
    g.add(Polygon(
        np.array([x + r * 0.86 * math.cos(a), y + r * 0.86 * math.sin(a), 0]),
        np.array([x + r * 0.10 * math.cos(a + PI / 2),
                  y + r * 0.10 * math.sin(a + PI / 2), 0]),
        np.array([x + r * 0.10 * math.cos(a - PI / 2),
                  y + r * 0.10 * math.sin(a - PI / 2), 0]),
    ).set_stroke(width=0).set_fill("#1d222b", 1))
    g.add(Dot(np.array([x, y, 0]), radius=r * 0.13, color="#3a424f"))
    g.add(label(tag, (x, y - r * 1.75), size=9, colour=TAG_TEXT, opacity=0.8))
    return g


# ═════════════════════════════════════════════════════════════════
# WALKWAY, STRUCTURE, DISTANCE
# ═════════════════════════════════════════════════════════════════
# ── perspective ground plane ─────────────────────────────────────
# One-point perspective. The equipment stays in near-elevation, which keeps
# E-101 canonical and readable, and the FLOOR carries the depth. This is the
# difference between a side elevation and a place you could walk into.
VP = (-2.0, 2.05)          # vanishing point, on the horizon
DECK_NEAR_Y = -3.10        # near edge of the grating, bottom of frame
DECK_FAR_Y = 0.0           # far edge, where the equipment line begins


def _ray_x(x_near, y):
    """Where a floor line from x_near on the near edge sits at height y."""
    t = (y - DECK_NEAR_Y) / (VP[1] - DECK_NEAR_Y)
    return x_near + t * (VP[0] - x_near)


def build_walkway(x0=-11.0, x1=13.5):
    """Grating deck, in perspective. Far edge (the equipment line) is y = 0."""
    g = VGroup()
    g.add(band_rect(-16, 20, DECK_NEAR_Y, DECK_FAR_Y, GRATE_DARK))

    # bearing bars running away from camera, converging on the vanishing point
    xn = -16.0
    while xn < 21.0:
        a = np.array([xn, DECK_NEAR_Y, 0.0])
        b = np.array([_ray_x(xn, DECK_FAR_Y), DECK_FAR_Y, 0.0])
        g.add(Line(a, b).set_stroke(GRATE_LIGHT, 1.3, opacity=0.13))
        xn += 1.05

    # transverse bars, spacing compressing with distance
    j = 0
    while True:
        y = VP[1] - (VP[1] - DECK_NEAR_Y) / (1.0 + 0.30 * j)
        if y > DECK_FAR_Y - 0.05:
            break
        w = 0.070 * (1.0 - (y - DECK_NEAR_Y) / (VP[1] - DECK_NEAR_Y)) + 0.014
        g.add(band_rect(-16, 20, y, y + w, GRATE_LIGHT, 0.17))
        j += 1

    # the far lip catches the sun, and separates deck from equipment
    g.add(band_rect(-16, 20, DECK_FAR_Y - 0.055, DECK_FAR_Y, "#1e2530"))
    g.add(band_rect(-16, 20, DECK_FAR_Y - 0.016, DECK_FAR_Y, STEEL_RIM, 0.40))

    # Where the shafts land. This is what stops the floor reading as a grid
    # overlay and starts it reading as a lit surface.
    for px, pw, po in ((-4.4, 7.0, 0.030), (1.2, 5.4, 0.020), (7.4, 4.2, 0.013)):
        for k in (1.0, 0.62, 0.34):
            e = Ellipse(width=pw * k, height=pw * k * 0.13)
            e.set_stroke(width=0).set_fill("#f0c79a", po)
            e.move_to(np.array([px, -1.15, 0]))
            g.add(e)
    # wet sheen along the deck edge, catching the dawn
    g.add(band_rect(-16, 20, DECK_FAR_Y - 0.30, DECK_FAR_Y - 0.05,
                    SUN_CORE, 0.030))
    return g


def build_handrail(x0=-11.0, x1=13.5, y=0.0, opacity=1.0):
    """Rail behind the walking line — it sits between operator and equipment."""
    g = VGroup()
    for yy, w in ((1.05, 2.6), (0.55, 2.0)):
        g.add(band_rect(x0, x1, y + yy - 0.022 * w / 2.6,
                        y + yy + 0.022 * w / 2.6,
                        mix(STEEL_MID, STEEL_LIGHT, 0.35), opacity * 0.9))
    for i in range(int((x1 - x0) / 1.9) + 1):
        sx = x0 + 1.9 * i
        g.add(band_rect(sx - 0.026, sx + 0.026, y, y + 1.07, STEEL_MID,
                        opacity * 0.9))
    g.add(band_rect(x0, x1, y + 0.02, y + 0.12, STEEL_DARK, opacity * 0.85))
    return g


def build_structure():
    """Steel frame and pipe rack. Open enough that dawn sky reads between it —
    a solid wall of structure kills the light and flattens the frame."""
    g = VGroup()
    for cx in (-6.9, -0.55, 7.35, 12.4):
        g.add(cyl_v(0.0, 7.4, cx, 0.34, MID_DARK, MID_LIGHT, bands=9))
        g.add(band_rect(cx - 0.32, cx + 0.32, 0.0, 0.12, MID_DARK))
        for by in (2.5, 5.2):
            g.add(Line(np.array([cx + 0.17, by, 0]),
                       np.array([cx + 2.2, by + 1.55, 0]))
                  .set_stroke(mix(MID_DARK, MID_LIGHT, 0.40), 2.6))
    g.add(band_rect(-11.5, 15.0, RACK_Y + 0.56, RACK_Y + 0.76,
                    mix(MID_DARK, MID_LIGHT, 0.30)))
    # rack pipes overhead. Kept dark and few — structure, not subject.
    for py, pod, t in ((RACK_Y + 1.06, 0.28, 0.30), (RACK_Y + 1.44, 0.16, 0.18)):
        g.add(cyl_h(-11.5, 15.0, py, pod, MID_DARK,
                    mix(MID_LIGHT, STEEL_LIGHT, t), bands=8, rim=True))
    return g


def build_far():
    """Distant plant standing on HORIZON_Y.

    Placement is deliberate: everything here sits in the OPEN zones of the
    composition, left of E-101 and right of it. Put a silhouette behind the
    hero and it is simply never seen, and the horizon reads as an empty
    sunset instead of as a working site.
    """
    g = VGroup()
    d, l = FAR_DARK, FAR_LIGHT
    h = HORIZON_Y
    g.add(band_rect(-34, 44, h - 0.04, h + 0.02, mix(d, SKY_HORIZON, 0.55)))

    # cooling water tower bank — the low sun sits just off its right edge
    g.add(band_rect(-5.15, -3.05, h, h + 2.45, mix(d, l, 0.10)))
    for i2 in range(5):
        lx = -5.00 + i2 * 0.40
        g.add(band_rect(lx, lx + 0.21, h + 0.30, h + 2.20, mix(d, l, 0.30), 0.5))
    g.add(band_rect(-5.15, -3.05, h + 2.45, h + 2.55, mix(d, l, 0.16)))

    # C-201, in the open gap between the operator and the bay
    g.add(cyl_v(h, h + 4.65, -1.35, 0.86, d, mix(d, l, 0.55), bands=10))
    for py in (1.35, 2.55, 3.75, 4.35):
        g.add(band_rect(-1.98, -0.72, h + py, h + py + 0.07, mix(d, l, 0.34)))
    g.add(dome(h + 4.65, +1, -1.35, 0.86, 0.0, d, l, bands=2))

    # stack and low clutter, right of the bay
    g.add(cyl_v(h, h + 6.9, 8.55, 0.38, d, mix(l, "#635a66", 0.35), bands=8))
    for hx, hw, hh in ((7.35, 1.0, 1.55), (9.25, 1.5, 2.15), (11.1, 1.2, 1.2),
                       (13.4, 2.2, 1.7)):
        g.add(band_rect(hx, hx + hw, h, h + hh, mix(d, l, 0.12)))
    for hx, hw, hh in ((-9.4, 2.4, 1.9), (-7.0, 1.4, 1.2), (-2.55, 0.62, 1.05)):
        g.add(band_rect(hx, hx + hw, h, h + hh, mix(d, l, 0.12)))
    return g


def build_sky(x0=-34, x1=44, y0=-6.0, y1=12.0):
    """Dawn. The sky is the brightest value in frame and the light source.

    The bright band sits between the deck edge and the pipe rack, so the bay
    is seen against open sky. Close that band off and the shot stops being
    outdoors.
    """
    g = VGroup()
    g.add(vgradient(x0, x1, 5.0, y1, SKY_TOP, SKY_UPPER, bands=26))
    g.add(vgradient(x0, x1, 1.85, 5.0, SKY_UPPER, SKY_BAND, bands=26))
    g.add(vgradient(x0, x1, HORIZON_Y, 1.85, SKY_BAND, SKY_HORIZON,
                    bands=26))
    g.add(vgradient(x0, x1, y0, HORIZON_Y, "#4e3d3c", "#2b2833", bands=16))

    # Low sun sitting on the horizon, behind the bay. Contre-jour: the plant
    # is silhouette with warm rims, which is what makes this read as morning
    # rather than as a lit diagram.
    for i in range(16):
        r = 0.42 + i * 0.78
        g.add(Circle(radius=r).set_stroke(width=0)
              .set_fill(SUN_CORE, 0.078 * (1 - i / 16) ** 1.9)
              .move_to(np.array([-2.6, HORIZON_Y + 0.55, 0])))
    for i in range(10):
        r = 0.16 + i * 0.13
        g.add(Circle(radius=r).set_stroke(width=0)
              .set_fill("#f6d3a8", 0.075 * (1 - i / 10) ** 1.2)
              .move_to(np.array([-2.6, HORIZON_Y + 0.55, 0])))
    return g


def light_shaft(x_top, spread=4.6, width=1.25, opacity=0.030, y_top=11.0,
                y_bot=DECK_NEAR_Y):
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


def build_foreground():
    """Near handrail at the camera edge of the deck, plus a framing column.
    Almost pure silhouette — foreground is where the darkest values live."""
    g = VGroup()
    for yy in (-2.30, -2.86):
        g.add(band_rect(-34, 44, yy - 0.035, yy + 0.035, "#0d1017"))
    for i in range(30):
        sx = -32.0 + 2.35 * i
        g.add(band_rect(sx - 0.045, sx + 0.045, DECK_NEAR_Y, -2.26, "#0d1017"))
    g.add(band_rect(-34, 44, -6.0, DECK_NEAR_Y, FORE_BLACK))
    return g


def build_proscenium(x=-4.78):
    """A near structural column at the frame edge — something to look past.
    Backlit: a dark shape with one warm edge, never a black slab."""
    g = VGroup()
    g.add(band_rect(x - 0.20, x + 0.20, -6.0, 12.0, "#0b0e15"))
    g.add(band_rect(x + 0.20, x + 0.235, -6.0, 12.0, STEEL_RIM, 0.34))
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


# ═════════════════════════════════════════════════════════════════
# OPERATOR_01
# ═════════════════════════════════════════════════════════════════
# Name is not frozen. He is experienced and this is his workplace, so the
# rig is built for small movements: a pace that never hurries, a head that
# pitches up to read an instrument, a body that turns back for a second
# look. There is no facial animation and there is no theatrical acting.
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


def build_operator(x, phase=0.0, facing=1, walking=True, head_pitch=0.0,
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


# ═════════════════════════════════════════════════════════════════
# WATERMARK — brand rule, present on every frame, never occluded
# ═════════════════════════════════════════════════════════════════
def build_watermark():
    ring = Circle(radius=0.42, fill_opacity=0)
    ring.set_stroke(WHITE, width=1.2, opacity=0.85)
    mono = Text("LWA", font="Georgia", slant=ITALIC, font_size=17, color=WHITE)
    mono.move_to(ring.get_center())
    mono.set_opacity(0.85)
    wm = VGroup(ring, mono)
    wm.set_z_index(100)
    return wm


def pin_watermark(wm, frame, base_width):
    def _upd(m):
        s = frame.width / config.frame_width
        m.set(width=base_width * s)
        m.move_to(frame.get_corner(DR) + s * (UP + LEFT) * 0.77)
    return _upd
