#!/bin/bash
# Genera las imágenes de escena vía Pollinations (FLUX) con reintentos.
set -u
cd "$(dirname "$0")/../public/img"
CA=/root/.ccr/ca-bundle.crt
BASE="https://image.pollinations.ai/prompt"

declare -A PROMPTS=(
  [img2]="Macro cinematic shot of a human hand holding a glass of pure glowing water in darkness, luminous blue-teal swirling liquid light inside the glass, caustic light patterns projected on the skin, black background, high contrast, hyper realistic film still, vertical composition"
  [img3]="Planet Earth seen from deep space, swirling white storm clouds over glowing deep blue oceans, thin luminous atmosphere rim light, dense star field background, epic cinematic realism, awe inspiring scale, vertical composition"
  [img4]="Torrential prehistoric rainstorm over dense primeval jungle at twilight, giant sauropod dinosaurs silhouetted in the misty distance, heavy rain streaks catching dramatic amber light, lightning glow inside storm clouds, cinematic epic atmosphere, hyper realistic, vertical composition"
  [img6]="Vast primordial ocean with towering dark waves under a violent young sky, smoking volcanic islands on the horizon, golden god rays breaking through storm clouds, ancient prehistoric Earth, epic cinematic seascape, vertical composition"
  [img7]="Lush Jurassic fern forest with giant prehistoric plants, shafts of golden light through the primeval canopy, dark oily swamp water below reflecting the vegetation, floating spores glowing in the light beams, cinematic hyper realistic, vertical composition"
  [img8]="Surreal macro shot of a glass of water on a dark table, inside the glass swirls a miniature glowing galaxy with stardust and a small golden hourglass suspended in the water, cosmic dust particles floating around, deep blue and gold palette, dreamlike cinematic realism, vertical composition"
  [img9]="Cinematic silhouette of a person in a dark room raising a glass of water to eye level, the glass glows with ethereal blue light illuminating their face with wonder and awe, floating dust particles in the light beam, dramatic chiaroscuro, film still, vertical composition"
)
declare -A SEEDS=([img2]=21 [img3]=33 [img4]=44 [img6]=66 [img7]=77 [img8]=88 [img9]=99)

urlencode() { python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"; }

for key in img2 img3 img4 img6 img7 img8 img9; do
  seed=${SEEDS[$key]}
  enc=$(urlencode "${PROMPTS[$key]}")
  ok=0
  for attempt in 1 2 3 4; do
    code=$(curl -sSL --cacert $CA -G "$BASE/$enc" \
      -d "width=1080" -d "height=1920" -d "model=flux" -d "nologo=true" -d "seed=$seed" \
      -o "$key.jpg" --max-time 240 -w "%{http_code}" 2>/dev/null)
    size=$(stat -c%s "$key.jpg" 2>/dev/null || echo 0)
    if [ "$code" = "200" ] && [ "$size" -gt 25000 ] && file "$key.jpg" | grep -q JPEG; then
      echo "OK $key seed=$seed intento=$attempt $(file "$key.jpg" | grep -o '[0-9]*x[0-9]*' | head -1) ${size}B"
      ok=1; break
    fi
    echo "RETRY $key intento=$attempt code=$code size=$size"
    seed=$((seed + 10)); sleep 4
  done
  [ $ok -eq 0 ] && echo "FAIL $key"
  sleep 2
done
echo "DONE"
