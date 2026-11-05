"""
LearnWithAvisha · Plant Mysteries · S1 · E2 — The Fouling Problem
Video generation pipeline: Kokoro TTS narration + programmatic animation + moviepy assembly

Run from the learnwithavisha folder:
    cd ~/Documents/Avisha/learnwithavisha
    .venv/bin/python3 pipeline/ep02_v2_pipeline.py

Install (once):
    .venv/bin/pip install kokoro-onnx soundfile

ffmpeg is taken from the micromamba manim env if it is not already on PATH.

Output (in <repo>/out/; copy approved files to episodes/):
    lwa_s1e02_the_fouling_problem_master.mp4      1080x1920 H.264 30fps, no captions
    lwa_s1e02_the_fouling_problem_captioned.mp4   master with burned-in captions (release file)
    lwa_s1e02_the_fouling_problem_web.mp4         720x1280 web derivative (<=5 MB)
    lwa_s1e02_the_fouling_problem.srt / .vtt      captions, timed from the narration itself
    lwa_s1e02_the_fouling_problem_poster.jpg      poster frame

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
EP_TAG   = "S1 · E2"
EP_TITLE = "The Fouling Problem"
EP_SLUG  = "lwa_s1e02_the_fouling_problem"           # output filename stem
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

# ── EP02 worked example (illustrative) ───────────────────────────────────────
# Counterflow, equal heat-capacity rates (Cr = 1), hot in 90 °C, cold in 10 °C,
# clean U = 500 W/m²·K and NTU = 2 (same exchanger as EP01). Deposit 0.08 mm,
# k = 0.2 W/m·K → R_f = 0.0004 m²·K/W. 1/U: 0.0020 → 0.0024, U → 416.7,
# NTU → 1.667, ε = NTU/(1+NTU): 0.667 → 0.625, duty −6.25 %.
# Outlets: cold 63.3 → 60.0 °C, hot 36.7 → 40.0 °C. Steel (k ≈ 16) equivalent of
# R_f: 6.4 mm. Temperature profiles are deliberately not drawn: with less heat
# moved the counterflow gap widens (26.7 → 30 K), which would read as a
# contradiction of EP01 without a longer explanation.
BROWN = (150,100,50)
DEPOSIT_TXT = (230,170,100)

def draw_box(draw, y_top, lines, size=52, colour=(255,230,140)):
    f = get_font(size, True)
    lh = int(f.size*1.25)
    h = lh*len(lines) + 40
    draw.rounded_rectangle([50,y_top,W-50,y_top+h], radius=18, fill=(30,34,50), outline=YELLOW, width=4)
    for i, line in enumerate(lines):
        draw.text((W//2, y_top+20+lh//2+i*lh), line, font=f, fill=colour, anchor="mm")
    return y_top+h

ASSUMPTION = ["Illustrative worked example —",
              "counterflow, equal heat-capacity rates,",
              "clean NTU = 2,",
              "deposit 0.08 mm, k = 0.2 W/m·K"]

# ── Scene A: Hook — same exchanger, outlet three degrees colder ──────────────
def render_a(t, m, dur):
    drift = t >= 1.0
    img = draw_illustration(counter=True, hot_out=40 if drift else 37,
                            cold_out=60 if drift else 63,
                            cold_out_colour=YELLOW if drift else None)
    draw = ImageDraw.Draw(img)
    draw.text((W//2, 130), f"{EP_TAG} — {EP_TITLE}", font=get_font(64,True), fill=GREY, anchor="mm")
    draw.text((W//2, 250), "Nothing broke.", font=get_font(64,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 340), "Nothing leaked.", font=get_font(64,True), fill=WHITE, anchor="mm")
    if drift:
        draw.text((W//2, 1330), "Outlet: 3 °C colder", font=get_font(84,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene B: Same plant, same flows, different outlets ───────────────────────
def render_b(t, m, dur):
    now = t >= m[1]
    img = draw_illustration(counter=True,
                            hot_out="37→40" if now else 37,
                            cold_out="63→60" if now else 63,
                            cold_out_colour=YELLOW if now else None)
    draw = ImageDraw.Draw(img)
    draw.text((W//2, 330), "Same exchanger · same flows", font=get_font(58,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 1300), "Inlets unchanged: 90 °C and 10 °C", font=get_font(50,True), fill=GREY, anchor="mm")
    if now:
        draw.text((W//2, 1400), "Clean → today", font=get_font(56,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene C: The layer inside the tube, then the layers heat must cross ──────
def _tube_section(draw, frac=1.0, cy=760):
    cx, R_o = W//2, 330
    R_w = R_o-44; R_f = R_w-int(78*frac)
    draw.ellipse([cx-R_o,cy-R_o,cx+R_o,cy+R_o], fill=WALL)
    draw.ellipse([cx-R_w,cy-R_w,cx+R_w,cy+R_w], fill=BROWN)
    draw.ellipse([cx-R_f,cy-R_f,cx+R_f,cy+R_f], fill=HOT_BG)
    draw.text((cx,cy), "hot fluid", font=get_font(52,True), fill=HOT, anchor="mm")
    lx, ly = cx+int((R_w-30)*0.70), cy-int((R_w-30)*0.70)
    draw.line([(lx,ly),(860,cy-R_o-30)], fill=DEPOSIT_TXT, width=5)
    draw.text((1040,cy-R_o-60), "Deposit 0.08 mm", font=get_font(52,True), fill=DEPOSIT_TXT, anchor="rm")
    draw.line([(cx-int(R_o*0.72), cy+int(R_o*0.72)),(170,cy+R_o+40)], fill=GREY, width=5)
    draw.text((40,cy+R_o+70), "Tube wall", font=get_font(50,True), fill=GREY, anchor="lm")

def _layer_strip(draw, y0=420):
    """Heat path from hot fluid to cold fluid: deposit and wall in series."""
    rows = [("HOT FLUID", HOT_BG, HOT, 200), ("DEPOSIT", BROWN, WHITE, 90),
            ("TUBE WALL", WALL, (30,30,36), 120), ("COLD FLUID", COLD_BG, (150,190,255), 200)]
    y = y0
    for name, fill, tcol, h in rows:
        draw.rectangle([140,y,940,y+h], fill=fill)
        draw.text((W//2, y+h//2), name, font=get_font(50,True), fill=tcol, anchor="mm")
        y += h
    draw.rectangle([140,y0,940,y], outline=(210,210,215), width=4)
    x = 990
    draw.line([(x,y0+40),(x,y-40)], fill=YELLOW, width=10)
    draw.polygon([(x-26,y-60),(x+26,y-60),(x,y-14)], fill=YELLOW)
    draw.text((x-10,y0+10), "heat", font=get_font(44,True), fill=YELLOW, anchor="rb")
    return y

def render_c(t, m, dur):
    img, draw = canvas()
    if t < m[1]:
        draw.text((W//2, 230), "Inside the tube", font=get_font(60,True), fill=WHITE, anchor="mm")
        _tube_section(draw, _ease(t/2.5))
        draw.text((W//2, 1270), "Thinner than a sheet of paper", font=get_font(54,True), fill=YELLOW, anchor="mm")
        draw.text((W//2, 1350), "(drawn thicker so you can see it)", font=get_font(42), fill=GREY, anchor="mm")
    else:
        draw.text((W//2, 300), "Heat must cross every layer", font=get_font(60,True), fill=WHITE, anchor="mm")
        yb = _layer_strip(draw)
        draw.text((W//2, yb+110), "Flow passes freely —", font=get_font(52,True), fill=GREY, anchor="mm")
        draw.text((W//2, yb+180), "the deposit sits in the heat path", font=get_font(52,True), fill=GREY, anchor="mm")
    return img

# ── Scene D: Resistances in series add ───────────────────────────────────────
def render_d(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 230), "Resistances in series add", font=get_font(62,True), fill=WHITE, anchor="mm")
    draw.text((W//2, 330), "1/U = R(clean) + R(deposit)", font=get_font(56,True), fill=GREY, anchor="mm")
    x0, y0, y1, scale = 90, 470, 620, 900/0.0024
    xc = x0 + int(0.0020*scale)
    draw.rectangle([x0,y0,xc,y1], fill=(70,110,170))
    draw.text(((x0+xc)//2,(y0+y1)//2), "Clean 0.0020", font=get_font(52,True), fill=WHITE, anchor="mm")
    if t >= m[1]:
        k = _ease((t-m[1]-1.5)/1.0)
        xd = xc + int(0.0004*scale*k)
        if xd > xc:
            draw.rectangle([xc,y0,xd,y1], fill=BROWN)
        if k > 0.9:
            draw.text((xd-4, y0-30), "+0.0004 deposit", font=get_font(44,True), fill=DEPOSIT_TXT, anchor="rb")
            draw.text((W//2, y1+70), "Total 0.0024 m²·K/W", font=get_font(54,True), fill=WHITE, anchor="mm")
    draw.rectangle([x0,y0,x0+900,y1], outline=(210,210,215), width=3)
    if t >= m[2]:
        draw.text((W//2, 880), "U:  500 → 417 W/m²·K", font=get_font(74,True), fill=YELLOW, anchor="mm")
        draw.text((W//2, 975), "about 17% lower", font=get_font(50,True), fill=GREY, anchor="mm")
    if t >= m[3]:
        # Same resistance: 0.08 mm of deposit vs 6.4 mm of stainless steel (drawn to scale)
        ys0, ys1, px = 1110, 1400, 600/6.4
        draw.rectangle([200,ys0,200+max(8,int(0.08*px)),ys1], fill=BROWN)
        draw.text((204, ys1+22), "0.08 mm", font=get_font(44,True), fill=DEPOSIT_TXT, anchor="mt")
        draw.text((204, ys1+72), "deposit", font=get_font(44,True), fill=DEPOSIT_TXT, anchor="mt")
        draw.rectangle([400,ys0,400+int(6.4*px),ys1], fill=(165,170,180))
        draw.text((400+int(3.2*px), ys1+22), "6.4 mm", font=get_font(44,True), fill=GREY, anchor="mt")
        draw.text((400+int(3.2*px), ys1+72), "stainless steel", font=get_font(44,True), fill=GREY, anchor="mt")
        draw.text((W//2, ys0-50), "Same resistance to heat", font=get_font(52,True), fill=WHITE, anchor="mm")
    return img

# ── Scene E: Payoff — fewer transfer units, less heat ────────────────────────
def render_e(t, m, dur):
    img, draw = canvas()
    draw.text((W//2, 230), "Same exchanger, lower U", font=get_font(62,True), fill=WHITE, anchor="mm")
    f_lbl, f_val = get_font(56,True), get_font(76,True)
    draw.text((90, 420), "NTU", font=f_lbl, fill=GREY, anchor="lm")
    draw.text((990, 420), "2.00 → 1.67", font=f_val, fill=WHITE, anchor="rm")
    if t >= m[1]:
        draw.text((90, 560), "Effectiveness", font=f_lbl, fill=GREY, anchor="lm")
        draw.text((990, 560), "0.67 → 0.63", font=f_val, fill=WHITE, anchor="rm")
        k = _ease((t-m[1]-2.0)/1.2)
        base, bw, full = 1380, 300, 470
        for x, pct, name, col in [(160, 100, "Clean", (70,110,170)), (620, 100-6.25*k, "Fouled", BROWN)]:
            h = int(full*pct/100)
            draw.rectangle([x,base-h,x+bw,base], fill=col)
            draw.text((x+bw//2, base-h-45), f"{pct:.0f}%", font=get_font(60,True), fill=WHITE, anchor="mm")
            draw.text((x+bw//2, base+45), name, font=get_font(52,True), fill=GREY, anchor="mm")
        if k > 0.9:
            draw.text((W//2, 720), "Heat moved: about 6% less", font=get_font(60,True), fill=YELLOW, anchor="mm")
    return img

# ── Scene F: Easy to miss — flow steady, one thermometer drifting ────────────
def _trend_card(draw, y0, title, value, series, hi=False):
    draw.rounded_rectangle([60,y0,W-60,y0+470], radius=22, fill=(26,30,44),
                           outline=YELLOW if hi else (70,76,96), width=5 if hi else 3)
    draw.text((100,y0+60), title, font=get_font(52,True), fill=WHITE, anchor="lm")
    draw.text((W-100,y0+60), value, font=get_font(56,True), fill=YELLOW if hi else GREY, anchor="rm")
    gx0, gx1, gy0, gy1 = 110, W-110, y0+130, y0+400
    draw.line([(gx0,gy1),(gx1,gy1)], fill=(90,96,116), width=3)
    pts = [(gx0+(gx1-gx0)*i/(len(series)-1), gy0+(gy1-gy0)*(1-v)) for i, v in enumerate(series)]
    draw.line(pts, fill=YELLOW if hi else (150,200,255), width=7)
    draw.text((gx1, gy1+30), "time →", font=get_font(40), fill=GREY, anchor="rm")

def render_f(t, m, dur):
    img, draw = canvas()
    n = 60
    flow = [0.55 + 0.02*math.sin(i*1.7) for i in range(n)]
    temp = [0.75 - 0.45*(i/(n-1)) + 0.02*math.sin(i*2.3) for i in range(n)]   # 63 → 60 °C, illustrative
    _trend_card(draw, 230, "Flow", "steady", flow)
    _trend_card(draw, 790, "Cold outlet", "63 → 60 °C", temp, hi=(t >= m[1]))
    draw.text((W//2, 1330), "Trends illustrative", font=get_font(40), fill=GREY, anchor="mm")
    return img

# ── Scene G: The idea, and the limits of the example ─────────────────────────
def render_g(t, m, dur):
    img, draw = canvas()
    draw_text_centre(draw, "Fouling is a resistance in series", 330, get_font(64,True))
    draw_text_centre(draw, "Watch the temperatures, not just the flow", 560, get_font(58,True), YELLOW)
    if t >= m[1]:
        draw_box(draw, 800, ASSUMPTION, size=50)
    return img

# ── Scene H: Closing question over a baffle teaser (holds to the end) ────────
def render_h(t, m, dur):
    img, draw = canvas()
    sx0, sx1, sy0, sy1 = 90, 990, 420, 900
    draw.rounded_rectangle([sx0,sy0,sx1,sy1], radius=60, fill=COLD_BG, outline=(210,210,215), width=6)
    k = _ease(t/2.5)
    plates = [(260, True), (440, False), (620, True), (800, False)]
    for i, (x, from_top) in enumerate(plates):
        if k*len(plates) <= i:
            continue
        if from_top:
            draw.rectangle([x-9, sy0, x+9, sy1-150], fill=(190,195,205))
        else:
            draw.rectangle([x-9, sy0+150, x+9, sy1], fill=(190,195,205))
    if k > 0.95:
        # shell-side path weaves under top-hung plates and over bottom-standing ones
        path = [(140,820),(350,820),(350,500),(530,500),(530,820),(710,820),(710,500),(900,500),(930,500)]
        draw.line(path, fill=(150,190,255), width=8, joint="curve")
        draw.polygon([(925,480),(965,500),(925,520)], fill=(150,190,255))
    draw.text((W//2, 330), "Plates inside the shell", font=get_font(56,True), fill=GREY, anchor="mm")
    draw_text_centre(draw, "Next: why are there plates inside the shell?", 1150, get_font(66,True))
    draw.text((W//2, 1380), "S1 · E3 next: Baffles", font=get_font(72,True), fill=YELLOW, anchor="mm")
    return stamp_wordmark(img)

# ── Script: scenes → narration lines ─────────────────────────────────────────
# Each line is (narration, caption). The caption is what the viewer reads and
# must say what the narrator says; numbers are written as digits.
SCENES = [
    (render_a, [
        ("Nothing broke. Nothing leaked. Yet the outlet is three degrees colder.",
         "Nothing broke. Nothing leaked. Yet the outlet is 3 °C colder."),
    ]),
    (render_b, [
        ("Same exchanger. Same flows. Hot in at ninety, cold in at ten degrees Celsius.",
         "Same exchanger. Same flows. Hot in at 90, cold in at 10 °C."),
        ("Clean, the cold stream left at sixty-three. Now it leaves at sixty.",
         "Clean, the cold stream left at 63. Now it leaves at 60."),
    ]),
    (render_c, [
        ("What changed is a layer inside the tubes, eight hundredths of a millimetre thick. "
         "Thinner than a sheet of paper.",
         "What changed is a layer inside the tubes, 0.08 mm thick. Thinner than a sheet of paper."),
        ("It doesn't block the flow. It sits in the path of the heat.",
         "It doesn't block the flow. It sits in the path of the heat."),
    ]),
    (render_d, [
        ("Resistances in series simply add.",
         "Resistances in series simply add."),
        ("Clean, the resistance to heat flow is two thousandths of a square-metre-kelvin per watt. "
         "The deposit adds four ten-thousandths.",
         "Clean, the resistance to heat flow is 0.0020 m²·K/W. The deposit adds 0.0004."),
        ("So U falls from five hundred to about four hundred seventeen watts per square-metre-kelvin.",
         "So U falls from 500 to about 417 W/m²·K."),
        ("That sliver resists heat like six millimetres of stainless steel.",
         "That sliver resists heat like 6 mm of stainless steel."),
    ]),
    (render_e, [
        ("Lower U means fewer transfer units: two becomes about one point seven.",
         "Lower U means fewer transfer units: 2 becomes about 1.7."),
        ("Effectiveness slips from point six seven to point six three, "
         "and the exchanger moves about six percent less heat.",
         "Effectiveness slips from 0.67 to 0.63, and the exchanger moves about 6% less heat."),
    ]),
    (render_f, [
        ("Six percent is easy to miss. Flow is normal.",
         "6% is easy to miss. Flow is normal."),
        ("The only clue is a drifting thermometer.",
         "The only clue is a drifting thermometer."),
    ]),
    (render_g, [
        ("Fouling is a resistance in series. Watch the temperatures, not just the flow.",
         "Fouling is a resistance in series. Watch the temperatures, not just the flow."),
        ("These numbers are an illustrative worked example.",
         "These numbers are an illustrative worked example."),
    ]),
    (render_h, [
        ("Next: why are there plates inside the shell?",
         "Next: why are there plates inside the shell?"),
    ]),
]
MIN_SCENE = {}
TAIL_HOLD = {render_h: END_HOLD}
POSTER_AT = (render_d, 3, 2.5)    # resistance bar, U drop and the steel comparison all on screen

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
