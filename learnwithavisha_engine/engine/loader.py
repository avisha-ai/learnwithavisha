"""
engine/loader.py — the world registry.

The one architectural rule this file exists to enforce:

    EPISODES NEVER OWN ASSETS. THE WORLD OWNS ASSETS.

An episode names a location, some equipment and some characters. It gets
back the canonical ones. There is no way for an episode to pass in its own
drawing, which is what stops the world drifting apart episode by episode.
"""

import importlib.util
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     ".."))
WORLD = os.path.join(ROOT, "world")


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _json(path):
    with open(path) as f:
        return json.load(f)


class Location:
    def __init__(self, name):
        self.name = name
        self.dir = os.path.join(WORLD, "locations", name)
        self.data = _json(os.path.join(self.dir, "location.json"))
        self.background = _module(os.path.join(self.dir, "background.py"),
                                  "loc_%s_background" % name)
        self.pipework = _module(os.path.join(self.dir, "pipework.py"),
                                "loc_%s_pipework" % name)
        self.foreground = _module(os.path.join(self.dir, "foreground.py"),
                                  "loc_%s_foreground" % name)

    def framing(self, key):
        f = self.data["framings"][key]
        return f["centre"][0], f["centre"][1], f["width"]

    def stand_mark(self, key):
        return self.data["stand_marks"]["at_" + key]

    def instrument(self, tag):
        for i in self.data["instruments_placed"]:
            if i["tag"] == tag:
                return i
        raise KeyError("%s is not placed in %s" % (tag, self.name))


class Equipment:
    def __init__(self, tag):
        self.tag = tag
        self.dir = os.path.join(WORLD, "equipment", tag)
        self.metadata = _json(os.path.join(self.dir, "metadata.json"))
        self.exterior = _module(os.path.join(self.dir, "exterior.py"),
                                "eq_%s_exterior" % tag.replace("-", "_"))

    @property
    def geometry(self):
        return self.metadata["geometry"]

    def extent(self):
        g = self.geometry
        return (g["head_x0"], g["bonnet_x1"], g["ycl"])


class Character:
    def __init__(self, name):
        self.name = name
        self.dir = os.path.join(WORLD, "characters", name)
        self.data = _json(os.path.join(self.dir, "character.json"))
        self.poses = _json(os.path.join(self.dir, "poses.json"))
        self.rig = _module(os.path.join(self.dir, "rig.py"),
                           "ch_%s_rig" % name)
        lp = os.path.join(self.dir, "log_sheet.py")
        self.log_sheet = _module(lp, "ch_%s_log" % name) \
            if os.path.exists(lp) else None


class Instrument:
    def __init__(self, asset):
        self.asset = asset
        self.module = _module(os.path.join(WORLD, "instruments",
                                           asset + ".py"), "inst_" + asset)
        self.style = _json(os.path.join(WORLD, "instruments", asset + ".json"))


class World:
    """Everything an episode is allowed to reach for."""

    def __init__(self, episode):
        self.episode = episode
        self.location = Location(episode["location"])
        self.equipment = {t: Equipment(t) for t in episode.get("equipment", [])}
        self.characters = {c: Character(c)
                           for c in episode.get("characters", [])}
        self.instruments = {}
        for i in self.location.data["instruments_placed"]:
            a = i["asset"]
            if a not in self.instruments:
                self.instruments[a] = Instrument(a)

    def resolve(self, name):
        """A target name -> (x, y, extent). Cameras aim with this."""
        if name == self.location.name:
            cx, cy, w = self.location.framing("establishing")
            return cx, cy, w
        if name in self.equipment:
            x0, x1, ycl = self.equipment[name].extent()
            return (x0 + x1) / 2.0, ycl, x1 - x0
        if name in self.characters:
            # A character resolves to the mark he ends the shot on, so a
            # camera can be aimed at a person without knowing the blocking.
            mark = self.episode["blocking"][name]["stands_at"]
            m = self.location.data["stand_marks"][mark]
            return m["x"], m.get("frame_y", 1.72), 1.8
        try:
            i = self.location.instrument(name)
            return i["x"], i["y"], 0.36
        except KeyError:
            pass
        raise KeyError("cannot resolve target %r" % name)


def load_episode(path):
    return _json(path)
