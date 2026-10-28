"""Draw the browser-tab and home-screen icons: a white serif "S" over an orange bar on navy.

Writes static/favicon.ico (16, 32 and 48 px), static/favicon-32.png and
static/apple-touch-icon.png (180 px, square corners because iOS rounds them itself). Each size
is drawn at eight times its final size and scaled down, so the letter stays crisp at tab size.

Usage (PowerShell):  python tools/make_favicon.py <path to a serif .ttf>
The site's display face is Source Serif 4 SemiBold; without a font path the script falls back to
Georgia Bold, which ships with Windows.
"""

from __future__ import annotations

import struct
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "static"

# Colours from the site's design tokens (static/css/site.css).
NAVY = (0x22, 0x30, 0x41, 255)
ORANGE = (0xF3, 0x9A, 0x24, 255)
WHITE = (255, 255, 255, 255)

SCALE = 8  # supersampling factor
FALLBACK_FONT = Path(r"C:\Windows\Fonts\georgiab.ttf")


def draw_icon(size: int, font_path: Path, rounded: bool) -> Image.Image:
    """One icon at `size` pixels: navy ground, the S centred above a short orange bar."""
    big = size * SCALE
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    radius = int(big * 0.2) if rounded else 0
    draw.rounded_rectangle((0, 0, big - 1, big - 1), radius=radius, fill=NAVY)

    # Centre the letter and the bar as one block, measuring the letter's ink, not its line box.
    font = ImageFont.truetype(str(font_path), int(big * 0.72))
    left, top, right, bottom = draw.textbbox((0, 0), "S", font=font)
    glyph_w, glyph_h = right - left, bottom - top
    gap = int(big * 0.07)
    # The bar is snapped to whole final pixels so it stays a crisp line at 16 and 32 px.
    bar_w = max(round(big * 0.36 / SCALE), 2) * SCALE
    bar_h = max(round(big * 0.065 / SCALE), 1) * SCALE
    block_top = (big - (glyph_h + gap + bar_h)) / 2

    draw.text(((big - glyph_w) / 2 - left, block_top - top), "S", font=font, fill=WHITE)
    bar_top = round((block_top + glyph_h + gap) / SCALE) * SCALE
    bar_left = round((big - bar_w) / 2 / SCALE) * SCALE
    draw.rectangle((bar_left, bar_top, bar_left + bar_w - 1, bar_top + bar_h - 1), fill=ORANGE)
    # Box averaging of each SCALE x SCALE block: no ringing halo beside the bar, unlike Lanczos.
    return image.resize((size, size), Image.BOX)


def save_ico(images: list[Image.Image], path: Path) -> None:
    """Write a .ico whose entries are exactly the given images, each stored as PNG data.

    Pillow's own ICO writer rescales one source image for every size; writing the entries
    directly keeps each hand-drawn size.
    """
    blobs = []
    for image in images:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        blobs.append(buffer.getvalue())
    offset = 6 + 16 * len(images)
    entries = b""
    for image, blob in zip(images, blobs):
        width, height = image.size
        entries += struct.pack(
            "<BBBBHHII", width % 256, height % 256, 0, 0, 1, 32, len(blob), offset
        )
        offset += len(blob)
    path.write_bytes(struct.pack("<HHH", 0, 1, len(images)) + entries + b"".join(blobs))


def main() -> None:
    font_path = Path(sys.argv[1]) if len(sys.argv) > 1 else FALLBACK_FONT
    tab = {size: draw_icon(size, font_path, rounded=True) for size in (16, 32, 48)}
    save_ico([tab[16], tab[32], tab[48]], STATIC / "favicon.ico")
    tab[32].save(STATIC / "favicon-32.png")
    draw_icon(180, font_path, rounded=False).convert("RGB").save(STATIC / "apple-touch-icon.png")
    print(f"wrote favicon.ico, favicon-32.png and apple-touch-icon.png using {font_path.name}")


if __name__ == "__main__":
    main()
