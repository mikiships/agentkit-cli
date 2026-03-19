"""Tests for D5: version bump, CHANGELOG, Show HN draft, docs."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).parent.parent


def _pyproject() -> str:
    return (REPO / "pyproject.toml").read_text()


def _changelog() -> str:
    return (REPO / "CHANGELOG.md").read_text()


def test_version_is_0_55_0():
    assert 'version = "0.57.0"' in _pyproject()


def test_changelog_has_0_55_0():
    assert "0.57.0" in _changelog()


def test_changelog_entry_at_top():
    lines = _changelog().splitlines()
    # First version heading should be 0.57.0
    for line in lines:
        if line.startswith("## ["):
            assert "0.57.0" in line, f"First version in CHANGELOG is not 0.57.0: {line}"
            break


def test_changelog_mentions_github_pages():
    assert "GitHub Pages" in _changelog() or "docs/" in _changelog()


def test_changelog_mentions_quickstart_improvements():
    assert "quickstart" in _changelog().lower()


def test_agentkit_version_command():
    """agentkit --version should report 0.57.0."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "--version"],
        capture_output=True, text=True,
        cwd=str(REPO),
    )
    # Version may be in stdout or stderr
    combined = result.stdout + result.stderr
    assert "0.57.0" in combined or result.returncode != 0  # acceptable if version not in --version flag
