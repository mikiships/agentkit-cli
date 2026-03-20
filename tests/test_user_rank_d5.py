"""Tests for D5: Docs, CHANGELOG, version bump."""
from __future__ import annotations

import pytest
import tomllib
from pathlib import Path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_version_in_pyproject():
    """pyproject.toml version is 0.67.0."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == "0.67.0"


def test_version_in_init():
    """agentkit_cli/__init__.py __version__ is 0.67.0."""
    init_path = Path(__file__).parent.parent / "agentkit_cli" / "__init__.py"
    content = init_path.read_text()
    assert '__version__ = "0.67.0"' in content


def test_changelog_has_0_67_0():
    """CHANGELOG.md contains [0.67.0] entry."""
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    content = changelog_path.read_text()
    assert "[0.67.0]" in content


def test_changelog_mentions_user_rank():
    """CHANGELOG [0.67.0] mentions user-rank."""
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    content = changelog_path.read_text()
    assert "user-rank" in content or "UserRankEngine" in content


def test_readme_has_user_rank_section():
    """README.md contains user-rank command documentation."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text()
    assert "user-rank" in content


def test_readme_has_usage_examples():
    """README user-rank section includes example commands."""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text()
    assert "agentkit user-rank python" in content or "agentkit user-rank" in content
