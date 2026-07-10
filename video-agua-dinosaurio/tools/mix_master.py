#!/usr/bin/env python3
"""Mezcla master profesional: voz + música (con envolvente/ducking) + SFX,
soft-limit y normalización de loudness a -14 LUFS (estándar redes sociales)."""
import json
import os
import subprocess
import wave

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
AUDIO = os.path.join(ROOT, "public", "audio")
FF = os.path.join(ROOT, "node_modules", "@ffmpeg-installer", "linux-x64", "ffmpeg")
SR = 44100

TL = json.load(open(os.path.join(AUDIO, "timeline.json")))
TOTAL = TL["total"]
N = int(TOTAL * SR)
scn = {s["id"]: s for s in TL["scenes"]}


def decode(path: str) -> np.ndarray:
    """Decodifica cualquier audio a float32 estéreo 44.1k con ffmpeg."""
    out = subprocess.run(
        [FF, "-i", path, "-f", "f32le", "-acodec", "pcm_f32le",
         "-ac", "2", "-ar", str(SR), "-loglevel", "error", "pipe:1"],
        capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).copy()


def read_wav(path: str) -> np.ndarray:
    w = wave.open(path)
    data = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return data.reshape(-1, w.getnchannels()).astype(np.float32) / 32768


master = np.zeros((N, 2), dtype=np.float32)

# --- Voz ---------------------------------------------------------------
for s in TL["scenes"]:
    v = decode(os.path.join(AUDIO, f"vo_{s['id']}.mp3"))
    i0 = int(s["audioStart"] * SR)
    n = min(len(v), N - i0)
    master[i0:i0 + n] += v[:n] * 1.0

# --- Música con envolvente (ducking en s5, subida en s7) ----------------
music = read_wav(os.path.join(AUDIO, "music.wav"))[:N]
s5, s7 = scn["s5"], scn["s7"]
bp_t = [0, 0.4,
        s5["visualStart"], s5["visualStart"] + 0.47,
        s5["visualEnd"] - 0.47, s5["visualEnd"],
        s7["visualStart"], s7["visualStart"] + 0.4,
        TOTAL - 0.67, TOTAL]
bp_v = [0.0, 0.46, 0.46, 0.32, 0.32, 0.46, 0.46, 0.56, 0.56, 0.34]
env = np.interp(np.arange(N) / SR, bp_t, bp_v).astype(np.float32)
master[:len(music)] += music * env[:len(music), None]

# --- SFX -----------------------------------------------------------------
sfx = read_wav(os.path.join(AUDIO, "sfx.wav"))[:N]
master[:len(sfx)] += sfx * 0.9

# --- Limitador suave ------------------------------------------------------
peak = np.abs(master).max()
print(f"pre-limit peak={peak:.3f}")
if peak > 0.97:
    over = np.abs(master) > 0.85
    master[over] = np.sign(master[over]) * (
        0.85 + np.tanh((np.abs(master[over]) - 0.85) * 2.2) / 2.2 * 0.6)
    print(f"post-limit peak={np.abs(master).max():.3f}")

pre = os.path.join(AUDIO, "master_pre.wav")
pcm = (np.clip(master, -1, 1) * 32767).astype("<i2")
with wave.open(pre, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())

# --- Loudness a -14 LUFS --------------------------------------------------
final = os.path.join(AUDIO, "master.wav")
subprocess.run(
    [FF, "-y", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.2:LRA=11",
     "-ar", str(SR), "-loglevel", "error", final], check=True)
os.remove(pre)

# Medir resultado
probe = subprocess.run(
    [FF, "-i", final, "-af", "loudnorm=I=-14:TP=-1.2:LRA=11:print_format=json",
     "-f", "null", "-"], capture_output=True, text=True).stderr
tail = probe[probe.rfind("{"):probe.rfind("}") + 1]
if tail:
    stats = json.loads(tail)
    print(f"master.wav: LUFS={stats.get('input_i')} TP={stats.get('input_tp')} "
          f"LRA={stats.get('input_lra')}")
print("MASTER OK", round(os.path.getsize(final) / 1e6, 1), "MB")
