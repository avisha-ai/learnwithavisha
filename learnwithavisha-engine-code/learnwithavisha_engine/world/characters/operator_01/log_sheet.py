"""
world/characters/operator_01/log_sheet.py

His log sheet. It belongs to the character, not to the episode, because
check_log() is a character action and he carries the same board everywhere.

Deliberately not an infographic: no highlight, no arrow, no colour on the
numbers. Three handwritten readings, and the reader does the arithmetic.
"""

from engine.draw import *


def build(x, y, scale=1.0, rows=(("09 SEP", "87"), ("08 SEP", "85"),
                                          ("07 SEP", "83"))):
    """His log sheet, held up beside the instrument.

    Deliberately not an infographic: no highlight, no arrow, no colour on the
    numbers. Three handwritten readings and the reader does the arithmetic.
    """
    g = VGroup()
    s_ = scale
    bw, bh = 1.05 * s_, 1.42 * s_
    g.add(band_rect(x - bw / 2, x + bw / 2, y - bh / 2, y + bh / 2, "#20252d"))
    g.add(band_rect(x - bw / 2, x - bw / 2 + 0.028 * s_, y - bh / 2,
                    y + bh / 2, STEEL_RIM, 0.40))
    pw, ph = bw - 0.10 * s_, bh - 0.16 * s_
    g.add(band_rect(x - pw / 2, x + pw / 2, y - ph / 2 - 0.02 * s_,
                    y + ph / 2 - 0.02 * s_, "#9aa3ae"))
    g.add(band_rect(x - pw / 2, x - pw / 2 + 0.022 * s_,
                    y - ph / 2 - 0.02 * s_, y + ph / 2 - 0.02 * s_,
                    "#c6ccd4"))
    g.add(band_rect(x - bw * 0.20, x + bw * 0.20, y + bh / 2 - 0.13 * s_,
                    y + bh / 2 - 0.02 * s_, "#4d5563"))

    hd = label("E-101   TI-1014", (x, y + ph / 2 - 0.20 * s_), size=20,
               colour="#2b313a")
    hd.set_width(pw * 0.66)
    hd.move_to(np.array([x - pw * 0.04, y + ph / 2 - 0.21 * s_, 0]))
    g.add(hd)
    g.add(band_rect(x - pw * 0.40, x + pw * 0.40, y + ph / 2 - 0.28 * s_,
                    y + ph / 2 - 0.272 * s_, "#6b7382"))
    for i2, (day, val) in enumerate(rows):
        ry = y + ph / 2 - 0.42 * s_ - i2 * 0.245 * s_
        d_ = label(day, (0, 0), size=18, colour="#3a414c")
        d_.set_width(pw * 0.34)
        d_.move_to(np.array([x - pw * 0.21, ry, 0]))
        g.add(d_)
        v_ = label(val, (0, 0), size=22, colour="#22272f")
        v_.set_width(pw * 0.155)
        v_.move_to(np.array([x + pw * 0.26, ry, 0]))
        g.add(v_)
    # his thumb on the board
    th = Ellipse(width=0.20 * s_, height=0.34 * s_)
    th.set_stroke(width=0).set_fill(SKIN, 1)
    th.rotate(-0.30).move_to(np.array([x - bw / 2 + 0.05 * s_,
                                       y - bh * 0.16, 0]))
    g.add(th)
    return g
