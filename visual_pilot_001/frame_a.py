"""
DELIVERABLE A — style frame.
The exchanger bay, E-101, OPERATOR_01 on his normal route. Ordinary morning.
Nothing in this frame is allowed to say that something is about to happen.

Render: manim -s -qh frame_a.py FrameA
"""

from manim import *
import plant_world as w
import bay

config.background_color = w.BRAND_DEEP


class FrameA(MovingCameraScene):
    def construct(self):
        f = self.camera.frame
        f.set(width=14.6).move_to(np.array([2.35, 2.05, 0.0]))

        L = bay.assemble(t=6.3)
        bay.add_bay(self, L)

        # OPERATOR_01 mid-stride, mid-route. Small in frame on purpose:
        # the bay is the subject of this frame, he is a person inside it.
        self.add(w.build_operator(-2.05, phase=0.9, facing=1, walking=True))
        self.add(L["fore"])

        bay.place_watermark(self, f)
        self.wait(0.05)
