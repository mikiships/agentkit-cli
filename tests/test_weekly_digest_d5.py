"""D5 tests: version, CHANGELOG, BUILD-REPORT — ≥5 tests."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


class TestVersionBump:
    def test_version_is_0_92_0(self):
        import agentkit_cli
        assert agentkit_cli.__version__ == "0.94.0"

    def test_pyproject_version(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        assert 'version = "0.94.0"' in pyproject

    def test_changelog_entry(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "0.94.0" in changelog

    def test_changelog_weekly_digest_mentioned(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "weekly-digest" in changelog or "weekly digest" in changelog.lower()

    def test_build_report_has_v0_92_0(self):
        build_report = (REPO_ROOT / "BUILD-REPORT.md").read_text()
        assert "0.94.0" in build_report
