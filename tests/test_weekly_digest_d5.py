"""D5 tests: version, CHANGELOG, BUILD-REPORT — ≥5 tests."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


class TestVersionBump:
    def test_version_is_current(self):
        import agentkit_cli
        assert agentkit_cli.__version__ >= "0.94.1"

    def test_pyproject_version(self):
        import re
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        m = re.search(r'version = "(\d+\.\d+\.\d+)"', pyproject)
        assert m is not None
        assert m.group(1) >= "0.94.1"

    def test_changelog_entry(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "0.94" in changelog

    def test_changelog_weekly_digest_mentioned(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "weekly-digest" in changelog or "weekly digest" in changelog.lower()

    def test_build_report_exists(self):
        build_report = (REPO_ROOT / "BUILD-REPORT.md").read_text()
        assert len(build_report) > 100
