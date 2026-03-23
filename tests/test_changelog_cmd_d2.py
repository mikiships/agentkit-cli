"""Tests for D2: agentkit changelog CLI command."""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.changelog_engine import CommitSummary, ScoreDelta

runner = CliRunner()


def _fake_commits():
    return [
        CommitSummary(hash="aaa", message="feat: add changelog", files_changed=2, author="dev", ts="2026-01-01T00:00:00Z"),
        CommitSummary(hash="bbb", message="fix: handle edge case", files_changed=1, author="dev", ts="2026-01-01T00:00:00Z"),
        CommitSummary(hash="ccc", message="chore: bump deps", files_changed=1, author="dev", ts="2026-01-01T00:00:00Z"),
    ]


def _patch_engine(commits=None, delta=None):
    if commits is None:
        commits = _fake_commits()
    return (
        patch("agentkit_cli.changelog_engine.ChangelogEngine.from_git", return_value=commits),
        patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=delta),
    )


def test_changelog_default_markdown():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog"])
    assert result.exit_code == 0
    assert "Features" in result.output or "feat" in result.output.lower() or "add changelog" in result.output


def test_changelog_format_release():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--format", "release", "--version", "v0.93.0"])
    assert result.exit_code == 0
    assert "pip install" in result.output
    assert "v0.93.0" in result.output


def test_changelog_format_json():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "commits" in data
    assert isinstance(data["commits"], list)


def test_changelog_github_release_alias():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--github-release", "--version", "v0.93.0"])
    assert result.exit_code == 0
    assert "pip install" in result.output


def test_changelog_no_chore_excludes_chore():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--no-chore"])
    assert result.exit_code == 0
    assert "bump deps" not in result.output


def test_changelog_with_score_delta():
    delta = ScoreDelta(before=70.0, after=82.0, delta=12.0, project="test")
    p1, p2 = _patch_engine(delta=delta)
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--version", "v0.93.0"])
    assert result.exit_code == 0
    assert "70" in result.output
    assert "82" in result.output


def test_changelog_no_score_delta_flag():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--no-score-delta"])
    assert result.exit_code == 0
    # No score delta line expected


def test_changelog_output_to_file(tmp_path):
    out = tmp_path / "CHANGELOG_OUT.md"
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "feat" in out.read_text().lower() or "Changes" in out.read_text() or "add changelog" in out.read_text()


def test_changelog_empty_commits():
    p1 = patch("agentkit_cli.changelog_engine.ChangelogEngine.from_git", return_value=[])
    p2 = patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None)
    with p1, p2:
        result = runner.invoke(app, ["changelog"])
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_changelog_since_passed_to_engine():
    captured = {}
    def fake_from_git(since, path="."):
        captured["since"] = since
        return []
    p1 = patch("agentkit_cli.changelog_engine.ChangelogEngine.from_git", side_effect=fake_from_git)
    p2 = patch("agentkit_cli.changelog_engine.ChangelogEngine.from_history", return_value=None)
    with p1, p2:
        runner.invoke(app, ["changelog", "--since", "v0.92.0"])
    assert captured.get("since") == "v0.92.0"


def test_changelog_version_in_header():
    p1, p2 = _patch_engine()
    with p1, p2:
        result = runner.invoke(app, ["changelog", "--version", "v0.93.0"])
    assert "v0.93.0" in result.output
