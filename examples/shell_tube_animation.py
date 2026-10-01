"""
LearnWithAvisha — Pilot Video
Topic: Shell and Tube Heat Exchanger
Animation: Manim Community Edition

Built to SKILL.md v1.0 (frozen brand + animation rules):
  • No "LearnWithAvisha" heading at the top of the frame — LWA monogram
    watermark only, bottom right, present on every frame of the video.
  • No end card. The word "free" appears nowhere.
  • 2.5 s breathing pause after every major element reveal. The lower text
    strip tracks the narration continuously and is exempt — it has to be,
    or the video falls out of sync with the voice.
  • Total duration matches voiceover.mp3 exactly (194.351 s); the last
    frame holds until the narration ends.

Every cue below is an ABSOLUTE timestamp in seconds, aligned to the
narration by silence detection on the audio track.

Run: manim -qh shell_tube_animation.py ShellTubeScene
"""

from manim import *

TOTAL_RUNTIME = 194.351          # exact duration of voiceover.mp3
BREATH = 2.5                     # SKILL.md: pause after each major reveal


class ShellTubeScene(Scene):

    # ── absolute-time helpers ────────────────────────────────────
    def hold_until(self, t):
        dt = t - self.clock
        if dt > 1e-3:
            self.wait(dt)
            self.clock = t

    def at(self, t, *anims, run_time=1.0, **kwargs):
        """Play anims starting at absolute time t."""
        self.hold_until(t)
        self.play(*anims, run_time=run_time, **kwargs)
        self.clock += run_time

    def caption(self, t, *lines, run_time=0.7):
        """Cross-fade the lower text strip. Never leaves the strip empty."""
        new = VGroup(*[
            Text(line, font_size=24 if i == 0 else 20,
                 color=WHITE if i == 0 else "#b0bec5")
            for i, line in enumerate(lines)
        ]).arrange(DOWN, buff=0.2).move_to(self.LOWER_POS)

        old = self.lower
        self.lower = new
        if old is None:
            self.at(t, FadeIn(new), run_time=run_time)
        else:
            self.at(t, FadeOut(old), FadeIn(new), run_time=run_time)

    def swap_lower(self, t, new, run_time=0.8):
        old = self.lower
        self.lower = new
        self.at(t, FadeOut(old), FadeIn(new), run_time=run_time)

    # ── scene ────────────────────────────────────────────────────
    def construct(self):
        self.clock = 0.0
        self.lower = None
        self.LOWER_POS = DOWN * 2.74

        # Colours
        HOT_IN, HOT_OUT = RED, ORANGE
        COLD_IN, COLD_OUT = BLUE, "#90caf9"
        SHELL_COL, TUBE_COL = "#b0bec5", "#78909c"
        BRAND = YELLOW

        SH_Y = 0.95              # vertical centre of the exchanger
        SH_H = 2.0               # shell height  -> spans -0.05 .. 1.95
        SH_W = 7.0

        # ══ LWA MONOGRAM WATERMARK ═══════════════════════════════
        # White italic serif inside a thin circle, bottom right, 85 % opacity.
        # Added before the first frame so it is present for the whole video.
        ring = Circle(radius=0.42, fill_opacity=0)
        ring.set_stroke(WHITE, width=1.2, opacity=0.85)
        mono = Text("LWA", font="Georgia", slant=ITALIC, font_size=17,
                    color=WHITE).move_to(ring.get_center())
        mono.set_opacity(0.85)
        watermark = VGroup(ring, mono).to_corner(DR, buff=0.35)
        self.add(watermark)

        # ══ TOPIC TITLE — no channel name at the top ═════════════
        topic = Text("Shell and Tube Heat Exchanger", font_size=26,
                     color=WHITE).move_to(UP * 3.3)
        rule = Line(LEFT * 6.4 + UP * 2.85, RIGHT * 6.4 + UP * 2.85,
                    color="#455a64", stroke_width=2)

        self.at(0.3, FadeIn(topic), run_time=1.2)
        self.at(1.8, Create(rule), run_time=0.6)          # title reveal ends 2.4
        # BREATH 2.5 s

        # ── 0:00–0:10  intro ─────────────────────────────────────
        self.caption(4.9, "The most common piece of equipment",
                     "in any chemical plant", run_time=0.8)

        # ── 0:10–0:19  what a heat exchanger does ────────────────
        self.caption(10.4, "One job — move heat from a hot fluid to a cold fluid")

        hot_block = VGroup(
            Rectangle(width=2.0, height=1.2, color=HOT_IN, stroke_width=3,
                      fill_color="#3a1414", fill_opacity=1),
            Text("HOT FLUID", font_size=16, color=HOT_IN),
        ).move_to(LEFT * 2.7 + UP * SH_Y)
        cold_block = VGroup(
            Rectangle(width=2.0, height=1.2, color=COLD_IN, stroke_width=3,
                      fill_color="#0f2233", fill_opacity=1),
            Text("COLD FLUID", font_size=16, color=COLD_IN),
        ).move_to(RIGHT * 2.7 + UP * SH_Y)

        c_arrow = Arrow(LEFT * 1.5 + UP * SH_Y, RIGHT * 1.5 + UP * SH_Y,
                        color=YELLOW, stroke_width=5, buff=0,
                        max_tip_length_to_length_ratio=0.15)
        c_arrow_lbl = Text("HEAT", font_size=16, color=YELLOW
                           ).next_to(c_arrow, UP, buff=0.14)

        wall = DashedLine(UP * (SH_Y - 0.85), UP * (SH_Y + 0.85),
                          color="#b0bec5", stroke_width=4, dash_length=0.12)
        wall_lbl = Text("wall — no mixing", font_size=14, color="#b0bec5"
                        ).next_to(wall, DOWN, buff=0.14)

        self.at(11.0, FadeIn(hot_block), FadeIn(cold_block), run_time=1.2)
        self.at(14.7, GrowArrow(c_arrow), FadeIn(c_arrow_lbl), run_time=1.0)
        self.caption(16.3, "The two fluids never mix")
        self.at(17.2, Create(wall), FadeIn(wall_lbl), run_time=1.0)
        # concept diagram complete at 18.2 — BREATH 2.5 s

        # ── 0:19–0:27  why this design ───────────────────────────
        self.caption(20.7, "The most widely used exchanger type in industry")
        self.caption(23.8, "Let us see how it works")

        concept = VGroup(hot_block, cold_block, c_arrow, c_arrow_lbl,
                         wall, wall_lbl)

        # ══ THE EQUIPMENT ════════════════════════════════════════
        shell = Rectangle(width=SH_W, height=SH_H, color=SHELL_COL,
                          stroke_width=3, fill_color="#161629",
                          fill_opacity=1).move_to(UP * SH_Y)
        shell_label = Text("SHELL", font_size=16, color=SHELL_COL
                           ).next_to(shell, DOWN, buff=0.14).shift(LEFT * 2.6)

        tube_dy = [-0.50, -0.25, 0.0, 0.25, 0.50]
        tubes = VGroup(*[
            Rectangle(width=SH_W - 0.4, height=0.15, color=TUBE_COL,
                      stroke_width=2, fill_color="#37474f", fill_opacity=1
                      ).move_to(UP * (SH_Y + dy))
            for dy in tube_dy
        ])
        tube_label = Text("TUBE BUNDLE", font_size=16, color=TUBE_COL
                          ).next_to(shell, DOWN, buff=0.14).shift(RIGHT * 2.4)

        # ── 0:27–0:38  two main parts ────────────────────────────
        self.caption(27.3, "Two main parts — the shell and the tubes")
        self.at(28.4, Create(shell), FadeIn(shell_label), FadeOut(concept),
                run_time=1.6)                       # shell reveal ends 30.0
        # BREATH 2.5 s
        self.at(33.4, LaggedStart(*[Create(t) for t in tubes], lag_ratio=0.15),
                FadeIn(tube_label), run_time=2.2)   # tube bundle ends 35.6
        # BREATH 2.5 s

        # ── 0:38–0:43  two fluids, never touching ────────────────
        self.caption(38.3, "Two fluids flow through — but they never touch")

        # ══ TUBE SIDE — HOT FLUID (left to right) ════════════════
        hot_in_arrow = Arrow(LEFT * 5.25 + UP * SH_Y, LEFT * 3.6 + UP * SH_Y,
                             color=HOT_IN, stroke_width=6, buff=0,
                             max_tip_length_to_length_ratio=0.25)
        hot_in_label = VGroup(
            Text("Hot Fluid In", font_size=16, color=HOT_IN),
            Text("150 °C", font_size=16, color=HOT_IN),
        ).arrange(DOWN, buff=0.08).next_to(hot_in_arrow, LEFT, buff=0.18)

        hot_out_arrow = Arrow(RIGHT * 3.6 + UP * SH_Y, RIGHT * 5.25 + UP * SH_Y,
                              color=HOT_OUT, stroke_width=6, buff=0,
                              max_tip_length_to_length_ratio=0.25)
        hot_out_label = VGroup(
            Text("Hot Fluid Out", font_size=16, color=HOT_OUT),
            Text("80 °C", font_size=16, color=HOT_OUT),
        ).arrange(DOWN, buff=0.08).next_to(hot_out_arrow, RIGHT, buff=0.18)

        self.caption(42.9, "Tube side — the hot process fluid")
        self.at(46.3, GrowArrow(hot_in_arrow), FadeIn(hot_in_label),
                run_time=1.2)                       # inlet ends 47.5
        # BREATH 2.5 s

        hot_dots = VGroup(*[
            Dot(RIGHT * x + UP * (SH_Y + dy), radius=0.06, color=HOT_IN)
            for dy in tube_dy for x in (-3.9, -3.45, -3.0)
        ])
        self.at(50.0, FadeIn(hot_dots), run_time=0.4)
        self.at(50.7, hot_dots.animate.shift(RIGHT * 7.0).set_color(HOT_OUT),
                run_time=5.3, rate_func=linear)
        self.at(56.3, GrowArrow(hot_out_arrow), FadeIn(hot_out_label),
                FadeOut(hot_dots), run_time=1.2)    # hot stream ends 57.5
        # BREATH 2.5 s

        # ══ SHELL SIDE — COOLING WATER (right to left) ═══════════
        BAND_DY = 0.775                     # centre of the shell-side space
        bands = VGroup(*[
            Rectangle(width=SH_W - 0.1, height=0.33, color=COLD_IN,
                      stroke_width=0, fill_color=COLD_IN, fill_opacity=0.20
                      ).move_to(UP * (SH_Y + s * BAND_DY))
            for s in (1, -1)
        ])
        band_lbl = Text("shell-side space", font_size=14, color=COLD_OUT
                        ).next_to(bands[0], LEFT, buff=0.22)

        cw_in_arrow = Arrow(RIGHT * 2.3 + UP * 2.68, RIGHT * 2.3 + UP * 1.98,
                            color=COLD_IN, stroke_width=6, buff=0,
                            max_tip_length_to_length_ratio=0.4)
        cw_in_label = VGroup(
            Text("CW In", font_size=16, color=COLD_IN),
            Text("30 °C", font_size=16, color=COLD_IN),
        ).arrange(DOWN, buff=0.08).next_to(cw_in_arrow, RIGHT, buff=0.18)

        cw_out_arrow = Arrow(LEFT * 2.3 + UP * 1.98, LEFT * 2.3 + UP * 2.68,
                             color=COLD_OUT, stroke_width=6, buff=0,
                             max_tip_length_to_length_ratio=0.4)
        cw_out_label = VGroup(
            Text("CW Out", font_size=16, color=COLD_OUT),
            Text("55 °C", font_size=16, color=COLD_OUT),
        ).arrange(DOWN, buff=0.08).next_to(cw_out_arrow, LEFT, buff=0.18)

        self.caption(60.5, "Shell side — the cooling water")
        self.at(61.5, FadeIn(bands), FadeIn(band_lbl),
                run_time=1.2)                       # shell-side space ends 62.7
        # BREATH 2.5 s
        self.at(67.9, GrowArrow(cw_in_arrow), FadeIn(cw_in_label),
                run_time=1.2)                       # inlet ends 69.1
        # BREATH 2.5 s

        cw_dots = VGroup(*[
            Dot(RIGHT * x + UP * (SH_Y + s * BAND_DY), radius=0.07,
                color=COLD_IN)
            for s in (1, -1) for x in (3.2, 2.75, 2.3)
        ])
        self.at(71.6, FadeIn(cw_dots), run_time=0.4)
        self.at(72.2, cw_dots.animate.shift(LEFT * 5.5).set_color(COLD_OUT),
                run_time=4.2, rate_func=linear)
        self.at(76.6, GrowArrow(cw_out_arrow), FadeIn(cw_out_label),
                FadeOut(cw_dots), run_time=1.2)     # CW stream ends 77.8
        # BREATH 2.5 s

        # ══ COUNTER-CURRENT FLOW ═════════════════════════════════
        cc_label = VGroup(
            Text("Counter-Current Flow", font_size=20, color=GREEN),
            Line(LEFT * 1.2, RIGHT * 1.2, color=GREEN, stroke_width=2),
        ).arrange(DOWN, buff=0.08).move_to(DOWN * 1.05)

        self.caption(80.4, "Hot fluid enters left — cooling water enters right")
        self.at(81.6, Indicate(VGroup(hot_in_arrow, hot_in_label),
                               color=HOT_IN), run_time=1.3)
        self.at(84.0, Indicate(VGroup(cw_in_arrow, cw_in_label),
                               color=COLD_IN), run_time=1.3)
        self.caption(86.2, "They flow in opposite directions")
        self.at(87.6, Write(cc_label), run_time=1.3)   # counter-current ends 88.9
        # BREATH 2.5 s

        # ── temperature difference at each end ───────────────────
        dt_left = VGroup(
            Text("hot end", font_size=14, color="#b0bec5"),
            Text("ΔT = 95 °C", font_size=16, color=YELLOW),
        ).arrange(DOWN, buff=0.07).move_to(LEFT * 3.0 + DOWN * 1.05)
        dt_right = VGroup(
            Text("cold end", font_size=14, color="#b0bec5"),
            Text("ΔT = 50 °C", font_size=16, color=YELLOW),
        ).arrange(DOWN, buff=0.07).move_to(RIGHT * 3.0 + DOWN * 1.05)

        self.caption(89.3, "Counter-current keeps a large temperature difference")
        self.at(91.5, FadeIn(dt_left), run_time=0.9)   # ends 92.4
        # BREATH 2.5 s
        self.at(94.9, FadeIn(dt_right), run_time=0.9)  # ΔT pair ends 95.8
        # BREATH 2.5 s
        self.caption(97.6, "A large ΔT along the whole length",
                     "makes heat transfer more efficient")

        # ══ HEAT TRANSFER THROUGH THE TUBE WALL ══════════════════
        # short, thick arrows contained inside the shell: tube surface -> shell
        heat_arrows = VGroup()
        for x in (-2.0, 0.0, 2.0):
            for s in (1, -1):
                heat_arrows.add(Arrow(
                    RIGHT * x + UP * (SH_Y + s * 0.56),
                    RIGHT * x + UP * (SH_Y + s * 0.92),
                    color=YELLOW, stroke_width=5, buff=0,
                    max_tip_length_to_length_ratio=0.45))
        heat_label = Text("Heat Transfer", font_size=16, color=YELLOW
                          ).move_to(UP * 2.42)

        self.caption(100.4, "The driving force is the temperature difference")
        self.at(105.6,
                LaggedStart(*[GrowArrow(a) for a in heat_arrows],
                            lag_ratio=0.12),
                FadeIn(heat_label), run_time=1.6)   # heat transfer ends 107.2
        # BREATH 2.5 s
        self.caption(109.8, "Heat moves hot to cold through the tube wall")

        # ── the tube wall ────────────────────────────────────────
        self.caption(114.7, "The tube wall must be thin enough",
                     "to let heat pass through easily")
        self.at(116.8, Indicate(tubes, color=WHITE, scale_factor=1.06),
                run_time=1.5)
        self.caption(119.6, "and strong enough for the pressure",
                     "of both fluids")

        # ── sizes in a real plant ────────────────────────────────
        self.caption(124.3, "In a real plant they come in many sizes")
        self.caption(129.2, "From table-top units to exchangers",
                     "several metres long and over a metre across")

        # ══ WHERE THEY ARE USED ══════════════════════════════════
        apps = VGroup(
            Text("Where they are used", font_size=21, color=BRAND, weight=BOLD),
            Text("•  Cooling reactor effluents", font_size=19, color=WHITE),
            Text("•  Preheating feed streams", font_size=19, color=WHITE),
            Text("•  Condensing vapours", font_size=19, color=WHITE),
            Text("•  Heating cold fluids before a distillation column",
                 font_size=19, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.24).move_to(self.LOWER_POS)

        self.swap_lower(136.5, apps[0], run_time=0.6)
        self.at(138.3, FadeIn(apps[1]), run_time=0.6)
        self.at(140.5, FadeIn(apps[2]), run_time=0.6)
        self.at(142.7, FadeIn(apps[3]), run_time=0.6)
        self.at(144.6, FadeIn(apps[4]), run_time=0.6)
        self.lower = apps                       # block fades out together

        # ══ DESIGN BASIS ═════════════════════════════════════════
        design_head = VGroup(
            Text("Design basis", font_size=19, color=BRAND, weight=BOLD),
            Text("Q  =  U  ×  A  ×  ΔT_lm", font_size=26, color=WHITE),
        ).arrange(DOWN, buff=0.13)

        terms = VGroup(
            Text("A  —  required heat transfer area",
                 font_size=16, color="#cfd8dc"),
            Text("Q  —  heat duty", font_size=16, color="#cfd8dc"),
            Text("U  —  overall heat transfer coefficient",
                 font_size=16, color="#cfd8dc"),
            Text("ΔT_lm  —  log mean temperature difference",
                 font_size=16, color="#cfd8dc"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.13)

        note = Text("Each of these — in future videos",
                    font_size=15, color="#78909c")

        design = VGroup(design_head, terms, note
                        ).arrange(DOWN, buff=0.15).move_to(self.LOWER_POS + UP * 0.14)

        self.swap_lower(147.3, design_head, run_time=0.8)
        self.at(149.3, FadeIn(terms[0]), run_time=0.6)
        self.at(153.3, FadeIn(terms[1]), run_time=0.6)
        self.at(155.3, FadeIn(terms[2]), run_time=0.6)
        self.at(158.1, FadeIn(terms[3]), run_time=0.6)
        self.at(161.2, FadeIn(note), run_time=0.6)
        self.lower = design

        # ══ KEY POINTS ═══════════════════════════════════════════
        kp = VGroup(
            Text("Key Points", font_size=21, color=BRAND, weight=BOLD),
            Text("•  Heat passes between two fluids through the tube wall",
                 font_size=18, color=WHITE),
            Text("•  Hot fluid inside the tubes", font_size=18, color=WHITE),
            Text("•  Cold fluid on the shell side", font_size=18, color=WHITE),
            Text("•  Counter-current flow for maximum efficiency",
                 font_size=18, color=WHITE),
            Text("•  Temperature difference is the driving force",
                 font_size=18, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.20).move_to(self.LOWER_POS)

        self.swap_lower(164.2, kp[0], run_time=0.8)
        self.at(166.9, FadeIn(kp[1]), run_time=0.6)
        self.at(173.2, FadeIn(kp[2]),
                Indicate(VGroup(tubes, hot_in_arrow, hot_out_arrow),
                         color=HOT_IN, scale_factor=1.04), run_time=1.0)
        self.at(175.8, FadeIn(kp[3]),
                Indicate(VGroup(bands, cw_in_arrow, cw_out_arrow),
                         color=COLD_IN, scale_factor=1.04), run_time=1.0)
        self.at(178.3, FadeIn(kp[4]),
                Indicate(cc_label, color=GREEN), run_time=1.0)
        self.at(181.2, FadeIn(kp[5]),
                Indicate(VGroup(dt_left, dt_right), color=YELLOW),
                run_time=1.0)
        self.lower = kp

        # ══ CLOSE — watermark pulses gently, no end card ═════════
        tagline = Text("Chemical engineering fundamentals, explained simply.",
                       font_size=24, color=WHITE).move_to(self.LOWER_POS)
        # key points summary complete at 182.2 — BREATH 2.5 s
        self.swap_lower(184.7, tagline, run_time=0.9)
        self.at(186.4, Indicate(watermark, color=WHITE, scale_factor=1.12),
                run_time=1.2)

        # bottom LEFT — keeps the bottom right corner clear for the watermark
        reference = Text(
            "Reference: Coulson & Richardson — Chemical Engineering Vol. 1, Ch. 12",
            font_size=13, color="#607d8b"
        ).to_corner(DL, buff=0.22)
        self.at(188.9, FadeIn(reference), run_time=0.8)

        # Everything stays on screen until the narration ends.
        self.hold_until(TOTAL_RUNTIME)
