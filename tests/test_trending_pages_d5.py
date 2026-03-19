"""Tests for D5: version bump, CHANGELOG, README, BUILD-REPORT."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
README_PATH = REPO_ROOT / "README.md"
BUILD_REPORT_PATH = REPO_ROOT / "BUILD-REPORT.md"


def test_version_is_0_59_0():
    content = PYPROJECT_PATH.read_text()
    assert 'version = "0.62.0"' in content

def test_changelog_has_0_59_0_section():
    content = CHANGELOG_PATH.read_text()
    assert "0.62.0" in content

def test_changelog_mentions_pages_trending():
    content = CHANGELOG_PATH.read_text()
    assert "pages-trending" in content

def test_changelog_section_at_top():
    content = CHANGELOG_PATH.read_text()
    idx_059 = content.index("0.62.0")
    idx_058 = content.index("0.58.0")
    assert idx_059 < idx_058

def test_readme_has_pages_trending_in_commands():
    content = README_PATH.read_text()
    assert "pages-trending" in content

def test_readme_has_usage_example():
    content = README_PATH.read_text()
    assert "agentkit pages-trending" in content

def test_readme_shows_language_flag():
    content = README_PATH.read_text()
    assert "--language" in content

def test_build_report_exists():
    assert BUILD_REPORT_PATH.exists(), "BUILD-REPORT.md must exist"

def test_build_report_mentions_deliverables():
    content = BUILD_REPORT_PATH.read_text()
    assert "D1" in content or "TrendingPagesEngine" in content

def test_build_report_mentions_test_count():
    content = BUILD_REPORT_PATH.read_text()
    assert "test" in content.lower()
