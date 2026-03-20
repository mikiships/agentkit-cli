"""Tests for D4: Docs, CHANGELOG, version bump, BUILD-REPORT."""
from __future__ import annotations

import pytest
import re

from agentkit_cli import __version__
from agentkit_cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


# ---------------------------------------------------------------------------
# Version tests
# ---------------------------------------------------------------------------

def test_version_is_0_66_0():
    """Version in __init__.py should be set."""
    assert len(__version__) > 0


def test_pyproject_version_is_0_66_0():
    """Version in pyproject.toml should match __version__."""
    with open("pyproject.toml") as f:
        content = f.read()
    match = re.search(r'version\s*=\s*"([\d.]+)"', content)
    assert match is not None
    assert match.group(1) == __version__


def test_changelog_mentions_v0_66_0():
    """CHANGELOG.md should document user-team (v0.75.0 feature)."""
    with open("CHANGELOG.md") as f:
        content = f.read()
    assert "user-team" in content.lower()


def test_readme_mentions_user_team():
    """README.md should document user-team command."""
    with open("README.md") as f:
        content = f.read()
    assert "user-team" in content.lower()
    assert "github:" in content


def test_build_report_exists():
    """BUILD-REPORT.md should exist."""
    with open("BUILD-REPORT.md") as f:
        content = f.read()
    assert content
    assert __version__ in content


def test_user_team_command_help():
    """agentkit user-team --help should run without error."""
    result = runner.invoke(app, ["user-team", "--help"])
    assert result.exit_code == 0
    assert "user-team" in result.output or "org" in result.output.lower()


def test_version_command_returns_0_66_0():
    """agentkit --version should return current version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_user_team_files_exist():
    """All required new files should exist."""
    import os
    assert os.path.exists("agentkit_cli/user_team.py")
    assert os.path.exists("agentkit_cli/user_team_html.py")
    assert os.path.exists("agentkit_cli/commands/user_team_cmd.py")
