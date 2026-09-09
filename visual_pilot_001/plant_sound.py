"""
DELIVERABLE C — the sound bed. Synthesised, not sampled.

Sound is part of this test, not decoration, so it is built to the same rule
as the picture: nothing may announce that something is wrong.

  • The machine bed NEVER changes. Same drone, same blade-pass, same level,
    start to finish. If the plant sounded wrong the story would be over.
  • Footsteps are locked to the animated gait and to his distance from the
    camera, so they swell as he approaches and STOP when he stops. The
    silence where the next footstep should have been is the loudest thing
    in the film.
  • At the third shot the world narrows: the wide top end comes down about
    eight decibels and the stereo image closes. The machine stays exactly
    where it was. The viewer leans in without being told to.
  • No music. No riser. No drone swell on the reveal.

Run: python plant_sound.py out.wav
"""

import math
import sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 27.0
N = int(SR * DUR)
t = np.arange(N) / SR

rng = np.random.default_rng(20260909)

# ── walk, matched to pilot001.py ─────────────────────────────────
WALK_SPEED, STOP_T, STOP_X, STRIDE = 0.60, 15.40, 2.85, 1.44
START_X = STOP_X - WALK_SPEED * STOP_T


def sos_bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "bandpass",
                                        fs=SR, output="sos"), x)


def sos_lp(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "lowpass", fs=SR,
                                        output="sos"), x)


def sos_hp(x, hz, order=2):
    return signal.sosfilt(signal.butter(order, hz, "highpass", fs=SR,
                                        output="sos"), x)


def env(times, vals):
    return np.interp(t, times, vals)


# ═════════════════════════════════════════════════════════════════
# 1. Machine bed. Constant for the whole film — this is the point.
# ═════════════════════════════════════════════════════════════════
def norm(x):
    return x / (np.max(np.abs(x)) + 1e-12)


brown = norm(np.cumsum(rng.normal(0, 1, N)))
bed = norm(sos_lp(brown, 190)) * 0.55
bed += norm(sos_lp(np.cumsum(rng.normal(0, 1, N)), 45)) * 0.28

drone = np.zeros(N)
for f0, amp, det in ((49.8, 1.00, 0.05), (99.6, 0.46, 0.09),
                     (149.4, 0.22, 0.13), (199.2, 0.10, 0.17)):
    drone += amp * np.sin(2 * np.pi * (f0 + det) * t)
drone *= 0.055

# induced-draught fan: shaft tone plus blade pass, slow amplitude wander
shaft = 24.6
fan = 0.85 * np.sin(2 * np.pi * shaft * t)
fan += 0.55 * np.sin(2 * np.pi * shaft * 12 * t + 0.7)     # 12 blades
fan += 0.22 * np.sin(2 * np.pi * shaft * 24 * t + 1.9)
fan *= (1.0 + 0.10 * np.sin(2 * np.pi * 0.33 * t)
        + 0.05 * np.sin(2 * np.pi * 0.117 * t + 2.1))
fan = sos_lp(fan, 900) * 0.030

machine = bed * 0.115 + drone + fan

print("  rms  machine %.4f  drone %.4f  fan %.4f"
      % (np.sqrt(np.mean(machine ** 2)), np.sqrt(np.mean(drone ** 2)),
         np.sqrt(np.mean(fan ** 2))))

# ═════════════════════════════════════════════════════════════════
# 2. Air and steam. Wide, high, and the first thing to go in Shot 3.
# ═════════════════════════════════════════════════════════════════
hiss_l = sos_bp(rng.normal(0, 1, N), 1400, 6500) * 0.020
hiss_r = sos_bp(rng.normal(0, 1, N), 1500, 7000) * 0.020

swell = np.zeros(N)
for at, dur_, amp in ((3.4, 3.6, 1.0), (12.6, 4.2, 0.75), (20.2, 3.4, 0.55)):
    i0, i1 = int(at * SR), int((at + dur_) * SR)
    k = np.linspace(0, 1, i1 - i0)
    swell[i0:i1] += amp * np.sin(np.pi * k) ** 2
vent = sos_bp(rng.normal(0, 1, N), 900, 4200) * swell * 0.026

# ═════════════════════════════════════════════════════════════════
# 3. Footsteps on grating. Locked to the gait, and they stop when he does.
# ═════════════════════════════════════════════════════════════════
def grating_step(seed):
    n = int(0.42 * SR)
    k = np.arange(n) / SR
    body = sos_bp(np.random.default_rng(seed).normal(0, 1, n), 420, 5200)
    body *= np.exp(-k * 46.0)
    ring = np.zeros(n)
    for f0, a, d in ((1147, 0.35, 22), (2358, 0.24, 30), (3910, 0.13, 40)):
        ring += a * np.sin(2 * np.pi * f0 * k) * np.exp(-k * d)
    thud = sos_lp(np.random.default_rng(seed + 7).normal(0, 1, n), 160)
    thud *= np.exp(-k * 30.0)
    s = body * 0.75 + ring * 0.55 + thud * 1.1
    return s / (np.max(np.abs(s)) + 1e-9)


steps_l = np.zeros(N)
steps_r = np.zeros(N)
step_i = 0
while True:
    st = step_i * (0.5 * STRIDE / WALK_SPEED)          # one step per half gait
    if st > STOP_T:
        break
    x = START_X + WALK_SPEED * st
    cam_x = 2.35 + (2.80 - 2.35) * min(1.0, st / 10.5)
    if st > 10.5:
        cam_x = 2.80 + (1.95 - 2.80) * min(1.0, (st - 10.5) / 5.0)
    d = abs(cam_x - x) + 1.2
    gain = 0.34 / (1.0 + d / 2.6)
    pan = np.clip((x - cam_x) / 7.0, -0.72, 0.42)
    sig = grating_step(1000 + step_i) * gain * (0.90 + 0.20 * ((step_i * 37) % 7) / 7)
    i0 = int(st * SR)
    i1 = min(N, i0 + len(sig))
    steps_l[i0:i1] += sig[:i1 - i0] * (0.5 - pan * 0.5 + 0.25)
    steps_r[i0:i1] += sig[:i1 - i0] * (0.5 + pan * 0.5 + 0.25)
    step_i += 1

# the last foot settling as he comes to a stop, then nothing
for st, g in ((15.28, 0.155),):
    sig = grating_step(4242) * g
    i0 = int(st * SR)
    steps_l[i0:i0 + len(sig)] += sig * 0.68
    steps_r[i0:i0 + len(sig)] += sig * 0.80

# ═════════════════════════════════════════════════════════════════
# 4. Two distant events, both well before he notices anything.
# ═════════════════════════════════════════════════════════════════
events_l = np.zeros(N)
events_r = np.zeros(N)
for at, seed, g, pan in ((7.4, 91, 0.075, -0.5), (9.9, 55, 0.048, 0.6)):
    n = int(1.2 * SR)
    k = np.arange(n) / SR
    cl = sos_bp(np.random.default_rng(seed).normal(0, 1, n), 700, 3600)
    cl *= np.exp(-k * 9.0)
    for f0, a in ((880, 0.30), (1490, 0.18)):
        cl += a * np.sin(2 * np.pi * f0 * k) * np.exp(-k * 7.0)
    cl = sos_lp(cl / (np.max(np.abs(cl)) + 1e-9), 5000) * g
    i0 = int(at * SR)
    events_l[i0:i0 + n] += cl * (0.5 - pan * 0.5)
    events_r[i0:i0 + n] += cl * (0.5 + pan * 0.5)

# ═════════════════════════════════════════════════════════════════
# 5. The narrowing. Top end and stereo width only — never the machine.
# ═════════════════════════════════════════════════════════════════
wide = env([0, 22.4, 24.4, 27.0], [1.00, 1.00, 0.56, 0.52])
air = env([0, 22.4, 24.4, 27.0], [1.00, 1.00, 0.50, 0.46])

L = machine + (hiss_l + vent * 0.9) * air + steps_l + events_l
R = machine + (hiss_r + vent * 1.0) * air + steps_r + events_r

mid = (L + R) * 0.5
side = (L - R) * 0.5 * wide
L, R = mid + side, mid - side

# picture fade in and out
master = env([0, 0.05, 1.60, 25.9, 27.0], [0.0, 0.10, 1.0, 1.0, 0.0])
L *= master
R *= master

print("  rms  steps %.4f  hiss %.4f  events %.4f"
      % (np.sqrt(np.mean(steps_l ** 2)), np.sqrt(np.mean(hiss_l ** 2)),
         np.sqrt(np.mean(events_l ** 2))))
peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L, R = L / peak * 0.70, R / peak * 0.70

out = np.stack([L, R], axis=1)
path = sys.argv[1] if len(sys.argv) > 1 else "plant_bed.wav"
wavfile.write(path, SR, (out * 32767).astype(np.int16))
print("wrote %s  %.3f s  peak %.3f" % (path, DUR, peak))
