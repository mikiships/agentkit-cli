"""Tests for D5: Docs, CHANGELOG, version bump, BUILD-REPORT."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------

class TestVersionConsistency:
    def test_init_version(self):
        from agentkit_cli import __version__
        assert __version__ == "0.56.0"

    def test_pyproject_version(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        assert 'version = "0.56.0"' in pyproject

    def test_versions_match(self):
        from agentkit_cli import __version__
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        # Extract version from pyproject
        m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        assert m, "Could not find version in pyproject.toml"
        assert __version__ == m.group(1)


# ---------------------------------------------------------------------------
# CHANGELOG
# ---------------------------------------------------------------------------

class TestChangelog:
    def test_changelog_exists(self):
        assert (REPO_ROOT / "CHANGELOG.md").exists()

    def test_has_v056_entry(self):
        content = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "0.56.0" in content

    def test_mentions_daily_leaderboard(self):
        content = (REPO_ROOT / "CHANGELOG.md").read_text()
        lower = content.lower()
        assert "daily" in lower or "leaderboard" in lower


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------

class TestReadme:
    def test_readme_exists(self):
        assert (REPO_ROOT / "README.md").exists()

    def test_readme_mentions_daily(self):
        content = (REPO_ROOT / "README.md").read_text()
        assert "daily" in content.lower()

    def test_readme_has_example_command(self):
        content = (REPO_ROOT / "README.md").read_text()
        assert "agentkit daily" in content


# ---------------------------------------------------------------------------
# BUILD-REPORT
# ---------------------------------------------------------------------------

class TestBuildReport:
    def test_build_report_exists(self):
        assert (REPO_ROOT / "BUILD-REPORT.md").exists()

    def test_build_report_mentions_test_count(self):
        content = (REPO_ROOT / "BUILD-REPORT.md").read_text()
        # Should contain a number ≥ 2623
        numbers = [int(m) for m in re.findall(r"\d{4,}", content)]
        assert any(n >= 2623 for n in numbers), "BUILD-REPORT.md should have verified test count ≥ 2623"

    def test_build_report_has_deliverables(self):
        content = (REPO_ROOT / "BUILD-REPORT.md").read_text()
        assert "D1" in content
        assert "D2" in content
        assert "D3" in content
        assert "D4" in content
        assert "D5" in content

    def test_build_report_has_version(self):
        content = (REPO_ROOT / "BUILD-REPORT.md").read_text()
        assert "0.56.0" in content
