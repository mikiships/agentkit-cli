"""Tests for D5 — version bump, README, CHANGELOG."""
from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).parent.parent


def test_version_is_052():
    from agentkit_cli import __version__
    assert __version__ == "0.58.0"


def test_pyproject_version():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.58.0"' in pyproject


def test_changelog_has_052_entry():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.53.0" in changelog


def test_readme_mentions_search():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "agentkit search" in readme


def test_build_report_exists():
    report = REPO_ROOT / "BUILD-REPORT.md"
    assert report.exists(), "BUILD-REPORT.md must exist"


def test_search_py_exists():
    assert (REPO_ROOT / "agentkit_cli" / "search.py").exists()


def test_search_report_py_exists():
    assert (REPO_ROOT / "agentkit_cli" / "search_report.py").exists()


def test_search_cmd_py_exists():
    assert (REPO_ROOT / "agentkit_cli" / "commands" / "search_cmd.py").exists()
