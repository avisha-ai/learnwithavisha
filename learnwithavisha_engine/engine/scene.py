"""
engine/scene.py — turns an episode recipe into frames.

The episode says what happens. This file is the only place that knows how a
Manim scene is put together, so an episode never touches the renderer.

Layer order is the whole trick, far to near:

    sky -> shafts -> far -> haze -> mid -> haze -> near -> drift -> fore

Two rules hold it together. The sky is the brightest value in frame and the
plant silhouettes against it. Distance is loss of contrast, never a change
in light direction.
"""

import math
import os

from manim import *

from engine import _watermark
from engine.actions import ActionTrack
from engine.camera import CameraTrack
from engine.loader import World
import engine.draw as draw


def live(scene, build):
    """A group rebuilt every frame WITHOUT Manim's always_redraw.

    always_redraw drives updates through Mobject.become(), which aligns the
    old family against the new one and pads the point arrays when they do not
    match. Over sixteen hundred frames that padding grows without bound and
    the render time per frame climbs with it. Swapping the submobject list
    outright costs nothing and stays flat.
    """
    holder = VGroup()

    def _upd(m):
        m.submobjects = build().submobjects
    holder.add_updater(_upd)
    scene.add(holder)
    return holder


class Stage:
    """One episode, assembled. Both the style frame and the film use this."""

    def __init__(self, episode):
        self.episode = episode
        self.world = World(episode)
        self.camera_track = CameraTrack(self.world, episode["shots"])
        self.tracks = {
            name: ActionTrack(self.world, ch, episode.get("timeline", []))
            for name, ch in self.world.characters.items()}

    # ── the location, in layers ──────────────────────────────────
    def _steam(self, layer, t):
        g = VGroup()
        for s in self.world.location.data["steam"]:
            if s["layer"] != layer:
                continue
            g.add(draw.steam_column(s["x"], s["y"], t, n=s["n"],
                                    rise=s["rise"], size=s["size"],
                                    peak=s["peak"], drift=s["drift"],
                                    spread=s["spread"], seed=s["seed"]))
        return g

    def _shafts(self):
        g = VGroup()
        for s in self.world.location.data["light_shafts"]:
            g.add(draw.light_shaft(
                s["x_top"], spread=s["spread"], width=s["width"],
                opacity=s["opacity"],
                y_bot=self.world.location.data["ground"]["deck_near_y"]))
        return g

    def _near(self):
        """Equipment, its pipework and its instruments — one plane."""
        loc, g = self.world.location, VGroup()
        g.add(loc.pipework.build_pipework())
        for tag, eq in self.world.equipment.items():
            g.add(eq.exterior.build())
        readings = self.episode.get("readings", {})
        for i in loc.data["instruments_placed"]:
            inst = self.world.instruments[i["asset"]].module
            if i["style"] == "digital":
                val = str(readings.get(i["tag"], {}).get("now", ""))
                g.add(inst.build_digital(val, i["x"] + 0.44, y=i["y"]))
            else:
                g.add(inst.build_dial(i["tag"], i["x"], i["y"],
                                      r=i["r"], frac=i["frac"]))
        g.add(loc.foreground.build_handrail())
        g.add(loc.foreground.build_walkway())
        return g

    def add_location(self, scene, t=0.0, animated=False):
        loc = self.world.location
        scene.add(loc.background.build_sky())
        scene.add(self._shafts())
        scene.add(loc.background.build_far())
        if animated:
            live(scene, lambda: self._steam("far", scene.T.get_value()))
        else:
            scene.add(self._steam("far", t))
        scene.add(draw.haze_sheet(loc.data["haze"]["haze_far"]))
        scene.add(loc.background.build_structure())
        if animated:
            live(scene, lambda: self._steam("mid", scene.T.get_value()))
        else:
            scene.add(self._steam("mid", t))
        scene.add(draw.haze_sheet(loc.data["haze"]["haze_mid"]))
        scene.add(self._near())
        if animated:
            live(scene, lambda: self._steam("drift", scene.T.get_value()))
        else:
            scene.add(self._steam("drift", t))

    # ── the character ────────────────────────────────────────────
    def character_at(self, name, t):
        ch = self.world.characters[name]
        st = self.tracks[name].at(t)
        g = ch.rig.build(st["x"], phase=st["phase"], facing=st["facing"],
                         walking=st["walking"], head_pitch=st["head_pitch"],
                         clipboard=st["clipboard"])
        if st["squash"] < 0.999:
            g.stretch(st["squash"], dim=0,
                      about_point=np.array([st["x"], 0.9, 0.0]))
        return g, st

    def log_sheet_at(self, name, st):
        ch = self.world.characters[name]
        if ch.log_sheet is None:
            return VGroup()
        g = ch.log_sheet.build(st["log_sheet"]["x"], st["log_sheet"]["y"],
                               scale=st["log_sheet"]["scale"],
                               rows_visible=st["log_sheet"]["rows_visible"])
        if not st["log_sheet"]["visible"]:
            g.set_opacity(0.0)
        return g

    # ── brand ────────────────────────────────────────────────────
    def add_watermark(self, scene, frame, static_width=None):
        wm = _watermark.build_watermark()
        base = wm.width
        if static_width is not None:
            s = static_width / config.frame_width
            wm.set(width=base * s)
            wm.move_to(frame.get_corner(DR) + s * (UP + LEFT) * 0.77)
            scene.add(wm)
            return wm

        def pin(m):
            _, _, width = self.camera_track.at(scene.T.get_value())
            s = width / config.frame_width
            m.set(width=base * s)
            m.move_to(frame.get_corner(DR) + s * (UP + LEFT) * 0.77)
        wm.add_updater(pin)
        scene.add(wm)
        return wm


class StyleFrame(MovingCameraScene):
    """One held moment, rendered from the recipe. Renders with `manim -s`."""

    EPISODE = None
    AT = 5.0

    def construct(self):
        stage = Stage(self.EPISODE)
        cx, cy, w = stage.camera_track.at(self.AT)
        f = self.camera.frame
        f.set(width=w).move_to(np.array([cx, cy, 0.0]))

        stage.add_location(self, t=self.AT, animated=False)
        for name in stage.world.characters:
            g, st = stage.character_at(name, self.AT)
            self.add(g)
            self.add(stage.log_sheet_at(name, st))
        self.add(stage.world.location.foreground.build_foreground())
        self.add(stage.world.location.foreground.build_proscenium())
        stage.add_watermark(self, f, static_width=w)
        self.wait(0.05)


class Film(MovingCameraScene):
    """The episode, moving. Nothing below is episode-specific: the shots,
    the blocking and the timing all come out of the recipe.

    One ValueTracker drives everything, so the picture and the sound mix
    share a single clock and cannot drift apart.
    """

    EPISODE = None

    def construct(self):
        stage = Stage(self.EPISODE)
        ep = self.EPISODE
        runtime = float(os.environ.get("LWA_RUNTIME", ep["runtime"]))
        self.T = ValueTracker(0.0)
        f = self.camera.frame
        cx, cy, w = stage.camera_track.at(0.0)
        f.set(width=w).move_to(np.array([cx, cy, 0.0]))

        stage.add_location(self, animated=True)

        for name in stage.world.characters:
            def draw_ch(n=name):
                g, st = stage.character_at(n, min(self.T.get_value(),
                                                  ep["shots"][-1]["start"]
                                                  - 0.001))
                if self.T.get_value() >= ep["shots"][-1]["start"]:
                    g.set_opacity(0.0)      # the last shot is on the gauge
                return g
            live(self, draw_ch)

            ch = stage.world.characters[name]
            if ch.log_sheet is not None:
                def draw_sheet(n=name):
                    st = stage.tracks[n].at(self.T.get_value())
                    if not st["log_sheet"]["visible"]:
                        return VGroup()
                    return stage.log_sheet_at(n, st)
                live(self, draw_sheet)

        loc = stage.world.location
        self.add(loc.foreground.build_foreground())
        self.add(loc.foreground.build_proscenium())

        # The camera frame is NOT in Scene.mobjects by default, so an updater
        # on it never fires and the whole film renders at the opening framing.
        self.add(f)

        def move_cam(m):
            x, y, width = stage.camera_track.at(self.T.get_value())
            m.set(width=width).move_to(np.array([x, y, 0.0]))
        f.add_updater(move_cam)

        stage.add_watermark(self, f)

        fade = ep["fade"]
        black = Rectangle(width=1, height=1).set_stroke(width=0)
        black.set_fill("#000000", 1).set_z_index(200)

        def do_fade(m):
            t = self.T.get_value()
            o = (1.0 - np.interp(t, fade["in"], [0.0, 1.0])
                 + np.interp(t, fade["out"], [0.0, 1.0]))
            m.set_opacity(float(min(1.0, max(0.0, o))))
            m.set(width=f.width * 1.1, height=f.height * 1.1)
            m.move_to(f.get_center())
        black.add_updater(do_fade)
        self.add(black)

        card_cfg = ep.get("end_card")
        if card_cfg:
            # White on black, after the picture has gone. Two lines, because
            # one long line reads as a caption and this is the question the
            # whole episode was built to leave behind.
            head, tail = card_cfg["text"].split("—", 1)
            card = VGroup(
                Text(head.strip() + " —", font_size=30, color="#e9edf2"),
                Text(tail.strip(), font_size=30, color="#e9edf2"),
            ).arrange(DOWN, buff=0.34)
            card.set_z_index(210)

            def do_card(m):
                t = self.T.get_value()
                m.set(width=f.width * 0.62)
                m.move_to(f.get_center())
                a = card_cfg["at"]
                o = 0.0 if t < a else min(
                    1.0, (t - a) / max(card_cfg.get("fade_in", 0.7), 1e-6))
                m.set_opacity(float(o))
            card.add_updater(do_card)
            self.add(card)

        self.play(self.T.animate.set_value(runtime), run_time=runtime,
                  rate_func=linear)
