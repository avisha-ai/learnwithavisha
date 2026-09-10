"""
world/characters/character_sheet.py — the three canonical characters.

Three people, three poses each, lit by the same morning. The point of this
sheet is comparison: if two of them read the same at a glance, the designs
have failed, because in a wide shot that is all the audience gets.

Render: manim -s -qh character_sheet.py CharacterSheet
"""

import os
import sys

sys.path.insert(0, os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from manim import *                                          # noqa: E402
import engine.draw as draw                                   # noqa: E402
from engine.loader import Character                          # noqa: E402

config.background_color = draw.BRAND_DEEP

NAMES = ["wade", "lyra", "ellis"]
POSES = ["neutral", "walking", "inspecting"]
COL_X = {"neutral": -3.20, "walking": 0.80, "inspecting": 4.80}
ROW_Y = {"wade": 4.60, "lyra": 2.05, "ellis": -0.50}


class CharacterSheet(MovingCameraScene):
    def construct(self):
        f = self.camera.frame
        f.set(width=15.4).move_to(np.array([1.5, 2.50, 0.0]))

        self.add(draw.vgradient(-14, 16, -4.0, 9.0, "#151b2b", "#3b3340",
                                bands=30))
        for y in ROW_Y.values():
            self.add(draw.band_rect(-11, 13, y - 0.02, y + 0.015,
                                    draw.STEEL_RIM, 0.16))

        for name in NAMES:
            ch = Character(name)
            y = ROW_Y[name]
            tag = draw.label(ch.data["name"].upper(), (-6.35, y + 1.02),
                             size=20, colour="#cfd6df")
            tag.set_width(1.05)
            tag.move_to(np.array([-5.05, y + 1.30, 0]))
            self.add(tag)
            role = draw.label(ch.data["role"], (0, 0), size=13,
                              colour=draw.TAG_TEXT)
            role.set_width(2.05)
            role.move_to(np.array([-4.72, y + 1.00, 0]))
            self.add(role)

            for pose in POSES:
                p = ch.poses[pose]
                kw = dict(walking=p["walking"], head_pitch=p["head_pitch"],
                          y=y)
                if pose == "walking":
                    kw["phase"] = 0.95
                if pose == "inspecting":
                    kw["facing"] = -1
                self.add(ch.rig.build(COL_X[pose], **kw))

        for pose in POSES:
            for name in NAMES:
                t = draw.label(pose.upper(), (0, 0), size=13,
                               colour="#7f8a9a")
                t.set_width(0.58 * (1.0 if pose != "inspecting" else 1.30))
                t.move_to(np.array([COL_X[pose], ROW_Y[name] - 0.30, 0]))
                self.add(t)
        self.wait(0.05)
