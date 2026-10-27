"""Resize photos for the web.

Used by the one-off preparation scripts (portrait, gallery, notes images), not by build.py:
the repository keeps the already-resized files so the build stays a pure copy.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

Source = Path | BytesIO


def _load(source: Source) -> Image.Image:
    """Open a file or an in-memory buffer, honour EXIF rotation, and return the pixels.

    The file handle is released before returning, so callers on Windows can delete or
    overwrite the source straight away.
    """
    with Image.open(source) as opened:
        return ImageOps.exif_transpose(opened).convert("RGB")


def to_web(source: Source, target: Path, max_side: int = 1600, quality: int = 82) -> Path:
    """Write a WebP (or JPEG, by target suffix) no larger than max_side on its long edge."""
    image = _load(source)
    image.thumbnail((max_side, max_side))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix == ".webp":
        image.save(target, quality=quality, method=6)
    else:
        image.save(target, quality=quality, optimize=True)
    return target


def crop_to(
    source: Source,
    target: Path,
    box: tuple[int, int, int, int],
    size: tuple[int, int],
    quality: int = 85,
) -> Path:
    """Crop a box (left, top, right, bottom) out of source and save it at the given size."""
    image = _load(source).crop(box).resize(size, Image.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, quality=quality, optimize=True)
    return target
