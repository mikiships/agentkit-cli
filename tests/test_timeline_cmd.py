"""Tests for agentkit timeline CLI command — D2 (≥10 tests)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.history import HistoryDB

runner = CliRunner()


def _make_db(tmp_path: Path) -> tuple[HistoryDB, Path]:
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path=db_path)
    return db, db_path


def _populate(db: HistoryDB, project: str = "proj", n: int = 5) -> None:
    for i in range(n):
        db.record_run(project, "overall", float(60 + i * 5))
        db.record_run(project, "agentlint", float(55 + i * 4))


# -------------------------------------------------------------------------
# Basic invocation
# -------------------------------------------------------------------------

def test_timeline_help():
    result = runner.invoke(app, ["timeline", "--help"])
    assert result.exit_code == 0
    assert "timeline" in result.output.lower()


def test_timeline_empty_db(tmp_path):
    _, db_path = _make_db(tmp_path)
    result = runner.invoke(app, ["timeline", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "No history" in result.output


def test_timeline_writes_html(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    out_file = tmp_path / "out.html"
    result = runner.invoke(app, ["timeline", "--db", str(db_path), "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "<html" in content


def test_timeline_project_filter(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db, "alpha", n=3)
    _populate(db, "beta", n=3)
    out_file = tmp_path / "out.html"
    result = runner.invoke(app, [
        "timeline", "--db", str(db_path), "--project", "alpha", "--output", str(out_file)
    ])
    assert result.exit_code == 0
    content = out_file.read_text()
    assert "alpha" in content


def test_timeline_json_output(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, ["timeline", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "stats" in data
    assert "chart" in data


def test_timeline_json_chart_keys(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, ["timeline", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    chart = data["chart"]
    assert "dates" in chart
    assert "scores" in chart
    assert "per_tool" in chart
    assert "projects" in chart


def test_timeline_limit(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db, n=10)
    out_file = tmp_path / "out.html"
    result = runner.invoke(app, [
        "timeline", "--db", str(db_path), "--limit", "5", "--output", str(out_file)
    ])
    assert result.exit_code == 0


def test_timeline_since_filter(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db, n=5)
    result = runner.invoke(app, [
        "timeline", "--db", str(db_path), "--json", "--since", "2099-01-01"
    ])
    # empty after filter → "No history" and exit 0
    assert result.exit_code == 0
    assert "No history" in result.output


def test_timeline_summary_table_shown(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db, "proj", n=3)
    out_file = tmp_path / "out.html"
    result = runner.invoke(app, ["timeline", "--db", str(db_path), "--output", str(out_file)])
    assert result.exit_code == 0
    # Rich table output should mention project name
    assert "proj" in result.output


def test_timeline_multiproject(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db, "alpha", n=3)
    _populate(db, "beta", n=3)
    result = runner.invoke(app, ["timeline", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    projects = data["chart"]["projects"]
    assert len(projects) >= 2


def test_timeline_stats_in_json(tmp_path):
    db, db_path = _make_db(tmp_path)
    _populate(db)
    result = runner.invoke(app, ["timeline", "--db", str(db_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    stats = data["stats"]
    assert "min" in stats
    assert "max" in stats
    assert "avg" in stats
    assert "trend" in stats
    assert "streak" in stats
    assert "run_count" in stats
