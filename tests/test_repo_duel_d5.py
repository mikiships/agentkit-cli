"""Tests for D5: version bump, CHANGELOG, README, BUILD-REPORT."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_74_0():
    from agentkit_cli import __version__
    assert __version__ == "0.75.0"


def test_pyproject_version_is_0_74_0():
    content = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.75.0"' in content


def test_changelog_has_0_74_0_entry():
    content = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.75.0" in content


def test_changelog_repo_duel_mentioned():
    content = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "repo-duel" in content.lower() or "repo_duel" in content.lower()


def test_build_report_exists():
    build_report = REPO_ROOT / "BUILD-REPORT.md"
    assert build_report.exists()


def test_build_report_has_version():
    from agentkit_cli import __version__
    content = (REPO_ROOT / "BUILD-REPORT.md").read_text()
    assert __version__ in content


def test_build_report_versioned_copy_exists():
    from agentkit_cli import __version__
    versioned = REPO_ROOT / f"BUILD-REPORT-v{__version__}.md"
    assert versioned.exists()
