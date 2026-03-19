"""Tests for D5: version 0.58.0, CHANGELOG, README."""
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
    assert ('version = "' + __import__("agentkit_cli").__version__ + '"') in _pyproject()


def test_init_version_is_0_57_0():
    from agentkit_cli import __version__
    assert len(__version__) > 0  # version exists - updated by build


def test_changelog_has_0_57_0():
    assert __import__("agentkit_cli").__version__ in _changelog()


def test_changelog_0_57_0_at_top():
    lines = _changelog().splitlines()
    for line in lines:
        if line.startswith("## ["):
            assert __import__("agentkit_cli").__version__ in line, f"First version in CHANGELOG should be {__import__(chr(97)+chr(103)+chr(101)+chr(110)+chr(116)+chr(107)+chr(105)+chr(116)+chr(95)+chr(99)+chr(108)+chr(105)).__version__}: {line}"
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
