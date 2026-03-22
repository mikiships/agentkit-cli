"""D5 release tests — version bump, changelog, README, CLI smoke tests."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


class TestVersionBump:
    def test_init_version_is_084(self):
        from agentkit_cli import __version__
        assert __version__.startswith("0.86.")

    def test_pyproject_version_is_084(self):
        from agentkit_cli import __version__
        content = (REPO_ROOT / "pyproject.toml").read_text()
        assert __version__ in content

    def test_init_and_pyproject_versions_match(self):
        from agentkit_cli import __version__
        content = (REPO_ROOT / "pyproject.toml").read_text()
        assert __version__ in content


class TestCliSmokeTests:
    def test_populate_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["populate", "--help"])
        assert result.exit_code == 0
        assert "topic" in result.output.lower()

    def test_site_live_help_no_not_implemented(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["site", "--help"])
        assert result.exit_code == 0
        assert "not yet implemented" not in result.output

    def test_site_deploy_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["site", "--help"])
        assert result.exit_code == 0
        assert "deploy" in result.output.lower()

    def test_version_flag(self):
        from agentkit_cli import __version__
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        assert __version__ in result.output


class TestReadmeAndChangelog:
    def test_readme_has_populate_section(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "populate" in readme.lower()

    def test_changelog_has_084_entry(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "0.84" in changelog
