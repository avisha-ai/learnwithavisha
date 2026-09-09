"""
world/equipment/E-101/exterior.py

The hero asset. Geometry is NOT written here — it is read from
metadata.json, so the tag, the nozzle placement and the drawing can never
drift apart. Change the machine in one place and every episode that says
"use E-101" inherits the change.
"""

import json
import os

from engine.draw import *

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "metadata.json")) as _f:
    METADATA = json.load(_f)

E101 = METADATA["geometry"]
TAG = METADATA["tag"]


def build(detail=1.0):
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
