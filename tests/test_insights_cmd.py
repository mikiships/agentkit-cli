"""CLI tests for `agentkit insights` command."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "history.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            project TEXT NOT NULL,
            tool TEXT NOT NULL,
            score REAL NOT NULL,
            details TEXT,
            findings TEXT,
            label TEXT
        )
    """)
    conn.commit()
    conn.close()
    return db_path


def _insert(db_path: Path, project: str, score: float, ts: str, tool: str = "overall", findings=None):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score, findings) VALUES (?, ?, ?, ?, ?)",
        (ts, project, tool, score, json.dumps(findings) if findings is not None else None),
    )
    conn.commit()
    conn.close()


def _populated_db(tmp_path: Path) -> Path:
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-a", 90.0, "2026-01-01T00:00:00+00:00", findings=["issue-x"])
    _insert(db_path, "repo-b", 40.0, "2026-01-02T00:00:00+00:00", findings=["issue-x", "issue-y"])
    _insert(db_path, "repo-b", 65.0, "2026-01-03T00:00:00+00:00")
    _insert(db_path, "repo-c", 75.0, "2026-01-04T00:00:00+00:00")
    return db_path


# ---------------------------------------------------------------------------
# Basic invocation
# ---------------------------------------------------------------------------

def test_insights_no_db_shows_empty_message(tmp_path):
    result = runner.invoke(app, ["insights", "--db", str(tmp_path / "none.db")])
    assert result.exit_code == 0
    assert "No history found" in result.output or result.output.strip() == "" or "No history" in result.output


def test_insights_empty_db_shows_empty_message(tmp_path):
    db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_insights_default_shows_portfolio(tmp_path):
    db_path = _populated_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "Portfolio Health" in result.output


def test_insights_shows_avg_score(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-a", 80.0, "2026-01-01T00:00:00+00:00")
    _insert(db_path, "repo-b", 60.0, "2026-01-02T00:00:00+00:00")
    result = runner.invoke(app, ["insights", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "70.0" in result.output


# ---------------------------------------------------------------------------
# --common-findings
# ---------------------------------------------------------------------------

def test_insights_common_findings_flag(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-a", 80.0, "2026-01-01T00:00:00+00:00", findings=["shared-issue"])
    _insert(db_path, "repo-b", 75.0, "2026-01-02T00:00:00+00:00", findings=["shared-issue"])
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--common-findings"])
    assert result.exit_code == 0
    assert "shared-issue" in result.output


def test_insights_common_findings_empty(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-a", 80.0, "2026-01-01T00:00:00+00:00")
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--common-findings"])
    assert result.exit_code == 0
    assert "No common findings" in result.output


# ---------------------------------------------------------------------------
# --outliers
# ---------------------------------------------------------------------------

def test_insights_outliers_flag(tmp_path):
    db_path = _populated_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--outliers"])
    assert result.exit_code == 0
    # repo-b has the lowest score; should appear
    assert "Outlier" in result.output or "repo-b" in result.output


def test_insights_outliers_empty_db(tmp_path):
    db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--outliers"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# --trending
# ---------------------------------------------------------------------------

def test_insights_trending_flag_shows_movement(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-x", 40.0, "2026-01-01T00:00:00+00:00")
    _insert(db_path, "repo-x", 80.0, "2026-01-02T00:00:00+00:00")
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--trending"])
    assert result.exit_code == 0
    assert "repo-x" in result.output


def test_insights_trending_no_movement(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-stable", 75.0, "2026-01-01T00:00:00+00:00")
    _insert(db_path, "repo-stable", 76.0, "2026-01-02T00:00:00+00:00")
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--trending"])
    assert result.exit_code == 0
    assert "No significant" in result.output


# ---------------------------------------------------------------------------
# --all
# ---------------------------------------------------------------------------

def test_insights_all_shows_all_sections(tmp_path):
    db_path = _populated_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--all"])
    assert result.exit_code == 0
    assert "Portfolio Health" in result.output
    # At least one other section heading should appear
    assert any(h in result.output for h in ["Finding", "Outlier", "Trending", "No common", "No outlier", "No significant"])


# ---------------------------------------------------------------------------
# --json
# ---------------------------------------------------------------------------

def test_insights_json_output_structure(tmp_path):
    db_path = _populated_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "portfolio_summary" in data
    assert "common_findings" in data
    assert "outliers" in data
    assert "trending" in data


def test_insights_json_empty_db(tmp_path):
    db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["portfolio_summary"]["total_runs"] == 0
    assert data["common_findings"] == []
    assert data["outliers"] == []
    assert data["trending"] == []


def test_insights_json_portfolio_fields(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "repo-a", 85.0, "2026-01-01T00:00:00+00:00")
    result = runner.invoke(app, ["insights", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    ps = data["portfolio_summary"]
    assert "avg_score" in ps
    assert "total_runs" in ps
    assert "unique_repos" in ps
    assert "best_repo" in ps
    assert "worst_repo" in ps
    assert "top_issue" in ps


# ---------------------------------------------------------------------------
# --db path override
# ---------------------------------------------------------------------------

def test_insights_db_flag_overrides_path(tmp_path):
    db_path = _make_db(tmp_path)
    _insert(db_path, "custom-repo", 77.0, "2026-01-01T00:00:00+00:00")
    result = runner.invoke(app, ["insights", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "custom-repo" in result.output or "77" in result.output or "Portfolio" in result.output
