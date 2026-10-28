"""
engine/actions.py — the character's vocabulary.

An episode writes behaviour, not keyframes:

    {"t": 12.5, "who": "operator_01", "action": "look_at", "target": "TI-1014"}

Each action resolves into rig parameters over time. The rig never invents a
number: every pose it can hold is named in the character's poses.json, and
an action only decides WHEN he is in one and how he gets there.

Five actions exist because Pilot 001 uses five. turn_away() is deliberately
absent — he never turns away in this story, and writing it now would be
guessing at how the next one ends.
"""

import math

ACTIONS = {}


def action(fn):
    ACTIONS[fn.__name__] = fn
    return fn


def ease(a):
    return a * a * (3.0 - 2.0 * a)


def ramp(t, t0, t1, v0, v1, smooth=True):
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    a = (t - t0) / (t1 - t0)
    return v0 + (v1 - v0) * (ease(a) if smooth else a)


# ── the five ─────────────────────────────────────────────────────
@action
def walk_to(state, ev, t, world):
    """His normal route. Constant pace, arriving on the mark at `arrive`.

    He does not hurry and he does not slow down for the machine, because
    at this point in the story nothing has happened.
    """
    pose = state["poses"]["walking"]
    mark = world.location.data["stand_marks"][ev["mark"]]
    speed = pose["speed_mps"]
    x = min(mark["x"], mark["x"] - speed * (ev["arrive"] - t))
    state["x"] = x
    state["walking"] = t < ev["arrive"]
    state["phase"] = 2 * math.pi * (x - ev.get("from_x", -6.39)) \
        / pose["stride_m"]
    state["facing"] = 1


@action
def stop(state, ev, t, world):
    """He stops. In this film that is the entire second shot: everything
    else is holding still so that one man ending his stride registers."""
    if t >= ev["t"]:
        state["walking"] = False


@action
def look_at(state, ev, t, world):
    """The habitual glance, taken without breaking stride. Up, and back."""
    up, dwell = ev.get("rise", 0.70), ev.get("hold", 0.50)
    p = state["poses"]["glancing"]["head_pitch"]
    state["head_pitch"] += (
        ramp(t, ev["t"], ev["t"] + up, 0.0, p)
        - ramp(t, ev["t"] + up + dwell, ev["t"] + up + dwell + 0.60, 0.0, p))


@action
def second_glance(state, ev, t, world):
    """The one that matters. He turns his body back and looks again.

    The turn is played as a horizontal squash through zero, which is how a
    two-dimensional figure reads as pivoting. It is quick — 0.45 s — because
    a slow turn would look like a decision, and this is a reflex.
    """
    t0 = ev["t"]
    turn = ev.get("turn", 0.45)
    if t < t0:
        return
    a = min(1.0, (t - t0) / turn)
    state["facing"] = 1 if a < 0.5 else -1
    state["squash"] = max(0.12, abs(math.cos(math.pi * a))) if a < 1.0 else 1.0
    if t >= t0 + turn:
        state["facing"], state["squash"] = -1, 1.0
        state["head_pitch"] = ramp(t, t0 + turn, t0 + turn + 0.95, 0.0,
                                   state["poses"]["inspecting"]["head_pitch"])


@action
def check_log(state, ev, t, world):
    """He brings the log sheet up beside the instrument, and takes it down.

    The action owns both halves: his pose, and the board itself. Nothing in
    the episode places the prop, because the prop belongs to him.
    """
    up0, up1 = ev["t"], ev["t"] + ev.get("raise", 1.40)
    dn0 = ev["until"] - ev.get("lower", 1.20)
    y = (ramp(t, up0, up1, ev.get("low_y", 1.24), ev.get("high_y", 2.00))
         - ramp(t, dn0, ev["until"], 0.0,
                ev.get("high_y", 2.00) - ev.get("low_y", 1.24)))
    # the readings arrive one at a time, oldest first
    step = ev.get("row_every", 1.00)
    first = ev.get("rows_from", up1 + 0.40)
    n = ev.get("rows", 3)
    rows_visible = 0.0
    for k in range(n):
        rows_visible += ramp(t, first + k * step, first + k * step + 0.45,
                             0.0, 1.0)
    state["log_sheet"] = {
        "visible": (ev["t"] - 0.20) <= t <= (ev["until"] + 0.20),
        "x": ev.get("x", 1.63), "y": y, "scale": ev.get("scale", 0.40),
        "rows_visible": rows_visible}
    if ev["t"] <= t <= ev["until"]:
        state["head_pitch"] = state["poses"]["checking_log"]["head_pitch"]


class ActionTrack:
    """Resolves one character's timeline into rig parameters at any time t."""

    def __init__(self, world, character, timeline):
        self.world = world
        self.character = character
        self.events = [e for e in timeline if e["who"] == character.name]

    def at(self, t):
        state = {"poses": self.character.poses, "x": 0.0, "phase": 0.0,
                 "facing": 1, "walking": True, "head_pitch": 0.0,
                 "clipboard": 0.0, "squash": 1.0,
                 "log_sheet": {"visible": False, "x": 0.0, "y": 0.0,
                               "scale": 0.40, "rows_visible": 3.0}}
        for ev in self.events:
            ACTIONS[ev["action"]](state, ev, t, self.world)
        return state

    def footstep_times(self, until):
        """When his feet actually land. The sound mix reads this, so the
        footsteps can never drift out of step with the picture."""
        walk = [e for e in self.events if e["action"] == "walk_to"]
        if not walk:
            return []
        ev = walk[0]
        pose = self.character.poses["walking"]
        step = 0.5 * pose["stride_m"] / pose["speed_mps"]
        out, k = [], 0
        while k * step <= min(ev["arrive"], until):
            out.append(k * step)
            k += 1
        return out
