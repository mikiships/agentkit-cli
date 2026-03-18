"""Tests for D5: version bump, docs, CLI help."""
from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from agentkit_cli.main import app
import agentkit_cli

runner = CliRunner()
REPO_ROOT = Path(__file__).parent.parent


def test_version_is_0_44_0():
    assert agentkit_cli.__version__ == "0.45.0"


def test_pyproject_version():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.45.0"' in pyproject


def test_certify_help_output():
    result = runner.invoke(app, ["certify", "--help"])
    assert result.exit_code == 0
    assert "--json" in result.output or "json" in result.output.lower()


def test_certify_in_main_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "certify" in result.output


def test_changelog_has_v0_43_0():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.43.0" in changelog


def test_readme_has_certify_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "agentkit certify" in readme


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.45.0" in result.output
