"""Tests for D5: version 0.57.0, CHANGELOG, README."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).parent.parent


def _pyproject() -> str:
    return (REPO / "pyproject.toml").read_text()


def _changelog() -> str:
    return (REPO / "CHANGELOG.md").read_text()


def _readme() -> str:
    return (REPO / "README.md").read_text()


def test_version_is_0_57_0():
    assert 'version = "0.57.0"' in _pyproject()


def test_init_version_is_0_57_0():
    from agentkit_cli import __version__
    assert __version__ == "0.57.0"


def test_changelog_has_0_57_0():
    assert "0.57.0" in _changelog()


def test_changelog_0_57_0_at_top():
    lines = _changelog().splitlines()
    for line in lines:
        if line.startswith("## ["):
            assert "0.57.0" in line, f"First version in CHANGELOG is not 0.57.0: {line}"
            break


def test_changelog_mentions_pages():
    assert "Pages" in _changelog() or "pages" in _changelog()


def test_readme_has_daily_leaderboard_section():
    assert "## Daily Leaderboard" in _readme() or "Daily Leaderboard" in _readme()


def test_readme_has_pages_flag():
    assert "--pages" in _readme()


def test_readme_has_pages_repo_flag():
    assert "--pages-repo" in _readme()


def test_readme_has_github_actions_cron():
    assert "cron" in _readme()
    assert "github_token" in _readme().lower() or "GITHUB_TOKEN" in _readme()
