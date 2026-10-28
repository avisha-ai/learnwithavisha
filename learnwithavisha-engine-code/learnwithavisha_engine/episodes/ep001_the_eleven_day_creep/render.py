"""
ep001_the_eleven_day_creep — the film.

Nothing here describes the story. episode.json does that. This file exists
only to point Manim at it.

    manim -qh render.py Ep001            # picture
    python -m engine.sound               # world stems, if they are missing
    ./finish.sh                          # grade, pad to length, lay back sound
"""

import json
import os
import sys

sys.path.insert(0, os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))

from manim import *                                          # noqa: E402
import engine.draw as draw                                   # noqa: E402
from engine.scene import Film                                 # noqa: E402

config.background_color = draw.BRAND_DEEP

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "episode.json")) as _f:
    EPISODE = json.load(_f)


class Ep001(Film):
    EPISODE = EPISODE
