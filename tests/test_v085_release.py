"""Version assertion tests for v0.85.0+ release (forward-compatible)."""
from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from agentkit_cli import __version__
from agentkit_cli.main import app

runner = CliRunner()


def _version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in v.split("."))


class TestV085Release:
    def test_version_starts_with_085(self):
        # Accept any version >= 0.85.0 (forward-compatible)
        assert _version_tuple(__version__) >= (0, 85, 0), f"Expected version >= 0.85.0, got {__version__}"

    def test_version_cli_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_frameworks_command_exists(self):
        result = runner.invoke(app, ["frameworks", "--help"])
        assert result.exit_code == 0

    def test_frameworks_json_version_field(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["version"] == __version__

    def test_pyproject_version(self):
        from pathlib import Path
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        content = pyproject.read_text()
        assert f'version = "{__version__}"' in content

    def test_frameworks_command_in_help(self):
        result = runner.invoke(app, ["--help"])
        assert "frameworks" in result.output
