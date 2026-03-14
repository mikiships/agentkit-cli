"""Tests for agentkit history command (history_cmd.py)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.history import HistoryDB

runner = CliRunner()


def _make_db(tmp_path: Path) -> tuple[HistoryDB, Path]:
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path=db_path)
    return db, db_path


def _populate(db: HistoryDB, n: int = 5) -> None:
    for i in range(n):
        db.record_run("testproj", "agentlint", float(60 + i * 5))
    db.record_run("testproj", "overall", 80.0)
    db.record_run("testproj", "coderace", 70.0)


# ---------------------------------------------------------------------------
# Basic invocation
# ---------------------------------------------------------------------------

def test_history_no_history(tmp_path):
    _, db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["history", "--project", "testproj", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_history_shows_table(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, ["history", "--project", "testproj", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "testproj" in result.output


def test_history_limit(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db, n=10)
    result = runner.invoke(app, ["history", "--project", "testproj", "--db", str(db_path), "--limit", "3"])
    assert result.exit_code == 0


def test_history_tool_filter(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, [
        "history", "--project", "testproj", "--db", str(db_path), "--tool", "overall"
    ])
    assert result.exit_code == 0
    assert "overall" in result.output


# ---------------------------------------------------------------------------
# --json
# ---------------------------------------------------------------------------

def test_history_json_output(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, ["history", "--project", "testproj", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "runs" in data
    assert "sparkline" in data
    assert isinstance(data["runs"], list)


def test_history_json_empty(tmp_path):
    _, db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["history", "--project", "empty", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["runs"] == []


# ---------------------------------------------------------------------------
# --graph
# ---------------------------------------------------------------------------

def test_history_graph(tmp_path):
    db, db_path = _make_db(tmp_path)
    for score in [60.0, 70.0, 75.0, 80.0, 85.0]:
        db.record_run("testproj", "overall", score)
    result = runner.invoke(app, ["history", "--project", "testproj", "--db", str(db_path), "--graph"])
    assert result.exit_code == 0
    # Should include sparkline chars
    spark_chars = set("▁▂▃▄▅▆▇█")
    assert any(c in result.output for c in spark_chars)


def test_history_graph_json(tmp_path):
    db, db_path = _make_db(tmp_path)
    db.record_run("testproj", "overall", 80.0)
    result = runner.invoke(app, [
        "history", "--project", "testproj", "--db", str(db_path), "--graph", "--json"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "sparkline" in data
    assert "runs" in data


# ---------------------------------------------------------------------------
# --clear
# ---------------------------------------------------------------------------

def test_history_clear_with_yes(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, [
        "history", "--project", "testproj", "--db", str(db_path), "--clear", "--yes"
    ])
    assert result.exit_code == 0
    assert "Deleted" in result.output
    # Confirm it's gone
    rows = db.get_history(project="testproj")
    assert rows == []


def test_history_clear_prompt_confirm(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    # Simulate user confirming the prompt
    result = runner.invoke(app, [
        "history", "--project", "testproj", "--db", str(db_path), "--clear"
    ], input="y\n")
    assert result.exit_code == 0
    assert "Deleted" in result.output


def test_history_clear_prompt_abort(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, [
        "history", "--project", "testproj", "--db", str(db_path), "--clear"
    ], input="n\n")
    assert result.exit_code == 0
    assert "Aborted" in result.output
    # Records should still be there
    rows = db.get_history(project="testproj")
    assert len(rows) > 0


# ---------------------------------------------------------------------------
# --all-projects
# ---------------------------------------------------------------------------

def test_history_all_projects_table(tmp_path):
    db, db_path = _make_db(tmp_path)
    db.record_run("projA", "overall", 80.0)
    db.record_run("projB", "overall", 70.0)
    result = runner.invoke(app, ["history", "--db", str(db_path), "--all-projects"])
    assert result.exit_code == 0
    assert "projA" in result.output
    assert "projB" in result.output


def test_history_all_projects_json(tmp_path):
    db, db_path = _make_db(tmp_path)
    db.record_run("projA", "overall", 80.0)
    result = runner.invoke(app, ["history", "--db", str(db_path), "--all-projects", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert any(row["project"] == "projA" for row in data)


def test_history_all_projects_empty(tmp_path):
    _, db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["history", "--db", str(db_path), "--all-projects"])
    assert result.exit_code == 0
    assert "No history" in result.output


# ---------------------------------------------------------------------------
# sparkline helper
# ---------------------------------------------------------------------------

def test_sparkline_empty():
    from agentkit_cli.commands.history_cmd import _sparkline
    assert _sparkline([]) == ""


def test_sparkline_single():
    from agentkit_cli.commands.history_cmd import _sparkline
    result = _sparkline([80.0])
    assert len(result) == 1


def test_sparkline_range():
    from agentkit_cli.commands.history_cmd import _sparkline
    scores = [0.0, 25.0, 50.0, 75.0, 100.0]
    result = _sparkline(scores)
    assert len(result) == 5
    # ascending scores → ascending chars
    assert result[0] <= result[-1]
