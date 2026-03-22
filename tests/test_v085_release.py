"""Version assertion tests for v0.85.0 release (updated for v0.86.0)."""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from agentkit_cli import __version__
from agentkit_cli.main import app

runner = CliRunner()


class TestV085Release:
    def test_version_starts_with_085(self):
        # Updated: now at 0.86.0
        assert __version__.startswith("0.86."), f"Expected version 0.86.x, got {__version__}"

    def test_version_cli_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.86." in result.output

    def test_frameworks_command_exists(self):
        result = runner.invoke(app, ["frameworks", "--help"])
        assert result.exit_code == 0

    def test_frameworks_json_version_field(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["version"].startswith("0.86.")

    def test_pyproject_version(self):
        from pathlib import Path
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert 'version = "0.86.' in content

    def test_frameworks_command_in_help(self):
        result = runner.invoke(app, ["--help"])
        assert "frameworks" in result.output
