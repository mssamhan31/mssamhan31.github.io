"""Load data/cv.json and apply the CV page's grouping, merging and sorting rules.

Each public function returns plain dicts ready for a template. The rules:
formal and short-course education are split; consecutive experience rows at the same
company in the same role are merged into one entry with bullets; certifications are grouped
in Samhan's order; every list is newest first; every row carries a `show` level (featured or
detail) that drives the CV page's view switch.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

# (group name, workbook Type values it claims). None claims whatever is left.
CERTIFICATION_GROUPS = (
    ("Energy engineering", ("Solar Energy Engineering",)),
    ("Finance", ("Accounting / Finance",)),
    ("Data science", ("Data Science",)),
    ("Project management", ("Project Management",)),
    ("Other", None),
)

FEATURED_VOLUNTEERING = ("Phiwiki", "PPIA", "RESOC", "Causindy")

OPEN_ENDED = {"ongoing", "now", "still active", "present"}

# Workbook employment types -> how they read on the page.
EMPLOYMENT_TYPES = {
    "full time": "Full-time",
    "part time": "Part-time",
    "full time (internship)": "Full-time internship",
    "part time (internship)": "Part-time internship",
}


def load(path: Path | str) -> dict[str, list[dict]]:
    """Read the sanitised JSON export written by sync_cv.py; normalise every row's show level."""
    with open(path, encoding="utf-8") as handle:
        sheets = json.load(handle)["sheets"]
    for rows in sheets.values():
        for row in rows:
            row["show"] = show_level(row.get("show"))
    return sheets


def show_level(value) -> str:
    """'Featured' from the workbook is featured; anything else, including blank, is detail."""
    return "featured" if str(value or "").strip().lower() == "featured" else "detail"


def employment_type(value) -> str:
    return EMPLOYMENT_TYPES.get(str(value or "").strip().lower(), str(value or "").strip())


def parse_date(value) -> dt.date | None:
    """ISO date string to date; open-ended markers, bare years and blanks become None."""
    if value is None or isinstance(value, (int, float)):
        return None
    text = str(value).strip()
    if text.lower() in OPEN_ENDED or text in ("", "N/A"):
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def is_open_ended(value) -> bool:
    return str(value or "").strip().lower() in OPEN_ENDED


def is_incoming(value, today: dt.date | None = None) -> bool:
    """True when a start date lies in the future, so the entry reads as incoming."""
    date = parse_date(value)
    return bool(date and date > (today or dt.date.today()))


def year_of(value) -> int | None:
    """Best-effort year from a date string, a bare year or a 'YYYY' text."""
    if isinstance(value, (int, float)):
        return int(value)
    date = parse_date(value)
    if date:
        return date.year
    text = str(value or "")[:4]
    return int(text) if text.isdigit() else None


def _newest_first(rows: list[dict], field: str) -> list[dict]:
    """Open-ended rows first, then by full date, then by bare year."""

    def key(row):
        return (
            is_open_ended(row.get("end")),
            parse_date(row.get(field)) or dt.date.min,
            year_of(row.get(field)) or 0,
        )

    return sorted(rows, key=key, reverse=True)


# --- Education -------------------------------------------------------------------------


def education(sheets) -> dict[str, list[dict]]:
    rows = _newest_first(sheets["education"], "start")
    return {
        "formal": [r for r in rows if r.get("type") == "Formal Education"],
        "short": [r for r in rows if r.get("type") != "Formal Education"],
    }


# --- Experience ------------------------------------------------------------------------


def experience(sheets) -> list[dict]:
    """Merge consecutive rows for the same company and role into one entry with bullets."""
    merged: list[dict] = []
    for row in _newest_first(sheets["experience"], "start"):
        entry = dict(row)
        entry["bullets"] = [b.strip() for b in str(row.get("note") or "").split("\n") if b.strip()]
        entry["employment"] = employment_type(row.get("type"))
        previous = merged[-1] if merged else None
        same_position = previous and (previous["company"], previous["role"]) == (
            entry["company"],
            entry["role"],
        )
        if same_position:
            previous["start"] = min(previous["start"], entry["start"])
            continue
        merged.append(entry)
    return merged


# --- Certifications --------------------------------------------------------------------


def certifications(sheets) -> list[dict]:
    """Groups in Samhan's order, each newest first."""
    rows = sorted(
        sheets["certifications"],
        key=lambda r: parse_date(r.get("date")) or dt.date.min,
        reverse=True,
    )
    for row in rows:
        row["year"] = year_of(row.get("date"))

    unclaimed = list(rows)
    groups = []
    for name, types in CERTIFICATION_GROUPS:
        members = [r for r in unclaimed if types is None or r.get("type") in types]
        unclaimed = [r for r in unclaimed if r not in members]
        if members:
            groups.append({"name": name, "items": members})
    return groups


# --- Simple lists ----------------------------------------------------------------------


def awards(sheets) -> list[dict]:
    return sorted(sheets["awards"], key=lambda r: year_of(r.get("year")) or 0, reverse=True)


def publications(sheets) -> dict[str, list[dict]]:
    rows = sorted(sheets["publications"], key=lambda r: year_of(r.get("year")) or 0, reverse=True)
    return {
        "journal": [r for r in rows if r.get("type") == "Journal Article"],
        "conference": [r for r in rows if r.get("type") == "Conference Paper"],
        "popular": [r for r in rows if r.get("type") == "Popular Article"],
    }


def conferences(sheets) -> list[dict]:
    return sorted(
        sheets["conferences"], key=lambda r: parse_date(r.get("start")) or dt.date.min, reverse=True
    )


def talks(sheets) -> list[dict]:
    return sorted(
        sheets["talks"], key=lambda r: parse_date(r.get("date")) or dt.date.min, reverse=True
    )


def volunteering(sheets) -> list[dict]:
    """Ordered by the year each role ended, newest first, with roles still running at the top."""

    def key(row):
        return (
            is_open_ended(row.get("end")),
            year_of(row.get("end")) or 0,
            year_of(row.get("start")) or 0,
        )

    rows = sorted(sheets["volunteering"], key=key, reverse=True)
    for row in rows:
        organisation = str(row.get("organisation") or "")
        row["featured"] = any(name in organisation for name in FEATURED_VOLUNTEERING)
    return rows


def organisations(sheets) -> list[dict]:
    return sorted(sheets["organisations"], key=lambda r: year_of(r.get("start")) or 0, reverse=True)


def languages(sheets) -> list[dict]:
    return list(sheets["languages"])


def counts(sheets) -> dict[str, int]:
    """Headline numbers for the CV page, always computed from the data."""
    outputs = len(sheets["conferences"]) + len(sheets["talks"]) + len(sheets["publications"])
    return {
        "outputs": outputs,
        "conferences": len(sheets["conferences"]),
        "talks": len(sheets["talks"]),
        "publications": len(sheets["publications"]),
        "certifications": len(sheets["certifications"]),
        "awards": len(sheets["awards"]),
    }
