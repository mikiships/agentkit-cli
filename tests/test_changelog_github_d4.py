"""Tests for D4: GITHUB_STEP_SUMMARY support and GitHub Release creation."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agentkit_cli.changelog_engine import ChangelogEngine, CommitSummary


def test_write_step_summary_no_env():
    env_backup = os.environ.copy()
    env_backup.pop("GITHUB_STEP_SUMMARY", None)
    with patch.dict(os.environ, env_backup, clear=True):
        result = ChangelogEngine.write_github_step_summary("content")
    assert result is False


def test_write_step_summary_writes_to_file(tmp_path):
    summary_path = tmp_path / "step_summary.md"
    with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}):
        result = ChangelogEngine.write_github_step_summary("## My Changelog\n- feat: foo")
    assert result is True
    text = summary_path.read_text()
    assert "My Changelog" in text
    assert "feat: foo" in text


def test_write_step_summary_appends(tmp_path):
    summary_path = tmp_path / "step_summary.md"
    summary_path.write_text("existing content\n")
    with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}):
        ChangelogEngine.write_github_step_summary("new content")
    text = summary_path.read_text()
    assert "existing content" in text
    assert "new content" in text


def test_render_release_triggers_step_summary_when_env_set(tmp_path):
    summary_path = tmp_path / "summary.md"
    commits = [CommitSummary(hash="abc", message="feat: new thing", files_changed=1, author="dev", ts="2026-01-01T00:00:00Z")]
    with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}):
        # Simulate the cmd calling write_github_step_summary after render_release
        content = ChangelogEngine.render_release(commits, None, "v0.93.0")
        ChangelogEngine.write_github_step_summary(content)
    text = summary_path.read_text()
    assert "new thing" in text


def test_create_github_release_success():
    mock = MagicMock()
    mock.returncode = 0
    with patch("subprocess.run", return_value=mock) as mock_run:
        result = ChangelogEngine.create_github_release(version="v0.93.0", body="## Notes")
    assert result is True
    args = mock_run.call_args[0][0]
    assert "gh" in args
    assert "release" in args
    assert "create" in args


def test_create_github_release_failure():
    mock = MagicMock()
    mock.returncode = 1
    with patch("subprocess.run", return_value=mock):
        result = ChangelogEngine.create_github_release(version="v0.93.0", body="## Notes")
    assert result is False


def test_create_github_release_no_gh_cli():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = ChangelogEngine.create_github_release(version="v0.93.0", body="## Notes")
    assert result is False


def test_write_step_summary_bad_path():
    with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": "/nonexistent/path/summary.md"}):
        result = ChangelogEngine.write_github_step_summary("content")
    assert result is False
