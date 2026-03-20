"""Tests for version, changelog, README docs (D5)."""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


class TestVersionBump:
    def test_version_is_0_73_0_in_init(self):
        from agentkit_cli import __version__
        assert __version__ == "0.73.0"

    def test_version_is_0_73_0_in_pyproject(self):
        pyproject = REPO_ROOT / "pyproject.toml"
        content = pyproject.read_text()
        assert 'version = "0.73.0"' in content

    def test_version_cli_output(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        assert "0.73.0" in result.output


class TestChangelog:
    def test_changelog_has_v0_73_0_entry(self):
        changelog = REPO_ROOT / "CHANGELOG.md"
        content = changelog.read_text()
        assert "0.73.0" in content

    def test_changelog_mentions_gist(self):
        changelog = REPO_ROOT / "CHANGELOG.md"
        content = changelog.read_text()
        assert "gist" in content.lower()


class TestReadme:
    def test_readme_mentions_gist_command(self):
        readme = REPO_ROOT / "README.md"
        content = readme.read_text()
        assert "agentkit gist" in content

    def test_readme_mentions_gist_flag(self):
        readme = REPO_ROOT / "README.md"
        content = readme.read_text()
        assert "--gist" in content

    def test_readme_has_gist_usage_example(self):
        readme = REPO_ROOT / "README.md"
        content = readme.read_text()
        assert "GITHUB_TOKEN" in content or "gh auth" in content
