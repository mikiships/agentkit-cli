"""Tests for agentkit digest CLI command (D2) — ≥12 tests required."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(rows: list[dict] | None = None) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, "
        "project TEXT NOT NULL, tool TEXT NOT NULL, score REAL NOT NULL, "
        "details TEXT, label TEXT, findings TEXT, campaign_id TEXT)"
    )
    conn.execute("CREATE INDEX idx_runs_project ON runs(project)")
    conn.execute("CREATE INDEX idx_runs_ts ON runs(ts DESC)")
    for row in (rows or []):
        conn.execute(
            "INSERT INTO runs (ts, project, tool, score) VALUES (?, ?, ?, ?)",
            (row["ts"], row["project"], row.get("tool", "overall"), row["score"]),
        )
    conn.commit()
    conn.close()
    return path


def _ts(days_ago: float = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_digest_command_exists():
    result = runner.invoke(app, ["digest", "--help"])
    assert result.exit_code == 0
    assert "digest" in result.output.lower()


def test_digest_exit_0_empty_db():
    db = _make_db()
    result = runner.invoke(app, ["digest", "--db-path", str(db)])
    assert result.exit_code == 0


def test_digest_exit_0_with_data():
    db = _make_db([{"ts": _ts(2), "project": "proj", "score": 80.0}])
    result = runner.invoke(app, ["digest", "--db-path", str(db)])
    assert result.exit_code == 0


def test_digest_json_output_valid():
    db = _make_db([{"ts": _ts(2), "project": "proj", "score": 80.0}])
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "period_start" in data
    assert "period_end" in data
    assert "projects_tracked" in data
    assert "runs_in_period" in data
    assert "overall_trend" in data
    assert "per_project" in data
    assert "regressions" in data
    assert "improvements" in data
    assert "top_actions" in data
    assert "coverage_pct" in data


def test_digest_json_all_fields_present():
    db = _make_db()
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--json"])
    data = json.loads(result.output)
    assert isinstance(data["per_project"], list)
    assert isinstance(data["regressions"], list)
    assert isinstance(data["improvements"], list)
    assert isinstance(data["top_actions"], list)


def test_digest_quiet_flag():
    db = _make_db([{"ts": _ts(1), "project": "x", "score": 75.0}])
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--quiet"])
    assert result.exit_code == 0
    # Should be a single-line summary
    lines = [l for l in result.output.strip().splitlines() if l.strip()]
    assert len(lines) == 1
    assert "trend" in lines[0]


def test_digest_period_option():
    db = _make_db([
        {"ts": _ts(2), "project": "recent", "score": 80.0},
        {"ts": _ts(20), "project": "old", "score": 70.0},
    ])
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--period", "7", "--json"])
    data = json.loads(result.output)
    # Only "recent" should be in period
    assert data["runs_in_period"] == 1


def test_digest_projects_filter():
    db = _make_db([
        {"ts": _ts(2), "project": "alpha", "score": 80.0},
        {"ts": _ts(2), "project": "beta", "score": 70.0},
    ])
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--projects", "alpha", "--json"])
    data = json.loads(result.output)
    assert data["projects_tracked"] == 1
    assert data["per_project"][0]["name"] == "alpha"


def test_digest_output_writes_html(tmp_path):
    db = _make_db([{"ts": _ts(2), "project": "proj", "score": 80.0}])
    out_file = tmp_path / "digest.html"
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "<html" in content.lower()


def test_digest_share_skipped_without_key():
    """--share without HERENOW_API_KEY should not crash, just report failure."""
    db = _make_db()
    with patch("agentkit_cli.share.upload_scorecard", return_value=None):
        result = runner.invoke(app, ["digest", "--db-path", str(db), "--share"])
    assert result.exit_code == 0


def test_digest_notify_slack_calls_send(tmp_path):
    db = _make_db()
    with patch("agentkit_cli.notifier._send_with_retry", return_value=(True, "ok")) as mock_send:
        result = runner.invoke(app, ["digest", "--db-path", str(db), "--notify-slack", "https://hooks.slack.com/test"])
    assert result.exit_code == 0
    mock_send.assert_called_once()


def test_digest_notify_discord_calls_send(tmp_path):
    db = _make_db()
    with patch("agentkit_cli.notifier._send_with_retry", return_value=(True, "ok")) as mock_send:
        result = runner.invoke(app, ["digest", "--db-path", str(db), "--notify-discord", "https://discord.com/api/webhooks/test"])
    assert result.exit_code == 0
    mock_send.assert_called_once()


def test_digest_json_trend_values():
    db = _make_db()
    result = runner.invoke(app, ["digest", "--db-path", str(db), "--json"])
    data = json.loads(result.output)
    assert data["overall_trend"] in ("improving", "stable", "regressing")
