"""Build the site into _site/.

Reads site.yaml, data/cv.json and the content folder, renders the templates and copies static
files. Safe to run repeatedly; the output folder is recreated each time.

Usage (PowerShell):  python build.py            # writes _site/
                     python build.py --out dist # writes somewhere else
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sitegen.render import build

ROOT = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static site.")
    parser.add_argument("--out", default=ROOT / "_site", type=Path, help="output folder")
    args = parser.parse_args()
    pages = build(ROOT, args.out)
    print(f"built {len(pages)} pages into {args.out}")


if __name__ == "__main__":
    main()
