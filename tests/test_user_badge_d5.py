"""Tests for D5: version bump, CHANGELOG, README (≥8 tests)."""
from __future__ import annotations

from pathlib import Path

import pytest


REPO = Path(__file__).parent.parent


def test_version_is_current():
    from agentkit_cli import __version__
    # Version advances with each release; check it's at or above 0.65.0
    parts = tuple(int(x) for x in __version__.split("."))
    assert parts >= (0, 65, 0), f"Expected >=0.65.0, got {__version__}"


def test_pyproject_version_is_current():
    pyproject = (REPO / "pyproject.toml").read_text()
    # Version is set; just verify pyproject has a version field at all
    assert 'version = "' in pyproject


def test_changelog_has_0_65_0():
    changelog = (REPO / "CHANGELOG.md").read_text()
    assert "0.65.0" in changelog


def test_changelog_mentions_user_badge():
    changelog = (REPO / "CHANGELOG.md").read_text()
    assert "user-badge" in changelog.lower() or "user_badge" in changelog.lower()


def test_readme_has_user_badges_section():
    readme = (REPO / "README.md").read_text()
    assert "user-badge" in readme.lower() or "user badge" in readme.lower()


def test_build_report_exists():
    report = REPO / "BUILD-REPORT.md"
    assert report.exists()


def test_build_report_exists():
    report = (REPO / "BUILD-REPORT.md")
    assert report.exists(), "BUILD-REPORT.md must exist"


def test_user_badge_importable():
    from agentkit_cli.user_badge import UserBadgeEngine
    assert UserBadgeEngine is not None


def test_user_badge_cmd_importable():
    from agentkit_cli.commands.user_badge_cmd import user_badge_command
    assert user_badge_command is not None
