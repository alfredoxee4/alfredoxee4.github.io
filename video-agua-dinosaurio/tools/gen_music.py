#!/usr/bin/env python3
"""Sintetiza la banda sonora (music.wav) y los efectos (sfx.wav) desde timeline.json.

Todo procedural con numpy: pads con acordes por escena, sub-pulso, ruido oceánico,
shimmer, y SFX (drop, whoosh STFT, braam, riser, pop, latido). Sin samples externos.
"""
import json
import os
import wave

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
AUDIO = os.path.join(ROOT, "public", "audio")
SR = 44100

TL = json.load(open(os.path.join(AUDIO, "timeline.json")))
TOTAL = TL["total"]
N = int(TOTAL * SR)
scn = {s["id"]: s for s in TL["scenes"]}

NOTE = {"C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.0, "A2": 110.0,
        "Bb2": 116.54, "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61,
        "G3": 196.0, "A3": 220.0, "Bb3": 233.08, "C4": 261.63, "D4": 293.66,
        "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0}


def t_axis(n):
    return np.arange(n) / SR


def sine(f, n, phase=0.0):
    return np.sin(2 * np.pi * f * t_axis(n) + phase)


def saw(f, n):
    out = np.zeros(n)
    k = 1
    while k * f < 6500 and k <= 24:
        out += np.sin(2 * np.pi * k * f * t_axis(n)) / k
        k += 1
    return out * 0.6


def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    na, nr = min(na, n), min(nr, n)
    if na > 0:
        e[:na] = np.linspace(0, 1, na) ** 1.5
    if nr > 0:
        e[-nr:] = np.minimum(e[-nr:], np.linspace(1, 0, nr) ** 1.2)
    return e


def lowpass_fft(x, cutoff, soft=1.6):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = 1 / (1 + (f / max(cutoff, 20.0)) ** (2 * soft))
    return np.fft.irfft(X * mask, len(x))


def highpass_fft(x, cutoff, soft=1.6):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    mask = 1 - 1 / (1 + (f / max(cutoff, 20.0)) ** (2 * soft))
    return np.fft.irfft(X * mask, len(x))


def stft_sweep_noise(dur, f_curve, sigma_oct=0.7, seed=1):
    """Ruido con banda móvil (whoosh/riser). f_curve: función 0..1 -> Hz."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    win, hop = 1024, 256
    w = np.hanning(win)
    out = np.zeros(n + win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    pos = 0
    while pos + win <= n:
        prog = pos / max(n - win, 1)
        fc = f_curve(prog)
        X = np.fft.rfft(x[pos:pos + win] * w)
        lf = np.log2(np.maximum(freqs, 1))
        mask = np.exp(-0.5 * ((lf - np.log2(fc)) / sigma_oct) ** 2)
        out[pos:pos + win] += np.fft.irfft(X * mask, win) * w
        pos += hop
    out = out[:n]
    m = np.max(np.abs(out)) or 1
    return out / m


def add(buses, ch, start_s, sig, gain=1.0, pan=0.0):
    i0 = int(start_s * SR)
    if i0 >= N or i0 < 0:
        i0 = max(0, min(i0, N - 1))
    n = min(len(sig), N - i0)
    if n <= 0:
        return
    gl = gain * min(1.0, 1.0 - pan)
    gr = gain * min(1.0, 1.0 + pan)
    buses[ch][0][i0:i0 + n] += sig[:n] * gl
    buses[ch][1][i0:i0 + n] += sig[:n] * gr


# ============================== MÚSICA =======================================
music = [np.zeros(N), np.zeros(N)]
BUS = {"m": music}

CHORDS = []  # (start, end, root, pad_notes, energy 0..1)
s = scn
CHORDS.append((s["s1"]["visualStart"], s["s2"]["visualStart"], "D2", ["D3", "F3", "A3"], 0.5))
CHORDS.append((s["s2"]["visualStart"], s["s3"]["visualStart"], "Bb2", ["Bb2", "D3", "F3"], 0.55))
CHORDS.append((s["s3"]["visualStart"], s["s4"]["visualStart"], "F2", ["F3", "A3", "C4"], 0.65))
c4 = s["s4"]["cuts"]
sub_chords = [("G2", ["G3", "Bb3", "D4"]), ("D2", ["D3", "F3", "A3"]),
              ("Bb2", ["Bb3", "D4", "F4"]), ("C3", ["C4", "E4", "G4"])]
for cut, (root, notes) in zip(c4, sub_chords):
    CHORDS.append((cut["start"], cut["end"], root, notes, 0.75))
CHORDS.append((s["s5"]["visualStart"], s["s6"]["visualStart"], "D2", ["D3", "F3", "E4"], 0.3))
CHORDS.append((s["s6"]["visualStart"], s["s7"]["visualStart"], "Bb2", ["F3", "Bb3", "D4"], 0.6))
mid7 = (s["s7"]["visualStart"] + TOTAL) / 2
CHORDS.append((s["s7"]["visualStart"], mid7, "F2", ["F3", "A3", "C4"], 0.9))
CHORDS.append((mid7, TOTAL, "C3", ["C4", "E4", "G4"], 0.95))

for (t0, t1, root, notes, energy) in CHORDS:
    dur = t1 - t0 + 1.1  # colita para el crossfade
    n = int(dur * SR)
    seg = np.zeros(n)
    for note in notes:
        f = NOTE[note]
        for det, g in ((-0.004, 0.5), (0.0, 1.0), (0.004, 0.5)):
            fd = f * (1 + det)
            seg += g * (np.sin(2 * np.pi * fd * t_axis(n))
                        + 0.4 * np.sin(2 * np.pi * 2 * fd * t_axis(n))
                        + 0.13 * np.sin(2 * np.pi * 3 * fd * t_axis(n)))
    seg = lowpass_fft(seg, 1200 + 800 * energy)
    seg *= env_ar(n, 0.9, 1.1) * (0.035 + 0.03 * energy)
    add(BUS, "m", t0, np.tanh(seg * 1.3), 1.0, pan=-0.06)
    add(BUS, "m", t0 + 0.012, np.tanh(seg * 1.3), 1.0, pan=0.06)

# Sub-pulso rítmico (negras a 72bpm)
PULSE_GAIN = {"s1": 0.5, "s2": 0.5, "s3": 0.55, "s4": 0.72, "s5": 0.26, "s6": 0.5, "s7": 0.9}
step = 60 / 72
thump_n = int(0.42 * SR)
for sid, g in PULSE_GAIN.items():
    t0, t1 = scn[sid]["visualStart"], scn[sid]["visualEnd"]
    root = next(c for c in CHORDS if c[0] <= t0 + 0.01 < c[1])[2]
    f = NOTE[root]
    f = f / 2 if f > 100 else f
    t = t0
    while t < t1 - 0.2:
        envg = np.exp(-0.5 * ((t_axis(thump_n) - 0.05) / 0.075) ** 2)
        add(BUS, "m", t, sine(f, thump_n) * envg, 0.16 * g)
        t += step

# Ruido oceánico (brown noise + LFO lento)
rng = np.random.default_rng(7)
ocean = np.cumsum(rng.standard_normal(N))
ocean = ocean / (np.max(np.abs(ocean)) or 1)
ocean = lowpass_fft(ocean, 450)
lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t_axis(N) - 1.2)
oc_gain = np.interp(t_axis(N),
                    [0, s["s1"]["visualEnd"], s["s5"]["visualStart"], s["s5"]["visualEnd"], TOTAL],
                    [0.09, 0.05, 0.035, 0.06, 0.07])
music[0] += ocean * lfo * oc_gain
music[1] += np.roll(ocean, 2205) * (1 - 0.6 * lfo) * oc_gain

# Shimmer (arpegio pentatónico alto, escenas de asombro)
SHIMMER = {"s3": ["A4", "C4", "F4"], "s5": ["D4", "E4", "A4"],
           "s6": ["F4", "D4", "Bb3"], "s7": ["C4", "E4", "G4", "A4"]}
rng2 = np.random.default_rng(21)
for sid, notes in SHIMMER.items():
    t0, t1 = scn[sid]["visualStart"], scn[sid]["visualEnd"]
    t = t0 + 0.6
    k = 0
    while t < t1 - 1.0:
        f = NOTE[rng2.choice(notes)] * 2
        n = int(1.3 * SR)
        sig = sine(f, n) * np.exp(-t_axis(n) * 3.2) * (t_axis(n) * 60).clip(0, 1)
        pan = 0.35 if k % 2 == 0 else -0.35
        add(BUS, "m", t, sig, 0.05, pan)
        add(BUS, "m", t + 0.31, sig, 0.022, -pan)
        t += float(rng2.uniform(1.1, 1.9))
        k += 1

# Latido en s5 (asombro)
t = scn["s5"]["visualStart"] + 0.5
hb_n = int(0.3 * SR)
while t < scn["s5"]["visualEnd"] - 1.0:
    for off, g in ((0.0, 1.0), (0.29, 0.75)):
        envg = np.exp(-0.5 * ((t_axis(hb_n) - 0.04) / 0.05) ** 2)
        add(BUS, "m", t + off, sine(52, hb_n) * envg, 0.14 * g)
    t += 0.88

# Fade maestro inicial/final
fade_in = int(0.4 * SR)
fade_out = int(1.0 * SR)
for ch in music:
    ch[:fade_in] *= np.linspace(0, 1, fade_in)
    ch[-fade_out:] *= np.linspace(1, 0, fade_out) ** 1.3

peak = max(np.max(np.abs(music[0])), np.max(np.abs(music[1]))) or 1
music = [ch / peak * 0.72 for ch in music]

# ============================== SFX ==========================================
sfx = [np.zeros(N), np.zeros(N)]
BUS2 = {"x": sfx}


def ev_drop(t):
    n = int(0.9 * SR)
    fr = 850 * np.exp(-t_axis(n) * 26) + 240
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t_axis(n) * 7)
    splash = lowpass_fft(np.random.default_rng(3).standard_normal(n), 2400)
    splash *= np.exp(-t_axis(n) * 10) * 0.4
    add(BUS2, "x", t, body + splash, 0.55)


def ev_whoosh(t, seed):
    dur = 0.6
    sig = stft_sweep_noise(dur, lambda p: 260 + 2600 * np.sin(np.pi * min(p * 1.15, 1.0)) ** 2,
                           0.8, seed)
    envg = np.sin(np.pi * np.linspace(0, 1, len(sig))) ** 1.6
    add(BUS2, "x", t - 0.36, sig * envg, 0.42, pan=(0.25 if seed % 2 else -0.25))


def ev_braam(t, soft=False):
    dur = 1.5 if soft else 1.9
    n = int(dur * SR)
    seg = np.zeros(n)
    for f0 in (55.0, 110.0):
        for det in (-0.015, 0.0, 0.015):
            seg += saw(f0 * (1 + det), n)
    seg = lowpass_fft(seg, 620 if soft else 900)
    seg *= np.exp(-t_axis(n) * (3.4 if soft else 2.4)) * (t_axis(n) * 220).clip(0, 1)
    thump = lowpass_fft(np.random.default_rng(9).standard_normal(n), 300)
    thump *= np.exp(-t_axis(n) * 24)
    sub = sine(37, n) * np.exp(-t_axis(n) * 3.0)
    sig = np.tanh((seg * 0.8 + thump * 0.7 + sub * 0.9) * 1.6)
    add(BUS2, "x", t - 0.02, sig, 0.34 if soft else 0.5)


def ev_riser(t, pre, seed=5):
    sig = stft_sweep_noise(pre, lambda p: 300 * (24 ** p), 0.75, seed)
    envg = np.linspace(0, 1, len(sig)) ** 2.2
    n = len(sig)
    tone = np.sin(2 * np.pi * np.cumsum(180 * (4 ** np.linspace(0, 1, n))) / SR)
    add(BUS2, "x", t - pre, (sig * 0.8 + tone * 0.25) * envg, 0.32)


def ev_pop(t, seed):
    n = int(0.16 * SR)
    fr = 620 + (930 - 620) * (t_axis(n) * 18).clip(0, 1)
    body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t_axis(n) * 22)
    click = highpass_fft(np.random.default_rng(seed).standard_normal(n), 3000)
    click *= np.exp(-t_axis(n) * 70) * 0.5
    add(BUS2, "x", t, body + click, 0.5, pan=(0.2 if seed % 2 else -0.2))


wseed = 11
for ev in TL["sfx"]:
    ty, t = ev["type"], ev["t"]
    if ty == "drop":
        ev_drop(t)
    elif ty == "whoosh":
        ev_whoosh(t, wseed); wseed += 1
    elif ty == "braam":
        ev_braam(t)
    elif ty == "braamsoft":
        ev_braam(t, soft=True)
    elif ty == "riser":
        ev_riser(t, ev.get("pre", 1.2), wseed); wseed += 1
    elif ty == "pop":
        ev_pop(t, wseed); wseed += 1

peak = max(np.max(np.abs(sfx[0])), np.max(np.abs(sfx[1]))) or 1
if peak > 0.95:
    sfx = [ch / peak * 0.95 for ch in sfx]


def write_wav(path, chans):
    data = np.stack(chans, axis=1)
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"{os.path.basename(path)}: {len(chans[0])/SR:.2f}s "
          f"peak={np.max(np.abs(data)):.2f}")


write_wav(os.path.join(AUDIO, "music.wav"), music)
write_wav(os.path.join(AUDIO, "sfx.wav"), sfx)
