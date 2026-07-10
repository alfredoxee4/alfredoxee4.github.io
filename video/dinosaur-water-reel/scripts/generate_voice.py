from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build" / "voice"
PUBLIC = ROOT / "public"
TIMINGS_PATH = ROOT / "src" / "generatedTimings.json"
MODEL_DIR = ROOT / ".build" / "piper-model"
MODEL_NAME = "es_MX-ald-medium"
MODEL_PATH = MODEL_DIR / f"{MODEL_NAME}.onnx"
CONFIG_PATH = MODEL_DIR / f"{MODEL_NAME}.onnx.json"
MODEL_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium"
TARGET_SECONDS = 32.8


@dataclass(frozen=True)
class Segment:
    id: str
    text: str
    emphasis: str
    pause: float


SEGMENTS = [
    Segment("hook", "¿Sabías que el agua que estás tomando ahora mismo… ya la bebió un dinosaurio?", "dinosaurio", 0.30),
    Segment("same-water", "Esa misma agua que tienes en la mano nunca se crea ni se destruye.", "nunca", 0.15),
    Segment("four-billion", "Ha estado dando vueltas por la Tierra durante cuatro mil millones de años.", "cuatro mil millones", 0.10),
    Segment("rain", "Fue lluvia en la época de los dinosaurios…", "lluvia", 0.13),
    Segment("trex", "pasó por la garganta de un Tiranosaurio Rex…", "Tiranosaurio Rex", 0.13),
    Segment("oceans", "estuvo en océanos que ya no existen…", "océanos", 0.13),
    Segment("oil", "y tocó plantas del Jurásico que hoy son petróleo.", "petróleo", 0.22),
    Segment("history", "Cada vaso de agua que bebes es un pedacito de historia antigua… literalmente estás bebiendo tiempo.", "bebiendo tiempo", 0.20),
    Segment("different", "Así que la próxima vez que tomes agua… mírala diferente.", "diferente", 0.12),
    Segment("cta", "Si te voló la cabeza esto, dale like y síguenos, porque aquí vienen cosas aún más fuertes.", "síguenos", 0.0),
]


def run(*args: str, input_text: str | None = None) -> None:
    subprocess.run(args, check=True, input=input_text, text=input_text is not None)


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


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 1000:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 GitHub-Actions-Piper"})
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def ensure_model() -> None:
    download(f"{MODEL_BASE}/{MODEL_NAME}.onnx", MODEL_PATH)
    download(f"{MODEL_BASE}/{MODEL_NAME}.onnx.json", CONFIG_PATH)


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


def main() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    ensure_model()

    wavs: list[Path] = []
    segment_durations: list[float] = []

    for index, segment in enumerate(SEGMENTS):
        raw_wav = BUILD / f"segment-{index:02d}-raw.wav"
        wav = BUILD / f"segment-{index:02d}.wav"
        run(
            "piper",
            "--model", str(MODEL_PATH),
            "--config", str(CONFIG_PATH),
            "--output_file", str(raw_wav),
            input_text=segment.text,
        )
        run(
            "ffmpeg", "-y", "-v", "error", "-i", str(raw_wav),
            "-af", "highpass=f=70,lowpass=f=14500,acompressor=threshold=-18dB:ratio=2.2:attack=12:release=140",
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
        timeline.append(
            {
                "id": segment.id,
                "text": segment.text,
                "start": round(start, 4),
                "end": round(end, 4),
                "emphasis": segment.emphasis,
            }
        )
        cursor += seg_duration + segment.pause

    TIMINGS_PATH.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "engine": "Piper local neural TTS",
        "voice": MODEL_NAME,
        "target_seconds": TARGET_SECONDS,
        "raw_seconds": round(raw_total, 3),
        "speed_factor": round(speed, 4),
    }
    (PUBLIC / "voice-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {output} using local Piper voice {MODEL_NAME}")


if __name__ == "__main__":
    main()
