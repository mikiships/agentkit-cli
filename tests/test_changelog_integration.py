"""Integration test: run agentkit changelog against the agentkit-cli repo itself."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.changelog_engine import ChangelogEngine

runner = CliRunner()
REPO_ROOT = Path(__file__).parent.parent


def test_changelog_against_real_repo():
    """Run changelog against the actual repo. Uses real git, mock DB."""
    with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None):
        result = runner.invoke(app, ["changelog", "--version", "v0.93.0"])
    assert result.exit_code == 0
    assert "v0.93.0" in result.output


def test_changelog_engine_from_git_real_repo():
    """from_git against the real repo returns a list (may be empty if no recent commits)."""
    commits = ChangelogEngine.from_git(since="HEAD~5", path=str(REPO_ROOT))
    assert isinstance(commits, list)


def test_changelog_json_format_valid():
    with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None):
        result = runner.invoke(app, ["changelog", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "commits" in data
    assert "version" in data
    assert "score_delta" in data
