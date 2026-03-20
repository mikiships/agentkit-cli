"""D5 tests for docs and version bump (v0.70.0)."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).parent.parent


def test_pyproject_version():
    content = (REPO / "pyproject.toml").read_text()
    assert 'version = "0.70.0"' in content


def test_changelog_entry():
    content = (REPO / "CHANGELOG.md").read_text()
    assert "0.70.0" in content


def test_changelog_topic_league():
    content = (REPO / "CHANGELOG.md").read_text()
    assert "topic-league" in content.lower() or "topic_league" in content.lower()


def test_readme_topic_league():
    content = (REPO / "README.md").read_text()
    assert "topic-league" in content.lower() or "topic_league" in content.lower()


def test_build_report_exists():
    report = REPO / "BUILD-REPORT.md"
    assert report.exists()
    content = report.read_text()
    assert "0.70.0" in content or "topic-league" in content.lower()
