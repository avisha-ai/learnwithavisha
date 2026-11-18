"""
LearnWithAvisha · 3D shell-and-tube exchanger panel ("what it looks like in the plant")

Renders the right-hand panel of the widescreen side-by-side format with PyVista
(free, open source, runs offline). Same colour language as the 2D episodes:
red → orange = hot tube side cooling down, blue → light blue = cold shell side warming up.

Geometry matches the 2D illustration in the episode pipelines: hot fluid enters the
left channel head (top) and leaves the right head (bottom), single tube pass; the
cold fluid crosses the shell between segmental baffles, entering at the right
(countercurrent) or the left (parallel).

Usually called from side_by_side.py; standalone use:
    .venv/bin/python3 pipeline/hx3d.py --duration 20 --out out/hx3d_test.mp4
    .venv/bin/python3 pipeline/hx3d.py --still 5 --out out/hx3d_frame.png      # one frame, quick look
Options: --mode counter|parallel  --flip-at SECONDS (parallel → counter)  --fouling  --draft

Install (once):  .venv/bin/pip install pyvista
"""

import argparse, math, shutil, subprocess, sys
from pathlib import Path

import numpy as np

try:
    import pyvista as pv
except ImportError:
    sys.exit("pyvista not found — run:\n  .venv/bin/pip install pyvista")

ROOT = Path(__file__).resolve().parent.parent
_MAMBA_BIN = ROOT / ".micromamba/root/envs/manim/bin"
FFMPEG = shutil.which("ffmpeg") or str(_MAMBA_BIN / "ffmpeg")

# panel size in the 1920x1080 side-by-side frame (see side_by_side.py)
PANEL_W, PANEL_H = 1160, 1080
FPS = 30
SUPERSAMPLE = 2         # render at 2x the output size, scale down (Lanczos) for sharp edges

# colours shared with the 2D pipelines
BG = (18, 20, 28)
HOT, HOT_OUT = (235, 70, 60), (255, 190, 80)
COLD, COLD_OUT = (70, 140, 240), (160, 205, 255)
METAL, HEAD_METAL, SHEET_METAL = (118, 124, 136), (128, 104, 104), (165, 170, 180)
TUBE, DEPOSIT = (200, 205, 215), (105, 72, 45)   # dark deposit so the hot particles stand out
WHITE, GREY = (255, 255, 255), (185, 190, 200)

# geometry (arbitrary units; x = exchanger axis, z = up)
L = 6.0                  # shell length, tubesheet to tubesheet
R = 1.0                  # shell radius
HEAD_L = 0.6             # channel-head barrel length
TUBE_R = 0.07
BAFFLE_XS = (-1.8, -0.6, 0.6, 1.8)
BAFFLE_CUT = 0.55        # chord height of the baffle window (from the centre)
SHELL_NOZ_X = (-2.4, 2.4)
X0, X1 = -L / 2, L / 2

def rgb(c):
    return tuple(v / 255 for v in c)

# ── equipment ────────────────────────────────────────────────────────────────
def tube_centres(pitch=0.27, limit=R - 0.22):
    """Triangular-pitch bundle inside the shell, as (y, z) pairs."""
    pts = []
    for j in range(-4, 5):
        z = j * pitch * math.sqrt(3) / 2
        off = (j % 2) * pitch / 2
        for i in range(-5, 6):
            y = i * pitch + off
            if math.hypot(y, z) <= limit:
                pts.append((y, z))
    return pts

def segmental_baffle(x, top_cut):
    """Disc in the y-z plane at x with a window cut off the top (or bottom)."""
    r = R * 0.97
    a = math.asin(BAFFLE_CUT / r)
    th = np.linspace(math.pi - a, 2 * math.pi + a, 64)   # the long way round, via the bottom
    y, z = r * np.cos(th), r * np.sin(th)
    if not top_cut:
        z = -z
    pts = np.column_stack([np.full_like(y, x), y, z])
    return pv.PolyData(pts, faces=np.hstack([[len(pts)], np.arange(len(pts))]))

def nozzle(x, top, at_head=False):
    """Vertical flanged nozzle; returns (pipe, flange, open-end point)."""
    sign = 1 if top else -1
    z0 = sign * (0.0 if at_head else R * 0.95)    # starts at the vessel wall (inside the opaque head)
    z_end = sign * (R + 0.55)
    pipe = pv.Cylinder(center=(x, 0, (z0 + z_end) / 2), direction=(0, 0, 1), radius=0.2,
                       height=abs(z_end - z0))
    flange = pv.Cylinder(center=(x, 0, z_end), direction=(0, 0, 1), radius=0.3, height=0.08)
    # label anchor: bottom labels sit further out so the text clears the flange
    return pipe, flange, (x, 0, z_end + sign * (0.25 if top else 0.75))

class Exchanger:
    def __init__(self, plotter, fouling=False):
        p = self.p = plotter
        metal = dict(smooth_shading=True, specular=0.5, specular_power=20)
        # shell: see-through so the bundle and the flow inside are visible
        p.add_mesh(pv.Cylinder(center=(0, 0, 0), direction=(1, 0, 0), radius=R, height=L,
                               resolution=96, capping=False),
                   color=rgb(METAL), opacity=0.22, **metal)
        # channel heads (bonnets): barrel + domed end, opaque
        for sx in (-1, 1):
            xc = sx * (L / 2 + HEAD_L / 2)
            p.add_mesh(pv.Cylinder(center=(xc, 0, 0), direction=(1, 0, 0), radius=R,
                                   height=HEAD_L, resolution=96), color=rgb(HEAD_METAL), **metal)
            dome = pv.Sphere(radius=1.0, center=(0, 0, 0), theta_resolution=64, phi_resolution=64)
            dome = dome.scale([0.45, R, R], inplace=False).translate((sx * (L / 2 + HEAD_L), 0, 0),
                                                                     inplace=False)
            p.add_mesh(dome, color=rgb(HEAD_METAL), **metal)
        # tubesheets
        for x in (X0, X1):
            p.add_mesh(pv.Cylinder(center=(x, 0, 0), direction=(1, 0, 0), radius=R * 1.08,
                                   height=0.08, resolution=96), color=rgb(SHEET_METAL), **metal)
        # tube bundle
        self.tubes = tube_centres()
        bundle = pv.MultiBlock([pv.Cylinder(center=(0, y, z), direction=(1, 0, 0), radius=TUBE_R,
                                            height=L, resolution=24, capping=False)
                                for y, z in self.tubes]).combine()
        # fouled tubes stay brown but see-through enough for the hot fluid inside to read
        p.add_mesh(bundle, color=rgb(DEPOSIT if fouling else TUBE),
                   opacity=0.25 if fouling else 0.30, smooth_shading=True)
        # segmental baffles, windows alternating top / bottom
        for i, x in enumerate(BAFFLE_XS):
            p.add_mesh(segmental_baffle(x, top_cut=(i % 2 == 0)), color=rgb(SHEET_METAL),
                       opacity=0.35)
        # nozzles: tube side on the heads, shell side on the shell
        self.ends = {}
        hx_in, hx_out = X0 - HEAD_L / 2, X1 + HEAD_L / 2
        for key, x, top, head in [("hot_in", hx_in, True, True), ("hot_out", hx_out, False, True),
                                  ("shell_r", SHELL_NOZ_X[1], True, False),
                                  ("shell_l", SHELL_NOZ_X[0], False, False)]:
            pipe, flange, end = nozzle(x, top, head)
            p.add_mesh(pipe, color=rgb(HEAD_METAL if head else METAL), **metal)
            p.add_mesh(flange, color=rgb(SHEET_METAL), **metal)
            self.ends[key] = end


# ── flow ─────────────────────────────────────────────────────────────────────
class Flow:
    """Particles: tube side always left → right; shell side zig-zags round the baffles."""
    def __init__(self, plotter, tubes, point_size=12, n_per_tube=6, n_shell=220, seed=7):
        rng = np.random.default_rng(seed)
        self.tubes = np.array(tubes)
        self.hot_tube = np.repeat(np.arange(len(tubes)), n_per_tube)
        self.hot_s = rng.random(len(self.hot_tube))
        self.cold_s = rng.random(n_shell)
        self.cold_y = rng.uniform(-0.75, 0.75, n_shell)
        self.cold_jit = rng.uniform(-0.12, 0.12, n_shell)
        self.hot_speed, self.cold_speed = 0.10, 0.08     # fraction of length per second
        self.hot = pv.PolyData(self._hot_pts())
        self.cold = pv.PolyData(self._cold_pts(1))
        self.hot["rgb"] = self._colours(self.hot_s, HOT, HOT_OUT)
        self.cold["rgb"] = self._colours(self.cold_s, COLD, COLD_OUT)
        for mesh in (self.hot, self.cold):
            plotter.add_mesh(mesh, scalars="rgb", rgb=True, render_points_as_spheres=True,
                             point_size=point_size)

    @staticmethod
    def _colours(s, c0, c1):
        s = s[:, None]
        return ((1 - s) * np.array(c0) + s * np.array(c1)).astype(np.uint8)

    def _hot_pts(self):
        yz = self.tubes[self.hot_tube]
        x = X0 + self.hot_s * L
        return np.column_stack([x, yz[:, 0], yz[:, 1]])

    def _shell_z(self, x):
        """Height of the shell-side path at x: weaves through the alternating baffle windows."""
        knots_x = np.array([X0] + list(BAFFLE_XS) + [X1])
        knots_z = np.array([0.0] + [0.72 if i % 2 == 0 else -0.72 for i in range(len(BAFFLE_XS))] + [0.0])
        return np.interp(x, knots_x, knots_z)

    def _cold_pts(self, direction):
        # s runs inlet → outlet; direction +1: enters right (countercurrent), -1: enters left
        x = X1 - self.cold_s * L if direction > 0 else X0 + self.cold_s * L
        z = self._shell_z(x) + self.cold_jit
        y = self.cold_y * np.sqrt(np.clip(1 - (z / R) ** 2, 0.05, 1))
        return np.column_stack([x, y, z])

    def step(self, dt, direction):
        self.hot_s = (self.hot_s + self.hot_speed * dt) % 1.0
        self.cold_s = (self.cold_s + self.cold_speed * dt) % 1.0
        self.hot.points = self._hot_pts()
        self.cold.points = self._cold_pts(direction)
        self.hot["rgb"] = self._colours(self.hot_s, HOT, HOT_OUT)
        self.cold["rgb"] = self._colours(self.cold_s, COLD, COLD_OUT)


# ── scene ────────────────────────────────────────────────────────────────────
def _labels(plotter, ends, counter, size):
    cold_in, cold_out = ("shell_r", "shell_l") if counter else ("shell_l", "shell_r")
    actors = []
    for key, text, col in [("hot_in", "HOT IN", HOT), ("hot_out", "HOT OUT", HOT_OUT),
                           (cold_in, "COLD IN", COLD), (cold_out, "COLD OUT", COLD_OUT)]:
        actors.append(plotter.add_point_labels([ends[key]], [text], font_size=size, bold=True,
                                               text_color=rgb(col), shape=None, show_points=False,
                                               always_visible=True))
    return actors

def _set_visible(actors, on):
    for a in actors:
        a.SetVisibility(on)

def build(size, fouling, mode, flip_at):
    # everything is laid out from the render size, so text and particles look the same at any size
    w, h = size[0] * SUPERSAMPLE, size[1] * SUPERSAMPLE
    p = pv.Plotter(off_screen=True, window_size=(w, h))
    p.set_background(rgb(BG))
    if SUPERSAMPLE == 1:              # the 2x render + downscale already does the anti-aliasing
        try:
            p.enable_anti_aliasing("ssaa")
        except Exception:
            pass
    ex = Exchanger(p, fouling=fouling)
    flow = Flow(p, ex.tubes, point_size=max(4, round(12 * h / PANEL_H)))
    fs = max(12, int(h / 40))
    labels_par = _labels(p, ex.ends, counter=False, size=fs)
    labels_ctr = _labels(p, ex.ends, counter=True, size=fs)
    p.add_text("IN THE PLANT", position=(int(w * 0.05), int(h * 0.90)), font_size=int(fs * 0.9),
               color=rgb(GREY))
    sub = "Shell-and-tube exchanger" + (" · fouled tubes" if fouling else "")
    p.add_text(sub, position=(int(w * 0.05), int(h * 0.05)), font_size=int(fs * 0.75), color=rgb(GREY))
    place_camera(p, 0.0)
    p.show(auto_close=False)          # off-screen: initialises the render window, opens nothing
    state = dict(p=p, flow=flow, lab_par=labels_par, lab_ctr=labels_ctr, mode=mode, flip_at=flip_at)
    return state

def counter_at(state, t):
    if state["flip_at"] is not None:
        return t >= state["flip_at"]
    return state["mode"] == "counter"

def place_camera(p, t):
    # three-quarter view from the front, slow gentle orbit so the depth reads
    az = math.radians(-35 + 18 * math.sin(2 * math.pi * t / 30))
    el = math.radians(24)
    dist = 15.5          # far enough that both heads and all four nozzle labels stay in frame
    p.camera.position = (dist * math.cos(el) * math.sin(az), -dist * math.cos(el) * math.cos(az),
                         dist * math.sin(el))
    p.camera.focal_point = (0, 0, 0)
    p.camera.up = (0, 0, 1)

def frame_at(state, t, dt):
    ctr = counter_at(state, t)
    _set_visible(state["lab_ctr"], ctr)
    _set_visible(state["lab_par"], not ctr)
    state["flow"].step(dt, 1 if ctr else -1)
    place_camera(state["p"], t)
    state["p"].render()
    return state["p"].screenshot(return_img=True)


# ── output ───────────────────────────────────────────────────────────────────
def render_video(out, duration, size=(PANEL_W, PANEL_H), fps=FPS, fouling=False,
                 mode="counter", flip_at=None):
    state = build(size, fouling, mode, flip_at)
    n = int(math.ceil(duration * fps))
    first = frame_at(state, 0.0, 0.0)
    fh, fw = first.shape[:2]
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{fw}x{fh}", "-r", str(fps), "-i", "-",
           "-vf", f"scale={size[0]}:{size[1]}:flags=lanczos", "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-preset", "medium", "-crf", "18", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ff.stdin.write(np.ascontiguousarray(first[:, :, :3]).tobytes())
    for i in range(1, n):
        img = frame_at(state, i / fps, 1 / fps)
        ff.stdin.write(np.ascontiguousarray(img[:, :, :3]).tobytes())
        if i % (fps * 10) == 0:
            print(f"    3D: {i / fps:.0f}/{duration:.0f}s")
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("  3D panel: ffmpeg failed")
    state["p"].close()
    print(f"  3D panel: {out}")
    return Path(out)

def render_still(out, t, size=(PANEL_W, PANEL_H), fouling=False, mode="counter", flip_at=None):
    from PIL import Image
    state = build(size, fouling, mode, flip_at)
    # run the particles up to t so the still looks like the video at that moment
    steps = int(t * 10)
    for _ in range(steps):
        state["flow"].step(0.1, 1 if counter_at(state, t) else -1)
    img = frame_at(state, t, 0.0)
    Image.fromarray(img[:, :, :3]).resize(size, Image.LANCZOS).save(out)
    state["p"].close()
    print(f"  3D still: {out}")
    return Path(out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=10.0)
    ap.add_argument("--still", type=float, help="render one PNG at this time (s) instead of a video")
    ap.add_argument("--mode", choices=("counter", "parallel"), default="counter")
    ap.add_argument("--flip-at", type=float, help="start parallel, switch to countercurrent at this time (s)")
    ap.add_argument("--fouling", action="store_true", help="show fouled (brown) tubes")
    ap.add_argument("--draft", action="store_true", help="half size, 15 fps — layout check")
    a = ap.parse_args()
    size = (PANEL_W // 2, PANEL_H // 2) if a.draft else (PANEL_W, PANEL_H)
    if a.still is not None:
        render_still(a.out, a.still, size, a.fouling, a.mode, a.flip_at)
    else:
        render_video(a.out, a.duration, size, 15 if a.draft else FPS, a.fouling, a.mode, a.flip_at)

if __name__ == "__main__":
    main()
