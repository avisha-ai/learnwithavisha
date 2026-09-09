"""
world/locations/exchanger_bay/background.py

Everything behind the equipment line: dawn sky, the sun, the distant plant,
and the steel frame the bay sits inside.

Placement here is deliberate. The distant plant stands in the OPEN zones of
the composition, left of E-101 and right of it. Put a silhouette behind the
hero and it is never seen, and the horizon reads as an empty sunset instead
of as a working site.
"""

from engine.draw import *

RACK_Y = 3.55


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
