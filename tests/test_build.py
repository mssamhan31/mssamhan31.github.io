"""End-to-end checks on a full build: pages exist, links resolve, identity and layout rules hold."""

import datetime as dt
import re

from sitegen.render import (
    autolink_html,
    bold_name,
    date_range,
    load_content,
    month_year,
    year_range,
)


def test_every_nav_link_and_internal_link_resolves(built_site, settings):
    for item in settings["nav"]:
        assert (built_site / item["path"].strip("/") / "index.html").exists(), item["path"]
    for page in built_site.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        for href in re.findall(r'(?:href|src)="(/[^"#?]*)', html):
            target = built_site / href.strip("/")
            assert target.exists() or (target / "index.html").exists(), f"{page.name}: {href}"


def test_home_bio_is_under_300_words_and_has_no_bold(root, built_site):
    _, body = load_content(root / "content" / "home.md")
    assert len(body.split()) <= 300
    home = (built_site / "index.html").read_text(encoding="utf-8")
    bio = home.split('class="bio"')[1].split("</main>")[0]
    assert "<strong>" not in bio


def test_home_hero_has_three_buttons_and_no_cards(built_site, settings):
    html = (built_site / "index.html").read_text(encoding="utf-8")
    hero = html.split('class="hero-text"')[1].split("</div>")[0]
    assert settings["headline"].split(".")[0] in html
    assert hero.count('<a class="btn') == 3 and "Learn more about my PhD" in hero
    assert 'class="card"' not in html and 'class="options"' not in html
    assert "/img/portrait.jpg" in html


def test_every_page_uses_the_short_name_and_carries_last_updated(built_site, settings):
    for page in built_site.rglob("*.html"):
        html = page.read_text(encoding="utf-8")
        for forbidden in ("Muhammad", "Karlsruhe", "wwwproxy", "Download complete CV"):
            assert forbidden not in html, (page, forbidden)
        assert "Last updated" in html, page
        assert 'rel="icon"' in html and 'rel="apple-touch-icon"' in html, page
        assert settings["full_name"] in html, page


def test_cv_has_two_views_and_combined_count(built_site):
    html = (built_site / "cv" / "index.html").read_text(encoding="utf-8")
    assert 'data-view="featured"' in html
    assert "Full detail" in html and ">Normal<" not in html
    assert 'data-show="featured"' in html and 'data-show="detail"' in html
    assert "talks, presentations and publications" in html


def test_cv_expands_abbreviations_before_bare_use(built_site):
    html = (built_site / "cv" / "index.html").read_text(encoding="utf-8")
    text = re.sub(r"<[^>]+>", "", html)  # links wrap some long forms, so compare visible text
    for long_form, short in (
        ("Renewable Energy Society", "RESOC"),
        ("Indonesia Endowment Fund for Education", "LPDP"),
        ("Arc Postgraduate Council", "PGC"),
    ):
        expansion = f"{long_form} ({short})"
        assert expansion in text, expansion
        assert text.find(short) == text.find(expansion) + len(long_form) + 2, short


def test_gallery_reads_newest_first(built_site):
    html = (built_site / "gallery" / "index.html").read_text(encoding="utf-8")
    years = [int(y) for y in re.findall(r"· (\d{4})</figcaption>", html)]
    assert len(years) >= 10 and years == sorted(years, reverse=True)


def test_notes_index_shows_one_picture_per_post(built_site, root):
    html = (built_site / "notes" / "index.html").read_text(encoding="utf-8")
    posts = [p for p in (root / "content" / "notes").iterdir() if p.is_dir()]
    assert html.count('class="thumb"') == len(posts)


def test_date_filters():
    assert month_year("2025-01-01") == "Jan 2025"
    assert month_year("ongoing") == "present"
    assert month_year(2016) == "2016"
    assert date_range("2022-07-01", "ongoing") == "Jul 2022 – present"
    assert date_range("2025-08-26", "2025-08-26") == "Aug 2025"
    assert date_range("2027-05-03", "2027-07-30", today=dt.date(2026, 10, 27)) == "Incoming, 2027"
    assert year_range("2025-01-01", "now") == "2025 – present"
    assert year_range(2022, 2023) == "2022 – 2023"
    assert year_range("2019-02-01", "2019-12-01") == "2019"


def test_bold_name_wraps_only_samhan():
    html = str(bold_name("Phoebe Dennis, M. Syahman Samhan, Baran Yildiz"))
    assert html.count("<strong>") == 1 and "<strong>M. Syahman Samhan</strong>" in html


def test_autolink_links_first_mention_once_and_never_inside_links_or_headings():
    links = {"Ausgrid": "https://www.ausgrid.com.au/", "UNSW": "https://www.unsw.edu.au/"}
    html = "<h2>Ausgrid</h2><p>With Ausgrid and <a href='/x'>Ausgrid</a>. Ausgrid again, UNSW.</p>"
    out = autolink_html(html, links, once=True)
    assert out.count('href="https://www.ausgrid.com.au/"') == 1
    assert out.count('href="https://www.unsw.edu.au/"') == 1
    assert "<h2>Ausgrid</h2>" in out
    assert "<a href='/x'>Ausgrid</a>" in out or '<a href="/x">Ausgrid</a>' in out
