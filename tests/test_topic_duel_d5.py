"""D5 tests for docs, version, CHANGELOG assertions."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_69_0():
    from agentkit_cli import __version__
    # Version must be >= 0.70.0 (bumped through subsequent releases)
    parts = tuple(int(x) for x in __version__.split("."))
    assert parts >= (0, 70, 0)


def test_pyproject_version():
    from agentkit_cli import __version__
    content = (REPO_ROOT / "pyproject.toml").read_text()
    assert f'version = "{__version__}"' in content


def test_changelog_has_v0_69_0():
    content = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.69.0" in content


def test_readme_has_topic_duel_command():
    content = (REPO_ROOT / "README.md").read_text()
    assert "topic-duel" in content


def test_readme_has_topic_duel_section():
    content = (REPO_ROOT / "README.md").read_text()
    assert "agentkit topic-duel" in content
    assert "fastapi" in content or "topic1" in content.lower()
