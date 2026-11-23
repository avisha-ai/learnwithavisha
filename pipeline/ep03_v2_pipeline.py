"""
LearnWithAvisha · Plant Mysteries · S1 · E3 — Baffles: What They Do and Why
Video generation pipeline: Kokoro TTS narration + programmatic animation + moviepy assembly

Run from the learnwithavisha folder:
    cd ~/Documents/Avisha/learnwithavisha
    .venv/bin/python3 pipeline/ep03_v2_pipeline.py

Install (once):
    .venv/bin/pip install kokoro-onnx soundfile

ffmpeg is taken from the micromamba manim env if it is not already on PATH.

Output (in <repo>/out/; copy approved files to episodes/):
    lwa_s1e03_baffles_master.mp4      1080x1920 H.264 30fps, no captions
    lwa_s1e03_baffles_captioned.mp4   master with burned-in captions (release file)
    lwa_s1e03_baffles_web.mp4         720x1280 web derivative (<=5 MB)
    lwa_s1e03_baffles.srt / .vtt      captions, timed from the narration itself
    lwa_s1e03_baffles_poster.jpg      poster frame
    lwa_s1e03_baffles_wide.mp4        1920x1080 2D + 3D side by side (only with --wide;
                                                  needs pyvista, see side_by_side.py)

Timing model: every narration line is voiced as its own Kokoro clip, so each
scene's length and each caption's in/out times come from measured audio.
Captions are split into short cues (at most two lines) and burned in from an
ASS file authored at the real 1080x1920 resolution.

EP03 (23 Nov 2026) keeps the EP02 machinery (hook first, no duplicate subtitles, breath
  pauses) and adds the baffles cutaway; the 3D panel takes baffles out and back in with the 2D.
EP02 changes vs EP01 (spec, 17 Nov 2026):
  * Hook first: the opening line plants the mystery over the exchanger
    ("designed clean … six months later … what happened?") before any explanation.
  * No duplicate subtitles: a burned-in caption cue is dropped when the same words
    are already drawn on the canvas at that moment (found by probing each frame's
    drawn text, see onscreen_text()). The SRT/VTT sidecars keep every line.
  * Breath pauses: KEY_GAP (0.5 s) of silence after each key-reveal line.

Layout: diagrams live in y 0–1520; the caption band is the lower third
(y ≈ 1590–1760). Nothing drawn by the scenes may enter the caption band.
"""

import os, sys, math, textwrap, subprocess, hashlib, shutil, re
from pathlib import Path

try:
    from moviepy import VideoClip, AudioFileClip, concatenate_videoclips
except ImportError:
    sys.exit("moviepy not found — pip install moviepy")

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow / numpy missing — pip install Pillow numpy")

try:
    import kokoro_onnx
    import soundfile as sf
except ImportError:
    sys.exit("kokoro-onnx / soundfile not found — run:\n"
             "  .venv/bin/pip install kokoro-onnx soundfile")

# ffmpeg lives only in the micromamba manim env on this Mac
ROOT = Path(__file__).resolve().parent.parent   # repo root (this file lives in pipeline/)
_MAMBA_BIN = ROOT / ".micromamba/root/envs/manim/bin"
if not shutil.which("ffmpeg") and (_MAMBA_BIN / "ffmpeg").exists():
    os.environ["PATH"] = f"{_MAMBA_BIN}{os.pathsep}{os.environ['PATH']}"

W, H = 1080, 1920
FPS  = 30
BG   = (18, 20, 28)
# Kokoro voice — same provider and voice Isha (Nim-Isha) uses
KOKORO_VOICE = "af_heart"
KOKORO_SPEED = 0.95   # slightly slower for educational pacing
LINE_GAP  = 0.30      # silence between narration lines inside a scene (s)
SCENE_GAP = 0.50      # extra silence at the end of each scene (s)
KEY_GAP   = 0.50      # breath after a key-reveal line, so the idea lands (s)
BREATH    = "breath"  # third element of a SCENES line: pause KEY_GAP after it
END_HOLD  = 3.0       # final frame stays up after the last word (s)
CAPTION_MAX_CHARS = 50   # ≈ two lines at 60 px in the caption band
DIAGRAM_BOTTOM = 1520    # scenes draw nothing below this line
# Episode identity — every episode is Season 1
EP_TAG   = "S1 · E3"
EP_TITLE = "Baffles: What They Do and Why"
EP_SLUG  = "lwa_s1e03_baffles"           # output filename stem
WM_START, WM_END = 1.0, 4.0     # wordmark fully visible (absolute s); also on the end card
OUT = ROOT / "out"        # scratch render dir (gitignored); approved files go to episodes/
OUT.mkdir(exist_ok=True)
TTS_CACHE = OUT / "tts_cache"
TTS_CACHE.mkdir(exist_ok=True)

HOT, COLD = (235,70,60), (70,140,240)
HOT_BG, COLD_BG = (60,16,16), (14,26,64)
YELLOW, GREY, WHITE = (255,215,60), (185,190,200), (255,255,255)
WALL = (150,150,155)

# ── fonts (Mac paths first, Linux fallback) ───────────────────────────────────
_font_cache = {}
def get_font(size=48, bold=False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    candidates = [
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        # Linux (CI): Liberation Sans has Arial's metrics, so line breaks match the Mac
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                f = ImageFont.truetype(c, size)
                _font_cache[key] = f
                return f
            except Exception:
                pass
    return ImageFont.load_default()

def canvas(w=W, h=H, bg=BG):
    img = Image.new("RGB", (w, h), bg)
    return img, ImageDraw.Draw(img)

def draw_text_centre(draw, text, y, font, colour=WHITE, max_w=980):
    """Centred, word-wrapped to max_w pixels; y is the vertical centre of the block."""
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = f"{cur} {wd}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur); cur = wd
    if cur: lines.append(cur)
    line_h = int(font.size*1.22)
    y_cur = int(y - len(lines)*line_h/2 + line_h/2)
    for line in lines:
        draw.text((W//2, y_cur), line, font=font, fill=colour, anchor="mm")
        y_cur += line_h

def to_arr(img): return np.array(img)

def make_scene_clip(render_fn, duration, marks, t0=0.0):
    """t0 is the scene's start in the episode, so the opening wordmark follows absolute time."""
    def mf(t):
        img = render_fn(t, marks, duration)
        a = wordmark_alpha(t0+t)
        return to_arr(stamp_wordmark(img, a) if a > 0 else img)
    return VideoClip(mf, duration=duration).with_fps(FPS)

def _ease(x): x=max(0.0,min(1.0,x)); return 0.5-0.5*math.cos(math.pi*x)

def _arrow(draw, cx, cy, colour, right=True, w=76, h=88):
    if right:
        draw.polygon([(cx-w//2,cy-h//2),(cx+w//2,cy),(cx-w//2,cy+h//2)], fill=colour)
    else:
        draw.polygon([(cx+w//2,cy-h//2),(cx-w//2,cy),(cx+w//2,cy+h//2)], fill=colour)

def _ring_text(draw, xy, text, font, colour, anchor, ring=False):
    draw.text(xy, text, font=font, fill=colour, anchor=anchor)
    if ring:
        b = draw.textbbox(xy, text, font=font, anchor=anchor)
        draw.rounded_rectangle([b[0]-14,b[1]-12,b[2]+14,b[3]+12], radius=14, outline=YELLOW, width=5)

# ── Two-lane flow schematic (the simplified exchanger) ───────────────────────
SCH_Y0 = 560
def draw_schematic(draw, counter=False, hot_out=51, cold_out=49, y0=SCH_Y0,
                   labels=True, wall_hi=False, hi_hot=False, hi_cold=False,
                   cold_out_colour=None):
    x0, x1, lane, wall = 40, 1040, 220, 26
    h_top, h_bot = y0, y0+lane
    c_top, c_bot = h_bot+wall, h_bot+wall+lane
    draw.rectangle([x0,h_top,x1,h_bot], fill=HOT_BG)
    draw.rectangle([x0,c_top,x1,c_bot], fill=COLD_BG)
    draw.rectangle([x0,h_bot,x1,c_top], fill=YELLOW if wall_hi else WALL)
    draw.rectangle([x0,h_top,x1,c_bot], outline=(210,210,215), width=4)
    hy, cy = (h_top+h_bot)//2, (c_top+c_bot)//2
    for ax in (360, 540, 720):
        _arrow(draw, ax, hy, HOT, True)
        _arrow(draw, ax, cy, COLD, not counter)
    f = get_font(66, True)
    _ring_text(draw, (x0+24,hy), "90°C", f, HOT, "lm")
    _ring_text(draw, (x1-24,hy), f"{hot_out}°C", f, HOT, "rm", ring=hi_hot)
    cc = cold_out_colour or COLD
    if counter:
        _ring_text(draw, (x1-24,cy), "10°C", f, COLD, "rm")
        _ring_text(draw, (x0+24,cy), f"{cold_out}°C", f, cc, "lm", ring=hi_cold)
    else:
        _ring_text(draw, (x0+24,cy), "10°C", f, COLD, "lm")
        _ring_text(draw, (x1-24,cy), f"{cold_out}°C", f, cc, "rm", ring=hi_cold)
    if labels:
        draw.text((W//2,h_top-58), "HOT · inside the tube", font=get_font(50,True), fill=HOT, anchor="mm")
        draw.text((W//2,c_bot+58), "COLD · outside, in the shell", font=get_font(50,True), fill=COLD, anchor="mm")
    if wall_hi:
        draw.text((W//2,c_bot+150), "Heat crosses the tube wall", font=get_font(52,True), fill=YELLOW, anchor="mm")
    return (x0, x1, h_top, h_bot, c_top, c_bot)

# ── Brand: LWA wordmark, bottom right (seconds 1–4 and end card) ─────────────
def _georgia(size):
    for c in ("/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
              "/Library/Fonts/Georgia Italic.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"):   # Linux (CI)
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return get_font(size)

_wm_cache = {}
def _wordmark():
    """Ring + italic LWA monogram + 'LearnWithAvisha', solid white so it reads at phone size."""
    if "wm" not in _wm_cache:
        f_mono, f_word = _georgia(26), _georgia(46)
        tmp = ImageDraw.Draw(Image.new("L", (1,1)))
        word_w = int(tmp.textlength("LearnWithAvisha", font=f_word))
        r = 40; w = 2*r + 18 + word_w + 4; h = 2*r + 4
        mark = Image.new("L", (w, h), 0); d = ImageDraw.Draw(mark)
        d.ellipse([2,2,2+2*r,2+2*r], outline=255, width=4)
        d.text((2+r, 2+r), "LWA", font=f_mono, fill=255, anchor="mm")
        d.text((2*r+20, 2+r), "LearnWithAvisha", font=f_word, fill=255, anchor="lm")
        _wm_cache["wm"] = mark
    return _wm_cache["wm"]

def stamp_wordmark(img, alpha=1.0):
    mark = _wordmark()
    if alpha < 1.0:
        mark = mark.point(lambda v: int(v*alpha))
    x, y = W - mark.width - 40, H - mark.height - 40   # below the caption band
    img.paste(Image.new("RGB", mark.size, WHITE), (x, y), mark)
    return img

def wordmark_alpha(t_abs, fade=0.2):
    """Opening wordmark by absolute time: fades in just before WM_START, out just after WM_END."""
    if WM_START-fade <= t_abs <= WM_END+fade:
        return min(1.0, (t_abs-(WM_START-fade))/fade, ((WM_END+fade)-t_abs)/fade)
    return 0.0

# ── Shell-and-tube illustration (the real equipment) ─────────────────────────
# Side view: channel heads, tubesheets, a cylindrical shell with a cutaway
# window onto the tube bundle, and four flanged nozzles. The middle tube is the
# one that later becomes the hot lane of the schematic.
METAL = (118,124,136)
SHELL_BOX = (226,640,854,1000)
WINDOW = (270,670,810,970)
TUBE_YS = (724,772,820,868,916)
TUBE_H, TUBE_WALL = 24, 5
MID_TUBE = (WINDOW[0], 820-TUBE_H//2, WINDOW[2], 820+TUBE_H//2)
SHELL_NOZ = (300, 780)          # x centres of the shell-side nozzles
HOT_IN_X, HOT_OUT_X = 140, 935  # x centres of the channel-head nozzles

def _metal(img, box, mask_fn, base=METAL):
    """Paste a top-lit vertical gradient through a shape mask (reads as a cylinder)."""
    x0,y0,x1,y1 = box; w,h = x1-x0, y1-y0
    grad = Image.new("RGB", (w,h)); gd = ImageDraw.Draw(grad)
    for i in range(h):
        k = max(0.38, 0.5+0.5*math.cos((i/max(1,h-1)-0.32)*math.pi))
        gd.line([(0,i),(w,i)], fill=tuple(int(c*k) for c in base))
    mask = Image.new("L", (w,h), 0); mask_fn(ImageDraw.Draw(mask), w, h)
    img.paste(grad, (x0,y0), mask)

def _nozzle(img, cx, y_from, y_to, top):
    """Flanged nozzle from y_from (vessel side) to y_to (open end)."""
    a, b = sorted((y_from, y_to))
    _metal(img, (cx-28,a,cx+28,b), lambda d,w,h: d.rectangle([0,0,w,h], fill=255))
    fy = y_to-8 if top else y_to-8
    _metal(img, (cx-42,fy,cx+42,fy+16), lambda d,w,h: d.rectangle([0,0,w,h], fill=255), (150,155,165))

_illus_cache = {}
def _illustration_base(counter):
    if counter in _illus_cache:
        return _illus_cache[counter].copy()
    img, draw = canvas()
    full = lambda d,w,h: d.rectangle([0,0,w,h], fill=255)
    # channel heads (bonnets) with rounded outer ends
    _metal(img, (90,680,210,960), lambda d,w,h: (d.ellipse([0,0,160,h], fill=255), d.rectangle([80,0,w,h], fill=255)), (128,104,104))
    _metal(img, (870,680,990,960), lambda d,w,h: (d.ellipse([w-160,0,w,h], fill=255), d.rectangle([0,0,w-80,h], fill=255)), (128,104,104))
    # shell body and tubesheets
    _metal(img, SHELL_BOX, full)
    for x in (210, 854):
        _metal(img, (x,624,x+16,1016), full, (165,170,180))
    # nozzles: tube side on the heads, shell side on the shell
    _nozzle(img, HOT_IN_X, 690, 592, True)
    _nozzle(img, HOT_OUT_X, 950, 1048, False)
    cin, cout = (SHELL_NOZ[1], SHELL_NOZ[0]) if counter else SHELL_NOZ
    _nozzle(img, cin, 650, 572, True)
    _nozzle(img, cout, 990, 1068, False)
    draw = ImageDraw.Draw(img)
    # cutaway window onto the bundle
    wx0,wy0,wx1,wy1 = WINDOW
    draw.rectangle(WINDOW, fill=COLD_BG, outline=(40,44,56), width=4)
    for y in TUBE_YS:
        draw.rectangle([wx0,y-TUBE_H//2-TUBE_WALL,wx1,y+TUBE_H//2+TUBE_WALL], fill=WALL)
        draw.rectangle([wx0,y-TUBE_H//2,wx1,y+TUBE_H//2], fill=HOT_BG)
        for ax in (380, 660):
            _arrow(draw, ax, y, HOT, True, 22, 18)
    for y0, y1 in zip(TUBE_YS, TUBE_YS[1:]):
        for ax in (450, 590):
            _arrow(draw, ax, (y0+y1)//2, COLD, not counter, 20, 14)
    # flow direction arrows in the nozzle bores
    for cx, cy, col in [(HOT_IN_X,640,HOT),(HOT_OUT_X,1000,HOT),(cin,610,COLD),(cout,1030,COLD)]:
        draw.polygon([(cx-17,cy-15),(cx+17,cy-15),(cx,cy+15)], fill=col)
    _illus_cache[counter] = img
    return img.copy()

def draw_illustration(counter=False, hot_out=51, cold_out=49, emph=None,
                      inset=False, cold_out_colour=None):
    img = _illustration_base(counter)
    draw = ImageDraw.Draw(img)
    hot_c = GREY if emph == "cold" else HOT
    cold_c = GREY if emph == "hot" else COLD
    cin, cout = (SHELL_NOZ[1], SHELL_NOZ[0]) if counter else SHELL_NOZ
    fn, ft = get_font(44,True), get_font(50,True)
    def tag(cx, top, name, temp, col, tcol=None):
        y1, y2 = (478, 532) if top else (1102, 1156)
        x = min(max(cx, 120), W-120)
        draw.text((x,y1), name, font=fn, fill=col, anchor="mm")
        draw.text((x,y2), temp, font=ft, fill=tcol or col, anchor="mm")
    tag(HOT_IN_X, True, "HOT IN", "90°C", hot_c)
    tag(HOT_OUT_X, False, "HOT OUT", f"{hot_out}°C", hot_c)
    tag(cin, True, "COLD IN", "10°C", cold_c)
    tag(cout, False, "COLD OUT", f"{cold_out}°C", cold_c, cold_out_colour if emph != "hot" else None)
    if emph == "hot":
        draw.rectangle([MID_TUBE[0]-3,MID_TUBE[1]-TUBE_WALL-3,MID_TUBE[2]+3,MID_TUBE[3]+TUBE_WALL+3], outline=YELLOW, width=3)
    if inset:
        _wall_inset(img, draw)
    return img

def _wall_inset(img, draw):
    """Magnified look at one tube wall: hot inside above, cold outside below."""
    cx, cy, r = 400, 1370, 150
    s = Image.new("RGB", (2*r,2*r), COLD_BG); sd = ImageDraw.Draw(s)
    sd.rectangle([0,0,2*r,r-22], fill=HOT_BG)
    sd.rectangle([0,r-22,2*r,r+22], fill=YELLOW)
    sd.text((r,r-80), "HOT", font=get_font(44,True), fill=HOT, anchor="mm")
    sd.text((r,r+80), "COLD", font=get_font(44,True), fill=(150,190,255), anchor="mm")
    for dx in (-70, 70):
        sd.line([(r+dx,r-60),(r+dx,r+40)], fill=WHITE, width=6)
        sd.polygon([(r+dx-14,r+34),(r+dx+14,r+34),(r+dx,r+58)], fill=WHITE)
    mask = Image.new("L", (2*r,2*r), 0); ImageDraw.Draw(mask).ellipse([0,0,2*r,2*r], fill=255)
    img.paste(s, (cx-r,cy-r), mask)
    draw.ellipse([cx-r,cy-r,cx+r,cy+r], outline=YELLOW, width=5)
    draw.line([(560,MID_TUBE[3]+TUBE_WALL),(cx+int(r*0.55),cy-int(r*0.84))], fill=YELLOW, width=4)
    draw.text((585,1300), "TUBE WALL", font=get_font(60,True), fill=YELLOW, anchor="lm")
    draw.text((585,1378), "Keeps fluids apart", font=get_font(46,True), fill=WHITE, anchor="lm")
    draw.text((585,1438), "Heat crosses it", font=get_font(46,True), fill=WHITE, anchor="lm")

def _skeleton(u):
    """Geometry morph: shell → cold lane, middle tube → hot lane, its wall → divider."""
    lerp = lambda a, b: tuple(int(p+(q-p)*u) for p, q in zip(a, b))
    img, draw = canvas()
    y0 = SCH_Y0
    cold = lerp(SHELL_BOX, (40, y0+246, 1040, y0+466))
    wall = lerp((MID_TUBE[0], MID_TUBE[1]-TUBE_WALL, MID_TUBE[2], MID_TUBE[3]+TUBE_WALL),
                (40, y0+220, 1040, y0+246))
    hot = lerp(MID_TUBE, (40, y0, 1040, y0+220))
    draw.rectangle(cold, fill=COLD_BG, outline=(210,210,215), width=4)
    draw.rectangle(wall, fill=WALL)
    draw.rectangle(hot, fill=HOT_BG)
    return img

# ── EP03 baffles in the 2D cutaway (same layout as the 3D panel) ─────────────
# Four segmental baffles at the 3D's BAFFLE_XS (±1.8, ±0.6 on a 6-unit shell mapped onto the
# 2D tubesheets 218–854), windows alternating like hx3d: even plates cut at the top, odd at the
# bottom. Shell nozzles sit outside the first and last baffle, as in the 3D (±2.4).
BAFFLE_X2D = (339, 468, 596, 725)
WIN_H = 66                       # baffle window height in the cutaway (≈ the 3D's cut)
PLATE = (190,195,205)
FLOW_C = (150,190,255)
TUBE_GAPS = (748, 796, 844, 892)

def _plate_span(i):
    """(top, bottom) y of baffle i inside the window: even cut at the top, odd at the bottom."""
    wy0, wy1 = WINDOW[1], WINDOW[3]
    return (wy0+WIN_H, wy1) if i % 2 == 0 else (wy0, wy1-WIN_H)

def _window(img, draw, plates_k=0.0, sag=0.0, hi_plates=False):
    """Redraw the cutaway: tubes (optionally sagging between the tubesheets) and baffles."""
    wx0,wy0,wx1,wy1 = WINDOW
    draw.rectangle(WINDOW, fill=COLD_BG, outline=(40,44,56), width=4)
    if plates_k > 0:
        col = tuple(int(BG[j]+(PLATE[j]-BG[j])*plates_k) for j in range(3))
        for i, x in enumerate(BAFFLE_X2D):
            a, b = _plate_span(i)
            draw.rectangle([x-8,a,x+8,b], fill=col, outline=YELLOW if hi_plates else None,
                           width=3 if hi_plates else 0)
    for y in TUBE_YS:
        # tubes run through holes in the plates; with no support they bow down in the middle
        pts = [(x, y+sag*math.sin(math.pi*(x-wx0)/(wx1-wx0))) for x in range(wx0, wx1+1, 12)]
        top = [(x, yy-TUBE_H//2-TUBE_WALL) for x, yy in pts]
        bot = [(x, yy+TUBE_H//2+TUBE_WALL) for x, yy in reversed(pts)]
        draw.polygon(top+bot, fill=WALL)
        top = [(x, yy-TUBE_H//2) for x, yy in pts]
        bot = [(x, yy+TUBE_H//2) for x, yy in reversed(pts)]
        draw.polygon(top+bot, fill=HOT_BG)
        for ax in (400, 660):
            _arrow(draw, ax, int(y+sag*math.sin(math.pi*(ax-wx0)/(wx1-wx0))), HOT, True, 22, 18)

def _path_upto(draw, path, frac, colour=FLOW_C, width=9):
    """Draw the first frac of a polyline, with an arrowhead at its tip."""
    seg = [math.dist(a, b) for a, b in zip(path, path[1:])]
    left = sum(seg)*max(0.0, min(1.0, frac))
    pts = [path[0]]
    for (a, b), s in zip(zip(path, path[1:]), seg):
        if left <= 0: break
        u = min(1.0, left/s); left -= s
        pts.append((a[0]+(b[0]-a[0])*u, a[1]+(b[1]-a[1])*u))
    if len(pts) < 2: return
    draw.line(pts, fill=colour, width=width, joint="curve")
    (x0,y0),(x1,y1) = pts[-2], pts[-1]
    ang = math.atan2(y1-y0, x1-x0)
    tip = [(x1+22*math.cos(ang), y1+22*math.sin(ang)),
           (x1+18*math.cos(ang+2.3), y1+18*math.sin(ang+2.3)),
           (x1+18*math.cos(ang-2.3), y1+18*math.sin(ang-2.3))]
    draw.polygon(tip, fill=colour)

# countercurrent: cold enters top right (780), leaves bottom left (300)
STRAIGHT_PATH = [(780,690),(760,796),(320,796),(300,975)]
ZIGZAG_PATH = [(780,690),(770,935),(660,935),(645,705),(532,705),(520,935),(404,935),
               (390,705),(320,705),(300,975)]

def draw_exchanger(plates_k=0.0, sag=0.0, hi_plates=False):
    img = _illustration_base(True)
    draw = ImageDraw.Draw(img)
    _window(img, draw, plates_k, sag, hi_plates)
    fn = get_font(44,True)
    for x, y, name, col in [(HOT_IN_X,530,"HOT IN",HOT),(HOT_OUT_X,1110,"HOT OUT",HOT),
                            (SHELL_NOZ[1],530,"COLD IN",COLD),(SHELL_NOZ[0],1110,"COLD OUT",COLD)]:
        draw.text((min(max(x,120),W-120), y), name, font=fn, fill=col, anchor="mm")
    return img, draw

# ── EP03 worked example (illustrative): Kern shell-side method ──────────────
# Kakaç & Liu: Nu = 0.36 Re^0.55 Pr^(1/3) (μ/μw)^0.14, f = exp(0.576 − 0.19 ln Re),
# ΔP = f Gs² (Nb+1) Ds / (2 ρ De φ). Halving baffle spacing B halves the crossflow area, so
# Gs and Re double, and the crossings Nb+1 = L/B double.
H_RATIO = 2**0.55                    # 1.464 → "about 1.5×"
DP_RATIO = 2**-0.19 * 2**2 * 2       # 7.01  → "about 7×"
assert abs(H_RATIO-1.464) < 0.001 and abs(DP_RATIO-7.01) < 0.01

def draw_box(draw, y_top, lines, size=52, colour=(255,230,140)):
    f = get_font(size, True)
    lh = int(f.size*1.25)
    h = lh*len(lines) + 40
    draw.rounded_rectangle([50,y_top,W-50,y_top+h], radius=18, fill=(30,34,50), outline=YELLOW, width=4)
    for i, line in enumerate(lines):
        draw.text((W//2, y_top+20+lh//2+i*lh), line, font=f, fill=colour, anchor="mm")
    return y_top+h

ASSUMPTION = ["Illustrative worked example —",
              "Kern method, same shell and flow,",
              "baffle spacing halved"]

def _badge(draw, y, text, colour):
    f = get_font(60, True)
    w = draw.textlength(text, font=f)
    draw.rounded_rectangle([W//2-w/2-34, y-50, W//2+w/2+34, y+50], radius=50,
                           fill=(30,34,50), outline=colour, width=5)
    draw.text((W//2, y), text, font=f, fill=colour, anchor="mm")

# ── Scene A: Hook — open the shell, plates in the way ────────────────────────
def render_a(t, m, dur):
    img, draw = draw_exchanger(plates_k=1.0, hi_plates=(len(m) > 1 and t >= m[1]))
    draw.text((W//2, 130), f"{EP_TAG} — {EP_TITLE}", font=get_font(64,True), fill=GREY, anchor="mm")
    _badge(draw, 300, "INSIDE THE SHELL", YELLOW)
    if len(m) > 1 and t >= m[1]:
        draw.text((W//2, 1330), "?", font=get_font(160,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene B: Without baffles — straight, slow; tubes unsupported ─────────────
def render_b(t, m, dur):
    k = 1 - _ease(t/1.0)                       # plates fade out as "take them out" is said
    sag = 22*_ease((t-m[2])/1.5) if len(m) > 2 and t >= m[2] else 0.0
    img, draw = draw_exchanger(plates_k=k, sag=sag)
    _badge(draw, 300, "NO BAFFLES", FLOW_C)
    _path_upto(draw, STRAIGHT_PATH, _ease((t-0.8)/2.5))
    if len(m) > 1 and t >= m[1]:
        draw.text((W//2, 1270), "Slow along the tubes", font=get_font(56,True), fill=FLOW_C, anchor="mm")
        draw.text((W//2, 1350), "Still layer on the tubes", font=get_font(50,True), fill=GREY, anchor="mm")
    if sag > 0:
        draw.text((W//2, 1440), "Long tubes sag and shake", font=get_font(50,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene C: With baffles — zig-zag across the tubes, faster; plates hold the tubes ─
def render_c(t, m, dur):
    k = _ease(t/1.0)
    hi = len(m) > 3 and t >= m[3]
    img, draw = draw_exchanger(plates_k=k, hi_plates=hi)
    _badge(draw, 300, "WITH BAFFLES", YELLOW)
    if len(m) > 1 and t >= m[1]:
        _path_upto(draw, ZIGZAG_PATH, _ease((t-m[1])/3.0))
    if len(m) > 2 and t >= m[2]:
        draw.text((W//2, 1270), "Across the tubes: faster", font=get_font(56,True), fill=FLOW_C, anchor="mm")
        draw.text((W//2, 1350), "scrubs the surface, heat moves better", font=get_font(46,True), fill=GREY, anchor="mm")
    if hi:
        draw.text((W//2, 1440), "Plates hold the tubes up", font=get_font(50,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene D: The trade-off — halve the spacing (drawn to one scale) ──────────
def _bar_pair(draw, x0, title, ratio, label, k, colour):
    base, unit, bw = 1180, 75, 150          # 1× = 75 px for both quantities: same scale
    draw.text((x0+bw+20, 420), title, font=get_font(52,True), fill=WHITE, anchor="mm")
    for j, (r, name) in enumerate([(1.0, "B"), (1+(ratio-1)*k, "B/2")]):
        x = x0 + j*(bw+40)
        h = int(unit*r)
        draw.rectangle([x, base-h, x+bw, base], fill=(70,110,170) if j == 0 else colour)
        draw.text((x+bw//2, base+45), name, font=get_font(48,True), fill=GREY, anchor="mm")
        txt = "1×" if j == 0 else (label if k > 0.9 else "")
        if txt:
            draw.text((x+bw//2, base-h-40), txt, font=get_font(50,True), fill=WHITE if j == 0 else YELLOW, anchor="mm")

def render_d(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 200), "Every turn costs pressure", font=get_font(62,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 290), "Baffle spacing B → B/2", font=get_font(50,True), fill=GREY, anchor="mm")
    if len(m) > 1 and t >= m[1]:
        _bar_pair(draw, 80, "Shell-side h", H_RATIO, "≈1.5×", _ease((t-m[1])/1.2), (90,170,120))
    if len(m) > 2 and t >= m[2]:
        _bar_pair(draw, 580, "Pressure drop", DP_RATIO, "≈7×", _ease((t-m[2])/1.2), (200,110,70))
    if len(m) > 3 and t >= m[3]:
        draw.text((W//2, 1330), "Usual spacing", font=get_font(50,True), fill=WHITE, anchor="mm")
        draw.text((W//2, 1410), "1/5 of shell diameter → 1 diameter", font=get_font(50,True), fill=YELLOW, anchor="mm")
    draw.text((W//2, 1490), "Kern method · illustrative", font=get_font(38), fill=GREY, anchor="mm")
    return img

# ── Scene E: In today's plants — layouts compared in rating software ─────────
def render_e(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 220), "Before any steel is cut", font=get_font(60,True), fill=WHITE, anchor="mm")
    draw.rounded_rectangle([70,340,W-70,1260], radius=26, fill=(26,30,44), outline=(70,76,96), width=4)
    draw.text((120, 410), "Rating software · baffle layouts", font=get_font(44,True), fill=GREY, anchor="lm")
    draw.text((560, 490), "heat", font=get_font(40,True), fill=(90,170,120), anchor="mm")
    draw.text((820, 490), "pressure", font=get_font(40,True), fill=(200,110,70), anchor="mm")
    rows = [("Wide spacing", 0.45, 0.15), ("Medium", 0.75, 0.45), ("Tight", 0.95, 0.95)]
    pick = 1
    for i, (name, hk, pk) in enumerate(rows):
        y = 620 + i*210
        if t < 0.6*(i+1):
            continue
        draw.text((120, y), name, font=get_font(46,True), fill=WHITE, anchor="lm")
        draw.rectangle([470, y-26, 470+int(180*hk), y+26], fill=(90,170,120))
        draw.rectangle([730, y-26, 730+int(180*pk), y+26], fill=(200,110,70))
        if i == pick and t >= 3.0:
            draw.rounded_rectangle([96, y-80, W-96, y+80], radius=18, outline=YELLOW, width=5)
            draw.line([(W-160, y), (W-138, y+24), (W-100, y-28)], fill=YELLOW, width=9)   # tick
    draw.text((W//2, 1330), "Bars illustrative", font=get_font(40), fill=GREY, anchor="mm")
    return img

# ── Scene F: The idea, and the limits of the example ─────────────────────────
def render_f(t, m, dur):
    img, draw = canvas()
    draw_text_centre(draw, "Baffles trade pressure for heat transfer", 330, get_font(64,True))
    draw_text_centre(draw, "…and keep the tubes steady", 560, get_font(58,True), YELLOW)
    if len(m) > 1 and t >= m[1]:
        draw_box(draw, 800, ASSUMPTION, size=50)
    return img

# ── Scene G: Closing question (holds to the end) ─────────────────────────────
def render_g(t, m, dur):
    img, draw = canvas()
    cy = 700
    draw.rounded_rectangle([90,cy-220,990,cy+220], radius=80, fill=COLD_BG, outline=(210,210,215), width=6)
    draw.rectangle([90,cy-50,990,cy+50], fill=HOT_BG, outline=WALL, width=10)
    k = _ease(t/2.0)
    if k > 0.5:
        draw.text((W//2, cy), "tube side ?", font=get_font(52,True), fill=YELLOW, anchor="mm")
        draw.text((W//2, cy-140), "shell side ?", font=get_font(48,True), fill=FLOW_C, anchor="mm")
    draw.text((W//2, 330), "Tubes or shell?", font=get_font(56,True), fill=GREY, anchor="mm")
    draw_text_centre(draw, "Next: which fluid goes inside the tubes?", 1150, get_font(66,True))
    draw.text((W//2, 1380), "S1 · E4 next: Tubes or shell?", font=get_font(72,True), fill=YELLOW, anchor="mm")
    return stamp_wordmark(img)

# ── Script: scenes → narration lines ─────────────────────────────────────────
# Each line is (narration, caption). The caption is what the viewer reads and
# must say what the narrator says; numbers are written as digits.
SCENES = [
    (render_a, [
        ("Open up the shell of a heat exchanger and you find plates standing in the way.",
         "Open up the shell of a heat exchanger and you find plates standing in the way."),
        ("Why would anyone put walls in the path of the flow?",
         "Why would anyone put walls in the path of the flow?", BREATH),
    ]),
    (render_b, [
        ("Take them out, and the shell-side fluid takes the easy road: straight along the tubes, slowly.",
         "Take them out, and the shell-side fluid takes the easy road: straight along the tubes, slowly."),
        ("Slow flow leaves a still layer on the tubes, and heat crosses it poorly.",
         "Slow flow leaves a still layer on the tubes, and heat crosses it poorly."),
        ("And long tubes with nothing to hold them can sag and shake.",
         "And long tubes with nothing to hold them can sag and shake.", BREATH),
    ]),
    (render_c, [
        ("Baffles are plates with one edge cut away, alternating top and bottom.",
         "Baffles are plates with one edge cut away, alternating top and bottom."),
        ("They force the fluid to zigzag across the tubes, again and again.",
         "They force the fluid to zigzag across the tubes, again and again."),
        ("Flowing across the tubes, it moves faster and scrubs the surface, so heat moves better.",
         "Flowing across the tubes, it moves faster and scrubs the surface, so heat moves better."),
        ("The plates also hold the tubes up, so they stay steady.",
         "The plates also hold the tubes up, so they stay steady.", BREATH),
    ]),
    (render_d, [
        ("But every turn costs pressure.",
         "But every turn costs pressure."),
        ("In a classic textbook method, halving the baffle spacing raises the shell-side coefficient "
         "about one and a half times.",
         "Halve the baffle spacing: shell-side coefficient about 1.5×."),
        ("The pressure drop rises about seven times.",
         "Pressure drop: about 7×.", BREATH),
        ("So designers usually space baffles between a fifth of the shell diameter and the full diameter.",
         "Usual spacing: 1/5 of the shell diameter up to 1 diameter."),
    ]),
    (render_e, [
        ("Today, engineers try many baffle layouts in rating software before any steel is cut, "
         "weighing heat transfer against pressure drop.",
         "Today, engineers try many baffle layouts in rating software before any steel is cut, "
         "weighing heat transfer against pressure drop."),
    ]),
    (render_f, [
        ("Baffles trade pressure for heat transfer, and keep the tubes steady.",
         "Baffles trade pressure for heat transfer, and keep the tubes steady.", BREATH),
        ("These numbers are an illustrative worked example.",
         "These numbers are an illustrative worked example."),
    ]),
    (render_g, [
        ("Next: one fluid goes in the tubes, one in the shell. Which goes where?",
         "Next: one fluid goes in the tubes, one in the shell. Which goes where?"),
    ]),
]
MIN_SCENE = {}
TAIL_HOLD = {render_g: END_HOLD}
POSTER_AT = (render_c, 2, 1.5)    # baffles in place, zig-zag drawn, "faster" label on screen

VOICEOVER_SCRIPT = " ".join(ln[0] for _, lines in SCENES for ln in lines)

# ── Narration ─────────────────────────────────────────────────────────────────
_kokoro = None
def _tts(text):
    """One Kokoro clip per narration line, cached by text + voice settings."""
    global _kokoro
    key = hashlib.sha1(f"{KOKORO_VOICE}|{KOKORO_SPEED}|{text}".encode()).hexdigest()[:16]
    path = TTS_CACHE / f"{key}.wav"
    if path.exists() and path.stat().st_size > 1000:
        samples, sr = sf.read(str(path), dtype="float32")
        return samples, sr
    if _kokoro is None:
        # kokoro-onnx does not download weights itself; reuse the copies Isha's voice server keeps.
        # CI sets KOKORO_DIR (or KOKORO_MODEL / KOKORO_VOICES) to its cached download.
        kokoro_dir = Path(os.environ.get("KOKORO_DIR",
                                         Path.home() / "Library/Application Support/Isha/kokoro"))
        _kokoro = kokoro_onnx.Kokoro(
            os.environ.get("KOKORO_MODEL", str(kokoro_dir / "kokoro-v1.0.onnx")),
            os.environ.get("KOKORO_VOICES", str(kokoro_dir / "voices-v1.0.bin")),
        )
    samples, sr = _kokoro.create(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED, lang="en-us")
    sf.write(str(path), samples, sr)
    return samples, sr

def _trim(samples, sr, thresh=0.01):
    """Drop Kokoro's leading/trailing near-silence so gaps are ours, not the model's."""
    idx = np.where(np.abs(samples) > thresh)[0]
    if len(idx) == 0:
        return samples
    a = max(0, idx[0]-int(0.03*sr)); b = min(len(samples), idx[-1]+int(0.08*sr))
    return samples[a:b]

def _chunk_caption(text, max_chars=CAPTION_MAX_CHARS):
    """Split a caption into the fewest cues that fit, with balanced lengths.
    Break points prefer clause punctuation, so no cue is a stranded word."""
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    ends, c = [], 0                       # character offset after each word
    for wd in words:
        c += len(wd) + (1 if c else 0); ends.append(c)
    k = math.ceil(len(text)/max_chars)
    while True:
        cuts, prev = [], -1
        for j in range(1, k):
            target = j*len(text)/k
            best = min((i for i in range(prev+1, len(words)-1)),
                       key=lambda i: abs(ends[i]-target) - (10 if words[i][-1] in ",.;:?!—" or
                                                            (i+1 < len(words) and words[i+1] == "—") else 0))
            cuts.append(best); prev = best
        bounds = [-1] + cuts + [len(words)-1]
        cues = [" ".join(words[bounds[i]+1:bounds[i+1]+1]) for i in range(len(bounds)-1)]
        if all(len(q) <= max_chars for q in cues) or k >= len(words):
            return cues
        k += 1

def generate_narration():
    """Build the narration track and the timing plan from per-line clips.
    Returns (wav_path, plan, cues): plan = [(render_fn, duration, marks)],
    cues = [(start, end, caption)] in absolute seconds.
    """
    print(f"  narration via Kokoro ({KOKORO_VOICE}), one clip per line…")
    chunks, plan, cues = [], [], []
    sr = None
    t_abs = 0.0
    for render_fn, lines in SCENES:
        scene_start = t_abs
        marks = []
        for i, (narr, cap, *flags) in enumerate(lines):
            s, sr = _tts(narr)
            s = _trim(s, sr)
            marks.append(t_abs - scene_start)
            d = len(s)/sr
            # Short cues share the line's time in proportion to their length
            parts = _chunk_caption(cap)
            total_chars = sum(len(p) for p in parts)
            t_c = t_abs
            for p in parts:
                dc = d*len(p)/total_chars
                cues.append((t_c, t_c+dc, p, render_fn, scene_start, cap)); t_c += dc
            chunks.append(s)
            t_abs += d
            gap = LINE_GAP if i < len(lines)-1 else SCENE_GAP
            if BREATH in flags:
                gap = max(gap, KEY_GAP)
            chunks.append(np.zeros(int(gap*sr), dtype=np.float32))
            t_abs += gap
        extra = TAIL_HOLD.get(render_fn, 0.0)
        dur = t_abs - scene_start
        extra = max(extra, MIN_SCENE.get(render_fn, 0.0) - dur)
        if extra > 0:
            chunks.append(np.zeros(int(extra*sr), dtype=np.float32))
            t_abs += extra; dur += extra
        plan.append((render_fn, dur, marks))
    raw = OUT / "narration_kokoro_raw.wav"
    sf.write(str(raw), np.concatenate(chunks), sr)
    # Loudness to spec: −16 LUFS integrated, true peak ≤ −1.5 dBTP
    out_path = OUT / "narration_kokoro.wav"
    subprocess.run(["ffmpeg","-y","-i",str(raw),
                    "-af","loudnorm=I=-16:TP=-1.5:LRA=11","-ar",str(sr),str(out_path)],
                   capture_output=True, check=True)
    print(f"  narration: {t_abs:.1f}s, {len(cues)} caption cues")
    return out_path, plan, cues

# ── Captions ──────────────────────────────────────────────────────────────────
_STOP = set("a an the in at of to is it its s and or so from by on that this as be "
            "now yet just not c k w m".split())

def _tokens(text):
    return [w for w in re.findall(r"[a-z]+|\d+(?:\.\d+)?", text.lower()) if w not in _STOP]

def onscreen_text(render_fn, t, marks, dur):
    """Every string the scene draws at time t (probes ImageDraw.text, so labels,
    titles, tags and insets are all caught without a hand-kept list)."""
    seen, orig = [], ImageDraw.ImageDraw.text
    def spy(self, xy, text, *a, **kw):
        seen.append(str(text)); return orig(self, xy, text, *a, **kw)
    ImageDraw.ImageDraw.text = spy
    try:
        img = render_fn(t, marks, dur)
    finally:
        ImageDraw.ImageDraw.text = orig
    return " ".join(seen)

def is_on_canvas(line_cues, plan, ratio=0.6):
    """True when most of a narration line's words are already written on screen
    while it plays. Decided per whole line, so no sentence loses half its caption."""
    a, b = line_cues[0][0], line_cues[-1][1]
    _, _, _, fn, s0, text = line_cues[0]
    marks, dur = next((mk, d) for f, d, mk in plan if f is fn)
    screen = set()
    for c in line_cues:
        for x in (c[0] + 0.15, (c[0] + c[1])/2, c[1] - 0.1):
            screen |= set(_tokens(onscreen_text(fn, min(max(x - s0, 0), dur), marks, dur)))
    words = _tokens(text)
    hit = sum(w in screen for w in words)
    return bool(words) and hit >= min(2, len(words)) and hit/len(words) >= ratio

def burn_cues(cues, plan):
    """Cues for the burned-in subtitle bar: lines already on the canvas are left out."""
    lines, keep = [], []
    for c in cues:                       # regroup cues by the line they came from
        if lines and lines[-1][-1][5] is c[5] and lines[-1][-1][1] == c[0]:
            lines[-1].append(c)
        else:
            lines.append([c])
    for lc in lines:
        if is_on_canvas(lc, plan):
            print(f"  caption skipped (already on canvas) {lc[0][0]:5.1f}s: {lc[0][5]}")
        else:
            keep += lc
    return keep
def _ts(x, sep=","):
    ms = int(round(x*1000))
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}{sep}{ms%1000:03d}"

def write_captions(cues, plan):
    srt = OUT / f"{EP_SLUG}.srt"
    srt.write_text("\n".join(f"{i}\n{_ts(a)} --> {_ts(b)}\n{c}\n"
                             for i,(a,b,c,*_) in enumerate(cues, 1)), encoding="utf-8")
    vtt = OUT / f"{EP_SLUG}.vtt"
    vtt.write_text("WEBVTT\n\n" + "\n".join(f"{_ts(a,'.')} --> {_ts(b,'.')}\n{c}\n"
                                            for a,b,c,*_ in cues), encoding="utf-8")
    # Burn-in style authored at real resolution: lower third, opaque box, ≤ 2 lines
    def cs(x):
        cc = int(round(x*100))
        return f"{cc//360000}:{cc//6000%60:02d}:{cc//100%60:02d}.{cc%100:02d}"
    ass = OUT / f"{EP_SLUG}.ass"
    ass.write_text(
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Arial,60,&H00FFFFFF,&H00FFFFFF,&H20000000,&H20000000,-1,0,0,0,100,100,0,0,3,"
        "16,0,2,70,70,170,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        + "".join(f"Dialogue: 0,{cs(a)},{cs(b)},Default,,0,0,0,,{c}\n"
                  for a,b,c,*_ in burn_cues(cues, plan)),
        encoding="utf-8")
    return srt, ass

# ── Assembly ──────────────────────────────────────────────────────────────────
def assemble(narration_path, plan):
    print("  building scenes…")
    starts = np.cumsum([0.0] + [d for _, d, _ in plan[:-1]])
    scenes = [make_scene_clip(fn, d, marks, t0) for (fn, d, marks), t0 in zip(plan, starts)]
    total = sum(s.duration for s in scenes)
    audio = AudioFileClip(str(narration_path))
    print(f"  animation total: {total:.1f}s | audio: {audio.duration:.1f}s")
    video = concatenate_videoclips(scenes).with_audio(audio)
    master = OUT / f"{EP_SLUG}_master.mp4"
    video.write_videofile(str(master), fps=FPS, codec="libx264", audio_codec="aac",
                          audio_bitrate="128k", preset="medium", logger=None)
    print(f"  master: {master.stat().st_size/1e6:.1f} MB")
    return master

def add_captions(video_path, ass):
    out = OUT / f"{EP_SLUG}_captioned.mp4"
    r = subprocess.run(["ffmpeg","-y","-i",str(video_path),"-vf",f"ass={ass}",
                        "-c:a","copy",str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"  captions failed:\n{r.stderr[-800:]}")
    return out

def make_web(master):
    out = OUT / f"{EP_SLUG}_web.mp4"
    for crf in ("26", "30"):
        subprocess.run(["ffmpeg","-y","-i",str(master),"-vf","scale=720:1280",
                        "-c:v","libx264","-crf",crf,"-preset","medium",
                        "-c:a","aac","-b:a","96k","-movflags","+faststart",str(out)],
                       capture_output=True, check=True)
        if out.stat().st_size/1e6 <= 5.0:
            break
    print(f"  web: {out.stat().st_size/1e6:.1f} MB")
    return out

def poster(video, plan):
    # Representative frame chosen per episode (POSTER_AT), not a fixed timestamp
    fn_target, mark_i, offset = POSTER_AT
    t = 0.0
    for fn, d, marks in plan:
        if fn is fn_target:
            t += marks[mark_i] + offset
            break
        t += d
    p = OUT / f"{EP_SLUG}_poster.jpg"
    subprocess.run(["ffmpeg","-y","-ss",f"{t:.2f}","-i",str(video),
                    "-frames:v","1","-q:v","2",str(p)], capture_output=True, check=True)
    print(f"  poster: {p} (t={t:.1f}s)")
    return p


def scene_start(plan, render_fn):
    """Start time (s) of the given scene in the measured plan."""
    t = 0.0
    for fn, dur, _ in plan:
        if fn is render_fn:
            return t
        t += dur
    return 0.0

def scene_end(plan, render_fn):
    """End time (s) of the given scene in the measured plan."""
    t = 0.0
    for fn, dur, _ in plan:
        t += dur
        if fn is render_fn:
            return t
    return 0.0

def baffle_switches(plan):
    """3D baffles follow the 2D: in place for the hook (A), taken out with scene B, back with C."""
    return [(0.0, True), (round(scene_start(plan, render_b), 3), False),
            (round(scene_start(plan, render_c), 3), True)]

def main():
    print(f"=== LearnWithAvisha · {EP_TAG} — {EP_TITLE} ===")
    nar, plan, cues = generate_narration()
    srt, ass = write_captions(cues, plan)
    mstr  = assemble(nar, plan)
    cap   = add_captions(mstr, ass)
    web   = make_web(cap)
    pst   = poster(mstr, plan)   # clean frame, no half-sentence caption
    wide  = None
    if "--wide" in sys.argv:     # widescreen: this 2D on the left, 3D baffles out / back in on the right
        from side_by_side import make_wide
        switches = baffle_switches(plan)
        title_from = scene_end(plan, render_a)     # scene A carries the episode title
        print(f"  3D baffles: {switches}; ON PAPER from {title_from:.2f}s")
        wide = make_wide(cap, fouling=False, mode="counter", title_from=title_from,
                         baffles_at=switches)
    print(f"\n=== DONE ===")
    print(f"  Master:    {mstr}")
    print(f"  Captioned: {cap}")
    print(f"  Web:       {web}")
    print(f"  SRT:       {srt}")
    print(f"  Poster:    {pst}")
    if wide:
        print(f"  Wide 2D+3D: {wide}")

if __name__ == "__main__":
    main()
