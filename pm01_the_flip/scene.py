"""
LWA_PM_01 — The Flip — main animation and end card.

Topic: the shell and tube heat exchanger, narrated by voiceover.mp3 (repo root).
The main scene runs on the voiceover's clock: every cue below is the absolute
start time, in seconds, of a spoken word, read from voiceover_words.json
(a faster-whisper word-level transcription of voiceover.mp3). If the voiceover
is regenerated, re-transcribe it and update CUE.

Colour coding follows SKILL.md v1.0: hot is red to orange, cold is blue to
light blue, heat transfer is yellow, the equipment is steel grey, and labels
are white. The topic heading is the only text at the top of the frame. The
Avisha watermark is not drawn here; build.py overlays it on the whole video.

Run through build.py, which renders both scenes and assembles the final MP4.
"""

import math

from manim import *

VOICEOVER_SECONDS = 194.351
RUNTIME = 195.0                 # the voiceover plus a short hold on the last frame
END_CARD_SECONDS = 5.0

BG = "#0d0d1a"
TEXT = "#FFFFFF"
MUTED = "#9AA3B5"
STEEL = "#B0BEC5"
HOT = "#FF4444"
HOT_OUT = "#FF8C00"
COLD = "#4488FF"
COLD_OUT = "#90CAF9"
HEAT = "#FFD700"
FONT = "Avenir Next"

CUE = {
    "welcome": 0.0,
    "most_common": 3.12,
    "title": 7.18,
    "one_job": 11.1,
    "hot_to_cold": 14.0,
    "no_mixing": 15.74,
    "widely_used": 20.5,
    "how_it_works": 23.44,
    "shell": 29.34,
    "tubes": 32.48,
    "two_fluids": 37.9,
    "never_touch": 40.66,
    "inside_tubes": 42.62,
    "hot_in": 47.0,
    "t150": 49.32,
    "gives_up_heat": 52.0,
    "exits": 55.42,
    "t80": 58.08,
    "shell_side": 60.36,
    "space_between": 63.32,
    "cw_in": 68.34,
    "t30": 70.06,
    "absorbs_heat": 72.56,
    "cw_out": 75.54,
    "flow_directions": 78.52,
    "from_left": 81.92,
    "from_right": 84.54,
    "opposite": 86.82,
    "counter_current": 89.1,
    "max_difference": 94.24,
    "driving_force": 102.7,
    "greater_difference": 107.06,
    "tube_wall": 112.0,
    "thin": 116.06,
    "strong": 119.4,
    "real_plant": 123.72,
    "small_units": 128.76,
    "large_units": 131.12,
    "everywhere": 136.38,
    "use_cooling": 137.82,
    "use_preheating": 139.68,
    "use_condensing": 141.58,
    "use_heating": 143.16,
    "design": 146.76,
    "area": 151.24,
    "duty": 154.14,
    "coefficient": 155.24,
    "lmtd": 157.84,
    "future_videos": 162.46,
    "key_points": 165.12,
    "kp_wall": 166.48,
    "kp_sides": 172.38,
    "kp_counter": 177.12,
    "kp_driving": 180.64,
    "sign_off": 183.22,
    "tagline": 184.02,
    "reference": 187.82,
}


def label(text, size=28, color=TEXT, weight=NORMAL):
    return Text(text, font=FONT, font_size=size, color=color, weight=weight)


class ClockedScene(Scene):
    """A scene whose animations are placed at absolute times on the voiceover."""

    def setup(self):
        self.camera.background_color = BG
        self.clock = 0.0

    def hold_until(self, t):
        if t - self.clock > 1e-3:
            self.wait(t - self.clock)
            self.clock = t

    def at(self, t, *anims, run_time=1.0, **kwargs):
        if t < self.clock - 1e-3:
            raise ValueError(f"cue at {t:.2f}s is earlier than the clock ({self.clock:.2f}s)")
        self.hold_until(t)
        self.play(*anims, run_time=run_time, **kwargs)
        self.clock += run_time


def flow_particles(rows, x_from, x_to, color_from, color_to, gate, per_row=7, speed=0.9):
    """Dots that stream along each row, shading from color_from to color_to.

    gate is a ValueTracker from 0 to 1 that fades the whole stream in and out.
    """
    span = x_to - x_from
    seeds = [(y, (k + 0.5 * (i % 2)) / per_row) for i, y in enumerate(rows) for k in range(per_row)]
    dots = VGroup(*[Dot(radius=0.045) for _ in seeds])
    state = {"t": 0.0}

    def advance(group, dt):
        state["t"] += dt
        g = gate.get_value()
        for dot, (y, phase) in zip(group, seeds):
            f = (phase + state["t"] * speed / abs(span)) % 1.0
            dot.move_to([x_from + f * span, y, 0])
            edge = min(1.0, f * 10, (1 - f) * 10)
            dot.set_fill(interpolate_color(ManimColor(color_from), ManimColor(color_to), f),
                         opacity=g * edge)
            dot.set_stroke(width=0)

    dots.add_updater(advance)
    return dots


class Ep01Main(ClockedScene):

    def construct(self):
        self.opening()
        self.one_job()
        self.build_exchanger()
        self.tube_side()
        self.shell_side()
        self.counter_current()
        self.driving_force()
        self.tube_wall()
        self.sizes()
        self.uses()
        self.design()
        self.key_points()
        self.sign_off()
        self.hold_until(RUNTIME)

    # ── 0 – 27 s: what it is ─────────────────────────────────────
    def opening(self):
        eyebrow = label("HEAT TRANSFER", 26, HEAT, weight=MEDIUM).move_to(UP * 0.9)
        line = label("One of the most common pieces of equipment in any chemical plant",
                     32, MUTED).move_to(DOWN * 0.1)
        self.at(CUE["welcome"] + 0.3, FadeIn(eyebrow, shift=UP * 0.15), run_time=0.8)
        self.at(CUE["most_common"], FadeIn(line, shift=UP * 0.15), run_time=1.0)

        self.heading = label("Shell and Tube Heat Exchanger", 60, TEXT, weight=MEDIUM)
        self.at(CUE["title"] - 0.6, FadeOut(eyebrow), FadeOut(line), run_time=0.5)
        self.at(CUE["title"], Write(self.heading), run_time=1.6)

        rule = Line(LEFT * 6.6, RIGHT * 6.6, stroke_width=1.5, color=STEEL).set_opacity(0.5)
        rule.move_to(UP * 3.15)
        self.at(CUE["title"] + 2.6,
                self.heading.animate.scale(0.6).move_to(UP * 3.55),
                Create(rule), run_time=1.0)

    def one_job(self):
        hot = RoundedRectangle(corner_radius=0.2, width=3.0, height=2.0,
                               stroke_color=HOT, fill_color=HOT, fill_opacity=0.18)
        cold = hot.copy().set_stroke(COLD).set_fill(COLD, 0.18)
        hot.move_to(LEFT * 3.1 + UP * 0.6)
        cold.move_to(RIGHT * 3.1 + UP * 0.6)
        hot_t = label("HOT FLUID", 30, HOT, weight=MEDIUM).move_to(hot)
        cold_t = label("COLD FLUID", 30, COLD, weight=MEDIUM).move_to(cold)
        wall = Line(UP * 1.8, DOWN * 0.6, stroke_width=8, color=STEEL)
        heat = Arrow(LEFT * 1.4 + UP * 0.6, RIGHT * 1.4 + UP * 0.6, color=HEAT,
                     stroke_width=8, buff=0, max_tip_length_to_length_ratio=0.2)
        heat_t = label("heat", 26, HEAT).next_to(heat, UP, buff=0.12).shift(LEFT * 0.7)
        no_mix = label("A wall keeps them apart — they never mix", 32, TEXT).move_to(DOWN * 1.6)

        self.at(CUE["one_job"], FadeIn(hot), FadeIn(hot_t), FadeIn(cold), FadeIn(cold_t), run_time=1.0)
        self.at(CUE["hot_to_cold"], GrowArrow(heat), FadeIn(heat_t), run_time=1.0)
        self.at(CUE["no_mixing"], Create(wall), FadeIn(no_mix, shift=UP * 0.1), run_time=1.0)

        concept = VGroup(hot, cold, hot_t, cold_t, wall, heat, heat_t, no_mix)
        widely = label("The most widely used type in industry", 40, TEXT).move_to(UP * 0.4)
        how = label("How does it work?", 32, MUTED).next_to(widely, DOWN, buff=0.5)
        self.at(CUE["widely_used"], FadeOut(concept), FadeIn(widely, shift=UP * 0.15), run_time=1.0)
        self.at(CUE["how_it_works"], FadeIn(how, shift=UP * 0.1), run_time=0.8)
        self.at(CUE["shell"] - 2.4, FadeOut(widely), FadeOut(how), run_time=0.8)

    # ── 27 – 42 s: the two parts ─────────────────────────────────
    def build_exchanger(self):
        self.cy = cy = 0.95
        self.half = half = 3.9
        self.shell = Rectangle(width=2 * half, height=2.3, stroke_color=STEEL, stroke_width=4)
        self.shell.move_to(UP * cy)
        self.shell_fill = self.shell.copy().set_stroke(width=0).set_fill(COLD, 0.0)

        self.tube_rows = [cy + d for d in (-0.76, -0.38, 0.0, 0.38, 0.76)]
        self.tubes = VGroup(*[
            Rectangle(width=2 * half, height=0.13, stroke_color=STEEL, stroke_width=2,
                      fill_color=BG, fill_opacity=1).move_to([0, y, 0])
            for y in self.tube_rows
        ])
        sheets = VGroup(*[
            Line([x, cy - 1.15, 0], [x, cy + 1.15, 0], stroke_width=6, color=STEEL)
            for x in (-half, half)
        ])

        self.shell_label = label("SHELL", 24, STEEL).move_to([-2.6, -0.6, 0])
        shell_leader = Line([-2.6, -0.42, 0], [-2.6, cy - 1.15, 0], stroke_width=1.5, color=STEEL)
        self.tube_label = label("TUBE BUNDLE", 24, STEEL).move_to([2.6, -0.6, 0])
        tube_leader = Line([2.6, -0.42, 0], [2.6, self.tube_rows[0] - 0.065, 0],
                           stroke_width=1.5, color=STEEL)
        self.part_labels = VGroup(self.shell_label, shell_leader, self.tube_label, tube_leader)

        self.add(self.shell_fill)
        self.at(CUE["shell"], Create(self.shell), run_time=1.5)
        self.at(CUE["shell"] + 1.6, FadeIn(self.shell_label), Create(shell_leader), run_time=0.6)
        self.at(CUE["tubes"], LaggedStart(*[Create(t) for t in self.tubes], lag_ratio=0.15),
                Create(sheets), run_time=1.5)
        self.at(CUE["tubes"] + 1.6, FadeIn(self.tube_label), Create(tube_leader), run_time=0.6)
        self.sheets = sheets

        self.caption = label("Two fluids flow through it — they never touch", 32, TEXT)
        self.caption.move_to(DOWN * 1.7)
        self.at(CUE["two_fluids"] + 0.4, FadeIn(self.caption, shift=UP * 0.1), run_time=0.8)
        self.at(CUE["never_touch"],
                self.tubes.animate.set_stroke(TEXT, width=3), run_time=0.5)
        self.at(CUE["never_touch"] + 0.6,
                self.tubes.animate.set_stroke(STEEL, width=2), run_time=0.5)

    def recaption(self, t, text, run_time=0.6):
        new = label(text, 32, TEXT).move_to(self.caption)
        self.at(t, FadeOut(self.caption), FadeIn(new, shift=UP * 0.1), run_time=run_time)
        self.caption = new

    # ── 42 – 60 s: fluid 1, tube side ────────────────────────────
    def tube_side(self):
        cy, half = self.cy, self.half
        self.recaption(CUE["inside_tubes"], "Fluid 1 flows inside the tubes")
        self.at(CUE["inside_tubes"] + 0.7, self.tubes.animate.set_stroke(HOT, width=3), run_time=0.6)
        self.at(CUE["inside_tubes"] + 1.6, self.tubes.animate.set_stroke(STEEL, width=2), run_time=0.6)

        hot_in = Arrow([-6.4, cy, 0], [-half - 0.05, cy, 0], color=HOT, stroke_width=8, buff=0,
                       max_tip_length_to_length_ratio=0.15)
        hot_in_t = label("Hot Fluid In", 26, HOT, weight=MEDIUM).move_to([-5.3, cy + 0.42, 0])
        hot_in_v = label("150 °C", 26, TEXT).move_to([-5.3, cy - 0.42, 0])
        self.at(CUE["hot_in"], GrowArrow(hot_in), FadeIn(hot_in_t), run_time=1.0)
        self.at(CUE["t150"], FadeIn(hot_in_v, shift=UP * 0.1), run_time=0.6)

        self.hot_gate = ValueTracker(0)
        self.hot_flow = flow_particles(self.tube_rows, -half + 0.05, half - 0.05, HOT, HOT_OUT,
                                       self.hot_gate)
        self.add(self.hot_flow)
        self.recaption(CUE["gives_up_heat"], "It gives up heat as it travels through")
        self.at(CUE["gives_up_heat"] + 0.7, self.hot_gate.animate.set_value(1), run_time=1.2)

        hot_out = Arrow([half + 0.05, cy, 0], [6.4, cy, 0], color=HOT_OUT, stroke_width=8, buff=0,
                        max_tip_length_to_length_ratio=0.15)
        hot_out_t = label("Hot Fluid Out", 26, HOT_OUT, weight=MEDIUM).move_to([5.3, cy + 0.42, 0])
        hot_out_v = label("80 °C", 26, TEXT).move_to([5.3, cy - 0.42, 0])
        self.at(CUE["exits"], GrowArrow(hot_out), FadeIn(hot_out_t), run_time=1.0)
        self.at(CUE["t80"], FadeIn(hot_out_v, shift=UP * 0.1), run_time=0.6)

        self.hot_in, self.hot_out = hot_in, hot_out
        self.streams = VGroup(hot_in, hot_in_t, hot_in_v, hot_out, hot_out_t, hot_out_v)

    # ── 60 – 78 s: fluid 2, shell side ───────────────────────────
    def shell_side(self):
        cy, half = self.cy, self.half
        self.recaption(CUE["shell_side"], "Fluid 2 flows on the shell side, around the tubes")
        self.at(CUE["space_between"], self.shell_fill.animate.set_fill(COLD, 0.22), run_time=0.8)
        self.at(CUE["space_between"] + 1.2, self.shell_fill.animate.set_fill(COLD, 0.07), run_time=0.8)

        top = cy + 1.15
        cw_in = Arrow([3.0, top + 0.85, 0], [3.0, top + 0.02, 0], color=COLD, stroke_width=8, buff=0,
                      max_tip_length_to_length_ratio=0.25)
        cw_in_t = label("CW In", 28, COLD, weight=MEDIUM).move_to([4.15, top + 0.62, 0])
        cw_in_v = label("30 °C", 28, TEXT).move_to([4.15, top + 0.26, 0])
        self.at(CUE["cw_in"], GrowArrow(cw_in), FadeIn(cw_in_t), run_time=1.0)
        self.at(CUE["t30"], FadeIn(cw_in_v, shift=UP * 0.1), run_time=0.6)

        self.cold_gate = ValueTracker(0)
        shell_rows = [cy + d for d in (-0.95, -0.57, -0.19, 0.19, 0.57, 0.95)]
        self.cold_flow = flow_particles(shell_rows, half - 0.15, -half + 0.15, COLD, COLD_OUT,
                                        self.cold_gate, per_row=6, speed=0.75)
        self.add(self.cold_flow)
        self.recaption(CUE["absorbs_heat"], "It absorbs that heat and warms up")
        self.at(CUE["absorbs_heat"] + 0.7, self.cold_gate.animate.set_value(1), run_time=1.2)

        cw_out = Arrow([-3.0, top - 0.02, 0], [-3.0, top + 0.85, 0], color=COLD_OUT, stroke_width=8,
                       buff=0, max_tip_length_to_length_ratio=0.25)
        cw_out_t = label("CW Out", 28, COLD_OUT, weight=MEDIUM).move_to([-4.2, top + 0.62, 0])
        cw_out_v = label("55 °C", 28, TEXT).move_to([-4.2, top + 0.26, 0])
        self.at(CUE["cw_out"], GrowArrow(cw_out), FadeIn(cw_out_t), FadeIn(cw_out_v), run_time=1.0)

        self.cw_in = cw_in
        self.streams.add(cw_in, cw_in_t, cw_in_v, cw_out, cw_out_t, cw_out_v)

    # ── 78 – 102 s: counter-current ──────────────────────────────
    def counter_current(self):
        self.at(CUE["flow_directions"], FadeOut(self.caption), FadeOut(self.part_labels), run_time=0.8)

        self.at(CUE["from_left"], Indicate(self.hot_in, color=HOT, scale_factor=1.15), run_time=1.0)
        self.at(CUE["from_right"], Indicate(self.cw_in, color=COLD, scale_factor=1.15), run_time=1.0)

        y = -0.75
        right = Arrow([-3.6, y, 0], [-0.4, y, 0], color=HOT, stroke_width=6, buff=0)
        left = Arrow([3.6, y, 0], [0.4, y, 0], color=COLD, stroke_width=6, buff=0)
        right_t = label("tube side", 24, HOT).next_to(right, DOWN, buff=0.12)
        left_t = label("shell side", 24, COLD).next_to(left, DOWN, buff=0.12)
        arrows = VGroup(right, left, right_t, left_t)
        self.at(CUE["opposite"], GrowArrow(right), GrowArrow(left), FadeIn(right_t), FadeIn(left_t),
                run_time=1.0)

        cc = label("Counter-Current Flow", 40, HEAT, weight=MEDIUM).move_to(DOWN * 1.75)
        self.at(CUE["counter_current"], Write(cc), run_time=1.2)

        # Temperature along the exchanger. The hot and cold lines fall by the
        # same fraction of their total change at every point (a heat balance),
        # and the gap between them decays exponentially from 95 to 50 °C.
        x0, x1 = -self.half, self.half
        yb, yt = -3.5, -1.95

        def ty(temp):
            return yb + (temp - 20) / 130 * (yt - yb)

        def fraction(s):
            return (95 - 95 * (50 / 95) ** s) / 45

        axes = VGroup(
            Line([x0, yb, 0], [x1 + 0.2, yb, 0], stroke_width=2, color=STEEL),
            Line([x0, yb, 0], [x0, yt + 0.15, 0], stroke_width=2, color=STEEL),
        )
        hot_line = ParametricFunction(
            lambda s: [x0 + s * (x1 - x0), ty(150 - 70 * fraction(s)), 0], t_range=[0, 1],
            stroke_width=5).set_color([HOT_OUT, HOT])  # manim lays a stroke gradient out end to start
        cold_line = ParametricFunction(
            lambda s: [x0 + s * (x1 - x0), ty(55 - 25 * fraction(s)), 0], t_range=[0, 1],
            stroke_width=5).set_color([COLD, COLD_OUT])
        axis_t = label("length along the exchanger  →", 20, MUTED).move_to([0, yb - 0.28, 0])
        gap_l = DoubleArrow([x0 + 0.18, ty(55), 0], [x0 + 0.18, ty(150), 0], color=HEAT, buff=0,
                            stroke_width=3, tip_length=0.14)
        gap_r = DoubleArrow([x1 - 0.18, ty(30), 0], [x1 - 0.18, ty(80), 0], color=HEAT, buff=0,
                            stroke_width=3, tip_length=0.14)
        gap_l_t = label("hot end\nΔT = 95 °C", 26, HEAT).move_to([-5.2, (ty(55) + ty(150)) / 2, 0])
        gap_r_t = label("cold end\nΔT = 50 °C", 26, HEAT).move_to([5.2, (ty(30) + ty(80)) / 2 + 0.2, 0])

        self.at(CUE["counter_current"] + 2.4, FadeOut(arrows),
                cc.animate.move_to(DOWN * 0.75).scale(0.8), run_time=0.8)
        self.at(CUE["counter_current"] + 3.3, Create(axes), FadeIn(axis_t), run_time=0.8)
        self.at(CUE["max_difference"] - 1.0, Create(hot_line), Create(cold_line),
                run_time=1.5)
        self.at(CUE["max_difference"] + 0.8, GrowFromCenter(gap_l), FadeIn(gap_l_t),
                GrowFromCenter(gap_r), FadeIn(gap_r_t), run_time=1.0)

        self.profile = VGroup(cc, axes, hot_line, cold_line, axis_t, gap_l, gap_r, gap_l_t, gap_r_t)

    # ── 102 – 115 s: driving force ───────────────────────────────
    def driving_force(self):
        cy = self.cy
        self.at(CUE["driving_force"] - 0.6, FadeOut(self.profile), run_time=0.6)

        heat_arrows = VGroup()
        for x in (-2.6, -0.9, 0.8, 2.5):
            heat_arrows.add(Arrow([x, self.tube_rows[-1] + 0.08, 0], [x, cy + 1.12, 0], buff=0,
                                  color=HEAT, stroke_width=4, max_tip_length_to_length_ratio=0.45))
            heat_arrows.add(Arrow([x, self.tube_rows[0] - 0.08, 0], [x, cy - 1.12, 0], buff=0,
                                  color=HEAT, stroke_width=4, max_tip_length_to_length_ratio=0.45))
        self.heat_gate = ValueTracker(0)
        clock = {"t": 0.0}

        def pulse(group, dt):
            clock["t"] += dt
            group.set_opacity(self.heat_gate.get_value() * (0.6 + 0.4 * math.sin(clock["t"] * 4)))

        heat_arrows.add_updater(pulse)
        self.add(heat_arrows)
        self.heat_arrows = heat_arrows

        force = label("Driving force:  the temperature difference, ΔT", 34, TEXT).move_to(DOWN * 1.45)
        faster = label("Bigger ΔT  →  heat moves faster", 32, HEAT).move_to(DOWN * 2.3)
        wall = label("Heat crosses the tube wall", 32, TEXT).move_to(DOWN * 3.1)
        self.at(CUE["driving_force"], FadeIn(force, shift=UP * 0.1),
                self.heat_gate.animate.set_value(1), run_time=1.0)
        self.at(CUE["greater_difference"], FadeIn(faster, shift=UP * 0.1), run_time=0.8)
        self.at(CUE["tube_wall"], FadeIn(wall, shift=UP * 0.1),
                self.tubes.animate.set_stroke(HEAT, width=3), run_time=0.8)
        self.at(CUE["tube_wall"] + 1.4, self.tubes.animate.set_stroke(STEEL, width=2), run_time=0.6)
        self.force_text = VGroup(force, faster, wall)

    # ── 115 – 123 s: the tube wall ───────────────────────────────
    def tube_wall(self):
        focus = Circle(radius=0.3, color=HEAT, stroke_width=3).move_to([-2.6, self.tube_rows[2] + 0.065, 0])
        x0, x1 = -6.0, -0.8
        hot = Rectangle(width=x1 - x0, height=0.5, stroke_width=0, fill_color=HOT, fill_opacity=0.35)
        hot.move_to([(x0 + x1) / 2, -1.75, 0])
        wall = Rectangle(width=x1 - x0, height=0.16, stroke_width=0, fill_color=STEEL, fill_opacity=1)
        wall.next_to(hot, DOWN, buff=0)
        cold = hot.copy().set_fill(COLD, 0.35).next_to(wall, DOWN, buff=0)
        hot_t = label("inside the tube — hot fluid", 22, TEXT).move_to(hot)
        cold_t = label("shell side — cooling water", 22, TEXT).move_to(cold)
        crossings = VGroup(*[
            Arrow([x, hot.get_center()[1] + 0.1, 0], [x, cold.get_center()[1] - 0.1, 0], buff=0,
                  color=HEAT, stroke_width=4, max_tip_length_to_length_ratio=0.3)
            for x in (-5.6, -1.2)
        ])
        wall_t = label("TUBE WALL", 20, STEEL).next_to(wall, DOWN, buff=0.75).align_to(wall, LEFT)
        inset = VGroup(hot, wall, cold, hot_t, cold_t, crossings, wall_t)

        thin = label("Thin  →  heat passes through easily", 28, TEXT)
        strong = label("Strong  →  handles both fluid pressures", 28, TEXT)
        thin.move_to([0.3, -1.75, 0], aligned_edge=LEFT)
        strong.move_to([0.3, -2.55, 0], aligned_edge=LEFT)

        self.at(CUE["thin"] - 1.0, FadeOut(self.force_text), Create(focus), FadeIn(inset), run_time=1.0)
        self.at(CUE["thin"] + 0.2, FadeIn(thin, shift=RIGHT * 0.15), run_time=0.8)
        self.at(CUE["strong"], FadeIn(strong, shift=RIGHT * 0.15), run_time=0.8)

        exchanger = VGroup(self.shell, self.shell_fill, self.tubes, self.sheets, self.streams, focus)
        self.at(CUE["real_plant"] - 0.4,
                FadeOut(exchanger), FadeOut(inset), FadeOut(thin), FadeOut(strong),
                self.hot_gate.animate.set_value(0), self.cold_gate.animate.set_value(0),
                self.heat_gate.animate.set_value(0), run_time=0.9)
        for flow in (self.hot_flow, self.cold_flow, self.heat_arrows):
            flow.clear_updaters()
            self.remove(flow)

    # ── 123 – 136 s: sizes ───────────────────────────────────────
    def mini_exchanger(self, width, height, tubes):
        shell = Rectangle(width=width, height=height, stroke_color=STEEL, stroke_width=3)
        rows = VGroup(*[
            Line([-width / 2, (k - (tubes - 1) / 2) * height / (tubes + 1), 0],
                 [width / 2, (k - (tubes - 1) / 2) * height / (tubes + 1), 0],
                 stroke_width=2, color=STEEL)
            for k in range(tubes)
        ])
        return VGroup(shell, rows)

    def sizes(self):
        title = label("Many sizes", 40, TEXT).move_to(UP * 2.3)
        self.at(CUE["real_plant"] + 0.6, FadeIn(title, shift=UP * 0.1), run_time=0.8)

        table = VGroup(
            Line([-5.6, -0.75, 0], [-2.8, -0.75, 0], stroke_width=6, color=MUTED),
            Line([-5.35, -0.75, 0], [-5.35, -1.9, 0], stroke_width=5, color=MUTED),
            Line([-3.05, -0.75, 0], [-3.05, -1.9, 0], stroke_width=5, color=MUTED),
        )
        small = self.mini_exchanger(1.9, 0.55, 2).move_to([-4.2, -0.45, 0])
        small_t = label("the size of a table", 26, TEXT).move_to([-4.2, -2.4, 0])
        self.at(CUE["small_units"], FadeIn(table), FadeIn(small, shift=DOWN * 0.1), FadeIn(small_t),
                run_time=1.0)

        large = self.mini_exchanger(6.0, 1.7, 5).move_to([2.6, 0.1, 0])
        length = DoubleArrow([-0.4, -1.1, 0], [5.6, -1.1, 0], color=HEAT, buff=0, stroke_width=3,
                             tip_length=0.18)
        length_t = label("several metres long", 26, TEXT).next_to(length, DOWN, buff=0.15)
        dia = DoubleArrow([-0.75, -0.75, 0], [-0.75, 0.95, 0], color=HEAT, buff=0, stroke_width=3,
                          tip_length=0.18)
        dia_t = label("over 1 m\ndiameter", 24, TEXT).next_to(dia, LEFT, buff=0.18)
        self.at(CUE["large_units"], FadeIn(large, shift=DOWN * 0.1), run_time=1.0)
        self.at(CUE["large_units"] + 1.5, GrowFromCenter(length), FadeIn(length_t), run_time=0.8)
        self.at(CUE["large_units"] + 3.4, GrowFromCenter(dia), FadeIn(dia_t), run_time=0.8)

        self.size_group = VGroup(title, table, small, small_t, large, length, length_t, dia, dia_t)

    # ── 136 – 146 s: where they are used ─────────────────────────
    def uses(self):
        title = label("Used everywhere", 40, TEXT).move_to(UP * 2.3)
        self.at(CUE["everywhere"] - 0.3, FadeOut(self.size_group), FadeIn(title, shift=UP * 0.1),
                run_time=0.8)

        items = [
            ("use_cooling", "Cooling reactor effluents", COLD, [-3.25, 0.75, 0]),
            ("use_preheating", "Preheating feed streams", HOT_OUT, [3.25, 0.75, 0]),
            ("use_condensing", "Condensing vapours", COLD_OUT, [-3.25, -1.05, 0]),
            ("use_heating", "Heating cold fluids before\na distillation column", HOT, [3.25, -1.05, 0]),
        ]
        chips = VGroup(title)
        for cue, text, color, pos in items:
            box = RoundedRectangle(corner_radius=0.18, width=6.0, height=1.4, stroke_color=STEEL,
                                   stroke_width=2).move_to(pos)
            bar = Rectangle(width=0.14, height=1.0, stroke_width=0, fill_color=color, fill_opacity=1)
            bar.move_to(box.get_left() + RIGHT * 0.35)
            words = label(text, 28, TEXT).next_to(bar, RIGHT, buff=0.35)
            chip = VGroup(box, bar, words)
            chips.add(chip)
            self.at(CUE[cue], FadeIn(chip, shift=UP * 0.15), run_time=0.7)
        self.chips = chips

    # ── 146 – 165 s: design ──────────────────────────────────────
    def design(self):
        title = label("Designing one", 40, TEXT).move_to(UP * 2.3)
        self.at(CUE["design"], FadeOut(self.chips), FadeIn(title, shift=UP * 0.1), run_time=0.8)

        terms = {k: label(s, 72, TEXT) for k, s in
                 (("Q", "Q"), ("eq", "="), ("U", "U"), ("d1", "·"), ("A", "A"), ("d2", "·"), ("dT", "ΔT"))}
        equation = VGroup(*terms.values()).arrange(RIGHT, buff=0.35)
        lm = label("lm", 36, TEXT).next_to(terms["dT"], RIGHT, buff=0.05).align_to(terms["dT"], DOWN)
        lm.shift(DOWN * 0.12)
        terms["dT"].add(lm)
        equation = VGroup(*terms.values()).move_to(UP * 0.95)
        self.at(CUE["design"] + 2.4, Write(equation), run_time=1.5)

        lines = [
            ("area", "A", "A  —  heat transfer area, the size we calculate"),
            ("duty", "Q", "Q  —  heat duty"),
            ("coefficient", "U", "U  —  overall heat transfer coefficient"),
            ("lmtd", "dT", "ΔTlm  —  log mean temperature difference"),
        ]
        rows = VGroup()
        previous = None
        for i, (cue, key, text) in enumerate(lines):
            row = label(text, 30, TEXT).move_to([-4.6, -0.45 - i * 0.62, 0], aligned_edge=LEFT)
            anims = [FadeIn(row, shift=RIGHT * 0.1), terms[key].animate.set_color(HEAT)]
            if previous is not None:
                anims.append(terms[previous].animate.set_color(TEXT))
            self.at(CUE[cue], *anims, run_time=0.6)
            rows.add(row)
            previous = key

        later = label("Each of these gets its own video", 26, MUTED).move_to(DOWN * 3.1)
        self.at(CUE["future_videos"] - 0.6, FadeIn(later), terms[previous].animate.set_color(TEXT),
                run_time=0.8)
        self.design_group = VGroup(title, equation, rows, later)

    # ── 165 – 183 s: key points ──────────────────────────────────
    def key_points(self):
        title = label("Key points", 40, HEAT, weight=MEDIUM).move_to(UP * 2.3)
        self.at(CUE["key_points"] - 0.4, FadeOut(self.design_group), FadeIn(title, shift=UP * 0.1),
                run_time=0.8)

        points = [
            ("kp_wall", "Heat moves between two fluids through a tube wall", HEAT),
            ("kp_sides", "Hot fluid inside the tubes, cold fluid on the shell side", HOT),
            ("kp_counter", "Counter-current flow for maximum efficiency", COLD),
            ("kp_driving", "Temperature difference is the driving force", HOT_OUT),
        ]
        group = VGroup(title)
        for i, (cue, text, color) in enumerate(points):
            dot = Dot(radius=0.09, color=color)
            words = label(text, 34, TEXT)
            row = VGroup(dot, words).arrange(RIGHT, buff=0.35)
            row.move_to([-5.4, 1.15 - i * 0.95, 0], aligned_edge=LEFT)
            group.add(row)
            self.at(CUE[cue], FadeIn(row, shift=RIGHT * 0.15), run_time=0.8)
        self.points = group

    # ── 183 s – end: sign-off ────────────────────────────────────
    def sign_off(self):
        mark = VGroup(label("LearnWith", 64, TEXT, weight=MEDIUM),
                      label("Avisha", 64, HEAT, weight=MEDIUM)).arrange(RIGHT, buff=0.05)
        mark.move_to(UP * 0.5)
        tagline = label("Chemical engineering fundamentals, explained simply.", 32, MUTED)
        tagline.next_to(mark, DOWN, buff=0.45)
        self.at(CUE["sign_off"] - 0.3, FadeOut(self.points), FadeOut(self.heading),
                FadeIn(mark, shift=UP * 0.15), run_time=1.0)
        self.at(CUE["tagline"] + 0.3, FadeIn(tagline, shift=UP * 0.1), run_time=1.0)

        ref = label("Reference: Coulson & Richardson — Chemical Engineering, Vol. 1, Ch. 12", 22, MUTED)
        ref.move_to(DOWN * 3.2)
        self.at(CUE["reference"] + 0.2, FadeIn(ref), run_time=1.0)


class Ep01EndCard(ClockedScene):

    def construct(self):
        eyebrow = label("More lessons at", 32, MUTED).move_to(UP * 0.85)
        cta = label("learnwithavisha.ai", 84, TEXT, weight=MEDIUM).move_to(DOWN * 0.1)
        rule = Line(cta.get_corner(DL), cta.get_corner(DR), stroke_width=4, color=HEAT)
        rule.shift(DOWN * 0.25)
        self.at(0.0, FadeIn(eyebrow), FadeIn(cta, shift=UP * 0.15), run_time=0.8)
        self.at(0.9, Create(rule), run_time=0.8)
        self.hold_until(END_CARD_SECONDS)
