"""
DELIVERABLE C — Visual Pilot 001, the three-shot test. 27.000 s.

    Shot 1  0.0 - 10.5   The plant is normal.
    Shot 2 10.5 - 19.0   Something earns his attention.
    Shot 3 19.0 - 27.0   The number.

What this sequence is testing is whether a two-degree drift can hold a
viewer without an alarm, a red light, a warning graphic or a music cue.
So the discipline is subtraction:

  • Nothing in Shot 1 foreshadows. The camera drift is 2% over ten seconds.
  • The tension in Shot 2 is carried by ONE event: an experienced man stops
    walking. He glances at TI-1014 in passing, takes two more paces, and
    then stops. The stop is the whole shot. Everything else holds still so
    that it registers.
  • Shot 3 shows the reading and the log sheet and says nothing about them.
    No highlight, no arrow, no colour on the numbers. 87, 85, 83, and the
    viewer does the arithmetic.

Every cue below is an ABSOLUTE timestamp in seconds. One ValueTracker drives
the whole film so that picture and the procedurally generated sound bed stay
locked to the same clock.

Render: manim -qh pilot001.py Pilot001
"""

import math

from manim import *
import plant_world as w
import bay


def live(scene, build):
    """A group rebuilt every frame WITHOUT Manim's always_redraw.

    always_redraw drives the update through Mobject.become(), which aligns
    the old family against the new one and pads the point arrays when they
    do not match exactly. Over sixteen hundred frames that padding grows
    without bound and the render time per frame climbs with it — the reason
    a two minute job was taking forty. Swapping the submobject list outright
    costs nothing and stays flat.
    """
    holder = VGroup()

    def _upd(m):
        m.submobjects = build().submobjects
    holder.add_updater(_upd)
    scene.add(holder)
    return holder

config.background_color = w.BRAND_DEEP

import os
RUNTIME = float(os.environ.get("LWA_RUNTIME", "27.0"))

WALK_SPEED = 0.60          # m/s. A man on his own route, not hurrying.
STOP_T = 15.40             # he stops here
STOP_X = 2.85              # standing clear of the channel head
STRIDE = 1.44              # metres per full gait cycle
GAUGE_X = 1.18             # TI-1014 display centre


def ease(a):
    return a * a * (3.0 - 2.0 * a)


def seg(t, t0, t1, v0, v1, smooth=True):
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    a = (t - t0) / (t1 - t0)
    return v0 + (v1 - v0) * (ease(a) if smooth else a)


def camera_at(t):
    """(centre_x, centre_y, width). The cut at 19.0 is a hard cut."""
    if t < 10.5:                                   # Shot 1 — barely moving
        return (seg(t, 0, 10.5, 2.35, 2.80, False),
                seg(t, 0, 10.5, 2.05, 2.00, False),
                seg(t, 0, 10.5, 14.60, 14.25, False))
    if t < 19.0:                                   # Shot 2 — patient push
        return (seg(t, 10.5, 15.5, 2.80, 1.95),
                seg(t, 10.5, 15.5, 2.00, 1.72),
                seg(t, 10.5, 15.5, 14.25, 9.05))
    return (1.16,                                  # Shot 3 — cut to the gauge
            seg(t, 19.0, 27.0, 2.055, 2.030, False),
            seg(t, 19.0, 27.0, 1.66, 1.61, False))


def operator_at(t):
    """(x, phase, facing, walking, head_pitch, turn_squash)."""
    x = min(STOP_X, STOP_X - WALK_SPEED * (STOP_T - t))
    walking = t < STOP_T
    phase = 2 * PI * (x + 6.39) / STRIDE

    # The glance in passing. He does not break stride for it.
    pitch = 0.0
    if t < STOP_T:
        pitch = seg(t, 12.50, 13.20, 0.0, 14.0) - seg(t, 13.70, 14.30, 0.0, 14.0)

    # The turn, then the second look.
    facing, squash = 1, 1.0
    if t >= 17.00:
        a = min(1.0, (t - 17.00) / 0.45)
        facing = 1 if a < 0.5 else -1
        squash = max(0.12, abs(math.cos(PI * a)))
        if t >= 17.45:
            facing, squash = -1, 1.0
            pitch = seg(t, 17.45, 18.40, 0.0, 27.0)
    return x, phase, facing, walking, pitch, squash


class Pilot001(MovingCameraScene):
    def construct(self):
        f = self.camera.frame
        T = ValueTracker(0.0)
        cx, cy, cw = camera_at(0.0)
        f.set(width=cw).move_to(np.array([cx, cy, 0.0]))

        # ── the bay, rebuilt only where it moves ──────────────────
        static = bay.assemble(t=0.0)
        for k in ("sky", "shafts"):
            self.add(static[k])

        self.add(w.build_far())
        live(self, lambda: VGroup(
            w.steam_column(-4.1, 3.2, T.get_value(), n=10, rise=3.0, size=0.52,
                           peak=0.055, drift=1.9, spread=0.62, seed=0.62),
            w.steam_column(8.55, 7.5, T.get_value(), n=10, rise=3.4, size=0.34,
                           peak=0.045, drift=2.2, spread=0.75, seed=0.11),
            w.steam_column(-2.35, 0.70, T.get_value(), n=9, rise=3.2, size=0.26,
                           peak=0.115, drift=1.2, spread=0.38, seed=0.05),
        ))
        self.add(static["haze_far"])
        self.add(w.build_structure())
        live(self, lambda: VGroup(
            w.steam_column(-1.25, w.RACK_Y + 1.7, T.get_value(), n=7, rise=2.1,
                           size=0.15, peak=0.10, drift=0.8, spread=0.28,
                           seed=0.37),
        ))
        self.add(static["haze_mid"])
        self.add(static["near"])
        live(self, lambda: VGroup(
            w.steam_column(-5.0, -1.4, T.get_value(), n=6, rise=1.5, size=0.85,
                           peak=0.030, drift=3.4, spread=0.40, seed=0.83),
            w.steam_column(7.5, -1.9, T.get_value(), n=6, rise=1.3, size=0.80,
                           peak=0.026, drift=3.0, spread=0.35, seed=0.29),
        ))

        # ── OPERATOR_01 ───────────────────────────────────────────
        def draw_op():
            # Constant structure every frame — see the note in steam_column.
            # Out of shot he is built and faded, never removed.
            t = min(T.get_value(), 18.999)
            x, ph, facing, walking, pitch, squash = operator_at(t)
            g = w.build_operator(x, phase=ph, facing=facing, walking=walking,
                                 head_pitch=pitch)
            if squash < 0.999:
                g.stretch(squash, dim=0, about_point=np.array([x, 0.9, 0.0]))
            if T.get_value() >= 19.0:
                g.set_opacity(0.0)                 # Shot 3 is on the gauge
            return g
        live(self, draw_op)

        # ── his log sheet, Shot 3 only ────────────────────────────
        # Built once and moved, not rebuilt. It carries seven Text
        # mobjects and Pango is by far the most expensive thing per frame.
        log = w.build_logsheet(1.63, 2.00, scale=0.40)
        log_home = log.get_center()

        def move_log(m):
            t = T.get_value()
            y = (seg(t, 20.30, 21.70, 1.24, 2.00)
                 - seg(t, 24.20, 25.40, 0.0, 0.76))
            m.move_to(log_home + np.array([0.0, y - 2.00, 0.0]))
            m.set_opacity(0.0 if (t < 20.10 or t > 25.60) else 1.0)
        log.add_updater(move_log)
        self.add(log)

        # ── watermark, brand rule, on every frame ─────────────────
        wm = w.build_watermark()
        base_w = wm.width

        def pin(m):
            _, _, width = camera_at(T.get_value())
            s = width / config.frame_width
            m.set(width=base_w * s)
            m.move_to(f.get_corner(DR) + s * (UP + LEFT) * 0.77)
        wm.add_updater(pin)
        self.add(wm)

        # ── camera and fades ──────────────────────────────────────
        def move_cam(m):
            x, y, width = camera_at(T.get_value())
            m.set(width=width).move_to(np.array([x, y, 0.0]))
        # The camera frame is NOT in Scene.mobjects by default, so an updater
        # attached to it never fires and the whole film renders at the Shot 1
        # framing. It has to be added for the push and the cut to happen.
        self.add(f)
        f.add_updater(move_cam)

        black = Rectangle(width=1, height=1).set_stroke(width=0)
        black.set_fill("#000000", 1).set_z_index(200)

        def fade(m):
            t = T.get_value()
            o = 1.0 - seg(t, 0.0, 1.60, 0.0, 1.0) + seg(t, 26.00, 27.00, 0.0, 1.0)
            m.set_opacity(min(1.0, max(0.0, o)))
            m.set(width=f.width * 1.1, height=f.height * 1.1)
            m.move_to(f.get_center())
        black.add_updater(fade)
        self.add(black)

        self.play(T.animate.set_value(RUNTIME), run_time=RUNTIME,
                  rate_func=linear)
