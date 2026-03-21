"""Tests for agentkit hot D5 — docs, CHANGELOG, version, BUILD-REPORT."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent


def test_version_is_0_81_0():
    from agentkit_cli import __version__
    assert __version__ == "0.81.0"


def test_pyproject_version_is_0_81_0():
    content = (ROOT / "pyproject.toml").read_text()
    assert 'version = "0.81.0"' in content


def test_changelog_has_0_81_0():
    changelog = (ROOT / "CHANGELOG.md").read_text()
    assert "0.81.0" in changelog


def test_changelog_mentions_hot():
    changelog = (ROOT / "CHANGELOG.md").read_text()
    assert "hot" in changelog.lower()


def test_readme_mentions_hot():
    readme = (ROOT / "README.md").read_text()
    assert "agentkit hot" in readme


def test_readme_has_trending_repos_section():
    readme = (ROOT / "README.md").read_text()
    assert "Trending Repos" in readme


def test_build_report_exists():
    assert (ROOT / "BUILD-REPORT.md").exists(), "BUILD-REPORT.md not found"


def test_build_report_mentions_hot():
    content = (ROOT / "BUILD-REPORT.md").read_text()
    assert "hot" in content.lower()


def test_build_report_has_version():
    content = (ROOT / "BUILD-REPORT.md").read_text()
    assert "0.81.0" in content


def test_post_hot_script_exists():
    assert (ROOT / "scripts" / "post-hot.sh").exists()


def test_hot_cmd_module_exists():
    assert (ROOT / "agentkit_cli" / "commands" / "hot_cmd.py").exists()


def test_hot_module_exists():
    assert (ROOT / "agentkit_cli" / "hot.py").exists()
