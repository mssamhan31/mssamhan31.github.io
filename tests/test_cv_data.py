"""Rules in sitegen.cv_data and the sync export: merging, grouping, sorting, show levels."""

import datetime as dt

import openpyxl

import sync_cv
from sitegen import cv_data


def _experience(**overrides):
    row = {
        "start": "2023-01-01",
        "end": "2024-01-01",
        "company": "X",
        "role": "r",
        "note": "",
        "type": "Full Time",
    }
    row.update(overrides)
    return row


def test_experience_merges_consecutive_rows_for_same_position_only():
    sheets = {
        "experience": [
            _experience(start="2023-12-01", end="2024-05-01", company="AGL", role="Solar Engineer"),
            _experience(
                start="2023-08-01",
                end="2023-12-01",
                company="AGL",
                role="Graduate Solar Engineer",
                type="Part Time",
            ),
            _experience(
                start="2022-11-01",
                end="2023-01-01",
                company="SolarBay",
                role="Solar Installer",
                note="a\nb",
            ),
            _experience(
                start="2022-06-01", end="2022-11-01", company="SolarBay", role="Solar Installer"
            ),
        ]
    }
    entries = cv_data.experience(sheets)
    assert [(e["company"], e["role"]) for e in entries] == [
        ("AGL", "Solar Engineer"),
        ("AGL", "Graduate Solar Engineer"),
        ("SolarBay", "Solar Installer"),
    ]
    assert entries[2]["start"] == "2022-06-01" and entries[2]["bullets"] == ["a", "b"]
    assert entries[0]["employment"] == "Full-time" and entries[1]["employment"] == "Part-time"


def test_open_ended_experience_sorts_first():
    sheets = {
        "experience": [
            _experience(company="Old"),
            _experience(start="2022-07-01", end="ongoing", company="Current"),
        ]
    }
    assert cv_data.experience(sheets)[0]["company"] == "Current"


def test_certifications_grouped_in_order():
    sheets = {
        "certifications": [
            {"date": "2024-06-01", "type": "Project Management", "name": "PMP"},
            {"date": "2023-01-01", "type": "Solar Energy Engineering", "name": "Designer"},
            {"date": "2024-09-01", "type": "Data Science", "name": "DL"},
            {"date": "2022-07-01", "type": "Construction", "name": "White Card"},
        ]
    }
    groups = cv_data.certifications(sheets)
    assert [g["name"] for g in groups] == [
        "Energy engineering",
        "Data science",
        "Project management",
        "Other",
    ]
    assert groups[0]["items"][0]["year"] == 2023


def test_show_levels_are_featured_or_detail():
    assert cv_data.show_level("Featured") == "featured"
    assert cv_data.show_level("featured ") == "featured"
    assert cv_data.show_level("Normal") == "detail"
    assert cv_data.show_level(None) == "detail"
    assert cv_data.is_incoming("2027-05-03", today=dt.date(2026, 10, 27))
    assert not cv_data.is_incoming("2024-05-20", today=dt.date(2026, 10, 27))
    assert cv_data.employment_type("Full Time (Internship)") == "Full-time internship"


def test_volunteering_sorts_by_end_year_with_ongoing_first():
    sheets = {
        "volunteering": [
            {"start": 2015, "end": 2016, "organisation": "Tutoring"},
            {"start": "2022-10-01", "end": "2023-06-01", "organisation": "RESOC UNSW"},
            {"start": 2025, "end": "now", "organisation": "Causindy"},
            {"start": 2024, "end": 2025, "organisation": "PGC UNSW"},
            {"start": "2022-01-01", "end": "now", "organisation": "Solarin"},
        ]
    }
    order = [r["organisation"] for r in cv_data.volunteering(sheets)]
    assert order == ["Causindy", "Solarin", "PGC UNSW", "RESOC UNSW", "Tutoring"]


def test_education_split_and_counts():
    sheets = {
        "education": [
            {
                "start": "2016-08-22",
                "end": "2020-08-05",
                "institution": "ITB",
                "type": "Formal Education",
            },
            {
                "start": "2019-10-10",
                "end": "2019-12-08",
                "institution": "KAIST",
                "type": "Short Course",
            },
        ],
        "conferences": [{}] * 10,
        "talks": [{}] * 12,
        "certifications": [{}] * 30,
        "awards": [{}] * 24,
        "publications": [{}] * 6,
    }
    assert [e["institution"] for e in cv_data.education(sheets)["formal"]] == ["ITB"]
    assert cv_data.counts(sheets)["outputs"] == 28


def _sheet(headers, rows):
    ws = openpyxl.Workbook().active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    return ws


def test_sync_skips_period_markers_and_hidden_rows_and_exports_show():
    ws = _sheet(
        ["Start", "End", "Company", "Name", "Note", "Company Website", "Reference", "Web", "Show"],
        [
            [
                dt.datetime(2025, 1, 1),
                "ongoing",
                "Ausgrid",
                "Researcher",
                "ok",
                "https://ausgrid.com.au",
                "Secret Person",
                None,
                "Featured",
            ],
            [
                dt.datetime(2024, 5, 1),
                None,
                "Start of PhD Study Period",
                None,
                None,
                None,
                None,
                None,
                None,
            ],
            [
                dt.datetime(2020, 1, 1),
                "2020-06-01",
                "Hidden Co",
                "Role",
                "x",
                "https://drive.google.com/x",
                None,
                "N",
                None,
            ],
            [
                dt.datetime(2019, 1, 1),
                "2019-06-01",
                "Plain Co",
                "Role",
                "x",
                None,
                None,
                None,
                None,
            ],
        ],
    )
    _, required, mapping = sync_cv.SHEETS["2. Experience"]
    rows = sync_cv.export_sheet(ws, required, mapping)
    assert [r["company"] for r in rows] == ["Ausgrid", "Plain Co"]
    assert rows[0]["show"] == "Featured" and rows[1]["show"] == "Normal"
    assert rows[0]["start"] == "2025-01-01" and "Reference" not in rows[0]


def test_sync_drops_private_links_and_phone_numbers():
    ws = _sheet(
        ["Language", "Credential", "Link"],
        [["English", "TOEFL, call +61 412 345 678", "https://drive.google.com/open?id=1"]],
    )
    _, required, mapping = sync_cv.SHEETS["10. Languages"]
    row = sync_cv.export_sheet(ws, required, mapping)[0]
    assert "+61" not in row["credential"] and "link" not in row
