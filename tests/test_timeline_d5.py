"""Tests for D5: docs, CHANGELOG, version bump, BUILD-REPORT."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent


def test_version_in_init():
    from agentkit_cli import __version__
    assert __version__ == "0.54.0"


def test_version_in_pyproject():
    pyproject = (REPO / "pyproject.toml").read_text()
    assert 'version = "0.54.0"' in pyproject


def test_changelog_has_044():
    changelog = (REPO / "CHANGELOG.md").read_text()
    assert "0.45.0" in changelog


def test_changelog_mentions_timeline():
    changelog = (REPO / "CHANGELOG.md").read_text()
    assert "timeline" in changelog.lower()


def test_readme_has_timeline_section():
    readme = (REPO / "README.md").read_text()
    assert "timeline" in readme.lower()


def test_readme_timeline_command_listed():
    readme = (REPO / "README.md").read_text()
    assert "agentkit timeline" in readme


def test_build_report_exists():
    report = REPO / "BUILD-REPORT.md"
    assert report.exists(), "BUILD-REPORT.md must exist"


def test_build_report_has_d1():
    report = (REPO / "BUILD-REPORT.md").read_text()
    assert "D1" in report


def test_build_report_has_d2():
    report = (REPO / "BUILD-REPORT.md").read_text()
    assert "D2" in report


def test_build_report_has_d3():
    report = (REPO / "BUILD-REPORT.md").read_text()
    assert "D3" in report


def test_build_report_has_d4():
    report = (REPO / "BUILD-REPORT.md").read_text()
    assert "D4" in report


def test_build_report_has_d5():
    report = (REPO / "BUILD-REPORT.md").read_text()
    assert "D5" in report
