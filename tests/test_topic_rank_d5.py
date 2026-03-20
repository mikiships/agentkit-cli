"""D5 tests — version bump, CHANGELOG, docs."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_68_0():
    from agentkit_cli import __version__
    assert __version__ == "0.68.0"


def test_pyproject_version_is_0_68_0():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.68.0"' in pyproject


def test_changelog_has_0_68_0_entry():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.68.0" in changelog


def test_changelog_mentions_topic_command():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    idx = changelog.find("0.68.0")
    assert idx != -1
    section = changelog[idx:idx + 1000]
    assert "topic" in section.lower()


def test_readme_has_topic_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "agentkit topic" in readme


def test_build_report_v068_exists():
    report = REPO_ROOT / "BUILD-REPORT-v0.68.0.md"
    assert report.exists(), "BUILD-REPORT-v0.68.0.md not found"


def test_build_report_v068_mentions_topic():
    report = (REPO_ROOT / "BUILD-REPORT-v0.68.0.md").read_text()
    assert "topic" in report.lower()
