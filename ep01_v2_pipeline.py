"""
Plant Mysteries · HX EP01 v2 · The Flip
Video generation pipeline: Kokoro TTS narration + programmatic animation + moviepy assembly

Run from the learnwithavisha folder:
    cd ~/Documents/Avisha/learnwithavisha
    .venv/bin/python3 ep01_v2_pipeline.py

Install (once):
    .venv/bin/pip install kokoro-onnx soundfile

Output (in ./out/):
    hx_ep01_v2_master.mp4      1080x1920 H.264 30fps master
    hx_ep01_v2_web.mp4         720x1280 web derivative (<=5 MB)
    hx_ep01_v2.srt             SRT captions
    hx_ep01_v2_poster.jpg      poster frame
"""

import os, sys, math, textwrap, subprocess
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

W, H = 1080, 1920
FPS  = 30
BG   = (18, 20, 28)
# Kokoro voice — same provider and voice Isha (Nim-Isha) uses
KOKORO_VOICE = "af_heart"
KOKORO_SPEED = 0.95   # slightly slower for educational pacing
OUT = Path("out")
OUT.mkdir(exist_ok=True)

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

def draw_text_centre(draw, text, y, font, colour=(255,255,255)):
    lines = textwrap.wrap(text, width=34)
    try:
        line_h = font.size + 10
    except AttributeError:
        line_h = 20
    y_cur = int(y - len(lines)*line_h//2)
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font)
        x = (W - (bbox[2]-bbox[0])) // 2
        draw.text((x, y_cur), line, font=font, fill=colour)
        y_cur += line_h

def to_arr(img): return __import__('numpy').array(img)

def make_scene_clip(render_fn, duration):
    def mf(t): return to_arr(render_fn(t))
    return VideoClip(mf, duration=duration).with_fps(FPS)

# ── Scene A: Opening hook (3 s) ───────────────────────────────────────────────
def render_a(t):
    phase = int(t)
    counterflow = (phase == 1)
    cold_temp = 63 if counterflow else 49
    img, draw = canvas()
    ew, eh = 800, 200
    ex, ey = (W-ew)//2, H//2-230
    mid_y = ey+eh//2
    draw.rectangle([ex,ey,ex+ew,ey+eh], outline=(180,180,180), width=3)
    draw.line([(ex,mid_y),(ex+ew,mid_y)], fill=(200,200,200), width=2)
    col_hot=(220,60,60); col_cold=(60,120,220)
    draw.rectangle([ex+4,ey+4,ex+ew-4,mid_y-4], fill=(40,12,12))
    for i in range(3):
        ax = ex+120+i*200
        draw.polygon([(ax,mid_y-55),(ax+45,mid_y-30),(ax,mid_y-8)], fill=col_hot)
    draw.text((ex+14,ey+12), "90°C", font=get_font(40,True), fill=col_hot)
    draw.text((ex+ew-100,ey+12), "37°C" if counterflow else "51°C",
              font=get_font(40,True), fill=col_hot)
    draw.rectangle([ex+4,mid_y+4,ex+ew-4,ey+eh-4], fill=(12,20,50))
    if not counterflow:
        for i in range(3):
            ax = ex+120+i*200
            draw.polygon([(ax,mid_y+8),(ax+45,mid_y+33),(ax,mid_y+55)], fill=col_cold)
        draw.text((ex+14,ey+eh-55), "10°C", font=get_font(40,True), fill=col_cold)
        draw.text((ex+ew-100,ey+eh-55), f"{cold_temp}°C", font=get_font(40,True), fill=col_cold)
    else:
        for i in range(3):
            ax = ex+ew-120-i*200
            draw.polygon([(ax,mid_y+8),(ax-45,mid_y+33),(ax,mid_y+55)], fill=col_cold)
        draw.text((ex+ew-100,ey+eh-55), "10°C", font=get_font(40,True), fill=col_cold)
        draw.text((ex+14,ey+eh-55), f"{cold_temp}°C", font=get_font(40,True), fill=(255,220,40))
    draw_text_centre(draw, "Reverse one stream. Same exchanger.", H//2+240, get_font(48,True))
    draw_text_centre(draw, "More heat.  Why?", H//2+330, get_font(54,True), (255,220,40))
    return img

# ── Scene B: Parallel flow labelled (7 s) ────────────────────────────────────
def render_b(t):
    img, draw = canvas()
    ew, eh = 820, 230
    ex, ey = (W-ew)//2, H//2-180
    mid_y = ey+eh//2
    hw = (t >= 4.0)
    draw.rectangle([ex,ey,ex+ew,ey+eh], outline=(200,200,200), width=4)
    draw.line([(ex,mid_y),(ex+ew,mid_y)], fill=(255,220,80) if hw else (200,200,200), width=4 if hw else 2)
    col_hot=(220,60,60); col_cold=(60,120,220)
    draw.rectangle([ex+4,ey+4,ex+ew-4,mid_y-4], fill=(40,12,12))
    for i in range(4):
        ax=ex+70+i*175
        draw.polygon([(ax,mid_y-58),(ax+50,mid_y-33),(ax,mid_y-10)], fill=col_hot)
    draw.text((ex+14,ey+12), "90°C", font=get_font(40,True), fill=col_hot)
    draw.text((ex+ew-95,ey+12), "51°C", font=get_font(40,True), fill=col_hot)
    draw_text_centre(draw, "TUBE SIDE (hot)", ey+eh//4, get_font(36,True), col_hot)
    draw.rectangle([ex+4,mid_y+4,ex+ew-4,ey+eh-4], fill=(12,20,50))
    for i in range(4):
        ax=ex+70+i*175
        draw.polygon([(ax,mid_y+10),(ax+50,mid_y+35),(ax,mid_y+57)], fill=col_cold)
    draw.text((ex+14,ey+eh-55), "10°C", font=get_font(40,True), fill=col_cold)
    draw.text((ex+ew-95,ey+eh-55), "49°C", font=get_font(40,True), fill=col_cold)
    draw_text_centre(draw, "SHELL SIDE (cold)", ey+3*eh//4, get_font(36,True), col_cold)
    msg = "Heat crosses through this wall" if hw else "Hot fluid inside · Cold fluid outside"
    draw_text_centre(draw, msg, H//2+220, get_font(44,True), (255,220,80) if hw else (200,200,200))
    return img

# ── Scene C: Parallel temp graph (13 s) ──────────────────────────────────────
GX,GY,GW,GH = 140,820,780,520

def _draw_parallel_graph(draw, show_gaps=False):
    draw.line([(GX,GY-GH),(GX,GY),(GX+GW,GY)], fill=(200,200,200), width=3)
    draw.text((GX-10,GY+22), "Hot inlet end", font=get_font(30), fill=(200,200,200))
    draw.text((GX+GW-130,GY+22), "Hot outlet end", font=get_font(30), fill=(200,200,200))
    for tv,lbl in [(10,"10"),(49,"49"),(51,"51"),(90,"90")]:
        yp=int(GY-(tv/100)*GH)
        draw.line([(GX-8,yp),(GX+5,yp)], fill=(160,160,160), width=1)
        draw.text((GX-55,yp-12), lbl, font=get_font(28), fill=(160,160,160))
    pts_h=[(int(GX+x*(GW/10)),int(GY-((90-x*39/10)/100)*GH)) for x in range(11)]
    for i in range(10): draw.line([pts_h[i],pts_h[i+1]], fill=(220,60,60), width=4)
    pts_c=[(int(GX+x*(GW/10)),int(GY-((10+x*39/10)/100)*GH)) for x in range(11)]
    for i in range(10): draw.line([pts_c[i],pts_c[i+1]], fill=(60,120,220), width=4)
    if show_gaps:
        for frac, side in [(0.1,"Large ΔT"),(0.9,"Small ΔT")]:
            xp=int(GX+frac*GW)
            hy=int(GY-((90-frac*39)/100)*GH)
            cy=int(GY-((10+frac*39)/100)*GH)
            draw.line([(xp,hy),(xp,cy)], fill=(255,220,0), width=3)
            draw.text((xp-10,(hy+cy)//2-55), side, font=get_font(34,True), fill=(255,220,0))

def render_c(t):
    img, draw = canvas()
    _draw_parallel_graph(draw, show_gaps=(t>=5.0))
    if t < 5.0:
        draw_text_centre(draw, "Hot drops.  Cold rises.  They converge.", H-200, get_font(44,True), (200,200,200))
    elif t < 9.0:
        draw_text_centre(draw, "Near the outlet, the gap becomes very small.", H-200, get_font(44,True), (200,200,200))
    if t >= 9.0:
        ax1,ay1,ax2,ay2 = 80,GY-GH-360,W-80,GY-GH-70
        draw.rectangle([ax1,ay1,ax2,ay2], fill=(28,33,48), outline=(255,220,0), width=2)
        draw.text((ax1+20,ay1+18), "Idealised worked example", font=get_font(38,True), fill=(255,220,80))
        for i,l in enumerate([
            "· Equal heat-capacity rates (ṁCp equal for both)",
            "· Constant UA · Steady state · No phase change",
            "· NTU = 2 · Fixed inlet temperatures",
        ]):
            draw.text((ax1+20,ay1+70+i*42), l, font=get_font(30), fill=(200,200,200))
    return img

# ── Scene D: Flip transition (4 s) ───────────────────────────────────────────
def render_d(t):
    p = 0.0
    if t >= 2.5:
        raw=(t-2.5)/1.5
        p=max(0.0,min(1.0,0.5-0.5*math.cos(math.pi*raw)))
    img, draw = canvas()
    ew,eh=820,230; ex,ey=(W-ew)//2,H//2-190; mid_y=ey+eh//2
    draw.rectangle([ex,ey,ex+ew,ey+eh], outline=(200,200,200), width=4)
    draw.line([(ex,mid_y),(ex+ew,mid_y)], fill=(200,200,200), width=2)
    col_hot=(220,60,60); col_cold=(60,120,220)
    draw.rectangle([ex+4,ey+4,ex+ew-4,mid_y-4], fill=(40,12,12))
    for i in range(4):
        ax=ex+70+i*175
        draw.polygon([(ax,mid_y-58),(ax+50,mid_y-33),(ax,mid_y-10)], fill=col_hot)
    draw.text((ex+14,ey+12), "90°C", font=get_font(40,True), fill=col_hot)
    draw.text((ex+ew-95,ey+12), f"{int(51+(37-51)*p)}°C", font=get_font(40,True), fill=col_hot)
    draw.rectangle([ex+4,mid_y+4,ex+ew-4,ey+eh-4], fill=(12,20,50))
    cold_out=int(49+(63-49)*p)
    if p < 0.5:
        for i in range(4):
            ax=ex+70+i*175
            draw.polygon([(ax,mid_y+10),(ax+50,mid_y+35),(ax,mid_y+57)], fill=col_cold)
        draw.text((ex+14,ey+eh-55), "10°C", font=get_font(40,True), fill=col_cold)
        draw.text((ex+ew-95,ey+eh-55), f"{cold_out}°C", font=get_font(40,True), fill=col_cold)
    else:
        for i in range(4):
            ax=ex+ew-70-i*175
            draw.polygon([(ax,mid_y+10),(ax-50,mid_y+35),(ax,mid_y+57)], fill=col_cold)
        draw.text((ex+ew-95,ey+eh-55), "10°C", font=get_font(40,True), fill=col_cold)
        draw.text((ex+14,ey+eh-55), f"{cold_out}°C", font=get_font(40,True), fill=col_cold)
    draw_text_centre(draw, "Now reverse the cold stream.", H//2+250, get_font(48,True))
    return img

# ── Scene E: Counterflow + 3-beat outlet explanation (14 s) ──────────────────
def _draw_cf_hx(draw, label=""):
    ew,eh=820,230; ex,ey=(W-ew)//2,H//2-220; mid_y=ey+eh//2
    draw.rectangle([ex,ey,ex+ew,ey+eh], outline=(200,200,200), width=4)
    draw.line([(ex,mid_y),(ex+ew,mid_y)], fill=(200,200,200), width=2)
    col_hot=(220,60,60); col_cold=(60,120,220)
    draw.rectangle([ex+4,ey+4,ex+ew-4,mid_y-4], fill=(40,12,12))
    for i in range(4):
        ax=ex+70+i*175
        draw.polygon([(ax,mid_y-58),(ax+50,mid_y-33),(ax,mid_y-10)], fill=col_hot)
    draw.text((ex+14,ey+12), "90°C", font=get_font(40,True), fill=col_hot)
    draw.text((ex+ew-95,ey+12), "37°C", font=get_font(40,True), fill=col_hot)
    draw.rectangle([ex+4,mid_y+4,ex+ew-4,ey+eh-4], fill=(12,20,50))
    for i in range(4):
        ax=ex+ew-70-i*175
        draw.polygon([(ax,mid_y+10),(ax-50,mid_y+35),(ax,mid_y+57)], fill=col_cold)
    draw.text((ex+ew-95,ey+eh-55), "10°C", font=get_font(40,True), fill=col_cold)
    draw.text((ex+14,ey+eh-55), "63°C", font=get_font(40,True), fill=col_cold)
    if label:
        draw_text_centre(draw, label, H//2+230, get_font(44,True))
    return ex,ey,ew,eh

def render_e(t):
    img, draw = canvas()
    if t < 4.0:
        _draw_cf_hx(draw, "The fluids still never mix — separated by the same wall.")
    elif t < 7.0:
        _draw_cf_hx(draw, "Hot stream outlet: 37°C")
    elif t < 10.0:
        _draw_cf_hx(draw, "Cold stream outlet: 63°C")
    else:
        ex,ey,ew,eh=_draw_cf_hx(draw)
        mid_y=ey+eh//2; r=90
        col_hot=(220,60,60); col_cold=(60,120,220)
        for cx2,cy2,th,tc in [(ex,mid_y,"90°C hot","63°C cold"),(ex+ew,mid_y,"37°C hot","10°C cold")]:
            draw.ellipse([cx2-r,cy2-r,cx2+r,cy2+r], outline=(255,220,40), width=3)
            draw.text((cx2-90,cy2-115), th, font=get_font(34,True), fill=col_hot)
            draw.text((cx2-90,cy2+70), tc, font=get_font(34,True), fill=col_cold)
        draw_text_centre(draw, "These outlets are at opposite ends.", H//2+230, get_font(44,True))
        draw_text_centre(draw, "Locally, hot is always hotter than cold.", H//2+300, get_font(40), (200,200,200))
    return img

# ── Scene F: Counterflow graph + bar chart (14 s) ────────────────────────────
def render_f(t):
    img, draw = canvas()
    if t < 9.0:
        gx,gy,gw,gh=140,820,780,520
        draw.line([(gx,gy-gh),(gx,gy),(gx+gw,gy)], fill=(200,200,200), width=3)
        draw.text((gx-10,gy+22), "Hot inlet end", font=get_font(30), fill=(200,200,200))
        draw.text((gx+gw-130,gy+22), "Hot outlet end", font=get_font(30), fill=(200,200,200))
        for tv,lbl in [(10,"10"),(37,"37"),(63,"63"),(90,"90")]:
            yp=int(gy-(tv/100)*gh)
            draw.line([(gx-8,yp),(gx+5,yp)], fill=(160,160,160), width=1)
            draw.text((gx-55,yp-12), lbl, font=get_font(28), fill=(160,160,160))
        pts_h=[(int(gx+x*(gw/10)),int(gy-((90-x*53/10)/100)*gh)) for x in range(11)]
        for i in range(10): draw.line([pts_h[i],pts_h[i+1]], fill=(220,60,60), width=4)
        pts_c=[(int(gx+x*(gw/10)),int(gy-((63-x*53/10)/100)*gh)) for x in range(11)]
        for i in range(10): draw.line([pts_c[i],pts_c[i+1]], fill=(60,120,220), width=4)
        for j in range(1,10,2):
            xj=int(gx+j*(gw/10))
            hy=int(gy-((90-j*53/10)/100)*gh)
            cy=int(gy-((63-j*53/10)/100)*gh)
            draw.line([(xj,hy),(xj,cy)], fill=(255,220,0), width=2)
        draw_text_centre(draw, "ΔT stays constant — in this example", gy-gh-60, get_font(40,True), (255,220,0))
        draw_text_centre(draw, "Counterflow maintains a useful driving force — all the way along.", H-200, get_font(40,True), (200,200,200))
    else:
        progress=min((t-9.0)/3.0,1.0)
        bw=230; par_h=400; par_x=W//2-bw-50
        draw.rectangle([par_x,H//2-par_h,par_x+bw,H//2], fill=(80,80,160))
        draw_text_centre(draw, "Parallel", H//2-par_h-55, get_font(38,True), (200,200,220))
        draw_text_centre(draw, "baseline", H//2-par_h-100, get_font(34), (180,180,200))
        ctr_h=int(par_h*1.36*progress); ctr_x=W//2+50
        if ctr_h>0: draw.rectangle([ctr_x,H//2-ctr_h,ctr_x+bw,H//2], fill=(220,80,60))
        if progress>0.1: draw_text_centre(draw, "Counterflow", H//2-ctr_h-55, get_font(38,True), (255,180,160))
        if progress>0.9:
            draw_text_centre(draw, "≈36% more", H//2-ctr_h-100, get_font(36,True), (255,220,40))
            draw_text_centre(draw, "in this example", H//2+70, get_font(36), (200,200,200))
        draw_text_centre(draw, "Same exchanger · Same inlet temperatures", H//2+140, get_font(38,True), (200,200,200))
    return img

# ── Scene G: End card (5 s) ───────────────────────────────────────────────────
def render_g(t):
    img, draw = canvas()
    draw_text_centre(draw, "That's why counterflow is often preferred for heat recovery.", H//2-60, get_font(54,True))
    draw_text_centre(draw, "Plant Mysteries · HX EP01 · The Flip", H//2+140, get_font(38), (180,180,180))
    return img

# ── Scene H: Deposit teaser (8 s) ────────────────────────────────────────────
def render_h(t):
    frac=min(t/6.0,1.0)
    img, draw = canvas()
    cx,cy=W//2,H//2-120; R_o=220; R_w=R_o-30; R_f=R_w-int(60*frac)
    draw.ellipse([cx-R_o,cy-R_o,cx+R_o,cy+R_o], fill=(70,70,70))
    draw.ellipse([cx-R_w,cy-R_w,cx+R_w,cy+R_w], fill=(90,60,35) if frac>0 else (110,110,110))
    draw.ellipse([cx-R_f,cy-R_f,cx+R_f,cy+R_f], fill=(180,40,40))
    draw_text_centre(draw, "Next: what changes when deposits build up?", H//2+240, get_font(46,True))
    draw_text_centre(draw, "Plant Mysteries · HX EP02", H//2+340, get_font(38), (180,180,180))
    return img

# ── Voiceover ─────────────────────────────────────────────────────────────────
VOICEOVER_SCRIPT = (
    "Here's a heat exchanger — hot fluid on the inside, cold fluid on the outside. "
    "They flow in the same direction — parallel flow. Heat crosses through this wall. "
    "Watch the temperatures. Hot drops. Cold rises. They converge. "
    "The temperature gap is what pushes heat across. Near the outlet, the gap becomes very small — so less heat transfers there. "
    "This is an idealised example — equal flow rates, same heat capacity, steady state. "
    "Now reverse the cold stream. "
    "Counterflow. The fluids still never mix — separated by the same wall. "
    "Hot stream outlet: thirty-seven degrees. "
    "Cold stream outlet: sixty-three degrees. "
    "These outlets are at opposite ends. Locally, the hot fluid is always hotter than the cold — heat only flows one way. "
    "In this example, the temperature gap stays constant along the whole exchanger. "
    "Counterflow maintains a useful driving force — all the way along. "
    "Same exchanger. Same inlet temperatures. Counterflow transfers approximately thirty-six percent more heat — in this example. "
    "That's why counterflow is often preferred for heat recovery. "
    "Next time: what changes when deposits start building up?"
)

def generate_narration(_unused=None):
    """Generate narration with Kokoro (local, no API key needed).
    Same voice (af_heart) that Isha / Nim-Isha uses on Avisha's voice server.
    Output is WAV; moviepy handles it without conversion.
    """
    out_path = OUT / "narration_kokoro.wav"
    if out_path.exists() and out_path.stat().st_size > 1000:
        print(f"  narration cached: {out_path}")
        return out_path
    if out_path.exists():
        out_path.unlink()   # remove stale zero-byte file
    print(f"  generating narration via Kokoro ({KOKORO_VOICE})…")
    # kokoro-onnx does not download weights itself; reuse the copies Isha's voice server keeps
    kokoro_dir = Path.home() / "Library/Application Support/Isha/kokoro"
    kokoro = kokoro_onnx.Kokoro(
        os.environ.get("KOKORO_MODEL", str(kokoro_dir / "kokoro-v1.0.onnx")),
        os.environ.get("KOKORO_VOICES", str(kokoro_dir / "voices-v1.0.bin")),
    )
    samples, sample_rate = kokoro.create(
        VOICEOVER_SCRIPT,
        voice=KOKORO_VOICE,
        speed=KOKORO_SPEED,
        lang="en-us",
    )
    sf.write(str(out_path), samples, sample_rate)
    print(f"  saved: {out_path} ({out_path.stat().st_size/1e3:.0f} kB, {sample_rate} Hz)")
    return out_path

# ── SRT ───────────────────────────────────────────────────────────────────────
SRT_CONTENT = """\
1
00:00:00,000 --> 00:00:03,000
Reverse one stream. Same exchanger. More heat. Why?

2
00:00:04,000 --> 00:00:07,000
Hot fluid on the inside, cold fluid on the outside.

3
00:00:07,000 --> 00:00:11,000
They flow in the same direction — parallel flow.

4
00:00:11,000 --> 00:00:16,000
Hot drops. Cold rises. They converge.

5
00:00:16,000 --> 00:00:20,000
Near the outlet, the gap becomes very small — so less heat transfers there.

6
00:00:20,000 --> 00:00:24,000
Idealised worked example

7
00:00:24,000 --> 00:00:28,000
Now reverse the cold stream.

8
00:00:28,000 --> 00:00:32,000
The fluids still never mix — separated by the same wall.

9
00:00:32,000 --> 00:00:35,000
Hot stream outlet: 37°C

10
00:00:35,000 --> 00:00:38,000
Cold stream outlet: 63°C

11
00:00:38,000 --> 00:00:42,000
These outlets are at opposite ends. Locally, hot is always hotter than cold.

12
00:00:42,000 --> 00:00:48,000
In this example, the temperature gap stays constant.

13
00:00:48,000 --> 00:00:51,000
Counterflow maintains a useful temperature difference.

14
00:00:51,000 --> 00:00:56,000
≈36% more heat transferred in this example

15
00:00:56,000 --> 00:01:00,000
That's why counterflow is often preferred for heat recovery.

16
00:01:00,000 --> 00:01:08,000
Next: what changes when deposits build up?
"""

# ── Assembly ──────────────────────────────────────────────────────────────────
def assemble(narration_path):
    print("  building scenes…")
    scenes = [
        make_scene_clip(render_a,  3.0),
        make_scene_clip(render_b,  7.0),
        make_scene_clip(render_c, 13.0),
        make_scene_clip(render_d,  4.0),
        make_scene_clip(render_e, 14.0),
        make_scene_clip(render_f, 14.0),
        make_scene_clip(render_g,  5.0),
        make_scene_clip(render_h,  8.0),
    ]
    total = sum(s.duration for s in scenes)
    print(f"  total: {total:.0f}s")
    video = concatenate_videoclips(scenes)
    audio = AudioFileClip(str(narration_path))
    dur = min(audio.duration, video.duration)
    video = video.with_audio(audio.with_duration(dur))
    master = OUT / "hx_ep01_v2_master.mp4"
    video.write_videofile(str(master), fps=FPS, codec="libx264", audio_codec="aac",
                          audio_bitrate="128k", preset="medium", logger=None)
    print(f"  master: {master.stat().st_size/1e6:.1f} MB")
    return master

def add_captions(video_path):
    srt = OUT / "hx_ep01_v2.srt"
    srt.write_text(SRT_CONTENT, encoding="utf-8")
    out = OUT / "hx_ep01_v2_captioned.mp4"
    r = subprocess.run(
        ["ffmpeg","-y","-i",str(video_path),
         "-vf",f"subtitles={srt}:force_style='FontName=Arial,FontSize=22,"
               "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
               "BorderStyle=3,Outline=2,Shadow=1,MarginV=80'",
         "-c:a","copy",str(out)],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("  captions failed, using uncaptioned")
        return video_path
    return out

def make_web(master):
    out = OUT / "hx_ep01_v2_web.mp4"
    subprocess.run(["ffmpeg","-y","-i",str(master),"-vf","scale=720:1280",
                    "-c:v","libx264","-crf","26","-preset","medium",
                    "-c:a","aac","-b:a","96k",str(out)],
                   capture_output=True, check=True)
    mb = out.stat().st_size/1e6
    if mb > 5.0:
        subprocess.run(["ffmpeg","-y","-i",str(master),"-vf","scale=720:1280",
                        "-c:v","libx264","-crf","30","-preset","medium",
                        "-c:a","aac","-b:a","96k",str(out)],
                       capture_output=True, check=True)
    print(f"  web: {out.stat().st_size/1e6:.1f} MB")
    return out

def poster(master, t=4.5):
    p = OUT / "hx_ep01_v2_poster.jpg"
    subprocess.run(["ffmpeg","-y","-ss",str(t),"-i",str(master),
                    "-frames:v","1","-q:v","2",str(p)], capture_output=True, check=True)
    print(f"  poster: {p}")
    return p

def main():
    print("=== Plant Mysteries · HX EP01 v2 ===")
    nar   = generate_narration()
    mstr  = assemble(nar)
    cap   = add_captions(mstr)
    (OUT/"hx_ep01_v2.srt").write_text(SRT_CONTENT, encoding="utf-8")
    web   = make_web(cap)
    pst   = poster(cap)
    print(f"\n=== DONE ===")
    print(f"  Master:  {mstr}")
    print(f"  Web:     {web}")
    print(f"  SRT:     {OUT/'hx_ep01_v2.srt'}")
    print(f"  Poster:  {pst}")

if __name__ == "__main__":
    main()
