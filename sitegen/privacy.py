"""Rules for what must never reach the public site.

The patterns here are shared by sync_cv.py (which scrubs the workbook export), import_notes.py
(which scrubs the blog imports) and tests/test_privacy.py (which scans every built page).
Only patterns live here, never the private values themselves, because this file is public.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# International (+61 4xx..., +62 8xx...) and local (04xx..., 081x...) phone formats.
PHONE_PATTERNS = (
    re.compile(r"\+\d{1,3}[\s-]?\d[\d\s-]{6,}\d"),
    re.compile(r"\b0\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4}\b"),
)

# Links that lead to private files or to blog commenters' profiles.
PRIVATE_LINK_HOSTS = (
    "drive.google.com",
    "docs.google.com",
    "blogger.com/profile",
)

# Requires a letters-only top-level domain so a font URL such as "wght@8..60" is not an address.
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")


def is_private_link(url: str | None) -> bool:
    """True when a link points at a private host and must be dropped."""
    return bool(url) and any(host in url for host in PRIVATE_LINK_HOSTS)


def scrub_phones(text: str) -> str:
    """Remove anything that looks like a phone number from free text."""
    for pattern in PHONE_PATTERNS:
        text = pattern.sub("", text)
    return text


def find_violations(text: str, allowed_emails: Iterable[str]) -> list[tuple[str, str]]:
    """Return (kind, match) pairs for every private detail found in text.

    Used by the privacy test over the built HTML. Any email other than the public contact
    addresses counts as a violation, so a reference's address can never slip through.
    """
    allowed = {email.lower() for email in allowed_emails}
    found: list[tuple[str, str]] = []
    for pattern in PHONE_PATTERNS:
        found += [("phone", match) for match in pattern.findall(text)]
    found += [("private link", host) for host in PRIVATE_LINK_HOSTS if host in text]
    found += [
        ("email", match)
        for match in EMAIL_PATTERN.findall(text)
        if match.lower().rstrip(".") not in allowed
    ]
    return found
