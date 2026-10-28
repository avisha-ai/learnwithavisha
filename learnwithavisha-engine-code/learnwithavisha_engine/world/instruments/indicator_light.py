"""
world/instruments/indicator_light.py

Running lamps and beacons. The small lights that tell you, at a glance from
forty metres away, that the plant is doing what it is supposed to.

Two reasons this asset exists and matters more than its size suggests.

The first is atmosphere: a still plant is a drawing, and a plant with a few
lamps breathing at different rates is a place that has been running all
night. Each lamp carries its own period and phase so they never blink
together — synchronised lights read as decoration, staggered ones read as
independent machines.

The second is the story. Red in this world is reserved for real alarms, so
these are green and amber. Every lamp in Episode 1 says RUNNING NORMALLY,
including the one bolted to the exchanger that is quietly fouling shut. The
plant is not lying. Nobody has asked it the right question yet.
"""

import math

from engine.draw import *

RUNNING = "#4f9d6b"
STANDBY = "#c08a3e"
PILOT = "#cfd8e2"


def build(x, y, colour=RUNNING, r=0.045, t=0.0, period=0.0, phase=0.0,
          base=0.72, amp=0.28, glow=1.0, bracket=True):
    """One lamp. period=0 is a steady lamp with a faint breath on it;
    anything above zero is a beacon that pulses on its own clock."""
    g = VGroup()
    if period > 0.01:
        k = base + amp * (0.5 + 0.5 * math.sin(2 * math.pi * t / period
                                               + phase))
    else:
        k = base + 0.05 * math.sin(2 * math.pi * t / 7.3 + phase)
    k = max(0.0, min(1.0, k))

    if bracket:
        g.add(band_rect(x - r * 0.42, x + r * 0.42, y - r * 2.10, y - r * 0.80,
                        mix(STEEL_DARK, STEEL_MID, 0.55)))
    g.add(Dot(np.array([x, y, 0]), radius=r * 1.34, color=GAUGE_CASE))
    g.add(Dot(np.array([x, y, 0]), radius=r, color=mix("#0b0e13", colour, k)))
    g.add(Dot(np.array([x - r * 0.30, y + r * 0.30, 0]), radius=r * 0.28,
              color=mix(colour, "#ffffff", 0.45)).set_opacity(0.55 * k))
    if glow > 0.01:
        for m, o in ((3.4, 0.055), (2.2, 0.075), (1.6, 0.095)):
            g.add(Dot(np.array([x, y, 0]), radius=r * m, color=colour)
                  .set_opacity(o * k * glow))
    return g


def panel(x, y, lamps, t=0.0, w=0.30, h=0.24):
    """A local control station: a small box with a couple of lamps on it."""
    g = VGroup()
    g.add(band_rect(x - w / 2, x + w / 2, y - h / 2, y + h / 2,
                    mix(STEEL_DARK, STEEL_MID, 0.42)))
    g.add(band_rect(x - w / 2, x - w / 2 + w * 0.09, y - h / 2, y + h / 2,
                    STEEL_RIM, 0.34))
    g.add(band_rect(x - w / 2, x + w / 2, y + h / 2 - h * 0.08, y + h / 2,
                    STEEL_RIM, 0.20))
    n = len(lamps)
    for i, spec in enumerate(lamps):
        lx = x - w * 0.24 + (w * 0.48) * (i / max(n - 1, 1))
        g.add(build(lx, y + h * 0.06, t=t, bracket=False, r=w * 0.115,
                    **spec))
    return g
