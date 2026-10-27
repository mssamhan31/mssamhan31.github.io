"""Import saved Samhan Notes posts (Blogger, Indonesian) into content/notes/.

For each saved page in the source folder this keeps the post title, date, body, images and
reader comments, and drops Blogger's chrome, scripts, avatars and profile links. Images are
fetched at full size from Blogger's public image host where the saved page links to one, and
fall back to the copy saved alongside the page. Phone numbers and emails in the body or the
comments are scrubbed. The run is incremental: an optional name filter limits it to matching
pages, and the index keeps the hand-chosen `image` and `summary` of posts already listed.

Usage (PowerShell):  python import_notes.py            # every saved page
                     python import_notes.py KAIST      # only pages whose file name contains KAIST
Writes:  content/notes/<slug>/index.html   the post body as an HTML fragment
         content/notes/<slug>/comments.yaml the comment thread (author, date, text, reply, owner)
         content/notes/<slug>/images/       web-sized WebP images
         content/notes/notes.yaml           the index, newest first
"""

from __future__ import annotations

import datetime as dt
import re
import sys
import urllib.request
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote

import yaml
from bs4 import BeautifulSoup

from sitegen.images import to_web
from sitegen.privacy import EMAIL_PATTERN, is_private_link, scrub_phones

ROOT = Path(__file__).parent
SOURCE = Path(r"G:\My Drive\0 General Documents\Misc")
OUTPUT = ROOT / "content" / "notes"
INDEX = OUTPUT / "notes.yaml"

# One-line English summaries for the index page (the posts themselves stay in Indonesian).
# A summary already in notes.yaml wins over this table, so edits there survive re-imports.
SUMMARIES = {
    "pengalaman-merakit-drone": "How I built a quadcopter from parts during a university break, "
    "what each component cost, and the tuning that finally made it fly.",
    "energi-surya-sebagai-solusi-permasalahan-energi-di-indonesia": "A 2017 essay on why solar "
    "energy is the practical answer to Indonesia's energy problem.",
    "pengalaman-memasang-panel-surya": "Step by step through the small PV system I designed and "
    "installed for the family garden in 2018, and the questions readers asked.",
    "pengalaman-mengikuti-program-sakura-science-plan-ke-jepang": "What the Sakura Science Plan "
    "exchange at Osaka University was like, from the application to the days in Japan.",
}

# Presentation attributes Blogger bakes in; the site's own CSS takes over.
STRIP_ATTRIBUTES = (
    "style",
    "width",
    "height",
    "border",
    "imageanchor",
    "data-original-width",
    "data-original-height",
)
MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def scrub(text: str) -> str:
    return scrub_phones(EMAIL_PATTERN.sub("[email hidden]", text))


def fetch(url: str) -> BytesIO | None:
    """Download a public image into memory; None on any failure so the local copy is used."""
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return BytesIO(response.read(MAX_DOWNLOAD_BYTES))
    except Exception:  # noqa: BLE001 - any network or HTTP error means "use the local copy"
        return None


def import_images(body, files_dir: Path, images_dir: Path, slug: str) -> int:
    """Rewrite every <img> to a web-sized local copy; unwrap the Blogger link around it."""
    images_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for number, img in enumerate(body.find_all("img"), start=1):
        src = img.get("src", "")
        local = files_dir / unquote(Path(src).name)
        anchor = img.find_parent("a")
        full_url = anchor.get("href", "") if anchor else ""
        # Prefixed with a letter so a numeric file name can never read as a phone number.
        name = f"img{number:02d}-{slugify(local.stem)[:40] or 'image'}.webp"

        downloaded = fetch(full_url) if "googleusercontent.com" in full_url else None
        if downloaded is None and not local.exists():
            print(f"  skipped image with no local copy: {src[:80]}")
            img.decompose()
            continue
        to_web(downloaded or local, images_dir / name, max_side=1200)

        img.attrs = {
            "src": f"/notes/{slug}/images/{name}",
            "alt": img.get("alt") or "",
            "loading": "lazy",
        }
        if anchor:
            anchor.unwrap()
        count += 1
    return count


def clean_body(body) -> None:
    """Drop scripts and inline presentation; keep text, headings, lists, links and images."""
    for tag in body.find_all(["script", "iframe", "style", "noscript"]):
        tag.decompose()
    for tag in body.select(".post-share-buttons, .post-footer, .share-button"):
        tag.decompose()  # some Blogger templates place the share bar inside the post body
    for tag in body.find_all(True):
        for attribute in STRIP_ATTRIBUTES:
            tag.attrs.pop(attribute, None)
        if tag.name == "a" and is_private_link(tag.get("href")):
            tag.unwrap()
    for text in body.find_all(string=True):
        cleaned = scrub(str(text))
        if cleaned != text:
            text.replace_with(cleaned)


def extract_comments(soup) -> list[dict]:
    thread = soup.select_one(".comment-thread")
    comments = []
    for item in thread.select("li.comment") if thread else []:
        content = item.select_one(".comment-content")
        if content is None:
            continue
        author = item.select_one(".comment-header .user")
        when = item.select_one(".comment-header .datetime")
        comments.append(
            {
                "author": author.get_text(strip=True) if author else "Anonymous",
                "date": when.get_text(strip=True) if when else "",
                "text": scrub(content.get_text("\n", strip=True)),
                "reply": item.find_parent(class_="comment-replies") is not None,
                "owner": item.select_one(".comment-header .blog-author") is not None,
            }
        )
    return comments


def import_post(page: Path) -> dict:
    soup = BeautifulSoup(page.read_bytes(), "html.parser")
    title = soup.select_one(".post-title").get_text(strip=True)
    date = dt.datetime.strptime(
        soup.select_one(".date-header").get_text(strip=True), "%A, %B %d, %Y"
    )
    slug = slugify(title)
    folder = OUTPUT / slug
    folder.mkdir(parents=True, exist_ok=True)

    body = soup.select_one(".post-body")
    images = import_images(body, page.with_name(page.stem + "_files"), folder / "images", slug)
    clean_body(body)
    (folder / "index.html").write_text(body.decode_contents().strip() + "\n", encoding="utf-8")

    comments = extract_comments(soup)
    (folder / "comments.yaml").write_text(
        yaml.safe_dump(comments, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    words = len(body.get_text(" ", strip=True).split())
    print(f"{slug}: {words} words, {images} images, {len(comments)} comments")
    return {
        "slug": slug,
        "title": title,
        "date": date.date().isoformat(),
        "summary": SUMMARIES.get(slug, ""),
        "comments": len(comments),
        "words": words,
    }


def merge_index(imported: list[dict]) -> list[dict]:
    """Fold freshly imported entries into the existing index, keeping hand-edited fields."""
    listed = yaml.safe_load(INDEX.read_text("utf-8")) if INDEX.exists() else None
    existing = {n["slug"]: n for n in (listed or [])}
    for entry in imported:
        previous = existing.get(entry["slug"], {})
        for field in ("image", "summary"):
            if previous.get(field):
                entry[field] = previous[field]
        existing[entry["slug"]] = entry
    return sorted(existing.values(), key=lambda n: n["date"], reverse=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    name_filter = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    pages = [p for p in sorted(SOURCE.glob("*.htm")) if name_filter in p.name.lower()]
    if not pages:
        sys.exit(f"no saved page in {SOURCE} matches {name_filter!r}")
    notes = merge_index([import_post(page) for page in pages])
    INDEX.write_text(
        "# Imported Samhan Notes posts, written by import_notes.py. Newest first.\n"
        "# `image` is the picture shown on the Notes index, chosen by hand from the post.\n"
        + yaml.safe_dump(notes, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"index now lists {len(notes)} notes")


if __name__ == "__main__":
    main()
