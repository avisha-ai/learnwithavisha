"""
world/locations/exchanger_bay/pipework.py

Every line in this file lands on a real nozzle on E-101 and goes somewhere.
The nozzle coordinates are READ from the equipment's metadata rather than
retyped here, so the pipework and the machine can never drift apart.
"""

import json
import os

from engine.draw import *

_EQ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "equipment", "E-101",
                                    "metadata.json"))
with open(_EQ) as _f:
    E101 = json.load(_f)["geometry"]

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
