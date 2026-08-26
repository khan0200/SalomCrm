"""Generate the marketing site's image assets from the master logo.

The source logo is a 2000x2000 PNG of roughly 600 KB. Shipping that to every
visitor would dominate Largest Contentful Paint for no visual benefit, so this
script emits the handful of sizes the site actually references, plus a social
card and a multi-resolution favicon.

    venv/Scripts/python marketing/tools/build_assets.py

Re-run it whenever logo.png changes. Output goes to marketing/public/, which
the site generator copies to the root of dist/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "logo.png"
PUBLIC = ROOT / "marketing" / "public"
ASSETS = PUBLIC / "assets"

BRAND = "SalomCRM"
TAGLINE = "Student recruitment CRM for education agencies"

# Sizes the layout and the web manifest reference by name.
PNG_SIZES = (64, 180, 192, 512)
ICO_SIZES = ((16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256))

INK = (22, 24, 29)
MUTED = (91, 100, 114)
CARD_BG = (255, 255, 255)
RULE = (227, 230, 234)
ACCENT = (29, 78, 216)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Best available system sans-serif, falling back to PIL's bitmap font."""
    candidates = (
        ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def square(img: Image.Image) -> Image.Image:
    """Centre-crop to a square so downscales are not distorted."""
    w, h = img.size
    if w == h:
        return img
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def write_pngs(master: Image.Image) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for size in PNG_SIZES:
        out = ASSETS / f"salomcrm-logo-{size}.png"
        master.resize((size, size), Image.LANCZOS).save(
            out, "PNG", optimize=True
        )
        print(f"  {out.relative_to(ROOT)}  {out.stat().st_size / 1024:.1f} KB")


def write_favicon(master: Image.Image) -> None:
    out = PUBLIC / "favicon.ico"
    master.resize((256, 256), Image.LANCZOS).save(out, "ICO", sizes=ICO_SIZES)
    print(f"  {out.relative_to(ROOT)}  {out.stat().st_size / 1024:.1f} KB")


def write_og_card(master: Image.Image) -> None:
    """The 1200x630 card used for og:image and twitter:image."""
    card = Image.new("RGB", (1200, 630), CARD_BG)
    draw = ImageDraw.Draw(card)

    # Accent bar along the top edge.
    draw.rectangle([0, 0, 1200, 10], fill=ACCENT)

    logo_px = 190
    logo = master.resize((logo_px, logo_px), Image.LANCZOS)
    card.paste(logo, (96, 132))

    brand_font = load_font(78, bold=True)
    tag_font = load_font(35)
    meta_font = load_font(27)

    draw.text((96, 372), BRAND, font=brand_font, fill=INK)
    draw.text((96, 474), TAGLINE, font=tag_font, fill=MUTED)

    draw.line([(96, 552), (1104, 552)], fill=RULE, width=2)
    draw.text((96, 572), "salomkorea.uz", font=meta_font, fill=ACCENT)

    out = ASSETS / "salomcrm-og.png"
    card.save(out, "PNG", optimize=True)
    print(f"  {out.relative_to(ROOT)}  {out.stat().st_size / 1024:.1f} KB")


def main() -> int:
    if not SOURCE.exists():
        print(f"error: {SOURCE} not found", file=sys.stderr)
        return 1

    with Image.open(SOURCE) as img:
        master = square(img.convert("RGBA"))

    print(f"\n  source: logo.png {img.size[0]}x{img.size[1]}\n")
    write_pngs(master)
    write_favicon(master)
    write_og_card(master.convert("RGB"))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
