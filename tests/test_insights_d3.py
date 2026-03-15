"""Tests for D3: findings storage and schema migration in history DB."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from agentkit_cli.history import HistoryDB, record_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    return HistoryDB(db_path=tmp_path / "history.db")


# ---------------------------------------------------------------------------
# D3.1 — findings column in HistoryDB.record_run
# ---------------------------------------------------------------------------

def test_record_run_with_findings(db, tmp_path):
    """record_run stores findings as JSON in the findings column."""
    findings = ["missing-tools", "stale-date"]
    db.record_run("myproject", "overall", 75.0, findings=findings)
    db_path = tmp_path / "history.db"
    # Read directly from sqlite to confirm findings column is populated
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT findings FROM runs WHERE project = 'myproject'").fetchone()
    conn.close()
    assert row is not None
    assert json.loads(row[0]) == findings


def test_record_run_findings_none_by_default(db, tmp_path):
    """record_run without findings stores NULL in the findings column."""
    db.record_run("proj", "overall", 80.0)
    db_path = tmp_path / "history.db"
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT findings FROM runs WHERE project = 'proj'").fetchone()
    conn.close()
    assert row[0] is None


def test_module_level_record_run_passes_findings(tmp_path):
    """Module-level record_run convenience function forwards findings kwarg."""
    db_path = tmp_path / "h.db"
    db = HistoryDB(db_path=db_path)
    record_run("proj", "overall", 70.0, db=db, findings=["finding-abc"])
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT findings FROM runs").fetchone()
    conn.close()
    assert row is not None
    assert json.loads(row[0]) == ["finding-abc"]


# ---------------------------------------------------------------------------
# D3.2 — Schema migration: existing DB without findings column
# ---------------------------------------------------------------------------

def test_migration_adds_findings_column(tmp_path):
    """HistoryDB adds findings column to an existing DB that doesn't have it."""
    db_path = tmp_path / "old.db"
    # Create old-style DB without findings column
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            project TEXT NOT NULL,
            tool TEXT NOT NULL,
            score REAL NOT NULL,
            details TEXT,
            label TEXT
        )
    """)
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score) VALUES (?, ?, ?, ?)",
        ("2026-01-01T00:00:00+00:00", "old-proj", "overall", 65.0),
    )
    conn.commit()
    conn.close()

    # Opening with InsightsEngine triggers migration
    from agentkit_cli.insights import InsightsEngine
    engine = InsightsEngine(db_path=db_path)

    # Must not crash and old data must still be accessible
    summary = engine.get_portfolio_summary()
    assert summary["total_runs"] == 1

    # findings column should now exist
    conn = sqlite3.connect(str(db_path))
    cols = [row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()]
    conn.close()
    assert "findings" in cols


def test_migration_idempotent(tmp_path):
    """Running InsightsEngine twice on same DB doesn't fail (migration is idempotent)."""
    db_path = tmp_path / "history.db"
    HistoryDB(db_path=db_path)  # creates proper schema

    from agentkit_cli.insights import InsightsEngine
    InsightsEngine(db_path=db_path)
    InsightsEngine(db_path=db_path)  # second time must not raise


# ---------------------------------------------------------------------------
# D3.3 — record-findings flag accepted by CLI commands
# ---------------------------------------------------------------------------

def test_run_command_accepts_record_findings_flag():
    """agentkit run --help shows --record-findings flag."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "record-findings" in result.output


def test_analyze_command_accepts_record_findings_flag():
    """agentkit analyze --help shows --record-findings flag."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "record-findings" in result.output
