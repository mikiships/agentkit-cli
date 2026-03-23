"""Tests for D1: ChangelogEngine core."""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agentkit_cli.changelog_engine import (
    ChangelogEngine,
    CommitSummary,
    ScoreDelta,
    _detect_prefix,
    _clean_message,
)


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------

def _make_commit(msg: str, hash_: str = "abc1234", author: str = "Test") -> CommitSummary:
    return CommitSummary(hash=hash_, message=msg, files_changed=1, author=author, ts="2026-01-01T00:00:00Z")


# ---------------------------------------------------------------------------
# D1-T01 to D1-T12
# ---------------------------------------------------------------------------

def test_detect_prefix_feat():
    assert _detect_prefix("feat: add changelog") == "feat"


def test_detect_prefix_fix():
    assert _detect_prefix("fix(core): correct offset calc") == "fix"


def test_detect_prefix_unknown_returns_other():
    assert _detect_prefix("random commit message") == "other"


def test_clean_message_strips_prefix():
    assert _clean_message("feat: add changelog") == "add changelog"


def test_clean_message_scoped():
    assert _clean_message("fix(api): handle 404") == "handle 404"


def test_clean_message_no_prefix():
    assert _clean_message("just some commit") == "just some commit"


def test_render_markdown_empty_commits():
    out = ChangelogEngine.render_markdown([], None, "v0.93.0")
    assert "v0.93.0" in out
    assert "No changes" in out


def test_render_markdown_groups_by_prefix():
    commits = [
        _make_commit("feat: new thing"),
        _make_commit("fix: broken thing"),
    ]
    out = ChangelogEngine.render_markdown(commits, None, "v0.93.0")
    assert "Features" in out
    assert "Bug Fixes" in out


def test_render_markdown_score_delta():
    delta = ScoreDelta(before=70.0, after=85.0, delta=15.0, project="test")
    out = ChangelogEngine.render_markdown([], delta, "v0.93.0")
    assert "70" in out
    assert "85" in out
    assert "+15" in out


def test_render_release_excludes_chore():
    commits = [
        _make_commit("feat: add thing"),
        _make_commit("chore: bump deps"),
    ]
    out = ChangelogEngine.render_release(commits, None, "v0.93.0")
    assert "add thing" in out
    assert "bump deps" not in out


def test_render_release_includes_pip_install():
    out = ChangelogEngine.render_release([], None, "v0.94.0")
    assert "pip install" in out
    assert "0.94.0" in out


def test_render_release_no_version_no_pip():
    out = ChangelogEngine.render_release([], None, version=None)
    assert "pip install" not in out


def test_render_markdown_no_version_header():
    out = ChangelogEngine.render_markdown([], None, None)
    assert "Unreleased" in out


def test_from_git_no_git(tmp_path):
    """Returns empty list when git is not available."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = ChangelogEngine.from_git(None, str(tmp_path))
    assert result == []


def test_from_git_git_error(tmp_path):
    mock = MagicMock()
    mock.returncode = 1
    mock.stdout = ""
    with patch("subprocess.run", return_value=mock):
        result = ChangelogEngine.from_git(None, str(tmp_path))
    assert result == []


def test_from_history_db_missing():
    """Returns None when db_path points to non-existent file."""
    result = ChangelogEngine.from_history(project="test", since_days=7, db_path="/nonexistent/history.db")
    assert result is None


def test_from_history_empty_db(tmp_path):
    db_path = tmp_path / "history.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, project TEXT NOT NULL, tool TEXT NOT NULL,
            score REAL NOT NULL, details TEXT, label TEXT, findings TEXT, campaign_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project);
        CREATE INDEX IF NOT EXISTS idx_runs_ts ON runs(ts DESC);
    """)
    conn.close()
    result = ChangelogEngine.from_history("myproject", since_days=7, db_path=str(db_path))
    assert result is None


def test_from_history_returns_delta(tmp_path):
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(tmp_path / "history.db")
    # Insert two "overall" runs separated in time
    db.record_run("myproject", "overall", 65.0)
    # Simulate an older entry by manually inserting
    conn = sqlite3.connect(str(tmp_path / "history.db"))
    old_ts = "2020-01-01T00:00:00+00:00"
    conn.execute("INSERT INTO runs (ts, project, tool, score) VALUES (?, ?, ?, ?)", (old_ts, "myproject", "overall", 50.0))
    conn.commit()
    conn.close()
    result = ChangelogEngine.from_history("myproject", since_days=7, db_path=str(tmp_path / "history.db"))
    assert result is not None
    assert result.after == 65.0
    assert result.before == 50.0
    assert result.delta == 15.0


def test_write_github_step_summary_no_env():
    env = os.environ.copy()
    env.pop("GITHUB_STEP_SUMMARY", None)
    with patch.dict(os.environ, env, clear=True):
        result = ChangelogEngine.write_github_step_summary("hello")
    assert result is False


def test_write_github_step_summary_with_env(tmp_path):
    summary_file = tmp_path / "summary.md"
    with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_file)}):
        result = ChangelogEngine.write_github_step_summary("## Changelog\n- foo")
    assert result is True
    assert "foo" in summary_file.read_text()
