from __future__ import annotations

import io
import math
import random
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

FIREFLY = [
    "https://photoshop-api.adobe.io/v2/short-url/urn:aaid:ps:US:3a8976f5-90f8-43ac-8910-da8b7b4bcecc",
    "https://photoshop-api.adobe.io/v2/short-url/urn:aaid:ps:US:2fc94deb-dc35-41da-8bdf-f6947df624b3",
    "https://photoshop-api.adobe.io/v2/short-url/urn:aaid:ps:US:4f49ea87-7982-4069-bfca-aba7da08f317",
    "https://photoshop-api.adobe.io/v2/short-url/urn:aaid:ps:US:d85ea884-7e9c-4424-a317-d15d28a2f620",
]

PROMPTS = [
    "macro cinematic glass of crystal clear water held in a human hand, black background, tiny glowing ancient particles inside the water, photorealistic, dramatic rim light, vertical composition, no text",
    "torrential rain falling over a lush Jurassic jungle at dusk, giant ferns, mist, cinematic natural history documentary, photorealistic, vertical composition, no text",
    "Tyrannosaurus rex drinking water from a prehistoric river, close dramatic low angle, rain droplets, photorealistic cinematic documentary, vertical composition, anatomically plausible, no text",
    "surreal geological cross section showing Jurassic plants slowly becoming dark petroleum underground, ancient time layers, cinematic scientific visualization, photorealistic, vertical, no text",
    "planet Earth from space wrapped by a luminous water cycle orbit, four billion years of time suggested through concentric rings, premium science documentary, cinematic, vertical, no text",
    "vast ancient ocean under an alien prehistoric sky, no modern objects, enormous clouds, shafts of sunlight through water, cinematic natural history documentary, vertical, no text",
    "single floating water droplet containing galaxies fossils and prehistoric landscapes, black deep space background, ultra detailed cinematic macro, vertical, no text",
    "modern clear glass of water on a dark reflective table, subtle prehistoric jungle reflected inside the glass, awe inspiring cinematic advertising image, vertical, no text",
]


def pollinations_url(prompt: str, seed: int) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1080&height=1920&seed={seed}&nologo=true&enhance=true&model=flux"
    )


def request_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (GitHub Actions; DinosaurWaterReel/3.0)",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.read()


def polish(raw: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(raw)).convert("RGB")
    src_ratio = image.width / image.height
    target_ratio = 1080 / 1920
    if src_ratio > target_ratio:
        width = int(image.height * target_ratio)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = int(image.width / target_ratio)
        top = (image.height - height) // 2
        image = image.crop((0, top, image.width, top + height))
    image = image.resize((1080, 1920), Image.Resampling.LANCZOS)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Color(image).enhance(1.06)
    return image


def fallback(index: int) -> Image.Image:
    random.seed(7100 + index)
    palettes = [
        ((2, 10, 25), (18, 112, 150)),
        ((6, 18, 18), (38, 118, 74)),
        ((18, 11, 7), (123, 73, 32)),
        ((15, 8, 20), (115, 62, 103)),
        ((1, 9, 29), (32, 91, 171)),
        ((4, 22, 31), (26, 121, 133)),
        ((7, 4, 22), (84, 51, 140)),
        ((4, 12, 22), (42, 109, 142)),
    ]
    top, bottom = palettes[index]
    image = Image.new("RGB", (1080, 1920), top)
    px = image.load()
    for y in range(1920):
        p = y / 1919
        glow = math.sin(p * math.pi) ** 2
        for x in range(1080):
            radial = max(0.0, 1.0 - math.hypot((x - 540) / 800, (y - 820) / 1350))
            mix = min(1.0, p * 0.65 + glow * radial * 0.42)
            px[x, y] = tuple(int(top[c] * (1 - mix) + bottom[c] * mix) for c in range(3))
    draw = ImageDraw.Draw(image, "RGBA")
    for _ in range(180):
        x = random.randrange(0, 1080)
        y = random.randrange(0, 1920)
        r = random.randrange(1, 6)
        draw.ellipse((x - r, y - r, x + r, y + r * 2), fill=(145, 235, 255, random.randrange(18, 80)))
    for r in (270, 355, 445):
        draw.ellipse((540 - r, 820 - r, 540 + r, 820 + r), outline=(121, 231, 255, 40), width=3)
    image = image.filter(ImageFilter.GaussianBlur(radius=0.55))
    return image


def main() -> None:
    for i, prompt in enumerate(PROMPTS):
        sources = []
        if i < len(FIREFLY):
            sources.append(FIREFLY[i])
        sources.append(pollinations_url(prompt, 5600 + i * 137))
        final = None
        for source in sources:
            try:
                print(f"Downloading scene {i + 1}: {source[:110]}")
                final = polish(request_bytes(source))
                break
            except Exception as exc:  # noqa: BLE001
                print(f"Source failed for scene {i + 1}: {exc}")
        if final is None:
            print(f"Using original generated fallback for scene {i + 1}")
            final = fallback(i)
        path = OUT / f"scene-{i + 1}.jpg"
        final.save(path, "JPEG", quality=93, optimize=True, progressive=True)
        print(f"Saved {path} ({path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
