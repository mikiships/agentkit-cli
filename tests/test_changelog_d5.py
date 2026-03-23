"""Tests for D5: version bump, CHANGELOG, docs."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_version_is_current():
    from agentkit_cli import __version__
    assert __version__ >= "0.94.1"


def test_pyproject_version_current():
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    import re
    m = re.search(r'version = "(\d+\.\d+\.\d+)"', text)
    assert m is not None
    assert m.group(1) >= "0.94.1"


def test_changelog_has_0_93_0():
    text = (Path(__file__).parent.parent / "CHANGELOG.md").read_text()
    assert "## [0.93.0]" in text


def test_changelog_mentions_changelog_command():
    text = (Path(__file__).parent.parent / "CHANGELOG.md").read_text()
    assert "changelog" in text.lower()


def test_readme_has_changelog_section():
    text = (Path(__file__).parent.parent / "README.md").read_text()
    assert "## Changelog Generation" in text


def test_readme_mentions_agentkit_changelog():
    text = (Path(__file__).parent.parent / "README.md").read_text()
    assert "agentkit changelog" in text


def test_changelog_engine_importable():
    from agentkit_cli.changelog_engine import ChangelogEngine, CommitSummary, ScoreDelta
    assert ChangelogEngine is not None


def test_changelog_cmd_importable():
    from agentkit_cli.commands.changelog_cmd import changelog_command
    assert changelog_command is not None
