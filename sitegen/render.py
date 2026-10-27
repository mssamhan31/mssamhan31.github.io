"""Render every page of the site from templates, data and content.

Inputs:  site.yaml (settings), data/cv.json (sanitised CV), content/*.md (prose with front
         matter), content/projects.yaml, content/gallery.yaml, content/notes/ (imported posts)
Output:  one folder per page under the output directory, each holding index.html, plus static/.

Page conventions: content/about.md becomes /about/, content/phd/index.md becomes /phd/. Level-2
Markdown headings feed the sticky "on this page" navigation. A line holding only
`<!-- name -->` in a Markdown page is replaced by the generated insert of that name. Names
listed under `org_links` in site.yaml are linked on their first mention in each page's prose
and wherever they appear in CV rows.
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
from pathlib import Path

import markdown
import yaml
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from sitegen import cv_data

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# Forms of Samhan's name as they appear in author strings, longest first.
NAME_FORMS = ("Muhammad Syahman Samhan", "M. Syahman Samhan", "M Syahman Samhan", "Samhan Samhan")

INSERT_MARKER = re.compile(r"<!--\s*(\w+)\s*-->")

PHD_FROM_YEAR = 2024  # conferences from this year onward belong to the PhD

NO_LINK_INSIDE = ("a", "h1", "h2", "h3", "script", "style")


# --- Template filters ------------------------------------------------------------------


def month_year(value) -> str:
    """'2025-01-01' -> 'Jan 2025'; open-ended -> 'present'; bare year -> '2025'."""
    if cv_data.is_open_ended(value):
        return "present"
    date = cv_data.parse_date(value)
    if date:
        return f"{MONTHS[date.month - 1]} {date.year}"
    year = cv_data.year_of(value)
    return str(year) if year else ""


def date_range(start, end, today: dt.date | None = None) -> str:
    """'Jul 2022 – present', 'Aug 2025', or 'Incoming, 2027' for a start in the future."""
    if cv_data.is_incoming(start, today):
        return f"Incoming, {cv_data.year_of(start)}"
    first, last = month_year(start), month_year(end)
    if not last or first == last:
        return first
    return f"{first} – {last}"


def year_range(start, end) -> str:
    """Years only: '2025 – present', '2022 – 2023', or '2019' when both fall in one year."""
    first = cv_data.year_of(start)
    last = "present" if cv_data.is_open_ended(end) else cv_data.year_of(end)
    if first is None:
        return str(last or "")
    if last is None or last == first:
        return str(first)
    return f"{first} – {last}"


def bold_name(authors) -> Markup:
    """Wrap Samhan's name in <strong> inside an author list."""
    text = str(escape(authors or ""))
    for form in NAME_FORMS:
        if form in text:
            return Markup(text.replace(form, f"<strong>{form}</strong>", 1))
    return Markup(text)


def lines(text) -> list[str]:
    """Split a multi-line cell into clean bullet strings."""
    return [line.strip() for line in str(text or "").split("\n") if line.strip()]


def join_present(*parts, sep=", ") -> str:
    """Join the parts that have a value: 'Degree, Institution' when the city is blank."""
    return sep.join(str(p) for p in parts if p)


# --- Linking ---------------------------------------------------------------------------------


def autolink_html(html: str, links: dict[str, str], once: bool = True) -> str:
    """Link organisation names inside HTML, never inside an existing link or a heading.

    With once=True each name is linked on its first mention only (page prose); with
    once=False every text node gets its first mention linked (CV rows, one per row).
    """
    soup = BeautifulSoup(html, "html.parser")
    linked: list[str] = []
    for name, url in sorted(links.items(), key=lambda item: -len(item[0])):
        if once and any(name in done for done in linked):
            continue  # "UNSW" is covered once "UNSW Sydney" has been linked on this page
        for text in soup.find_all(string=True):
            if name not in text or text.find_parent(NO_LINK_INSIDE):
                continue
            before, _, after = str(text).partition(name)
            anchor = soup.new_tag("a", href=url)
            anchor.string = name
            text.replace_with(before, anchor, after)
            linked.append(name)
            if once:
                break
    return str(soup)


# --- Content loading -------------------------------------------------------------------


def load_content(path: Path) -> tuple[dict, str]:
    """Split a Markdown file into its YAML front matter and body."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, meta, body = text.split("---", 2)
        return yaml.safe_load(meta) or {}, body.strip()
    return {}, text


def render_markdown(
    text: str, inserts: dict[str, Markup] | None = None
) -> tuple[Markup, list[dict]]:
    """Markdown to HTML plus the level-2 headings; `<!-- name -->` markers become inserts."""
    inserts = inserts or {}
    html: list[str] = []
    toc: list[dict] = []
    # re.split with one group alternates text chunks and marker names.
    for index, chunk in enumerate(INSERT_MARKER.split(text)):
        if index % 2:
            html.append(str(inserts.get(chunk, "")))
            continue
        converter = markdown.Markdown(
            extensions=["extra", "toc", "sane_lists"],
            extension_configs={"toc": {"toc_depth": "2-2"}},
        )
        html.append(converter.convert(chunk))
        toc += [{"id": token["id"], "title": token["name"]} for token in converter.toc_tokens]
    return Markup("".join(html)), toc


def load_yaml(path: Path, default):
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else default


# --- Builder -----------------------------------------------------------------------------


class SiteBuilder:
    """Holds the shared inputs and writes one page at a time."""

    def __init__(self, root: Path, out: Path, today: dt.date | None = None):
        self.root, self.out = root, out
        self.today = today or dt.date.today()
        self.content = root / "content"
        self.settings = yaml.safe_load((root / "site.yaml").read_text(encoding="utf-8"))
        self.links: dict[str, str] = self.settings.get("org_links", {})
        self.sheets = cv_data.load(root / "data" / "cv.json")
        self.env = Environment(
            loader=FileSystemLoader(root / "templates"),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters.update(
            month_year=month_year,
            date_range=lambda start, end: date_range(start, end, self.today),
            bold_name=bold_name,
            lines=lines,
            linked=self.linked,
            year_range=year_range,
        )
        self.env.globals.update(
            site=self.settings,
            join_present=join_present,
            last_updated=self.today.strftime("%B %Y"),
        )
        self.pages: list[str] = []

    # -- helpers ---------------------------------------------------------------------------

    def linked(self, text) -> Markup:
        """Filter for CV cells: escape, then link any organisation named in the cell."""
        if not text:
            return Markup("")
        return Markup(autolink_html(str(escape(text)), self.links, once=False))

    def write(self, page_path: str, template: str, **context) -> None:
        """Render a template to <out>/<page_path>/index.html."""
        html = self.env.get_template(template).render(page_path=page_path, **context)
        target = self.out / page_path.strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        self.pages.append(page_path)

    def partial(self, template: str, **context) -> Markup:
        """Render a partial template to safe HTML for insertion into a Markdown page."""
        return Markup(self.env.get_template(template).render(**context))

    def prose(
        self, body: str, inserts: dict[str, Markup] | None = None
    ) -> tuple[Markup, list[dict]]:
        """Markdown body to HTML with inserts applied and organisation names linked once."""
        html, toc = render_markdown(body, inserts)
        return Markup(autolink_html(str(html), self.links, once=True)), toc

    def markdown_page(
        self, source: Path, page_path: str, inserts: dict[str, Markup] | None = None, **extra
    ) -> None:
        meta, body = load_content(source)
        html, toc = self.prose(body, inserts)
        self.write(page_path, "page.html", body=html, toc=toc, **meta, **extra)

    # -- pages -----------------------------------------------------------------------------

    def home(self) -> None:
        meta, body = load_content(self.content / "home.md")
        bio, _ = self.prose(body)
        self.write("/", "home.html", bio=bio, **meta)

    def about(self) -> None:
        projects = load_yaml(self.content / "projects.yaml", [])
        cards = self.partial("partials/projects.html", projects=projects)
        self.markdown_page(self.content / "about.md", "/about/", inserts={"projects": cards})

    def phd(self) -> None:
        recent = [
            c
            for c in cv_data.conferences(self.sheets)
            if (cv_data.year_of(c.get("start")) or 0) >= PHD_FROM_YEAR
        ]
        inserts = {"conferences": self.partial("partials/conferences.html", conferences=recent)}
        for source in sorted((self.content / "phd").glob("*.md")):
            slug = "" if source.stem == "index" else f"{source.stem}/"
            self.markdown_page(source, f"/phd/{slug}", inserts=inserts)

    def cv(self) -> None:
        sheets = self.sheets
        self.write(
            "/cv/",
            "cv.html",
            title="Curriculum vitae",
            education=cv_data.education(sheets),
            experience=cv_data.experience(sheets),
            certifications=cv_data.certifications(sheets),
            awards=cv_data.awards(sheets),
            publications=cv_data.publications(sheets),
            conferences=cv_data.conferences(sheets),
            talks=cv_data.talks(sheets),
            volunteering=cv_data.volunteering(sheets),
            organisations=cv_data.organisations(sheets),
            languages=cv_data.languages(sheets),
            counts=cv_data.counts(sheets),
        )

    def notes(self) -> None:
        notes = load_yaml(self.content / "notes" / "notes.yaml", [])
        self.write("/notes/", "notes.html", title="Notes", notes=notes)
        for note in notes:
            folder = self.content / "notes" / note["slug"]
            body = Markup((folder / "index.html").read_text(encoding="utf-8"))
            comments = load_yaml(folder / "comments.yaml", [])
            self.write(
                f"/notes/{note['slug']}/", "note.html", note=note, body=body, comments=comments
            )
            if (folder / "images").exists():
                shutil.copytree(
                    folder / "images",
                    self.out / "notes" / note["slug"] / "images",
                    dirs_exist_ok=True,
                )

    def gallery(self) -> None:
        """Newest first, so the grid reads left to right and top to bottom in time order."""
        items = sorted(
            load_yaml(self.content / "gallery.yaml", []),
            key=lambda i: i.get("year") or 0,
            reverse=True,
        )
        for item in items:
            stem, suffix = item["file"].rsplit(".", 1)
            thumb = f"{stem}-480.{suffix}"
            has_thumb = (self.root / "static" / "img" / "gallery" / thumb).exists()
            item["src"] = f"/img/gallery/{item['file']}"
            item["thumb"] = f"/img/gallery/{thumb}" if has_thumb else item["src"]
        self.write("/gallery/", "gallery.html", title="Gallery", items=items)

    def contact(self) -> None:
        self.markdown_page(self.content / "contact.md", "/contact/")

    # -- orchestration ---------------------------------------------------------------------

    def build(self) -> list[str]:
        if self.out.exists():
            shutil.rmtree(self.out)
        shutil.copytree(self.root / "static", self.out)
        self.home()
        self.about()
        self.phd()
        self.cv()
        self.notes()
        self.gallery()
        self.contact()
        return self.pages


def build(root: Path, out: Path, today: dt.date | None = None) -> list[str]:
    """Build the whole site; returns the list of page paths written."""
    return SiteBuilder(root, out, today).build()
