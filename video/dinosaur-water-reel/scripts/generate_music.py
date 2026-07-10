from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "music.wav"
SAMPLE_RATE = 48_000
DURATION = 33.0
N = int(SAMPLE_RATE * DURATION)
T = np.arange(N, dtype=np.float64) / SAMPLE_RATE
RNG = np.random.default_rng(5606)


def midi(note: float) -> float:
    return 440.0 * 2 ** ((note - 69.0) / 12.0)


def soft_sine(freq: float, phase: float = 0.0) -> np.ndarray:
    base = np.sin(2 * np.pi * freq * T + phase)
    second = 0.22 * np.sin(2 * np.pi * freq * 2 * T + phase * 1.17)
    third = 0.08 * np.sin(2 * np.pi * freq * 3 * T + phase * 0.73)
    return (base + second + third) / 1.3


def segment_envelope(start: float, end: float, attack: float = 1.2, release: float = 1.4) -> np.ndarray:
    env = np.zeros(N, dtype=np.float64)
    mask = (T >= start) & (T < end)
    local = T[mask] - start
    duration = end - start
    fade_in = np.clip(local / max(attack, 0.001), 0, 1)
    fade_out = np.clip((duration - local) / max(release, 0.001), 0, 1)
    env[mask] = np.minimum(fade_in, fade_out)
    return env


def add_swell(track: np.ndarray, center: float, width: float, freq: float, gain: float) -> None:
    envelope = np.exp(-0.5 * ((T - center) / width) ** 2)
    track += soft_sine(freq, phase=center) * envelope * gain


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    music = np.zeros(N, dtype=np.float64)

    # Four slow cinematic chord beds: A minor, F, C, G.
    chords = [
        (0.0, 8.25, [45, 52, 57, 60]),
        (8.25, 16.5, [41, 48, 53, 57]),
        (16.5, 24.75, [48, 55, 60, 64]),
        (24.75, 33.0, [43, 50, 55, 59]),
    ]
    for chord_index, (start, end, notes) in enumerate(chords):
        env = segment_envelope(start, end, attack=1.35, release=1.5)
        for note_index, note in enumerate(notes):
            detune = (note_index - 1.5) * 0.018
            signal = soft_sine(midi(note) * (1 + detune / 100), phase=chord_index * 0.71 + note_index)
            music += signal * env * (0.052 / (1 + note_index * 0.18))

    # Quiet heartbeat/pulse to keep the Reel moving without fighting narration.
    bpm = 82
    beat = 60.0 / bpm
    for beat_index, start in enumerate(np.arange(0.25, DURATION, beat)):
        length = 0.42
        mask = (T >= start) & (T < start + length)
        local = T[mask] - start
        pulse = np.sin(2 * np.pi * (52 + 8 * np.exp(-local * 10)) * local)
        pulse *= np.exp(-local * 8.5)
        accent = 1.0 if beat_index % 4 == 0 else 0.55
        music[mask] += pulse * 0.07 * accent

    # Water-like glass harmonics.
    sparkle_times = [2.8, 6.6, 10.7, 14.8, 18.2, 22.9, 26.1, 29.4, 31.2]
    sparkle_notes = [84, 88, 81, 86, 91, 83, 88, 93, 86]
    for when, note in zip(sparkle_times, sparkle_notes):
        length = 1.45
        mask = (T >= when) & (T < when + length)
        local = T[mask] - when
        f = midi(note)
        chime = np.sin(2 * np.pi * f * local) + 0.38 * np.sin(2 * np.pi * f * 2.01 * local)
        chime *= np.exp(-local * 3.2)
        music[mask] += chime * 0.032

    # Cinematic swells at visual transitions.
    for center, freq, gain in [(4.0, 74, 0.04), (10.5, 62, 0.05), (16.8, 55, 0.055), (23.4, 82, 0.05), (28.3, 98, 0.055), (31.0, 124, 0.06)]:
        add_swell(music, center, 0.78, freq, gain)

    # A very soft rain/air bed, shaped to feel organic rather than static.
    noise = RNG.normal(0, 1, N)
    smooth = np.zeros_like(noise)
    alpha = 0.012
    for i in range(1, N):
        smooth[i] = smooth[i - 1] + alpha * (noise[i] - smooth[i - 1])
    air_env = 0.45 + 0.25 * np.sin(2 * np.pi * T / 9.0) ** 2
    music += smooth * air_env * 0.018

    # Fade in/out and gentle mastering.
    master = np.ones(N, dtype=np.float64)
    master *= np.clip(T / 1.1, 0, 1)
    master *= np.clip((DURATION - T) / 1.35, 0, 1)
    music *= master
    music = np.tanh(music * 1.65)
    peak = max(float(np.max(np.abs(music))), 1e-9)
    music = music / peak * 0.82

    # Slight stereo width using delayed/phase-shifted right channel.
    delay = int(0.013 * SAMPLE_RATE)
    right = np.roll(music, delay) * 0.93 + soft_sine(220, phase=1.3) * 0.0025 * master
    left = music
    stereo = np.stack([left, right], axis=1)
    pcm = np.int16(np.clip(stereo, -1, 1) * 32767)

    with wave.open(str(OUTPUT), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())

    print(f"Created original cinematic score: {OUTPUT} ({DURATION:.1f}s)")


if __name__ == "__main__":
    main()
