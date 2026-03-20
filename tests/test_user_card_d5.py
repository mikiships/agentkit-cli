"""Tests for D5: Docs, CHANGELOG, version bump (≥5 tests)."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_is_current():
    import agentkit_cli
    parts = tuple(int(x) for x in agentkit_cli.__version__.split("."))
    assert parts >= (0, 64, 0), f"Expected >=0.64.0, got {agentkit_cli.__version__}"


def test_pyproject_version_is_current():
    import tomllib
    pyproject = REPO_ROOT / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    parts = tuple(int(x) for x in data["project"]["version"].split("."))
    assert parts >= (0, 64, 0)


def test_changelog_has_0_64_0():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.64.0" in changelog


def test_readme_has_user_card_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "user-card" in readme


def test_build_report_exists():
    report = (REPO_ROOT / "BUILD-REPORT.md")
    assert report.exists(), "BUILD-REPORT.md must exist"
