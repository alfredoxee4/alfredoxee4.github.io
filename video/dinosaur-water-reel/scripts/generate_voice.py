from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import edge_tts
from gtts import gTTS

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build" / "voice"
PUBLIC = ROOT / "public"
TIMINGS_PATH = ROOT / "src" / "generatedTimings.json"
TARGET_SECONDS = 32.8


@dataclass(frozen=True)
class Segment:
    id: str
    text: str
    emphasis: str
    pause: float
    rate: str
    pitch: str


SEGMENTS = [
    Segment("hook", "¿Sabías que el agua que estás tomando ahora mismo… ya la bebió un dinosaurio?", "dinosaurio", 0.30, "+12%", "+2Hz"),
    Segment("same-water", "Esa misma agua que tienes en la mano nunca se crea ni se destruye.", "nunca", 0.15, "+12%", "+0Hz"),
    Segment("four-billion", "Ha estado dando vueltas por la Tierra durante cuatro mil millones de años.", "cuatro mil millones", 0.10, "+13%", "-1Hz"),
    Segment("rain", "Fue lluvia en la época de los dinosaurios…", "lluvia", 0.13, "+7%", "-2Hz"),
    Segment("trex", "pasó por la garganta de un Tiranosaurio Rex…", "Tiranosaurio Rex", 0.13, "+7%", "-2Hz"),
    Segment("oceans", "estuvo en océanos que ya no existen…", "océanos", 0.13, "+5%", "-3Hz"),
    Segment("oil", "y tocó plantas del Jurásico que hoy son petróleo.", "petróleo", 0.22, "+6%", "-3Hz"),
    Segment("history", "Cada vaso de agua que bebes es un pedacito de historia antigua… literalmente estás bebiendo tiempo.", "bebiendo tiempo", 0.20, "+3%", "-4Hz"),
    Segment("different", "Así que la próxima vez que tomes agua… mírala diferente.", "diferente", 0.12, "+8%", "+0Hz"),
    Segment("cta", "Si te voló la cabeza esto, dale like y síguenos, porque aquí vienen cosas aún más fuertes.", "síguenos", 0.0, "+15%", "+2Hz"),
]


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


async def choose_voice() -> str:
    preferred = [
        "es-MX-JorgeNeural",
        "es-US-AlonsoNeural",
        "es-ES-AlvaroNeural",
        "es-AR-TomasNeural",
    ]
    try:
        available = {voice["ShortName"] for voice in await edge_tts.list_voices()}
        for candidate in preferred:
            if candidate in available:
                return candidate
    except Exception as exc:  # noqa: BLE001
        print(f"Could not list Edge voices: {exc}")
    return preferred[0]


async def synthesize_edge(segment: Segment, voice: str, output: Path) -> None:
    communicator = edge_tts.Communicate(
        segment.text,
        voice,
        rate=segment.rate,
        pitch=segment.pitch,
        volume="+0%",
    )
    await communicator.save(str(output))


def synthesize_gtts(segment: Segment, output: Path) -> None:
    gTTS(text=segment.text, lang="es", tld="com.mx", slow=False).save(str(output))


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


async def main() -> None:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)

    voice = await choose_voice()
    print(f"Selected neural voice: {voice}")

    wavs: list[Path] = []
    segment_durations: list[float] = []
    engine = "Microsoft Edge Neural"

    for index, segment in enumerate(SEGMENTS):
        mp3 = BUILD / f"segment-{index:02d}.mp3"
        wav = BUILD / f"segment-{index:02d}.wav"
        try:
            await synthesize_edge(segment, voice, mp3)
        except Exception as exc:  # noqa: BLE001
            print(f"Edge TTS failed on segment {index + 1}: {exc}. Falling back to Google TTS.")
            engine = "Google TTS fallback"
            synthesize_gtts(segment, mp3)
        run(
            "ffmpeg", "-y", "-v", "error", "-i", str(mp3),
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
    print(f"Raw narration: {raw_total:.3f}s; target: {TARGET_SECONDS:.3f}s; speed factor: {speed:.4f}")

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
        "engine": engine,
        "voice": voice,
        "target_seconds": TARGET_SECONDS,
        "raw_seconds": round(raw_total, 3),
        "speed_factor": round(speed, 4),
    }
    (PUBLIC / "voice-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {output} using {engine} / {voice}")


if __name__ == "__main__":
    asyncio.run(main())
