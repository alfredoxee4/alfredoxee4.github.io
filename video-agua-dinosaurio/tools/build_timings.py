#!/usr/bin/env python3
"""Construye la línea de tiempo del video: escenas, karaoke por palabra, subcortes y SFX.

Lee public/audio/words.json + duraciones reales de los MP3 y emite:
  - src/timings.ts        (datos tipados para la composición Remotion)
  - public/audio/timeline.json (para el sintetizador de música/SFX)
"""
import json
import os

from mutagen.mp3 import MP3

ROOT = os.path.join(os.path.dirname(__file__), "..")
AUDIO = os.path.join(ROOT, "public", "audio")
FPS = 30

def probe(path: str) -> float:
    return MP3(path).info.length

words = json.load(open(os.path.join(AUDIO, "words.json")))

# --- Definición editorial de subtítulos -------------------------------------
# Cada grupo: lista de tokens (texto_mostrado, índice_palabra, flags)
# flags: a=acento agua (aqua), g=acento dorado, m=mega (grande), e=emoji pegado
G = {
 "s1": [
   [("¿SABÍAS", 0, ""), ("QUE", 1, "")],
   [("EL", 2, ""), ("AGUA", 3, "a")],
   [("QUE", 4, ""), ("ESTÁS", 5, ""), ("TOMANDO", 6, "")],
   [("AHORA", 7, ""), ("MISMO...", 8, "")],
   [("YA", 9, ""), ("LA", 10, ""), ("BEBIÓ", 11, "a")],
   [("UN", 12, "m"), ("DINOSAURIO", 13, "gm"), ("🦖", 13, "me")],
 ],
 "s2": [
   [("ESA", 0, ""), ("MISMA", 1, ""), ("AGUA", 2, "a")],
   [("QUE", 3, ""), ("TIENES", 4, ""), ("EN", 5, ""), ("LA", 6, ""), ("MANO", 7, "")],
   [("NUNCA", 8, "g"), ("SE", 9, ""), ("CREA", 10, "")],
   [("NI", 11, ""), ("SE", 12, ""), ("DESTRUYE", 13, "g")],
 ],
 "s3": [
   [("HA", 0, ""), ("ESTADO", 1, ""), ("DANDO", 2, ""), ("VUELTAS", 3, "")],
   [("POR", 4, ""), ("LA", 5, ""), ("TIERRA", 6, "a"), ("🌍", 6, "e")],
   [("DURANTE", 7, "")],
   # el contador gigante toma el relevo visual aquí
   [("COUNTER", 8, "counter"), ("DE", 11, ""), ("AÑOS", 12, "g")],
 ],
 "s4": [
   [("FUE", 0, ""), ("LLUVIA", 1, "a"), ("🌧️", 1, "e")],
   [("EN", 2, ""), ("LA", 3, ""), ("ÉPOCA", 4, "")],
   [("DE", 5, ""), ("LOS", 6, ""), ("DINOSAURIOS", 7, "g")],
   [("PASÓ", 8, ""), ("POR", 9, ""), ("LA", 10, ""), ("GARGANTA", 11, "a")],
   [("DE", 12, ""), ("UN", 13, "")],
   [("TIRANOSAURIO", 14, "gm"), ("REX", 15, "gm"), ("🦖", 15, "me")],
   [("ESTUVO", 16, ""), ("EN", 17, ""), ("OCÉANOS", 18, "a"), ("🌊", 18, "e")],
   [("QUE", 19, ""), ("YA", 20, ""), ("NO", 21, "g"), ("EXISTEN", 22, "g")],
   [("Y", 23, ""), ("TOCÓ", 24, ""), ("PLANTAS", 25, "")],
   [("DEL", 26, ""), ("JURÁSICO", 27, "g"), ("🌿", 27, "e")],
   [("QUE", 28, ""), ("HOY", 29, ""), ("SON", 30, "")],
   [("PETRÓLEO", 31, "gm"), ("🛢️", 31, "me")],
 ],
 "s5": [
   [("CADA", 0, ""), ("VASO", 1, ""), ("DE", 2, ""), ("AGUA", 3, "a")],
   [("QUE", 4, ""), ("BEBES", 5, "")],
   [("ES", 6, ""), ("UN", 7, ""), ("PEDACITO", 8, "")],
   [("DE", 9, ""), ("HISTORIA", 10, "g"), ("ANTIGUA", 11, "g")],
   [("LITERALMENTE...", 12, "")],
   [("ESTÁS", 13, "m"), ("BEBIENDO", 14, "m")],
   [("TIEMPO", 15, "gm"), ("⏳", 15, "me")],
 ],
 "s6": [
   [("ASÍ", 0, ""), ("QUE", 1, ""), ("LA", 2, ""), ("PRÓXIMA", 3, ""), ("VEZ", 4, "")],
   [("QUE", 5, ""), ("TOMES", 6, ""), ("AGUA...", 7, "a")],
   [("MÍRALA", 8, "am"), ("DIFERENTE", 9, "am"), ("✨", 9, "me")],
 ],
 "s7": [
   [("SI", 0, ""), ("TE", 1, ""), ("VOLÓ", 2, ""), ("LA", 3, ""), ("CABEZA", 4, "g"), ("🤯", 5, "e")],
   [("DALE", 6, "m"), ("LIKE", 7, "am"), ("❤️", 7, "me")],
   [("Y", 8, "m"), ("SÍGUENOS", 9, "am")],
   [("PORQUE", 10, ""), ("AQUÍ", 11, ""), ("VIENEN", 12, "")],
   [("COSAS", 13, ""), ("AÚN", 14, ""), ("MÁS", 15, "g"), ("FUERTES", 16, "g"), ("🚀", 16, "e")],
 ],
}

IMAGES = {"s1": ["img1.jpg"], "s2": ["img2.jpg"], "s3": ["img3.jpg"],
          "s4": ["img4.jpg", "img5.jpg", "img6.jpg", "img7.jpg"],
          "s5": ["img8.jpg"], "s6": ["img9.jpg"], "s7": []}
S4_CUT_WORDS = [8, 16, 23]          # pasó / estuvo / y
GAP_AFTER = {"s1": 0.32, "s2": 0.28, "s3": 0.34, "s4": 0.34, "s5": 0.5, "s6": 0.36}
LEAD_IN = 0.4                        # silencio antes de la primera frase
VISUAL_LEAD = 0.20                   # el corte visual entra un pelín antes de la voz
END_HOLD = 1.7                       # aguante final tras la última frase

order = ["s1", "s2", "s3", "s4", "s5", "s6", "s7"]
durs = {sid: probe(os.path.join(AUDIO, f"vo_{sid}.mp3")) for sid in order}

scenes = []
t_audio = LEAD_IN
sfx = [{"type": "drop", "t": 0.12}]
for i, sid in enumerate(order):
    a_start = t_audio
    # fin efectivo: última palabra + colita (los mp3 traen ~0.7s de silencio final)
    last_word_end = words[sid]["words"][-1]["end"]
    a_end = a_start + min(durs[sid], last_word_end + 0.22)
    v_start = 0.0 if i == 0 else a_start - VISUAL_LEAD
    ws = [{"t": round(a_start + w["start"], 3), "e": round(a_start + w["end"], 3)}
          for w in words[sid]["words"]]

    groups = []
    for gi, g in enumerate(G[sid]):
        toks = []
        for (txt, wi, fl) in g:
            toks.append({"t": txt, "s": ws[wi]["t"], "e": ws[wi]["e"], "f": fl})
        g_start = min(tok["s"] for tok in toks)
        g_end = (min(tok["s"] for tok in [
            {"s": ws[G[sid][gi + 1][0][1]]["t"]}]) if gi + 1 < len(G[sid]) else a_end + 0.3)
        groups.append({"start": round(g_start, 3), "end": round(g_end, 3), "tokens": toks})

    cuts = []
    if sid == "s4":
        bounds = [v_start] + [ws[w]["t"] - 0.1 for w in S4_CUT_WORDS]
        for k, img in enumerate(IMAGES[sid]):
            c_start = bounds[k]
            c_end = bounds[k + 1] if k + 1 < len(bounds) else None
            cuts.append({"img": img, "start": round(c_start, 3),
                         "end": None if c_end is None else round(c_end, 3)})
            if k > 0:
                sfx.append({"type": "whoosh", "t": round(c_start - 0.18, 3)})
    elif IMAGES[sid]:
        cuts.append({"img": IMAGES[sid][0], "start": round(v_start, 3), "end": None})

    scenes.append({"id": sid, "audioStart": round(a_start, 3), "audioEnd": round(a_end, 3),
                   "visualStart": round(v_start, 3), "groups": groups, "cuts": cuts,
                   "words": ws})
    if i > 0:
        sfx.append({"type": "whoosh", "t": round(v_start - 0.05, 3)})
    t_audio = a_end + GAP_AFTER.get(sid, 0.3)

total = scenes[-1]["audioEnd"] + END_HOLD
for i, sc in enumerate(scenes):
    sc["visualEnd"] = scenes[i + 1]["visualStart"] if i + 1 < len(scenes) else total
    if sc["cuts"]:
        for c in sc["cuts"]:
            if c["end"] is None:
                c["end"] = sc["visualEnd"]

def w_of(sid, wi):
    return next(s for s in scenes if s["id"] == sid)["words"][wi]

# SFX editoriales sobre palabras clave
sfx += [
    {"type": "braam", "t": w_of("s1", 13)["t"]},                 # DINOSAURIO
    {"type": "riser", "t": w_of("s3", 8)["t"], "pre": 1.3},      # contador 4.000M
    {"type": "braam", "t": w_of("s4", 14)["t"]},                 # TIRANOSAURIO
    {"type": "braamsoft", "t": w_of("s4", 31)["t"]},             # PETRÓLEO
    {"type": "braamsoft", "t": w_of("s5", 15)["t"]},             # TIEMPO
    {"type": "pop", "t": w_of("s7", 7)["t"]},                    # LIKE
    {"type": "pop", "t": w_of("s7", 9)["t"]},                    # SÍGUENOS
    {"type": "riser", "t": total - 0.25, "pre": 1.2},            # cierre
]
sfx.sort(key=lambda x: x["t"])

timeline = {"fps": FPS, "width": 1080, "height": 1920, "total": round(total, 3),
            "scenes": scenes, "sfx": sfx}
json.dump(timeline, open(os.path.join(AUDIO, "timeline.json"), "w"),
          ensure_ascii=False, indent=1)

ts = ("// GENERADO por tools/build_timings.py — no editar a mano\n"
      "export type Token = { t: string; s: number; e: number; f: string };\n"
      "export type Group = { start: number; end: number; tokens: Token[] };\n"
      "export type Cut = { img: string; start: number; end: number };\n"
      "export type Scene = { id: string; audioStart: number; audioEnd: number;\n"
      "  visualStart: number; visualEnd: number; groups: Group[]; cuts: Cut[];\n"
      "  words: { t: number; e: number }[] };\n"
      "export type Sfx = { type: string; t: number; pre?: number };\n"
      f"export const FPS = {FPS};\n"
      f"export const WIDTH = 1080;\nexport const HEIGHT = 1920;\n"
      f"export const TOTAL_SECONDS = {round(total, 3)};\n"
      f"export const TOTAL_FRAMES = {int(round(total * FPS))};\n"
      f"export const SCENES: Scene[] = {json.dumps(scenes, ensure_ascii=False)};\n"
      f"export const SFX: Sfx[] = {json.dumps(sfx, ensure_ascii=False)};\n")
open(os.path.join(ROOT, "src", "timings.ts"), "w").write(ts)

print(f"total={total:.2f}s  frames={int(round(total*FPS))}")
for sc in scenes:
    print(f"  {sc['id']}: visual {sc['visualStart']:.2f}-{sc['visualEnd']:.2f}  "
          f"voz {sc['audioStart']:.2f}-{sc['audioEnd']:.2f}  grupos={len(sc['groups'])}")
