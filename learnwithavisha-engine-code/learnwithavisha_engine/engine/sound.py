"""
engine/sound.py — the sound library and the episode mix.

Split the way the picture is split. The WORLD owns three stems:

    plant_ambience.wav   the machine. Constant, and it never changes level.
    steam.wav            air and vents. Wide, high, the first thing to go.
    footsteps_grating.wav  eight boot variants on grating, one per second.

The EPISODE owns only the placement. Its footsteps are read straight off the
character's gait, so the sound cannot drift out of step with the picture —
they swell as he approaches and they stop when he stops. The silence where
the next footstep should have been is the loudest thing in the film.

Rule that outranks the others: the machine bed never changes. If the plant
sounded wrong the story would be over. Only the air and the stereo width
close in the third shot.

Run: python -m engine.sound            # regenerate the world stems
"""

import os

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     ".."))
SOUND = os.path.join(ROOT, "world", "sound")
_FFMPEG = ("/Users/mrinalgala/Documents/Avisha/learnwithavisha/"
           ".micromamba/root/envs/manim/bin/ffmpeg")
STEM_SECONDS = 30.0
N_FOOTSTEPS = 8
FOOTSTEP_SLOT = 1.0


def _sos(x, kind, *cut, order=2):
    return signal.sosfilt(signal.butter(order, list(cut) if len(cut) > 1
                                        else cut[0], kind, fs=SR,
                                        output="sos"), x)


def _norm(x):
    return x / (np.max(np.abs(x)) + 1e-12)


# ═══ world stems ═════════════════════════════════════════════════
def synth_plant_ambience(seconds=STEM_SECONDS, seed=20260909):
    """Induced-draught fan and the low bed. Deliberately featureless: this
    is the sound that must NOT change when he notices something."""
    rng = np.random.default_rng(seed)
    n = int(SR * seconds)
    t = np.arange(n) / SR

    bed = _norm(_sos(_norm(np.cumsum(rng.normal(0, 1, n))), "lowpass", 190)) * 0.55
    bed += _norm(_sos(np.cumsum(rng.normal(0, 1, n)), "lowpass", 45)) * 0.28

    drone = np.zeros(n)
    for f0, amp, det in ((49.8, 1.00, 0.05), (99.6, 0.46, 0.09),
                         (149.4, 0.22, 0.13), (199.2, 0.10, 0.17)):
        drone += amp * np.sin(2 * np.pi * (f0 + det) * t)
    drone *= 0.055

    shaft = 24.6
    fan = 0.85 * np.sin(2 * np.pi * shaft * t)
    fan += 0.55 * np.sin(2 * np.pi * shaft * 12 * t + 0.7)      # 12 blades
    fan += 0.22 * np.sin(2 * np.pi * shaft * 24 * t + 1.9)
    fan *= (1.0 + 0.10 * np.sin(2 * np.pi * 0.33 * t)
            + 0.05 * np.sin(2 * np.pi * 0.117 * t + 2.1))
    fan = _sos(fan, "lowpass", 900) * 0.030

    m = bed * 0.115 + drone + fan
    return np.stack([m, m], axis=1)


def synth_steam(seconds=STEM_SECONDS, seed=771):
    """Air and vents, wide and high. Swells are slow and irregular."""
    rng = np.random.default_rng(seed)
    n = int(SR * seconds)
    L = _sos(rng.normal(0, 1, n), "bandpass", 1400, 6500) * 0.020
    R = _sos(rng.normal(0, 1, n), "bandpass", 1500, 7000) * 0.020
    swell = np.zeros(n)
    for at, dur, amp in ((3.4, 3.6, 1.0), (12.6, 4.2, 0.75), (20.2, 3.4, 0.55),
                         (26.0, 3.0, 0.65)):
        i0, i1 = int(at * SR), min(n, int((at + dur) * SR))
        if i1 > i0:
            swell[i0:i1] += amp * np.sin(np.pi * np.linspace(0, 1, i1 - i0)) ** 2
    vent = _sos(rng.normal(0, 1, n), "bandpass", 900, 4200) * swell * 0.026
    return np.stack([L + vent * 0.9, R + vent * 1.0], axis=1)


def synth_footsteps(n_variants=N_FOOTSTEPS, slot=FOOTSTEP_SLOT):
    """Boot on grating: a filtered transient, a metallic ring off the bars,
    and a low thud. One variant per second so the mix can pick between them
    and his walk never sounds looped."""
    n = int(SR * slot * n_variants)
    out = np.zeros(n)
    ln = int(0.42 * SR)
    k = np.arange(ln) / SR
    for v in range(n_variants):
        rng = np.random.default_rng(1000 + v)
        body = _sos(rng.normal(0, 1, ln), "bandpass", 420, 5200) * np.exp(-k * 46.0)
        ring = np.zeros(ln)
        for f0, a, d in ((1147, 0.35, 22), (2358, 0.24, 30), (3910, 0.13, 40)):
            ring += a * np.sin(2 * np.pi * f0 * (1 + 0.01 * v) * k) * np.exp(-k * d)
        thud = _sos(np.random.default_rng(2000 + v).normal(0, 1, ln),
                    "lowpass", 160) * np.exp(-k * 30.0)
        s = _norm(body * 0.75 + ring * 0.55 + thud * 1.1)
        i0 = int(v * slot * SR)
        out[i0:i0 + ln] = s
    return np.stack([out, out], axis=1)


def write_stems():
    os.makedirs(SOUND, exist_ok=True)
    for name, data in (("plant_ambience", synth_plant_ambience()),
                       ("steam", synth_steam()),
                       ("footsteps_grating", synth_footsteps())):
        p = os.path.join(SOUND, name + ".wav")
        wavfile.write(p, SR, (np.clip(data, -1, 1) * 32767).astype(np.int16))
        print("  %-52s %6.2f s  peak %.3f"
              % (os.path.relpath(p, ROOT), len(data) / SR,
                 float(np.max(np.abs(data)))))


# ═══ episode mix ═════════════════════════════════════════════════
def _load(name):
    sr, a = wavfile.read(os.path.join(SOUND, name + ".wav"))
    assert sr == SR, "%s is not %d Hz" % (name, SR)
    return a.astype(np.float64) / 32768.0


def _fit(stem, n):
    if len(stem) >= n:
        return stem[:n]
    reps = int(np.ceil(n / len(stem)))
    return np.tile(stem, (reps, 1))[:n]


def mix_episode(stage, out_path, episode_dir=None):
    """Place the world's stems against this episode's clock."""
    ep = stage.episode
    spec = ep["sound"]
    n = int(SR * ep["runtime"])
    t = np.arange(n) / SR
    mix = np.zeros((n, 2))

    machine = _fit(_load("plant_ambience"), n)
    air = _fit(_load(spec["stems"][1]), n) if len(spec["stems"]) > 1 \
        else np.zeros((n, 2))

    # the narrowing: air and stereo width only, never the machine
    nr = spec["narrow"]
    air_env = np.interp(t, [0, nr["from"], nr["to"], ep["runtime"]],
                        [1.0, 1.0, nr["air"], nr["air"] * 0.92])[:, None]
    width_env = np.interp(t, [0, nr["from"], nr["to"], ep["runtime"]],
                          [1.0, 1.0, nr["width"], nr["width"] * 0.93])

    mix += machine + air * air_env

    # footsteps, read straight off the gait
    steps = _load(spec["footsteps"])
    slot = int(FOOTSTEP_SLOT * SR)
    name = ep["characters"][0]
    track = stage.tracks[name]
    for i, st in enumerate(track.footstep_times(ep["runtime"])):
        x = track.at(st)["x"]
        cx, _, _ = stage.camera_track.at(st)
        d = abs(cx - x) + 1.2
        gain = 0.34 / (1.0 + d / 2.6)
        pan = float(np.clip((x - cx) / 7.0, -0.72, 0.42))
        v = i % N_FOOTSTEPS
        seg = steps[v * slot:v * slot + int(0.42 * SR)]
        i0 = int(st * SR)
        i1 = min(n, i0 + len(seg))
        if i1 <= i0:
            continue
        mix[i0:i1, 0] += seg[:i1 - i0, 0] * gain * (0.75 - pan * 0.5)
        mix[i0:i1, 1] += seg[:i1 - i0, 1] * gain * (0.75 + pan * 0.5)

    # Wade's line. It is the only voice in the episode, so it sits dry and
    # slightly forward — no reverb, no ducking. He is talking to himself.
    for vo in ep.get("voiceover", []):
        path = None if episode_dir is None else \
            os.path.join(episode_dir, vo.get("file", ""))
        if not path or not os.path.exists(path):
            print("  voiceover MISSING: %r at %.1fs — the beat plays as a "
                  "held silence until %s is dropped in"
                  % (vo["line"], vo["at"], vo.get("file")))
            continue
        wav = os.path.join(os.path.dirname(out_path), "_vo_tmp.wav")
        os.system('%s -v error -y -i "%s" -ac 1 -ar %d "%s"'
                  % (_FFMPEG, path, SR, wav))
        _sr, v = wavfile.read(wav)
        v = v.astype(np.float64) / 32768.0
        if v.ndim > 1:
            v = v.mean(axis=1)
        v = v / (np.max(np.abs(v)) + 1e-12) * vo.get("gain", 0.85)
        i0 = int(vo["at"] * SR)
        i1 = min(n, i0 + len(v))
        mix[i0:i1, 0] += v[:i1 - i0] * 0.92
        mix[i0:i1, 1] += v[:i1 - i0] * 0.92
        print("  voiceover placed: %r at %.1fs (%.2f s)"
              % (vo["line"], vo["at"], len(v) / SR))

    mid = (mix[:, 0] + mix[:, 1]) * 0.5
    side = (mix[:, 0] - mix[:, 1]) * 0.5 * width_env
    L, R = mid + side, mid - side

    # The PICTURE fades to black, but the plant does not stop running just
    # because the camera stopped looking. Sound dips under the end card and
    # is cut at the end, which is what "hold two seconds, cut" means. Fading
    # audio to digital silence under the card makes the file feel finished
    # a beat before the question has landed.
    f = ep["fade"]
    af = spec.get("under_end_card", 0.42)
    card = ep.get("end_card")
    if card:
        master = np.interp(
            t, [0, f["in"][0], f["in"][1], f["out"][0], f["out"][1] + 0.2,
                ep["runtime"] - 0.12, ep["runtime"]],
            [0.0, 0.0, 1.0, 1.0, af, af, 0.0])
    else:
        master = np.interp(
            t, [0, f["in"][0], f["in"][1], f["out"][0], f["out"][1]],
            [0.0, 0.0, 1.0, 1.0, 0.0])
    L, R = L * master, R * master
    peak = max(np.max(np.abs(L)), np.max(np.abs(R))) + 1e-12
    out = np.stack([L, R], axis=1) / peak * 0.70
    wavfile.write(out_path, SR, (out * 32767).astype(np.int16))
    return out_path


if __name__ == "__main__":
    write_stems()
