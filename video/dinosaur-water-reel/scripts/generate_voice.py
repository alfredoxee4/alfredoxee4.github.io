from __future__ import annotations

import json
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

from piper import PiperVoice, SynthesisConfig
from piper.download_voices import download_voice

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build" / "voice"
PUBLIC = ROOT / "public"
TIMINGS_PATH = ROOT / "src" / "generatedTimings.json"
MODEL_DIR = ROOT / ".build" / "piper-model"
MODEL_NAME = "es_MX-ald-medium"
MODEL_PATH = MODEL_DIR / f"{MODEL_NAME}.onnx"
CONFIG_PATH = MODEL_DIR / f"{MODEL_NAME}.onnx.json"
TARGET_SECONDS = 32.8


@dataclass(frozen=True)
class Segment:
    id: str
    text: str
    emphasis: str
    pause: float
    length_scale: float
    noise_scale: float
    noise_w_scale: float


SEGMENTS = [
    Segment("hook", "¿Sabías que el agua que estás tomando ahora mismo… ya la bebió un dinosaurio?", "dinosaurio", 0.30, 0.89, 0.58, 0.72),
    Segment("same-water", "Esa misma agua que tienes en la mano nunca se crea ni se destruye.", "nunca", 0.15, 0.91, 0.55, 0.70),
    Segment("four-billion", "Ha estado dando vueltas por la Tierra durante cuatro mil millones de años.", "cuatro mil millones", 0.10, 0.90, 0.54, 0.69),
    Segment("rain", "Fue lluvia en la época de los dinosaurios…", "lluvia", 0.13, 0.97, 0.60, 0.76),
    Segment("trex", "pasó por la garganta de un Tiranosaurio Rex…", "Tiranosaurio Rex", 0.13, 0.98, 0.62, 0.78),
    Segment("oceans", "estuvo en océanos que ya no existen…", "océanos", 0.13, 1.00, 0.60, 0.75),
    Segment("oil", "y tocó plantas del Jurásico que hoy son petróleo.", "petróleo", 0.22, 0.97, 0.58, 0.73),
    Segment("history", "Cada vaso de agua que bebes es un pedacito de historia antigua… literalmente estás bebiendo tiempo.", "bebiendo tiempo", 0.20, 1.03, 0.53, 0.67),
    Segment("different", "Así que la próxima vez que tomes agua… mírala diferente.", "diferente", 0.12, 0.94, 0.57, 0.72),
    Segment("cta", "Si te voló la cabeza esto, dale like y síguenos, porque aquí vienen cosas aún más fuertes.", "síguenos", 0.0, 0.87, 0.60, 0.74),
]


def run(*args: str) -> None:
    print("$", " ".join(args), flush=True)
    subprocess.run(args, check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def ensure_model() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and CONFIG_PATH.exists() and MODEL_PATH.stat().st_size > 10_000_000:
        print(f"Using cached Piper voice: {MODEL_PATH}", flush=True)
        return

    print(f"Downloading Piper voice with official downloader: {MODEL_NAME}", flush=True)
    download_voice(MODEL_NAME, MODEL_DIR, force_redownload=True)
    if not MODEL_PATH.exists() or MODEL_PATH.stat().st_size < 10_000_000:
        raise RuntimeError(f"Piper model download is incomplete: {MODEL_PATH}")
    if not CONFIG_PATH.exists() or CONFIG_PATH.stat().st_size < 1000:
        raise RuntimeError(f"Piper config download is incomplete: {CONFIG_PATH}")
    print(f"Model ready: {MODEL_PATH.stat().st_size / 1024 / 1024:.1f} MB", flush=True)


def atempo_chain(speed: float) -> str:
    filters: list[str] = []
    remaining = speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.7f}")
    return ",".join(filters)


def synthesize_segment(voice: PiperVoice, segment: Segment, raw_wav: Path) -> None:
    config = SynthesisConfig(
        length_scale=segment.length_scale,
        noise_scale=segment.noise_scale,
        noise_w_scale=segment.noise_w_scale,
        normalize_audio=True,
        volume=1.0,
    )
    with wave.open(str(raw_wav), "wb") as wav_file:
        voice.synthesize_wav(segment.text, wav_file, syn_config=config)
    if not raw_wav.exists() or raw_wav.stat().st_size < 1000:
        raise RuntimeError(f"Piper produced an invalid WAV for segment {segment.id}")


def main() -> None:
    print(f"Python: {sys.version}", flush=True)
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)

    ensure_model()
    print("Loading Piper model into ONNX Runtime…", flush=True)
    voice = PiperVoice.load(MODEL_PATH, config_path=CONFIG_PATH, use_cuda=False)
    print("Piper model loaded successfully.", flush=True)

    wavs: list[Path] = []
    segment_durations: list[float] = []

    for index, segment in enumerate(SEGMENTS):
        print(f"Synthesizing {index + 1}/{len(SEGMENTS)}: {segment.id}", flush=True)
        raw_wav = BUILD / f"segment-{index:02d}-raw.wav"
        wav = BUILD / f"segment-{index:02d}.wav"
        synthesize_segment(voice, segment, raw_wav)
        run(
            "ffmpeg", "-y", "-v", "error", "-i", str(raw_wav),
            "-af", "highpass=f=65,lowpass=f=15000,acompressor=threshold=-19dB:ratio=2.0:attack=14:release=150,equalizer=f=165:t=q:w=0.9:g=1.4,equalizer=f=3200:t=q:w=1.1:g=1.2",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(wav),
        )
        seg_duration = duration(wav)
        wavs.append(wav)
        segment_durations.append(seg_duration)

        if segment.pause > 0:
            silence = BUILD / f"silence-{index:02d}.wav"
            run(
                "ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{segment.pause:.3f}",
                "-c:a", "pcm_s16le", str(silence),
            )
            wavs.append(silence)

    concat_file = BUILD / "concat.txt"
    concat_file.write_text("\n".join(f"file '{path.as_posix()}'" for path in wavs), encoding="utf-8")
    merged = BUILD / "merged.wav"
    run(
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat_file), "-c:a", "pcm_s16le", str(merged),
    )

    raw_total = duration(merged)
    speed = raw_total / TARGET_SECONDS
    print(f"Narration before final timing: {raw_total:.3f}s; speed factor: {speed:.4f}", flush=True)
    output = PUBLIC / "narration.mp3"
    run(
        "ffmpeg", "-y", "-v", "error", "-i", str(merged),
        "-filter:a", f"{atempo_chain(speed)},loudnorm=I=-16:TP=-1.5:LRA=8",
        "-ar", "48000", "-ac", "2", "-b:a", "192k", str(output),
    )

    scale = TARGET_SECONDS / raw_total
    timeline: list[dict[str, object]] = []
    cursor = 0.0
    for segment, seg_duration in zip(SEGMENTS, segment_durations):
        start = cursor * scale
        end = (cursor + seg_duration) * scale
        timeline.append({
            "id": segment.id,
            "text": segment.text,
            "start": round(start, 4),
            "end": round(end, 4),
            "emphasis": segment.emphasis,
        })
        cursor += seg_duration + segment.pause

    TIMINGS_PATH.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "engine": "Piper local neural TTS via Python API",
        "voice": MODEL_NAME,
        "target_seconds": TARGET_SECONDS,
        "raw_seconds": round(raw_total, 3),
        "speed_factor": round(speed, 4),
        "model_mb": round(MODEL_PATH.stat().st_size / 1024 / 1024, 1),
    }
    (PUBLIC / "voice-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {output} using {metadata['engine']} / {MODEL_NAME}", flush=True)


if __name__ == "__main__":
    main()
