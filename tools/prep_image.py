#!/usr/bin/env python3
"""Подготовка фото с объекта для сайта: поворот по EXIF, удаление метаданных (в т.ч. GPS), ресайз, webp + jpg.

    python3 tools/prep_image.py <исходник> <имя-латиницей> [--width 1280]
    -> site/assets/blog/<имя>.webp и site/assets/blog/<имя>.jpg, печатает JSON {"src","w","h"} для поля hero.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent


def main():
    src, name = sys.argv[1], sys.argv[2]
    width = int(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else 1280
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    out = ROOT / "site" / "assets" / "blog"
    out.mkdir(parents=True, exist_ok=True)
    clean = Image.new("RGB", im.size)
    clean.paste(im)
    clean.save(out / f"{name}.webp", "WEBP", quality=82, method=6)
    clean.save(out / f"{name}.jpg", "JPEG", quality=85, optimize=True, progressive=True)
    print(json.dumps({"src": f"assets/blog/{name}.webp", "w": clean.width, "h": clean.height}))


if __name__ == "__main__":
    main()
