#!/usr/bin/env python3
"""Genera la voz IA (edge-tts, es-MX) por segmentos con timestamps por palabra."""
import asyncio
import json
import os
import sys

import edge_tts
import edge_tts.communicate as _etc

# El proxy del entorno intercepta TLS: añadir su CA al contexto de edge-tts
_etc._SSL_CTX.load_verify_locations("/root/.ccr/ca-bundle.crt")

BASE = os.path.join(os.path.dirname(__file__), "..", "public", "audio")
os.makedirs(BASE, exist_ok=True)

VOICE = "es-MX-JorgeNeural"

# (id, texto, rate, pitch) — prosodia por segmento según el guion
SEGMENTS = [
    ("s1", "¿Sabías que el agua que estás tomando ahora mismo... ya la bebió un dinosaurio?", "+12%", "+0Hz"),
    ("s2", "Esa misma agua que tienes en la mano, nunca se crea ni se destruye.", "+12%", "+0Hz"),
    ("s3", "Ha estado dando vueltas por la Tierra durante cuatro mil millones de años.", "+12%", "+0Hz"),
    ("s4", "Fue lluvia en la época de los dinosaurios... pasó por la garganta de un Tiranosaurio Rex... estuvo en océanos que ya no existen... y tocó plantas del Jurásico que hoy son petróleo.", "+15%", "+0Hz"),
    ("s5", "Cada vaso de agua que bebes, es un pedacito de historia antigua... literalmente, estás bebiendo tiempo.", "+2%", "-2Hz"),
    ("s6", "Así que la próxima vez que tomes agua... mírala diferente.", "+10%", "+0Hz"),
    ("s7", "Si te voló la cabeza esto, dale like y síguenos... porque aquí vienen cosas aún más fuertes.", "+17%", "+2Hz"),
]


async def gen(seg_id: str, text: str, rate: str, pitch: str):
    audio_path = os.path.join(BASE, f"vo_{seg_id}.mp3")
    words = []
    comm = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, boundary="WordBoundary")
    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 1e7,          # 100ns -> s
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    return seg_id, words


async def main():
    meta = {}
    for seg_id, text, rate, pitch in SEGMENTS:
        sid, words = await gen(seg_id, text, rate, pitch)
        meta[sid] = {"text": text, "words": words}
        last = words[-1]["end"] if words else 0
        print(f"{sid}: {len(words)} palabras, última acaba en {last:.2f}s")
    with open(os.path.join(BASE, "words.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("OK")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
