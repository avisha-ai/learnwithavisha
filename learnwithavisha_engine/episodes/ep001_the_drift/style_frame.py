"""
DELIVERABLE — style frame for ep001_the_drift, rendered FROM the recipe.

This is the proof that the architecture works. Nothing in this file draws
anything. It names an episode and a moment; the world supplies the bay,
E-101, the operator and the gauge, and the camera behaviour named in
episode.json decides the framing.

Render: manim -s -qh style_frame.py StyleFrameA
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
    """Shot 1. Ordinary morning, mid-route."""
    EPISODE = EPISODE
    AT = 6.5


class StyleFrameB(StyleFrame):
    """Shot 2, held. He has stopped and turned back to the gauge."""
    EPISODE = EPISODE
    AT = 18.6
