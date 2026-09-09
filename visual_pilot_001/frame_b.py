"""
DELIVERABLE B — character / world consistency frame.

Second camera setup on the same bay: closer, lower, at the channel-head end,
with OPERATOR_01 stopped at TI-1014 rather than walking past it.

Honest about what this is. The world is drawn, not projected, so this is a
second COMPOSITION of the same canonical assets rather than a reprojection
of a 3D set. What it tests is the thing that actually breaks illustrated
worlds: does the equipment still read as the same machine at three times the
size, does the light still come from one place, and does the operator still
look like he belongs on that deck when he is big enough to see properly.

Render: manim -s -qh frame_b.py FrameB
"""

from manim import *
import plant_world as w
import bay

config.background_color = w.BRAND_DEEP


class FrameB(MovingCameraScene):
    def construct(self):
        f = self.camera.frame
        f.set(width=8.8).move_to(np.array([1.55, 1.58, 0.0]))

        L = bay.assemble(t=21.4)
        bay.add_bay(self, L)

        # Stopped, turned back, reading TI-1014. This is the second look.
        self.add(w.build_operator(2.88, phase=0.0, facing=-1, walking=False,
                                  head_pitch=26.0))
        bay.place_watermark(self, f)
        self.wait(0.05)
