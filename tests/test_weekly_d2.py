"""Tests for `agentkit weekly` CLI command (D2)."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute(
        """CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            project TEXT NOT NULL,
            tool TEXT NOT NULL,
            score REAL NOT NULL,
            details TEXT,
            label TEXT,
            findings TEXT
        )"""
    )
    conn.execute("CREATE TABLE IF NOT EXISTS label_aliases (label TEXT, alias TEXT)")
    conn.commit()
    return conn


def _insert_run(
    conn: sqlite3.Connection,
    project: str,
    score: float,
    days_ago: float = 1.0,
    tool: str = "overall",
) -> None:
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score) VALUES (?, ?, ?, ?)",
        (ts, project, tool, score),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_weekly_help():
    result = runner.invoke(app, ["weekly", "--help"])
    assert result.exit_code == 0
    assert "weekly" in result.output.lower() or "digest" in result.output.lower()


def test_weekly_empty_db():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        _make_db(db_path)
        result = runner.invoke(app, ["weekly", "--db", str(db_path)])
        assert result.exit_code == 0


def test_weekly_json_output():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "proj1", 70.0, days_ago=2)
        _insert_run(conn, "proj1", 75.0, days_ago=1)
        result = runner.invoke(app, ["weekly", "--json", "--db", str(db_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "period_start" in data
        assert "per_project" in data
        assert data["projects_tracked"] == 1


def test_weekly_json_has_tweet():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "repo", 65.0, days_ago=1)
        result = runner.invoke(app, ["weekly", "--json", "--db", str(db_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "tweet_text" in data
        assert len(data["tweet_text"]) <= 280


def test_weekly_tweet_only():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "repo", 65.0, days_ago=1)
        result = runner.invoke(app, ["weekly", "--tweet-only", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "agentkit weekly" in result.output
        assert len(result.output.strip()) <= 300


def test_weekly_quiet():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "repo", 65.0, days_ago=1)
        result = runner.invoke(app, ["weekly", "--quiet", "--db", str(db_path)])
        assert result.exit_code == 0
        # quiet mode should produce no rich output
        assert result.output.strip() == ""


def test_weekly_output_html():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "myrepo", 70.0, days_ago=1)
        out_path = Path(tmp) / "report.html"
        result = runner.invoke(
            app, ["weekly", "--output", str(out_path), "--db", str(db_path)]
        )
        assert result.exit_code == 0
        assert out_path.exists()
        html = out_path.read_text()
        assert "<html" in html.lower() or "<!DOCTYPE" in html.lower()


def test_weekly_project_filter():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "wanted", 70.0, days_ago=1)
        _insert_run(conn, "unwanted", 50.0, days_ago=1)
        result = runner.invoke(
            app,
            ["weekly", "--json", "--project", "wanted", "--db", str(db_path)],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["projects_tracked"] == 1
        assert data["per_project"][0]["name"] == "wanted"


def test_weekly_days_option():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "old", 60.0, days_ago=20)  # outside 7-day window
        _insert_run(conn, "new", 70.0, days_ago=3)
        result = runner.invoke(
            app, ["weekly", "--json", "--days", "7", "--db", str(db_path)]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Only "new" should have runs in period
        projects_with_runs = [p for p in data["per_project"] if p["runs"] > 0]
        names = [p["name"] for p in projects_with_runs]
        assert "new" in names


def test_weekly_rich_table_shows():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "visible_project", 80.0, days_ago=2)
        _insert_run(conn, "visible_project", 90.0, days_ago=1)
        result = runner.invoke(app, ["weekly", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "visible_project" in result.output


def test_weekly_command_registered():
    """Verify 'weekly' is a registered subcommand."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "weekly" in result.output
