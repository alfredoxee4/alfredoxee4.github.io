# 💧🦖 Agua Jurásica — Video vertical 9:16

Video corto (40s, 1080×1920 @30fps) construido 100% con código: **"El agua que bebes
ya la bebió un dinosaurio"**.

## Pipeline

| Etapa | Herramienta |
|---|---|
| Voz IA (es-MX, con timestamps por palabra) | edge-tts (`tools/gen_voice.py`) |
| Imágenes cinematográficas | Pollinations FLUX (`tools/gen_images.sh`) |
| Super-resolución x2 | OpenCV dnn_superres EDSR (`tools/upscale.py`) |
| Línea de tiempo palabra-a-frame | `tools/build_timings.py` → `src/timings.ts` |
| Música + SFX procedurales (numpy) | `tools/gen_music.py` |
| Mezcla master -14 LUFS | `tools/mix_master.py` (ffmpeg loudnorm) |
| Composición, karaoke, FX y render | **Remotion** (`src/`) |

## Render

```bash
npm install
python3 tools/gen_voice.py      # regenerar voz (opcional)
python3 tools/build_timings.py  # reconstruir timeline
python3 tools/gen_music.py      # regenerar banda sonora
python3 tools/mix_master.py     # master de audio
npx remotion render src/index.ts AguaJurasica out/agua-jurasica.mp4
```

El resultado final está en `out/agua-jurasica.mp4` (y una copia en la raíz del
proyecto como `agua-jurasica.mp4`).

## Características de edición

- Subtítulos karaoke palabra a palabra sincronizados a la voz (timestamps reales del TTS)
- Contador animado de 4,000,000,000 años con gradiente dorado
- Ken Burns + punch-in por corte, sacudida de cámara en los impactos
- Montaje rápido de 4 planos en el segmento histórico (lluvia → T-Rex → océanos → Jurásico)
- Partículas: burbujas, polvo dorado y lluvia; cáusticas de agua; god rays
- Flashes de transición, viñeta, grano de cine y grade teal/ámbar global
- CTA final animado (like ❤️ + botón SEGUIR) con micro-corazones
- Sound design procedural: braams, whooshes, riser, gota de agua, latido, pops
