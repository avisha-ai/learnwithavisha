"""
Style frames for ep001_the_eleven_day_creep, rendered FROM the recipe.

Nothing here draws anything. Each class names a moment; the world supplies
the bay, E-101, Wade and the gauge, and the camera behaviour named in
episode.json decides the framing.

    manim -s -qh style_frame.py StyleFrameA    Shot 1 — ordinary morning
    manim -s -qh style_frame.py StyleFrameB    Shot 2 — the second look
    manim -s -qh style_frame.py StyleFrameC    Shot 3 — the readings arriving
    manim -s -qh style_frame.py StyleFrameD    the unresolved question
"""

import json
import os
import sys

sys.path.insert(0, os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from manim import *                                          # noqa: E402
import engine.draw as draw                                   # noqa: E402
from engine.scene import StyleFrame                           # noqa: E402

config.background_color = draw.BRAND_DEEP

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "episode.json")) as _f:
    EPISODE = json.load(_f)


class StyleFrameA(StyleFrame):
    """Shot 1. He is walking his normal rounds and nothing is wrong yet."""
    EPISODE = EPISODE
    AT = 6.0


class StyleFrameB(StyleFrame):
    """Shot 2, held. He has stopped, turned back, and looked again."""
    EPISODE = EPISODE
    AT = 17.0


class StyleFrameC(StyleFrame):
    """Shot 3. 87 on the instrument, and the log arriving one row at a time.
    Caught here at 22.6 s: 83 and 85 are up, 87 is still fading in."""
    EPISODE = EPISODE
    AT = 22.6


class StyleFrameD(MovingCameraScene):
    """The unresolved question. White on black, after the picture is gone."""

    def construct(self):
        card = EPISODE["end_card"]
        f = self.camera.frame
        f.set(width=14.6).move_to(ORIGIN)
        self.add(Rectangle(width=20, height=12).set_stroke(width=0)
                 .set_fill("#000000", 1))
        head, tail = card["text"].split("—", 1)
        g = VGroup(Text(head.strip() + " —", font_size=30, color="#e9edf2"),
                   Text(tail.strip(), font_size=30, color="#e9edf2")
                   ).arrange(DOWN, buff=0.34)
        g.set(width=f.width * 0.62).move_to(ORIGIN)
        self.add(g)
        self.wait(0.05)
