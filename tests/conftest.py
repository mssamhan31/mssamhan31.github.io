"""Shared fixtures: the repository root, its settings, and one full build per test session."""

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sitegen.render import build  # noqa: E402


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def settings(root) -> dict:
    return yaml.safe_load((root / "site.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def built_site(root, tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("site")
    build(root, out)
    return out
