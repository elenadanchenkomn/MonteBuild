#!/usr/bin/env python3
"""Карусель / картинка для Facebook и Instagram в стиле montebuild.com (1080×1350, тёмный фон, зелёный акцент).

    python3 tools/build_slides.py content/social/<файл>.json social/<папка>
    -> social/<папка>/slide-01.png, slide-02.png ... ; при переполнении текста печатает «TEXT OVERFLOWS slide N».

Формат JSON:
{
  "slides": [
    {"kind": "cover", "photo": "site/assets/blog/x.jpg", "kicker": "Плесень · Батуми", "title": "Почему плесень возвращается"},
    {"kind": "text", "num": "1", "title": "Короткий заголовок", "body": "2–4 коротких предложения."},
    {"kind": "photo", "photo": "путь", "caption": "подпись внизу (необязательно)"},
    {"kind": "final", "title": "Пришлите фото стены в WhatsApp", "body": "+995 595 01 96 15 · montebuild.com"}
  ]
}
Пути к фото — от корня репозитория.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FONT = str(ROOT / "tools" / "fonts" / "Onest.ttf")
LOGO = ROOT / "site" / "assets" / "logo-240.png"
W, H = 1080, 1350
BG, INK, MUTED, GREEN, LINE = (10, 10, 10), (255, 255, 255), (170, 181, 173), (46, 204, 90), (38, 50, 41)
PAD = 88


def font(size, weight=700):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def wrap(draw, text, f, width):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            test = (cur + " " + word).strip()
            if draw.textlength(test, font=f) <= width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def block(draw, xy, text, f, fill, width, spacing=1.25):
    x, y = xy
    for line in wrap(draw, text, f, width):
        draw.text((x, y), line, font=f, fill=fill)
        y += int(f.size * spacing)
    return y


def cover_photo(path):
    im = ImageOps.exif_transpose(Image.open(ROOT / path)).convert("RGB")
    return ImageOps.fit(im, (W, H), Image.LANCZOS)


def logo(img):
    if LOGO.exists():
        lg = Image.open(LOGO).convert("RGBA")
        lg.thumbnail((150, 130))
        img.paste(lg, (PAD, PAD - 20), lg)


def render(slide, n, total):
    kind = slide["kind"]
    overflow = False
    if kind in ("cover", "photo"):
        img = cover_photo(slide["photo"])
        shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shade)
        for i in range(H // 2):
            a = int(230 * (i / (H / 2)) ** 1.4)
            sd.line([(0, H // 2 + i), (W, H // 2 + i)], fill=(0, 0, 0, a))
        img = Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB")
        d = ImageDraw.Draw(img)
        logo(img)
        if kind == "cover":
            tf = font(76, 800)
            lines = wrap(d, slide["title"], tf, W - 2 * PAD)
            y = H - PAD - len(lines) * int(76 * 1.15) - 10
            if slide.get("kicker"):
                kf = font(34, 600)
                d.text((PAD, y - 70), slide["kicker"].upper(), font=kf, fill=GREEN)
            block(d, (PAD, y), slide["title"], tf, INK, W - 2 * PAD, 1.15)
            overflow = y < H * 0.35
        elif slide.get("caption"):
            cf = font(40, 500)
            lines = wrap(d, slide["caption"], cf, W - 2 * PAD)
            block(d, (PAD, H - PAD - len(lines) * 50), slide["caption"], cf, INK, W - 2 * PAD)
    else:
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        logo(img)
        y = 300
        if slide.get("num"):
            d.text((PAD, y - 20), slide["num"], font=font(120, 800), fill=GREEN)
            y += 150
        d.rectangle([PAD, y, PAD + 90, y + 8], fill=GREEN)
        y += 50
        y = block(d, (PAD, y), slide["title"], font(66, 800), INK, W - 2 * PAD, 1.15) + 36
        if slide.get("body"):
            y = block(d, (PAD, y), slide["body"], font(42, 400), MUTED if kind == "text" else INK, W - 2 * PAD, 1.35)
        overflow = y > H - 150
    d = ImageDraw.Draw(img)
    if total > 1:
        f = font(30, 500)
        t = f"{n}/{total}"
        d.text((W - PAD - d.textlength(t, font=f), PAD), t, font=f, fill=MUTED)
    d.text((PAD, H - 70), "montebuild.com", font=font(28, 500), fill=MUTED if kind not in ("cover", "photo") else INK)
    return img, overflow


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = ROOT / sys.argv[2]
    out.mkdir(parents=True, exist_ok=True)
    slides = spec["slides"]
    for i, s in enumerate(slides, 1):
        img, over = render(s, i, len(slides))
        img.save(out / f"slide-{i:02d}.png", optimize=True)
        if over:
            print(f"TEXT OVERFLOWS slide {i}")
    print(f"OK: {len(slides)} слайдов в {sys.argv[2]}")


if __name__ == "__main__":
    main()
