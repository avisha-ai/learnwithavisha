"""
LearnWithAvisha · Plant Mysteries · S1 · E1 — The Flip
Video generation pipeline: Kokoro TTS narration + programmatic animation + moviepy assembly

Run from the learnwithavisha folder:
    cd ~/Documents/Avisha/learnwithavisha
    .venv/bin/python3 pipeline/ep01_v2_pipeline.py

Install (once):
    .venv/bin/pip install kokoro-onnx soundfile

ffmpeg is taken from the micromamba manim env if it is not already on PATH.

Output (in <repo>/out/; copy approved files to episodes/):
    lwa_s1e01_the_flip_master.mp4      1080x1920 H.264 30fps, no captions
    lwa_s1e01_the_flip_captioned.mp4   master with burned-in captions (release file)
    lwa_s1e01_the_flip_web.mp4         720x1280 web derivative (<=5 MB)
    lwa_s1e01_the_flip.srt / .vtt      captions, timed from the narration itself
    lwa_s1e01_the_flip_poster.jpg      poster frame

Timing model: every narration line is voiced as its own Kokoro clip, so each
scene's length and each caption's in/out times come from measured audio.
Captions are split into short cues (at most two lines) and burned in from an
ASS file authored at the real 1080x1920 resolution.

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
END_HOLD  = 3.0       # final frame stays up after the last word (s)
CAPTION_MAX_CHARS = 50   # ≈ two lines at 60 px in the caption band
DIAGRAM_BOTTOM = 1520    # scenes draw nothing below this line
# Episode identity — every episode is Season 1
EP_TAG   = "S1 · E1"
EP_TITLE = "The Flip"
EP_SLUG  = "lwa_s1e01_the_flip"           # output filename stem
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
              "/Library/Fonts/Georgia Italic.ttf"):
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
SHELL_NOZ = (340, 660)          # x centres of the shell-side nozzles
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

# ── Scene 0: Intro — title card, what an exchanger is, a car radiator ────────
# Mechanism only on screen: hot coolant falls through the tubes and cools
# (red → orange), air crosses the core and warms (blue → orange). The narration
# carries the definition and why flow direction matters.
AMBER = (245,150,60)
def _mix(a, b, u): return tuple(int(p+(q-p)*u) for p, q in zip(a, b))

def _radiator(draw, t):
    cx0, cx1, cy0, cy1 = 300, 780, 560, 1080       # core
    n = 8; pitch = (cx1-cx0)/n
    draw.rounded_rectangle([cx0-20,cy0-70,cx1+20,cy0], radius=18, fill=(120,40,36))   # top tank
    draw.rounded_rectangle([cx0-20,cy1,cx1+20,cy1+70], radius=18, fill=(130,80,40))   # bottom tank
    for y in range(cy0+8, cy1, 16):                 # fins
        draw.line([(cx0,y),(cx1,y)], fill=(70,74,86), width=3)
    for i in range(n):                              # tubes, cooling top → bottom
        x = int(cx0+pitch*(i+0.5))
        for y in range(cy0, cy1, 8):
            draw.rectangle([x-9,y,x+9,y+8], fill=_mix(HOT, AMBER, (y-cy0)/(cy1-cy0)))
        for k in range(3):                          # coolant moving down
            yy = cy0 + ((t*120 + k*(cy1-cy0)/3) % (cy1-cy0))
            draw.ellipse([x-5,yy-5,x+5,yy+5], fill=WHITE)
    # hose in (top left) and out (bottom right)
    draw.rectangle([150,cy0-50,cx0-20,cy0-20], fill=HOT)
    draw.rectangle([cx1+20,cy1+20,930,cy1+50], fill=AMBER)
    # air crossing the core, warming as it goes
    for j, ay in enumerate((640, 760, 880, 1000)):
        ph = (t*0.6 + j*0.27) % 1.0
        ax = int(120 + ph*840)
        col = COLD if ax < cx0 else (AMBER if ax > cx1 else _mix(COLD, AMBER, (ax-cx0)/(cx1-cx0)))
        _arrow(draw, ax, ay, col, True, 46, 40)
    fl = get_font(46, True)
    draw.text((150, cy0-100), "Hot coolant", font=fl, fill=HOT, anchor="lm")
    draw.text((930, cy1+110), "Cooler coolant", font=fl, fill=AMBER, anchor="rm")
    draw.text((60, 1270), "Air", font=fl, fill=COLD, anchor="lm")
    draw.text((1020, 1270), "Warmer air", font=fl, fill=AMBER, anchor="rm")

def _mini_lanes(draw, x0, counter):
    w, lane = 300, 50
    draw.rectangle([x0,1330,x0+w,1330+lane], fill=HOT_BG)
    draw.rectangle([x0,1338+lane,x0+w,1338+2*lane], fill=COLD_BG)
    for ax in (x0+90, x0+210):
        _arrow(draw, ax, 1330+lane//2, HOT, True, 30, 30)
        _arrow(draw, ax, 1338+lane+lane//2, COLD, not counter, 30, 30)

def render_intro(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 200), f"{EP_TAG} — {EP_TITLE}", font=get_font(80,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 300), "Car radiator", font=get_font(52,True), fill=GREY, anchor="mm")
    _radiator(draw, t)
    if len(m) > 1 and t >= m[1]:
        _mini_lanes(draw, 140, False)
        draw.text((W//2, 1393), "vs", font=get_font(52,True), fill=GREY, anchor="mm")
        _mini_lanes(draw, 640, True)
    return img

# ── Scene A: Opening hook — the real exchanger, one stream reversed ──────────
def render_a(t, m, dur):
    counter = t >= 1.2
    img = draw_illustration(counter=counter, hot_out=37 if counter else 51,
                            cold_out=63 if counter else 49,
                            cold_out_colour=YELLOW if counter else None)
    draw = ImageDraw.Draw(img)
    draw.text((W//2, 250), "Same exchanger.", font=get_font(64,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 340), "One stream reversed.", font=get_font(64,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 1330), "More heat.  Why?", font=get_font(84,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene B: The exchanger, its wall, then simplify into the schematic ───────
def _parallel_schematic(t, m, wall_hi=False):
    img, draw = canvas()
    draw.text((W//2, 330), "Simplified", font=get_font(60,True), fill=WHITE, anchor="mm")
    draw_schematic(draw, counter=False, hot_out=51, cold_out=49, wall_hi=wall_hi)
    return img

MORPH = 1.6
def render_b(t, m, dur):
    if t < m[2]:
        cold_t = m[0] + 0.55*(m[1]-m[0])
        emph = "hot" if t < cold_t else ("cold" if t < m[1] else None)
        img = draw_illustration(counter=False, emph=emph, inset=(t >= m[1]))
        ImageDraw.Draw(img).text((W//2, 330), "Shell-and-tube heat exchanger",
                                 font=get_font(58,True), fill=WHITE, anchor="mm")
        return img
    u = (t-m[2])/MORPH
    if u < 0.35:
        img = Image.blend(draw_illustration(counter=False), _skeleton(0.0), u/0.35)
    elif u < 1.0:
        img = _skeleton(_ease((u-0.35)/0.65))
    else:
        k = min(1.0, (t-m[2]-MORPH)/0.4)
        img = Image.blend(_skeleton(1.0), _parallel_schematic(t, m), k)
    if t >= m[3]:
        draw = ImageDraw.Draw(img)
        draw.rectangle([0,250,W,400], fill=BG)
        draw.text((W//2, 330), "PARALLEL FLOW", font=get_font(64,True), fill=WHITE, anchor="mm")
        draw.text((W//2, 1240), "Both streams flow left → right", font=get_font(50,True), fill=GREY, anchor="mm")
    return img

# ── Temperature-profile graphs ───────────────────────────────────────────────
# Equal ṁCp, NTU = 2. Parallel: ΔT(x) = 80·exp(-4x), curves converge on 50 °C
# (hot out 50.7, cold out 49.3). Counterflow: straight, parallel lines,
# ΔT = 26.7 K everywhere (hot 90 → 36.7, cold 63.3 ← 10).
def par_hot(x):  return 50+40*math.exp(-4*x)
def par_cold(x): return 50-40*math.exp(-4*x)
def cf_hot(x):   return 90-53.333*x
def cf_cold(x):  return 63.333-53.333*x

def draw_graph(draw, gx, gtop, gw, gh, hot_fn, cold_fn, fill_gap=0.0, ticks=True,
               tick_font=44, end_font=40, x_labels=True):
    ybot = gtop+gh
    Y = lambda T: ybot - T/100*gh
    for T in (10, 50, 90):
        draw.line([(gx,Y(T)),(gx+gw,Y(T))], fill=(46,50,64), width=2)
        if ticks:
            draw.text((gx-14,Y(T)), f"{T}", font=get_font(tick_font,True), fill=GREY, anchor="rm")
    n = 80
    ph = [(gx+i/n*gw, Y(hot_fn(i/n))) for i in range(n+1)]
    pc = [(gx+i/n*gw, Y(cold_fn(i/n))) for i in range(n+1)]
    if fill_gap > 0:
        k = max(1, int(n*fill_gap))
        draw.polygon(ph[:k+1] + pc[:k+1][::-1], fill=(96,84,24))
    draw.line([(gx,gtop),(gx,ybot),(gx+gw,ybot)], fill=(210,210,215), width=4)
    draw.line(ph, fill=HOT, width=9)
    draw.line(pc, fill=COLD, width=9)
    if x_labels:
        f = get_font(end_font)
        draw.text((gx, ybot+20), "Hot inlet end", font=f, fill=GREY, anchor="lt")
        draw.text((gx+gw, ybot+20), "Hot outlet end", font=f, fill=GREY, anchor="rt")
    return Y

ASSUMPTION = ["Ideal single-pass comparison —",
              "same UA, inlet temperatures",
              "and heat-capacity rates."]

def draw_assumption_box(draw, y_top, compact=False):
    f = get_font(46 if compact else 56, True)
    lh = int(f.size*1.25)
    h = lh*len(ASSUMPTION) + 40
    draw.rounded_rectangle([50,y_top,W-50,y_top+h], radius=18, fill=(30,34,50), outline=YELLOW, width=4)
    for i, line in enumerate(ASSUMPTION):
        draw.text((W//2, y_top+20+lh//2+i*lh), line, font=f, fill=(255,230,140), anchor="mm")
    return y_top+h

# ── Scene C: Parallel temperature graph ──────────────────────────────────────
def render_c(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 120), "PARALLEL FLOW", font=get_font(64,True), fill=WHITE, anchor="mm")
    gx, gtop, gw, gh = 170, 560, 840, 820
    Y = draw_graph(draw, gx, gtop, gw, gh, par_hot, par_cold)
    draw.text((gx+20, gtop-10), "°C", font=get_font(44,True), fill=GREY, anchor="lb")
    if t >= m[1]:
        xp = gx+0.10*gw
        draw.line([(xp,Y(par_hot(0.10))),(xp,Y(par_cold(0.10)))], fill=YELLOW, width=7)
        draw.text((xp+22,(Y(par_hot(0.10))+Y(par_cold(0.10)))/2), "Large ΔT", font=get_font(54,True), fill=YELLOW, anchor="lm")
    if t >= m[2]:
        xp = gx+0.92*gw
        draw.line([(xp,Y(par_hot(0.92))-6),(xp,Y(par_cold(0.92))+6)], fill=YELLOW, width=7)
        draw.text((xp,Y(par_hot(0.92))-80), "Small ΔT", font=get_font(54,True), fill=YELLOW, anchor="rm")
    if t >= m[3]:
        draw_assumption_box(draw, 190)
    return img

# ── Scene D: Flip transition ─────────────────────────────────────────────────
def render_d(t, m, dur):
    p = _ease((t-0.25*dur)/(0.6*dur))
    img, draw = canvas()
    draw.text((W//2, 330), "Reverse the cold stream", font=get_font(64,True), fill=WHITE, anchor="mm")
    draw_schematic(draw, counter=(p >= 0.5), hot_out=round(51+(37-51)*p), cold_out=round(49+(63-49)*p))
    return img

# ── Scene E: Counterflow schematic and outlet temperatures ───────────────────
def render_e(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 330), "COUNTERFLOW", font=get_font(64,True), fill=WHITE, anchor="mm")
    x0, x1, h_top, h_bot, c_top, c_bot = draw_schematic(
        draw, counter=True, hot_out=37, cold_out=63,
        hi_hot=(m[1] <= t < m[3]), hi_cold=(m[2] <= t < m[3]))
    if t < m[3]:
        draw.text((W//2, 1240), "Hot →   ·   ← Cold", font=get_font(56,True), fill=GREY, anchor="mm")
    else:
        # The two outlets sit at opposite ends of the exchanger
        fe = get_font(52, True)
        draw.text((x0+10, 1240), "← Cold out 63°C", font=fe, fill=COLD, anchor="lm")
        draw.text((x1-10, 1330), "Hot out 37°C →", font=fe, fill=HOT, anchor="rm")
    return img

# ── Scene F: Side-by-side comparison — the payoff ────────────────────────────
def render_f(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 120), "Same scale, side by side", font=get_font(60,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 195), "°C · ideal single-pass case", font=get_font(46,True), fill=GREY, anchor="mm")
    gtop, gh, gw = 380, 820, 410
    panels = [(140, "PARALLEL", par_hot, par_cold, m[0]+1.2, "Gap narrows"),
              (620, "COUNTERFLOW", cf_hot, cf_cold, m[1], "Gap holds")]
    for i, (gx, title, hf, cf, t_fill, verdict) in enumerate(panels):
        fill = _ease((t-t_fill)/1.2) if t >= t_fill else 0.0
        draw.text((gx+gw//2, gtop-50), title, font=get_font(52,True), fill=WHITE, anchor="mm")
        draw_graph(draw, gx, gtop, gw, gh, hf, cf, fill_gap=fill, ticks=(i == 0), x_labels=False)
        # Position is measured along the hot stream in both panels; in counterflow
        # the cold stream enters at the hot outlet end, so say "hot" explicitly.
        draw.text((gx, gtop+gh+14), "Hot inlet end", font=get_font(36,True), fill=GREY, anchor="lt")
        draw.text((gx+gw, gtop+gh+58), "Hot outlet end", font=get_font(36,True), fill=GREY, anchor="rt")
        if t >= t_fill:
            draw.text((gx+gw//2, gtop+gh+150), verdict, font=get_font(54,True), fill=YELLOW, anchor="mm")
        if t >= m[2]:
            txt = "Heat: baseline" if i == 0 else "Heat: +36%"
            col = GREY if i == 0 else (255,160,140)
            draw.text((gx+gw//2, gtop+gh+245), txt, font=get_font(58,True), fill=col, anchor="mm")
    return img

# ── Scene G: Why it matters, and where it does not directly apply ────────────
def render_g(t, m, dur):
    img, draw = canvas()
    draw_text_centre(draw, "Counterflow is often preferred for heat recovery", 560, get_font(72,True))
    if t >= m[1]:
        y = draw_assumption_box(draw, 860)
        draw_text_centre(draw, "Real multi-pass exchangers need a separate calculation.",
                         y+150, get_font(58,True), WHITE)
    return img

# ── Scene H: Closing question over the deposit layer (holds to the end) ──────
def render_h(t, m, dur):
    frac = _ease(t/3.0)
    img, draw = canvas()
    cx, cy, R_o = W//2, 640, 330
    R_w = R_o-44; R_f = R_w-int(78*frac)
    draw.ellipse([cx-R_o,cy-R_o,cx+R_o,cy+R_o], fill=WALL)
    draw.ellipse([cx-R_w,cy-R_w,cx+R_w,cy+R_w], fill=(140,96,48))
    draw.ellipse([cx-R_f,cy-R_f,cx+R_f,cy+R_f], fill=HOT_BG)
    draw.text((cx,cy), "hot fluid", font=get_font(48,True), fill=HOT, anchor="mm")
    draw.text((W//2, 200), "Tube cross-section", font=get_font(52,True), fill=GREY, anchor="mm")
    if frac > 0.3:
        lx, ly = cx+int((R_w-30)*0.70), cy-int((R_w-30)*0.70)
        draw.line([(lx,ly),(860,335)], fill=(230,170,100), width=5)
        draw.text((1040,300), "Deposit layer", font=get_font(52,True), fill=(230,170,100), anchor="rm")
    draw.line([(cx-int(R_o*0.72), cy+int(R_o*0.72)),(150,1035)], fill=GREY, width=5)
    draw.text((40,1060), "Tube wall", font=get_font(48,True), fill=GREY, anchor="lt")
    draw_text_centre(draw, "What changes when deposits start building up?", 1230, get_font(66,True))
    draw.text((W//2, 1430), "S1 · E2 next: The Fouling Problem", font=get_font(56,True), fill=YELLOW, anchor="mm")
    return stamp_wordmark(img)

# ── Script: scenes → narration lines ─────────────────────────────────────────
# Each line is (narration, caption). The caption is what the viewer reads and
# must say what the narrator says; numbers are written as digits.
# Audio/visual split: the visuals show the mechanism (labels, numbers, arrows);
# the narration delivers the insight. A line must not read out on-screen text.
SCENES = [
    (render_intro, [
        ("A heat exchanger passes heat between fluids that never touch — like a car radiator.",
         "A heat exchanger passes heat between fluids that never touch — like a car radiator."),
        ("Flow direction decides how much.",
         "Flow direction decides how much."),
    ]),
    (render_a, [
        ("No new metal. No extra pumping. So where does the extra heat come from?",
         "No new metal. No extra pumping. So where does the extra heat come from?"),
    ]),
    (render_b, [
        ("Packing many tubes into one shell gives the heat a lot of surface to cross.",
         "Packing many tubes into one shell gives the heat a lot of surface to cross."),
        ("Every bit of it has to push through metal — so something has to do the pushing.",
         "Every bit of it has to push through metal — so something has to do the pushing."),
        ("Strip it down to one tube to see what that is.",
         "Strip it down to one tube to see what that is."),
        ("First, the arrangement that looks natural.",
         "First, the arrangement that looks natural."),
    ]),
    (render_c, [
        ("The two streams chase each other toward the same temperature.",
         "The two streams chase each other toward the same temperature."),
        ("That gap is the driving force — at the inlet, heat pours across.",
         "That gap is the driving force — at the inlet, heat pours across."),
        ("By the far end the push is almost gone, so that stretch of tube barely works.",
         "By the far end the push is almost gone, so that stretch of tube barely works."),
        ("Keep everything else fixed. Change one thing.",
         "Keep everything else fixed. Change one thing."),
    ]),
    (render_d, [
        ("Now — the flip.",
         "Now — the flip."),
    ]),
    (render_e, [
        ("The fluids still never mix. Only where they meet has changed.",
         "The fluids still never mix. Only where they meet has changed."),
        ("The hot stream leaves fourteen degrees cooler than before.",
         "The hot stream leaves 14 °C cooler than before."),
        ("And the cold stream now leaves hotter than the hot stream does.",
         "And the cold stream now leaves hotter than the hot stream does."),
        ("Each one exits at the other's inlet end — so at every point, hot is still hotter.",
         "Each one exits at the other's inlet end — so at every point, hot is still hotter."),
    ]),
    (render_f, [
        ("In one, the push fades out.",
         "In one, the push fades out."),
        ("In the other, it never does.",
         "In the other, it never does."),
        ("Every metre of tube keeps pulling its weight — that's where the extra heat comes from.",
         "Every metre of tube keeps pulling its weight — that's where the extra heat comes from."),
    ]),
    (render_g, [
        ("Same hardware, more heat recovered — just by choosing the direction.",
         "Same hardware, more heat recovered — just by choosing the direction."),
        ("Multi-pass units blend both patterns — that's a story for another day.",
         "Multi-pass units blend both patterns — that's a story for another day."),
    ]),
    (render_h, [
        ("But tubes don't stay clean. Next time — what a thin layer of grime does to all of this.",
         "But tubes don't stay clean. Next time — what a thin layer of grime does to all of this."),
    ]),
]
MIN_SCENE = {render_d: 3.5}
TAIL_HOLD = {render_h: END_HOLD}

VOICEOVER_SCRIPT = " ".join(n for _, lines in SCENES for n, _ in lines)

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
        # kokoro-onnx does not download weights itself; reuse the copies Isha's voice server keeps
        kokoro_dir = Path.home() / "Library/Application Support/Isha/kokoro"
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
        for i, (narr, cap) in enumerate(lines):
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
                cues.append((t_c, t_c+dc, p)); t_c += dc
            chunks.append(s)
            t_abs += d
            gap = LINE_GAP if i < len(lines)-1 else SCENE_GAP
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
def _ts(x, sep=","):
    ms = int(round(x*1000))
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}{sep}{ms%1000:03d}"

def write_captions(cues):
    srt = OUT / f"{EP_SLUG}.srt"
    srt.write_text("\n".join(f"{i}\n{_ts(a)} --> {_ts(b)}\n{c}\n"
                             for i,(a,b,c) in enumerate(cues, 1)), encoding="utf-8")
    vtt = OUT / f"{EP_SLUG}.vtt"
    vtt.write_text("WEBVTT\n\n" + "\n".join(f"{_ts(a,'.')} --> {_ts(b,'.')}\n{c}\n"
                                            for a,b,c in cues), encoding="utf-8")
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
        + "".join(f"Dialogue: 0,{cs(a)},{cs(b)},Default,,0,0,0,,{c}\n" for a,b,c in cues),
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
    # Representative frame: the finished side-by-side comparison, not a fixed timestamp
    t = 0.0
    for fn, d, marks in plan:
        if fn is render_f:
            t += marks[2] + 2.0
            break
        t += d
    p = OUT / f"{EP_SLUG}_poster.jpg"
    subprocess.run(["ffmpeg","-y","-ss",f"{t:.2f}","-i",str(video),
                    "-frames:v","1","-q:v","2",str(p)], capture_output=True, check=True)
    print(f"  poster: {p} (t={t:.1f}s)")
    return p

def main():
    print(f"=== LearnWithAvisha · {EP_TAG} — {EP_TITLE} ===")
    nar, plan, cues = generate_narration()
    srt, ass = write_captions(cues)
    mstr  = assemble(nar, plan)
    cap   = add_captions(mstr, ass)
    web   = make_web(cap)
    pst   = poster(mstr, plan)   # clean frame, no half-sentence caption
    print(f"\n=== DONE ===")
    print(f"  Master:    {mstr}")
    print(f"  Captioned: {cap}")
    print(f"  Web:       {web}")
    print(f"  SRT:       {srt}")
    print(f"  Poster:    {pst}")

if __name__ == "__main__":
    main()
