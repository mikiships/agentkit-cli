"""D5 tests — version string, docs content, CHANGELOG, and doctor integration."""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


class TestVersionBump:
    def test_version_is_0_47_0(self):
        from agentkit_cli import __version__
        assert __version__ == "0.52.0"

    def test_pyproject_version(self):
        content = (REPO_ROOT / "pyproject.toml").read_text()
        assert 'version = "0.52.0"' in content

    def test_version_cli_output(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])
        assert "0.52.0" in result.output


class TestChangelog:
    def test_changelog_has_0_47_0(self):
        content = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "0.52.0" in content

    def test_changelog_mentions_monitor(self):
        content = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "monitor" in content.lower()


class TestReadme:
    def test_readme_has_monitor_section(self):
        content = (REPO_ROOT / "README.md").read_text()
        assert "agentkit monitor" in content

    def test_readme_has_monitor_add(self):
        content = (REPO_ROOT / "README.md").read_text()
        assert "monitor add" in content

    def test_readme_has_monitor_start(self):
        content = (REPO_ROOT / "README.md").read_text()
        assert "monitor start" in content


class TestMonitorCommand:
    def test_monitor_in_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert "monitor" in result.output

    def test_monitor_subcommands_in_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.commands.monitor import monitor_app
        runner = CliRunner()
        result = runner.invoke(monitor_app, ["--help"])
        for cmd in ("add", "list", "run", "start", "stop", "status", "logs"):
            assert cmd in result.output
