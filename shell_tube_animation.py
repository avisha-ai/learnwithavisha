"""
LearnWithAvisha — Pilot Video
Topic: Shell and Tube Heat Exchanger
Animation: Manim Community Edition

Install: pip install manim
Run: manim -pql shell_tube_animation.py ShellTubeScene
     (use -pqh for high quality final render)
"""

from manim import *

class ShellTubeScene(Scene):
    def construct(self):

        # ── Colours ──────────────────────────────────────────────
        HOT_IN      = RED
        HOT_OUT     = ORANGE
        COLD_IN     = BLUE
        COLD_OUT    = "#90caf9"   # light blue
        SHELL_COL   = "#b0bec5"   # steel grey
        TUBE_COL    = "#78909c"   # darker grey
        LABEL_COL   = WHITE
        TITLE_COL   = YELLOW

        # ── Title ─────────────────────────────────────────────────
        title = Text(
            "Shell and Tube Heat Exchanger",
            font_size=36,
            color=TITLE_COL
        ).to_edge(UP, buff=0.3)

        subtitle = Text(
            "LearnWithAvisha | Heat Transfer Fundamentals",
            font_size=18,
            color=GREY
        ).next_to(title, DOWN, buff=0.1)

        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(subtitle), run_time=0.8)
        self.wait(0.5)

        # ── Shell (outer cylinder — shown as rectangle) ───────────
        shell = Rectangle(
            width=8.5,
            height=2.8,
            color=SHELL_COL,
            stroke_width=3,
            fill_color="#1a1a2e",
            fill_opacity=1
        ).shift(DOWN * 0.5)

        shell_label = Text(
            "SHELL",
            font_size=16,
            color=SHELL_COL
        ).next_to(shell, LEFT, buff=0.15).shift(UP * 0.9)

        self.play(Create(shell), run_time=1.2)
        self.play(FadeIn(shell_label), run_time=0.5)
        self.wait(0.3)

        # ── Tube bundle (5 tubes inside shell) ────────────────────
        tubes = VGroup()
        tube_y_positions = [-1.2, -0.7, -0.2, 0.3, 0.8]

        for y in tube_y_positions:
            tube = Rectangle(
                width=8.0,
                height=0.28,
                color=TUBE_COL,
                stroke_width=2,
                fill_color="#37474f",
                fill_opacity=1
            ).shift(DOWN * 0.5 + UP * y)
            tubes.add(tube)

        tube_label = Text(
            "TUBES",
            font_size=14,
            color=TUBE_COL
        ).next_to(shell, LEFT, buff=0.15).shift(DOWN * 0.3)

        self.play(LaggedStart(
            *[Create(t) for t in tubes],
            lag_ratio=0.15
        ), run_time=1.5)
        self.play(FadeIn(tube_label), run_time=0.4)
        self.wait(0.5)

        # ── Hot fluid — TUBE SIDE (left to right) ─────────────────
        hot_in_arrow = Arrow(
            start=LEFT * 5.8 + DOWN * 0.5,
            end=LEFT * 4.3 + DOWN * 0.5,
            color=HOT_IN,
            stroke_width=5,
            max_tip_length_to_length_ratio=0.25
        )
        hot_in_label = VGroup(
            Text("Hot Fluid In", font_size=16, color=HOT_IN),
            Text("150 °C", font_size=14, color=HOT_IN)
        ).arrange(DOWN, buff=0.05).next_to(hot_in_arrow, LEFT, buff=0.15)

        hot_out_arrow = Arrow(
            start=RIGHT * 4.3 + DOWN * 0.5,
            end=RIGHT * 5.8 + DOWN * 0.5,
            color=HOT_OUT,
            stroke_width=5,
            max_tip_length_to_length_ratio=0.25
        )
        hot_out_label = VGroup(
            Text("Hot Fluid Out", font_size=16, color=HOT_OUT),
            Text("80 °C", font_size=14, color=HOT_OUT)
        ).arrange(DOWN, buff=0.05).next_to(hot_out_arrow, RIGHT, buff=0.15)

        self.play(
            GrowArrow(hot_in_arrow),
            FadeIn(hot_in_label),
            run_time=0.9
        )
        self.wait(0.3)

        # Animate flow through tubes
        flow_dots = VGroup()
        for y in tube_y_positions:
            dot = Dot(
                point=LEFT * 4.0 + DOWN * 0.5 + UP * y,
                radius=0.06,
                color=HOT_IN
            )
            flow_dots.add(dot)

        self.play(FadeIn(flow_dots))
        self.play(
            flow_dots.animate.shift(RIGHT * 8.0),
            run_time=1.8,
            rate_func=linear
        )
        self.play(
            GrowArrow(hot_out_arrow),
            FadeIn(hot_out_label),
            FadeOut(flow_dots),
            run_time=0.9
        )
        self.wait(0.4)

        # ── Cooling water — SHELL SIDE (right to left) ────────────
        cw_in_arrow = Arrow(
            start=RIGHT * 5.8 + DOWN * 0.5 + UP * 1.1,
            end=RIGHT * 4.3 + DOWN * 0.5 + UP * 1.1,
            color=COLD_IN,
            stroke_width=5,
            max_tip_length_to_length_ratio=0.25
        )
        cw_in_label = VGroup(
            Text("CW In", font_size=16, color=COLD_IN),
            Text("30 °C", font_size=14, color=COLD_IN)
        ).arrange(DOWN, buff=0.05).next_to(cw_in_arrow, RIGHT, buff=0.15)

        cw_out_arrow = Arrow(
            start=LEFT * 4.3 + DOWN * 0.5 + UP * 1.1,
            end=LEFT * 5.8 + DOWN * 0.5 + UP * 1.1,
            color=COLD_OUT,
            stroke_width=5,
            max_tip_length_to_length_ratio=0.25
        )
        cw_out_label = VGroup(
            Text("CW Out", font_size=16, color=COLD_OUT),
            Text("55 °C", font_size=14, color=COLD_OUT)
        ).arrange(DOWN, buff=0.05).next_to(cw_out_arrow, LEFT, buff=0.15)

        self.play(
            GrowArrow(cw_in_arrow),
            FadeIn(cw_in_label),
            run_time=0.9
        )
        self.wait(0.3)

        # Animate cooling water flow through shell (right to left)
        cw_dot = Dot(
            point=RIGHT * 4.0 + DOWN * 0.5 + UP * 1.1,
            radius=0.08,
            color=COLD_IN
        )
        self.play(FadeIn(cw_dot))
        self.play(
            cw_dot.animate.shift(LEFT * 8.0),
            run_time=1.8,
            rate_func=linear
        )
        self.play(
            GrowArrow(cw_out_arrow),
            FadeIn(cw_out_label),
            FadeOut(cw_dot),
            run_time=0.9
        )
        self.wait(0.5)

        # ── Heat transfer arrow ────────────────────────────────────
        heat_arrow = Arrow(
            start=DOWN * 0.5 + DOWN * 0.3,
            end=DOWN * 0.5 + UP * 0.85,
            color=YELLOW,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.2
        ).shift(RIGHT * 1.5)

        heat_label = Text(
            "Heat Transfer",
            font_size=14,
            color=YELLOW
        ).next_to(heat_arrow, RIGHT, buff=0.1)

        self.play(
            GrowArrow(heat_arrow),
            FadeIn(heat_label),
            run_time=0.8
        )
        self.wait(0.5)

        # ── Counter current label ─────────────────────────────────
        cc_label = Text(
            "Counter-Current Flow",
            font_size=16,
            color=GREEN
        ).to_edge(DOWN, buff=0.35)

        cc_underline = Line(
            cc_label.get_left(),
            cc_label.get_right(),
            color=GREEN,
            stroke_width=1.5
        ).next_to(cc_label, DOWN, buff=0.05)

        self.play(
            Write(cc_label),
            Create(cc_underline),
            run_time=0.8
        )
        self.wait(0.5)

        # ── Key points summary ────────────────────────────────────
        self.wait(1)

        summary_box = Rectangle(
            width=9,
            height=3.2,
            color=GREY,
            stroke_width=1.5,
            fill_color="#0d0d1a",
            fill_opacity=0.95
        ).to_edge(DOWN, buff=0.1)

        summary_title = Text(
            "Key Points",
            font_size=20,
            color=YELLOW,
            weight=BOLD
        ).next_to(summary_box.get_top(), DOWN, buff=0.2)

        points = VGroup(
            Text("• Hot fluid flows inside the tubes", font_size=16, color=WHITE),
            Text("• Cold fluid flows on the shell side", font_size=16, color=WHITE),
            Text("• Counter-current flow = maximum efficiency", font_size=16, color=WHITE),
            Text("• Temperature difference drives heat transfer", font_size=16, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).next_to(
            summary_title, DOWN, buff=0.2
        ).shift(LEFT * 0.5)

        self.play(
            FadeOut(cc_label),
            FadeOut(cc_underline),
            FadeIn(summary_box),
            run_time=0.6
        )
        self.play(Write(summary_title), run_time=0.5)
        self.play(
            LaggedStart(
                *[Write(p) for p in points],
                lag_ratio=0.3
            ),
            run_time=2.0
        )
        self.wait(1.5)

        # ── Reference ─────────────────────────────────────────────
        ref = Text(
            "Reference: Coulson & Richardson — Chemical Engineering Vol. 1, Chapter 12",
            font_size=12,
            color=DARK_GREY
        ).to_corner(DR, buff=0.2)

        self.play(FadeIn(ref), run_time=0.5)
        self.wait(1)

        # ── End card ──────────────────────────────────────────────
        self.play(
            FadeOut(VGroup(
                shell, tubes, shell_label, tube_label,
                hot_in_arrow, hot_in_label,
                hot_out_arrow, hot_out_label,
                cw_in_arrow, cw_in_label,
                cw_out_arrow, cw_out_label,
                heat_arrow, heat_label,
                summary_box, summary_title, points, ref
            )),
            run_time=1.0
        )

        end_title = Text(
            "LearnWithAvisha",
            font_size=48,
            color=YELLOW,
            weight=BOLD
        )
        end_sub = Text(
            "Chemical Engineering — Made Simple. Made Free.",
            font_size=22,
            color=WHITE
        ).next_to(end_title, DOWN, buff=0.3)

        avisha_tag = Text(
            "Brought to you by Avisha.AI",
            font_size=16,
            color=GREY
        ).next_to(end_sub, DOWN, buff=0.4)

        self.play(
            Write(end_title),
            run_time=1.0
        )
        self.play(
            FadeIn(end_sub),
            FadeIn(avisha_tag),
            run_time=0.8
        )
        self.wait(2.5)

        self.play(
            FadeOut(VGroup(title, subtitle, end_title, end_sub, avisha_tag)),
            run_time=0.8
        )
