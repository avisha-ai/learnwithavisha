"""
LearnWithAvisha — Visual Pilot 001
bay.py — composition of the E-101 bay.

Layer order is the whole trick. Far to near:
    SKY -> shafts -> FAR (+haze) -> MID (+haze) -> NEAR -> drift -> FORE

Two rules hold this together:
  1. The sky is the brightest value. Everything else silhouettes against
     dawn. Invert that and the plant reads as flat clipart.
  2. Distance is loss of contrast, never a change in light direction.
"""

from manim import *
import plant_world as w


def assemble(t=0.0, detail=1.0):
    """Returns the bay as ordered layers. t is absolute seconds, for steam."""
    L = {}
    L["sky"] = w.build_sky()

    L["shafts"] = VGroup(
        w.light_shaft(-6.4, spread=4.4, width=1.6, opacity=0.030),
        w.light_shaft(-1.6, spread=3.8, width=1.1, opacity=0.022),
        w.light_shaft(4.6, spread=3.2, width=0.8, opacity=0.014),
    )

    far = VGroup(w.build_far())
    far.add(w.steam_column(8.55, 7.5, t, n=10, rise=3.4, size=0.34,
                           peak=0.045, drift=2.2, spread=0.75, seed=0.11))
    far.add(w.steam_column(-4.1, 3.2, t, n=10, rise=3.0, size=0.52,
                           peak=0.055, drift=1.9, spread=0.62, seed=0.62))
    # backlit vent plume just left of the bay — it sits in front of the sun
    far.add(w.steam_column(-2.35, 0.70, t, n=9, rise=3.2, size=0.26,
                           peak=0.115, drift=1.2, spread=0.38, seed=0.05))
    L["far"] = far
    L["haze_far"] = w.haze_sheet(0.26)

    mid = VGroup(w.build_structure())
    mid.add(w.steam_column(-1.25, w.RACK_Y + 1.7, t, n=7, rise=2.1,
                           size=0.15, peak=0.10, drift=0.8, spread=0.28,
                           seed=0.37))
    L["mid"] = mid
    L["haze_mid"] = w.haze_sheet(0.11)

    near = VGroup()
    near.add(w.build_pipework())
    near.add(w.build_e101(detail=detail))
    near.add(w.build_dial("TI-1013", 1.15, 0.62, r=0.115, frac=0.71))
    near.add(w.build_dial("PI-1012", 6.10, 0.86, r=0.125, frac=0.46))
    near.add(w.build_ti1014("87"))
    near.add(w.build_handrail())
    near.add(w.build_walkway())
    L["near"] = near

    L["drift"] = VGroup(
        w.steam_column(-5.0, -1.4, t, n=6, rise=1.5, size=0.85, peak=0.030,
                       drift=3.4, spread=0.40, seed=0.83),
        w.steam_column(7.5, -1.9, t, n=6, rise=1.3, size=0.80, peak=0.026,
                       drift=3.0, spread=0.35, seed=0.29),
    )
    L["fore"] = VGroup(w.build_foreground(), w.build_proscenium())
    return L


def add_bay(scene, L, order=("sky", "shafts", "far", "haze_far", "mid",
                             "haze_mid", "near", "drift")):
    for k in order:
        scene.add(L[k])


def place_watermark(scene, frame):
    """Brand rule: LWA monogram bottom right on every frame, never occluded.
    Positioned directly rather than by updater so it is correct in stills."""
    wm = w.build_watermark()
    s = frame.width / config.frame_width
    wm.set(width=wm.width * s)
    wm.move_to(frame.get_corner(DR) + s * (UP + LEFT) * 0.77)
    scene.add(wm)
    return wm
