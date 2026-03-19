"""Tests for D4 — agentkit run --digest / report --digest integration."""
from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app


runner = CliRunner()


def _ts(days_ago: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def test_run_digest_flag_in_help():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "--digest" in result.output


def test_report_digest_flag_in_help():
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "--digest" in result.output


def test_run_digest_produces_digest_output(tmp_path):
    """run --digest should print digest summary after pipeline."""
    fake_run = MagicMock()
    with patch("agentkit_cli.main.run_command", fake_run):
        result = runner.invoke(app, ["run", "--digest", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "digest" in result.output.lower()


def test_report_digest_produces_digest_output(tmp_path):
    """report --digest should append digest summary."""
    fake_report = MagicMock()
    with patch("agentkit_cli.main.report_command", fake_report):
        result = runner.invoke(app, ["report", "--digest", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "digest" in result.output.lower()


def test_run_digest_shows_trend(tmp_path):
    """Digest output should include trend word."""
    fake_run = MagicMock()
    with patch("agentkit_cli.main.run_command", fake_run):
        result = runner.invoke(app, ["run", "--digest", "--path", str(tmp_path)])
    output = result.output.lower()
    assert any(w in output for w in ("improving", "stable", "regressing"))


def test_report_digest_shows_trend(tmp_path):
    fake_report = MagicMock()
    with patch("agentkit_cli.main.report_command", fake_report):
        result = runner.invoke(app, ["report", "--digest", "--path", str(tmp_path)])
    output = result.output.lower()
    assert any(w in output for w in ("improving", "stable", "regressing"))


def test_digest_engine_works_with_existing_db_schema():
    """DigestEngine must work read-only on the real HistoryDB schema (no schema changes)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = Path(tmp.name)

    # Create a real HistoryDB (which runs all migrations)
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=db_path)
    db.record_run("testproj", "overall", 75.0)

    # DigestEngine should read it without error
    from agentkit_cli.digest import DigestEngine
    engine = DigestEngine(db_path=db_path, period_days=7)
    report = engine.generate()
    assert report.projects_tracked == 1
    assert report.runs_in_period == 1


def test_digest_engine_no_schema_changes(tmp_path):
    """Verify DigestEngine doesn't create new tables."""
    db_path = tmp_path / "test.db"
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=db_path)

    # Get initial table list
    conn = sqlite3.connect(str(db_path))
    before = set(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    conn.close()

    from agentkit_cli.digest import DigestEngine
    engine = DigestEngine(db_path=db_path, period_days=7)
    engine.generate()

    conn = sqlite3.connect(str(db_path))
    after = set(r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    conn.close()

    # No new tables should have been created
    assert after == before
