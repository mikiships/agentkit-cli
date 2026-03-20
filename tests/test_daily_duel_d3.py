"""Tests for D3: version bump to 0.75.0, README, CHANGELOG."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_version_init():
    from agentkit_cli import __version__
    assert __version__ == "0.75.0"


def test_version_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.75.0"' in pyproject


def test_changelog_entry():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.75.0" in changelog
    assert "daily-duel" in changelog.lower() or "daily_duel" in changelog.lower()


def test_readme_daily_duel_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "daily-duel" in readme.lower()


def test_build_report_exists():
    assert (REPO_ROOT / "BUILD-REPORT.md").exists()


def test_build_report_mentions_daily_duel():
    report = (REPO_ROOT / "BUILD-REPORT.md").read_text()
    assert "daily-duel" in report.lower() or "daily_duel" in report.lower()


def test_version_format():
    from agentkit_cli import __version__
    parts = __version__.split(".")
    assert len(parts) == 3
    assert parts == ["0", "75", "0"]
