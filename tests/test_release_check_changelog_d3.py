"""Tests for D3: agentkit release-check --changelog integration."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.changelog_engine import CommitSummary

runner = CliRunner()


def _fake_release_result(passed=True):
    from agentkit_cli.release_check import ReleaseCheckResult, CheckResult
    checks = [CheckResult(name="tests", status="pass", detail="1 passed", hint="")]
    return ReleaseCheckResult(
        path="/fake",
        package="agentkit-cli",
        version="0.93.0",
        registry="pypi",
        checks=checks,
        verdict="SHIPPED" if passed else "BUILT",
    )


def test_release_check_changelog_flag_appends_content():
    fake_result = _fake_release_result()
    fake_commits = [CommitSummary(hash="aaa", message="feat: add thing", files_changed=1, author="dev", ts="2026-01-01T00:00:00Z")]
    with patch("agentkit_cli.commands.release_check_cmd.run_release_check", return_value=fake_result):
        with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_git", return_value=fake_commits):
            with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None):
                result = runner.invoke(app, ["release-check", "--changelog"])
    assert result.exit_code == 0
    assert "Changelog" in result.output or "add thing" in result.output


def test_release_check_without_changelog_no_preview():
    fake_result = _fake_release_result()
    with patch("agentkit_cli.commands.release_check_cmd.run_release_check", return_value=fake_result):
        result = runner.invoke(app, ["release-check"])
    assert result.exit_code == 0
    assert "pip install" not in result.output


def test_release_check_changelog_json_has_key():
    fake_result = _fake_release_result()
    with patch("agentkit_cli.commands.release_check_cmd.run_release_check", return_value=fake_result):
        with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_git", return_value=[]):
            with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None):
                result = runner.invoke(app, ["release-check", "--changelog", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "changelog_preview" in data


def test_release_check_changelog_json_without_flag_no_key():
    fake_result = _fake_release_result()
    with patch("agentkit_cli.commands.release_check_cmd.run_release_check", return_value=fake_result):
        result = runner.invoke(app, ["release-check", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "changelog_preview" not in data


def test_release_check_changelog_empty_commits():
    fake_result = _fake_release_result()
    with patch("agentkit_cli.commands.release_check_cmd.run_release_check", return_value=fake_result):
        with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_git", return_value=[]):
            with patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None):
                result = runner.invoke(app, ["release-check", "--changelog"])
    assert result.exit_code == 0
