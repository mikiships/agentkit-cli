"""Tests for D5: Docs, CHANGELOG, version bump, BUILD-REPORT."""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_62_0():
    from agentkit_cli import __version__
    assert __version__ == "0.62.0"


def test_pyproject_version_is_0_62_0():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.62.0"' in pyproject


def test_changelog_has_0_62_0():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "[0.62.0]" in changelog


def test_changelog_mentions_user_tournament():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "user-tournament" in changelog


def test_readme_mentions_user_tournament():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "user-tournament" in readme


def test_build_report_header():
    build_report = (REPO_ROOT / "BUILD-REPORT.md").read_text()
    assert "v0.62.0" in build_report


def test_build_report_versioned_copy_exists():
    versioned = REPO_ROOT / "BUILD-REPORT-v0.62.0.md"
    assert versioned.exists()
    content = versioned.read_text()
    assert "v0.62.0" in content
