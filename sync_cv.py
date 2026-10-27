"""Export the CV workbook to data/cv.json with every private field removed.

Reads the Excel workbook named in site.yaml (it lives on Google Drive and is never committed),
keeps only the sheets and columns the site needs, scrubs anything private, and writes
data/cv.json. Run on Samhan's machine whenever the workbook changes, then read the JSON diff
before pushing: that diff is exactly what becomes public.

Usage (PowerShell):  python sync_cv.py
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import openpyxl
import yaml

from sitegen.privacy import is_private_link, scrub_phones

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "cv.json"

# Sheet name -> (json key, required column, {workbook header: json key}).
# Headers not listed are dropped, so the References sheet, phone numbers, reference names
# and Drive file links never leave the workbook.
SHEETS = {
    "1. Education": (
        "education",
        "Institution",
        {
            "Date Start": "start",
            "Date End": "end",
            "Institution": "institution",
            "Degree / Course": "degree",
            "Highlight": "highlight",
            "Major": "major",
            "Grade": "grade",
            "City": "city",
            "Country": "country",
            "Mode of Delivery": "mode",
            "Type": "type",
        },
    ),
    "2. Experience": (
        "experience",
        "Name",
        {
            "Start": "start",
            "End": "end",
            "Company": "company",
            "Name": "role",
            "Company Description": "company_description",
            "City": "city",
            "Country": "country",
            "Industry": "industry",
            "Type": "type",
            "Formal Role Name": "formal_role",
            "Note": "note",
            "Company Website": "website",
        },
    ),
    "3. Certification": (
        "certifications",
        "Certificate Name",
        {
            "Date": "date",
            "Expiry Date": "expiry",
            "Type": "type",
            "Certificate Name": "name",
            "Institution": "institution",
            "Country": "country",
        },
    ),
    "4. Publication": (
        "publications",
        "Title",
        {
            "Year": "year",
            "Type": "type",
            "Publisher": "publisher",
            "Title": "title",
            "Author": "authors",
            "Link": "link",
        },
    ),
    "5. Conference & Proceeding": (
        "conferences",
        "Conference",
        {
            "Year": "year",
            "Date Start": "start",
            "Date End": "end",
            "Conference": "conference",
            "Organiser": "organiser",
            "Level": "level",
            "Country": "country",
            "City": "city",
            "Type": "mode",
            "Participation": "participation",
            "Title": "title",
            "Highlight": "highlight",
            "Link": "link",
        },
    ),
    "6. Invited Speaker": (
        "talks",
        "Event",
        {
            "Date": "date",
            "Organiser": "organiser",
            "Event": "event",
            "Level": "level",
            "Audience": "audience",
            "Number of Audience": "audience_size",
            "Role (Invited)": "role",
            "Delivery": "delivery",
            "Highlight": "highlight",
            "Link": "link",
        },
    ),
    "7. Award": (
        "awards",
        "Award",
        {
            "Year": "year",
            "Level": "level",
            "Award": "award",
            "Awarding Body": "awarding_body",
            "Link": "link",
        },
    ),
    "8. Volunteering": (
        "volunteering",
        "Organization / Program",
        {
            "Time Start": "start",
            "Time End": "end",
            "Scope": "scope",
            "Organization / Program": "organisation",
            "Description": "description",
            "Role": "role",
        },
    ),
    "9. Organization": (
        "organisations",
        "Organization",
        {
            "Start": "start",
            "End": "end",
            "Organization": "organisation",
            "Description": "description",
            "Role": "role",
            "Note": "note",
        },
    ),
    "10. Languages": (
        "languages",
        "Language",
        {
            "Language": "language",
            "Proficiency": "proficiency",
            "Credential": "credential",
        },
    ),
}

WEB_COLUMN = "Web"  # optional column on any sheet: N hides the row from the site
SHOW_COLUMN = "Show"  # optional column on any sheet: Featured, Normal (default) or Detail
LINK_KEYS = {"link", "website"}


def clean(value, key: str):
    """Normalise one cell: dates to ISO, text stripped and phone-scrubbed, private links dropped."""
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str):
        value = scrub_phones(value.strip())
        if value in ("", "N/A"):
            return None
        if key in LINK_KEYS and is_private_link(value):
            return None
    return value


def export_sheet(worksheet, required: str, mapping: dict[str, str]) -> list[dict]:
    headers = [cell.value for cell in worksheet[1]]
    rows = []
    for raw in worksheet.iter_rows(min_row=2, values_only=True):
        record = dict(zip(headers, raw))
        hidden = str(record.get(WEB_COLUMN) or "").strip().upper() == "N"
        if not record.get(required) or hidden:
            continue  # period markers, blank rows, and rows hidden with Web = N
        row = {key: clean(record.get(header), key) for header, key in mapping.items()}
        row["show"] = str(record.get(SHOW_COLUMN) or "Normal").strip()
        rows.append(row)
    return rows


def main() -> None:
    settings = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
    workbook = openpyxl.load_workbook(settings["cv_source"], read_only=True, data_only=True)
    sheets = {}
    for sheet_name, (key, required, mapping) in SHEETS.items():
        sheets[key] = export_sheet(workbook[sheet_name], required, mapping)
        print(f"{key:15s} {len(sheets[key]):3d} rows")
    payload = {"generated": dt.date.today().isoformat(), "sheets": sheets}
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
