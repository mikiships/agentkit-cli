"""Tests for agentkit leaderboard-page D5 — version, docs, CHANGELOG."""
from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_82_0():
    from agentkit_cli import __version__
    assert __version__ == "0.82.0"


def test_pyproject_version_is_0_82_0():
    content = (REPO_ROOT / "pyproject.toml").read_text()
    assert '0.82.0' in content


def test_changelog_has_0_82_0_entry():
    content = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.82.0" in content


def test_readme_has_leaderboard_section():
    content = (REPO_ROOT / "README.md").read_text()
    assert "leaderboard" in content.lower()


def test_build_report_exists():
    assert (REPO_ROOT / "BUILD-REPORT.md").exists()


def test_build_report_v082_exists():
    assert (REPO_ROOT / "BUILD-REPORT-v0.82.0.md").exists()


def test_build_report_v082_has_content():
    content = (REPO_ROOT / "BUILD-REPORT-v0.82.0.md").read_text()
    assert "0.82.0" in content


def test_changelog_has_leaderboard_page_mention():
    content = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "leaderboard-page" in content or "leaderboard_page" in content


def test_readme_has_leaderboard_page_command():
    content = (REPO_ROOT / "README.md").read_text()
    assert "leaderboard-page" in content or "leaderboard_page" in content
