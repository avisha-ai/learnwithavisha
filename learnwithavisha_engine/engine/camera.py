"""
engine/camera.py — the camera language.

Named behaviours, so an episode asks for a MOVE rather than for numbers:

    {"camera": "slow_push_in", "target": "operator_01"}

Each behaviour returns f(u) -> (centre_x, centre_y, width) for u in [0, 1]
across its own shot. Framing is derived from the target through the world
registry, so Episode 7 can point the same move at a different machine in a
different bay and get the same grammar back.

Only three behaviours exist, because Pilot 001 only uses three. Adding
follow_character or return_to_wide before a story needs one would be
guessing at what that story wants.
"""

BEHAVIOURS = {}


def behaviour(fn):
    BEHAVIOURS[fn.__name__] = fn
    return fn


def _ease(a):
    return a * a * (3.0 - 2.0 * a)


@behaviour
def wide_establishing(world, shot, start_framing=None):
    """Hold the whole location. The frame drifts about two per cent across
    the shot — enough that the image is alive, far too little to read as a
    move. Nothing here is allowed to foreshadow."""
    cx, cy, w = world.location.framing(shot.get("framing", "establishing"))
    drift = shot.get("drift", [0.45, -0.05, -0.35])

    def f(u):
        return cx + drift[0] * u, cy + drift[1] * u, w + drift[2] * u
    return f


@behaviour
def slow_push_in(world, shot, start_framing=None):
    """Move in on a target and settle. Patient and eased, never a zoom.

    The end frame carries LEAD ROOM: it sits offset toward whatever the
    subject is attending to, so when a person stops and looks there is space
    in front of the look. That offset is the reusable part.
    """
    if start_framing is None:
        start_framing = world.location.framing("establishing")
    sx, sy, sw = start_framing
    tx, ty, _ = world.resolve(shot["target"])
    lead = shot.get("lead_room", -0.90)
    ex = shot.get("end_centre", [tx + lead, ty])[0]
    ey = shot.get("end_centre", [tx + lead, ty])[1]
    ew = shot.get("end_width", 9.05)
    settle = shot.get("settle", 0.59)          # fraction of the shot moving

    def f(u):
        a = _ease(min(1.0, u / settle)) if settle > 0 else 1.0
        return (sx + (ex - sx) * a, sy + (ey - sy) * a, sw + (ew - sw) * a)
    return f


@behaviour
def instrument_closeup(world, shot, start_framing=None):
    """Sit on one instrument close enough to read it. Arrives as a CUT —
    a push would make the reading feel like a reveal, and this reading is
    supposed to feel like something he simply noticed."""
    i = world.location.instrument(shot["target"])
    off = shot.get("offset", [-0.02, -0.095])
    w0 = shot.get("width", 1.66)
    w1 = shot.get("end_width", 1.61)

    def f(u):
        return i["x"] + off[0], i["y"] + off[1], w0 + (w1 - w0) * u
    return f


class CameraTrack:
    """Resolves the episode's shot list into a framing at any time t."""

    def __init__(self, world, shots):
        self.world = world
        self.shots = shots
        self._fns = []
        prev_end = None
        for s in shots:
            fn = BEHAVIOURS[s["camera"]](
                world, s,
                start_framing=prev_end if s.get("transition") == "continuous"
                else None)
            self._fns.append(fn)
            prev_end = fn(1.0)

    def at(self, t):
        for s, fn in zip(self.shots, self._fns):
            if t < s["end"] or s is self.shots[-1]:
                span = s["end"] - s["start"]
                u = 0.0 if span <= 0 else min(1.0, max(0.0,
                                                       (t - s["start"]) / span))
                return fn(u)
        return self._fns[-1](1.0)

    def shot_at(self, t):
        for s in self.shots:
            if t < s["end"] or s is self.shots[-1]:
                return s
        return self.shots[-1]
