"""D5 tests: docs, changelog, version bump, build report."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent


def test_version_bumped():
    from agentkit_cli import __version__
    assert __version__ == "0.74.0"


def test_pyproject_version():
    content = (REPO / "pyproject.toml").read_text()
    assert 'version = "0.74.0"' in content


def test_changelog_has_v071():
    content = (REPO / "CHANGELOG.md").read_text()
    assert "0.74.0" in content


def test_changelog_mentions_ecosystem():
    content = (REPO / "CHANGELOG.md").read_text()
    assert "ecosystem" in content.lower()


def test_readme_has_ecosystem_command():
    content = (REPO / "README.md").read_text()
    assert "agentkit ecosystem" in content


def test_readme_intro_has_ecosystem_usecase():
    content = (REPO / "README.md").read_text()
    assert "State of" in content or "ecosystem" in content.lower()
