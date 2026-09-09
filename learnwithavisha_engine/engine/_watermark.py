"""engine/_watermark.py — brand rule: LWA monogram, bottom right, always."""

from engine.draw import *


def build_watermark():
    ring = Circle(radius=0.42, fill_opacity=0)
    ring.set_stroke(WHITE, width=1.2, opacity=0.85)
    mono = Text("LWA", font="Georgia", slant=ITALIC, font_size=17, color=WHITE)
    mono.move_to(ring.get_center())
    mono.set_opacity(0.85)
    wm = VGroup(ring, mono)
    wm.set_z_index(100)
    return wm


def pin_watermark(wm, frame, base_width):
    def _upd(m):
        s = frame.width / config.frame_width
        m.set(width=base_width * s)
        m.move_to(frame.get_corner(DR) + s * (UP + LEFT) * 0.77)
    return _upd
