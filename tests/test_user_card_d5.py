"""Tests for D5: Docs, CHANGELOG, version bump (≥5 tests)."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_64_0():
    import agentkit_cli
    assert agentkit_cli.__version__ == "0.64.0"


def test_pyproject_version_is_0_64_0():
    import tomllib
    pyproject = REPO_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == "0.64.0"


def test_changelog_has_0_64_0():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.64.0" in changelog


def test_readme_has_user_card_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "user-card" in readme


def test_build_report_has_0_64_0():
    report = (REPO_ROOT / "BUILD-REPORT.md").read_text()
    assert "0.64.0" in report
