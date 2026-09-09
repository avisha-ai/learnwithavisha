"""
world/instruments/temperature_gauge.py

Two instrument bodies, one canonical style.

  build_digital()  a loop-powered digital head on a thermowell. It carries a
                   close-up in Shot 3, so the hardware is real: gland,
                   conduit, bracket, bezel, tag.
  build_dial()     a local dial. Its needle is stable and stays stable —
                   nothing in this world is allowed to look wrong.

The instrument does not know which machine it is bolted to. The LOCATION
places it, using the nozzle coordinate it reads from the equipment.
"""

from engine.draw import *


def build_digital(value, x, y=2.15, scale=1.0):
    """Process outlet temperature indicator — the hero instrument.

    A loop-powered digital head on a thermowell in the outlet riser, rotated
    to face the walkway so it can be read from the normal route. It carries a
    close-up in Shot 3, so the hardware is real: gland, conduit, bracket,
    bezel, tag. Nothing here is decoration.
    """
    rx = x
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
