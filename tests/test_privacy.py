"""The privacy rules, and a scan of every built page for anything they forbid."""

from sitegen import privacy


def test_phone_numbers_are_scrubbed_but_money_and_counts_survive():
    text = (
        "Call +61 423 657 780 or 0812-1458-8439 about the $1.6 million, 37-site rollout in 2024-29"
    )
    scrubbed = privacy.scrub_phones(text)
    assert "423" not in scrubbed and "1458" not in scrubbed
    assert "$1.6 million" in scrubbed and "37-site" in scrubbed and "2024-29" in scrubbed


def test_private_links_detected():
    assert privacy.is_private_link("https://drive.google.com/open?id=abc")
    assert privacy.is_private_link("https://www.blogger.com/profile/123")
    assert not privacy.is_private_link("https://www.sciencedirect.com/science/article/pii/S1")
    assert not privacy.is_private_link(None)


def test_find_violations_allows_only_contact_emails():
    allowed = ["samhanmail@gmail.com"]
    text = "Write to samhanmail@gmail.com, not to someone@example.com, phone +62 812 3456 7890"
    kinds = {kind for kind, _ in privacy.find_violations(text, allowed)}
    assert kinds == {"email", "phone"}
    assert privacy.find_violations("mail samhanmail@gmail.com.", allowed) == []


def test_built_site_contains_nothing_private(built_site, settings):
    pages = list(built_site.rglob("*.html"))
    assert pages, "the build produced no pages"
    violations = {
        page.relative_to(built_site).as_posix(): privacy.find_violations(
            page.read_text(encoding="utf-8"), settings["emails"]
        )
        for page in pages
    }
    assert {k: v for k, v in violations.items() if v} == {}
