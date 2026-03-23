"""Tests for D5: CHANGELOG, version bump, BUILD-REPORT."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_version_is_0_91_0():
    from agentkit_cli import __version__
    assert __version__ == "0.91.0"


def test_pyproject_version():
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    assert 'version = "0.91.0"' in text


def test_changelog_has_0_91_0():
    text = (Path(__file__).parent.parent / "CHANGELOG.md").read_text()
    assert "## [0.91.0]" in text


def test_changelog_mentions_interactive_ui():
    text = (Path(__file__).parent.parent / "CHANGELOG.md").read_text()
    assert "Interactive" in text or "interactive" in text


def test_changelog_mentions_post_analyze():
    text = (Path(__file__).parent.parent / "CHANGELOG.md").read_text()
    assert "POST /analyze" in text


def test_changelog_mentions_recent():
    text = (Path(__file__).parent.parent / "CHANGELOG.md").read_text()
    assert "/recent" in text
