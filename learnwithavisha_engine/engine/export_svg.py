"""
engine/export_svg.py — write a world asset out as a real SVG.

Be straight about what these files are. The RENDERER reads the Python; the
SVG is an export, not the source. It exists because the architecture asks
for one and because a canonical asset should be inspectable and diffable
without running Manim — you can open exterior.svg and see exactly the E-101
that every episode will get.

The reason the source is not SVG: these assets are parametric. E-101 shades
itself from world/lighting.json, so moving the sun re-lights the machine.
The operator is a solver, not a drawing — a single SVG cannot hold a gait.
If hand-drawn art ever replaces a builder, that is a real piece of work and
the loader is where it would go.

Run: python -m engine.export_svg
"""

import os
import sys

from manim import *

import engine.draw as draw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     ".."))


def _hex(c):
    try:
        return c.to_hex()
    except Exception:
        return str(c)


def to_svg(mob, path, pad=0.25, px=1600, title=""):
    fam = [m for m in mob.get_family()
           if isinstance(m, VMobject) and len(m.points) >= 4]
    if not fam:
        raise ValueError("nothing to export for %s" % path)
    xs, ys = [], []
    for m in fam:
        p = m.points
        xs += [float(p[:, 0].min()), float(p[:, 0].max())]
        ys += [float(p[:, 1].min()), float(p[:, 1].max())]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    s = px / (x1 - x0)
    w, h = px, (y1 - y0) * s

    def X(p):
        return (float(p[0]) - x0) * s

    def Y(p):
        return (y1 - float(p[1])) * s

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.0f" height="%.0f" '
           'viewBox="0 0 %.0f %.0f">' % (w, h, w, h),
           '<title>%s</title>' % (title or os.path.basename(path)),
           '<desc>Exported from the LearnWithAvisha world. The Python builder '
           'is the source; this file is a record of it.</desc>',
           '<rect width="100%%" height="100%%" fill="%s"/>' % draw.BRAND_DEEP]
    for m in fam:
        fo, so = m.get_fill_opacity(), m.get_stroke_opacity()
        if fo <= 0.003 and so <= 0.003:
            continue
        d = []
        for sp in m.get_subpaths():
            if len(sp) < 4:
                continue
            d.append("M%.2f %.2f" % (X(sp[0]), Y(sp[0])))
            for i in range(0, len(sp) - 3, 3):
                a, b, c = sp[i + 1], sp[i + 2], sp[i + 3]
                d.append("C%.2f %.2f %.2f %.2f %.2f %.2f"
                         % (X(a), Y(a), X(b), Y(b), X(c), Y(c)))
            d.append("Z")
        if not d:
            continue
        attrs = ['d="%s"' % " ".join(d)]
        attrs.append('fill="%s"' % _hex(m.get_fill_color()) if fo > 0.003
                     else 'fill="none"')
        if fo > 0.003 and fo < 0.999:
            attrs.append('fill-opacity="%.3f"' % fo)
        if so > 0.003 and m.get_stroke_width() > 0:
            attrs.append('stroke="%s"' % _hex(m.get_stroke_color()))
            attrs.append('stroke-width="%.2f"'
                         % max(0.3, m.get_stroke_width() * s / 135.0))
            if so < 0.999:
                attrs.append('stroke-opacity="%.3f"' % so)
        out.append("<path %s/>" % " ".join(attrs))
    out.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    return path, len(out) - 5


def main():
    sys.path.insert(0, ROOT)
    from engine.loader import Location, Equipment, Character, Instrument
    W = os.path.join(ROOT, "world")
    jobs = []

    loc = Location("exchanger_bay")
    d = os.path.join(W, "locations", "exchanger_bay")
    jobs.append((VGroup(loc.background.build_sky(), loc.background.build_far(),
                        loc.background.build_structure()),
                 os.path.join(d, "background.svg"), "exchanger_bay background"))
    jobs.append((loc.pipework.build_pipework(),
                 os.path.join(d, "pipework.svg"), "exchanger_bay pipework"))
    jobs.append((VGroup(loc.foreground.build_walkway(),
                        loc.foreground.build_handrail(),
                        loc.foreground.build_foreground(),
                        loc.foreground.build_proscenium()),
                 os.path.join(d, "foreground.svg"), "exchanger_bay foreground"))

    eq = Equipment("E-101")
    jobs.append((eq.exterior.build(),
                 os.path.join(W, "equipment", "E-101", "exterior.svg"),
                 "E-101 shell and tube exchanger, exterior"))

    inst = Instrument("temperature_gauge")
    jobs.append((VGroup(inst.module.build_digital("87", 1.62, y=2.15),
                        inst.module.build_dial("TI-1013", 2.55, 2.15,
                                               r=0.13, frac=0.62)),
                 os.path.join(W, "instruments", "temperature_gauge.svg"),
                 "temperature gauge, digital head and local dial"))

    for name in ("wade", "lyra", "ellis", "operator_01"):
        ch = Character(name)
        for pose in ("neutral", "walking", "inspecting"):
            p_ = ch.poses[pose]
            kw = dict(walking=p_["walking"], head_pitch=p_["head_pitch"])
            if pose == "walking":
                kw["phase"] = 0.95
            if pose == "inspecting":
                kw["facing"] = -1
            jobs.append((ch.rig.build(0.0, **kw),
                         os.path.join(W, "characters", name, pose + ".svg"),
                         "%s — %s" % (ch.data.get("name", name).upper(),
                                      pose)))

    for mob, path, title in jobs:
        p, n = to_svg(mob, path, title=title)
        print("  %-62s %4d paths" % (os.path.relpath(p, ROOT), n))


if __name__ == "__main__":
    main()
