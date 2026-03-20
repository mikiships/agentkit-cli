"""Tests for D2: agentkit user-badge CLI command (≥12 tests)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _make_scorecard(username="alice", avg_score=78.0, grade="B"):
    sc = MagicMock()
    sc.username = username
    sc.avg_score = avg_score
    sc.grade = grade
    sc.total_repos = 10
    sc.analyzed_repos = 8
    sc.skipped_repos = 2
    sc.context_coverage_pct = 60.0
    sc.top_repos = []
    sc.bottom_repos = []
    sc.all_repos = []
    sc.to_dict.return_value = {
        "username": username,
        "avg_score": avg_score,
        "grade": grade,
    }
    return sc


# ---------------------------------------------------------------------------
# --score fast mode
# ---------------------------------------------------------------------------

def test_user_badge_score_fast_mode():
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "85"])
    assert result.exit_code == 0
    assert "alice" in result.output


def test_user_badge_score_includes_badge_url():
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "85"])
    assert "img.shields.io" in result.output


def test_user_badge_score_json():
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "85", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "badge_url" in data
    assert "badge_markdown" in data


def test_user_badge_score_explicit_grade():
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "85", "--grade", "C"])
    assert result.exit_code == 0
    data_line = result.output
    # Grade C → yellow badge
    assert "C" in data_line


def test_user_badge_score_grade_in_json():
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "85", "--grade", "C", "--json"])
    data = json.loads(result.output)
    assert data["grade"] == "C"


def test_user_badge_invalid_user_exits_1():
    result = runner.invoke(app, ["user-badge", "github:"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# --output flag
# ---------------------------------------------------------------------------

def test_user_badge_output_writes_file(tmp_path):
    out_file = tmp_path / "badge.md"
    result = runner.invoke(app, [
        "user-badge", "github:alice", "--score", "80",
        "--output", str(out_file),
    ])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "img.shields.io" in content


# ---------------------------------------------------------------------------
# --inject flag
# ---------------------------------------------------------------------------

def test_user_badge_inject_no_readme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "80", "--inject"])
    assert result.exit_code == 0
    # Should print instructions since no README.md exists
    assert "img.shields.io" in result.output or "README" in result.output


def test_user_badge_inject_creates_section(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("# My Project\n\nHello world.\n")
    result = runner.invoke(app, ["user-badge", "github:alice", "--score", "80", "--inject"])
    assert result.exit_code == 0
    content = readme.read_text()
    assert "agentkit-user-badge-start" in content


def test_user_badge_dry_run_no_file_change(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    original = "# My Project\n\nHello.\n"
    readme.write_text(original)
    runner.invoke(app, ["user-badge", "github:alice", "--score", "80", "--inject", "--dry-run"])
    assert readme.read_text() == original


# ---------------------------------------------------------------------------
# JSON output structure
# ---------------------------------------------------------------------------

def test_user_badge_json_has_username():
    result = runner.invoke(app, ["user-badge", "github:bob", "--score", "60", "--json"])
    data = json.loads(result.output)
    assert data["username"] == "bob"


def test_user_badge_json_has_score():
    result = runner.invoke(app, ["user-badge", "github:bob", "--score", "60", "--json"])
    data = json.loads(result.output)
    assert data["score"] == 60.0


def test_user_badge_json_has_readme_snippet():
    result = runner.invoke(app, ["user-badge", "github:bob", "--score", "60", "--json"])
    data = json.loads(result.output)
    assert "readme_snippet" in data
