"""
world/locations/exchanger_bay/foreground.py

The near half of the bay: the grating deck the operator walks on, the rail
between him and the equipment, and the dark framing at the camera edge.

The deck is the only thing in this world drawn in perspective. The equipment
stays in near-elevation, which keeps E-101 canonical and readable at any
scale, and the FLOOR carries the depth instead.
"""

import json
import os

from engine.draw import *

# ── perspective ground plane ─────────────────────────────────────
# One-point perspective. The equipment stays in near-elevation, which keeps
# E-101 canonical and readable, and the FLOOR carries the depth. This is the
# difference between a side elevation and a place you could walk into.
#
# The numbers are READ from location.json — the deck is the location's own
# geometry, and a second copy of it here is a second thing to get wrong.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "location.json")) as _f:
    _GROUND = json.load(_f)["ground"]

VP = tuple(_GROUND["vanishing_point"])   # vanishing point, on the horizon
DECK_NEAR_Y = _GROUND["deck_near_y"]     # near edge, bottom of frame
DECK_FAR_Y = _GROUND["deck_y"]           # far edge, the equipment line


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
