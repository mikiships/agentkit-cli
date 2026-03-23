"""Tests for D2: POST /analyze and GET /analyze?repo= endpoints."""
from __future__ import annotations

import tempfile
import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from starlette.testclient import TestClient

from agentkit_cli.history import HistoryDB
from agentkit_cli.api_server import create_app, _analysis_semaphore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(score: float = 85.0, project: str = "github:testowner/testrepo") -> HistoryDB:
    tmp = tempfile.mktemp(suffix=".db")
    db = HistoryDB(db_path=tmp)
    db.record_run(project=project, tool="overall", score=score, details={"notes": "test"})
    return db


def _client(db: HistoryDB | None = None) -> TestClient:
    if db is None:
        db = _make_db()
    return TestClient(create_app(db=db))


# ---------------------------------------------------------------------------
# POST /analyze tests
# ---------------------------------------------------------------------------

def test_post_analyze_returns_cached():
    """A record < 1h old should be returned as cached."""
    db = _make_db(score=88.0, project="github:acme/cool")
    c = _client(db)
    resp = c.post("/analyze", json={"repo": "acme/cool"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["cached"] is True
    assert data["score"] == 88.0
    assert data["grade"] == "B"
    assert data["repo"] == "acme/cool"


def test_post_analyze_invalid_repo_format():
    c = _client()
    resp = c.post("/analyze", json={"repo": "invalid"})
    assert resp.status_code == 400
    assert "Invalid repo format" in resp.json()["detail"]


def test_post_analyze_empty_repo():
    c = _client()
    resp = c.post("/analyze", json={"repo": ""})
    assert resp.status_code == 400


def test_post_analyze_github_prefix():
    """github: prefix should be parsed correctly."""
    db = _make_db(score=75.0, project="github:org/repo")
    c = _client(db)
    resp = c.post("/analyze", json={"repo": "github:org/repo"})
    assert resp.status_code == 200
    assert resp.json()["cached"] is True


def test_post_analyze_github_url():
    """Full GitHub URL should be parsed."""
    db = _make_db(score=60.0, project="github:psf/requests")
    c = _client(db)
    resp = c.post("/analyze", json={"repo": "https://github.com/psf/requests"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["repo"] == "psf/requests"


def test_post_analyze_stale_triggers_subprocess():
    """A stale record should trigger fresh analysis."""
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    # Insert a record with old timestamp
    with db._connect() as conn:
        old_ts = "2020-01-01T00:00:00+00:00"
        conn.execute(
            "INSERT INTO runs (ts, project, tool, score, details) VALUES (?, ?, ?, ?, ?)",
            (old_ts, "github:old/repo", "overall", 50.0, None),
        )

    c = _client(db)
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "failed"
    with patch("agentkit_cli.api_server.subprocess.run", return_value=mock_result):
        resp = c.post("/analyze", json={"repo": "old/repo"})
    assert resp.status_code == 500


def test_post_analyze_timeout():
    """Subprocess timeout should return 504."""
    import subprocess as sp
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    c = _client(db)
    with patch("agentkit_cli.api_server.subprocess.run", side_effect=sp.TimeoutExpired("cmd", 120)):
        resp = c.post("/analyze", json={"repo": "slow/repo"})
    assert resp.status_code == 504
    assert "timed out" in resp.json()["detail"]


def test_post_analyze_cli_not_found():
    """FileNotFoundError should return 500."""
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    c = _client(db)
    with patch("agentkit_cli.api_server.subprocess.run", side_effect=FileNotFoundError):
        resp = c.post("/analyze", json={"repo": "some/repo"})
    assert resp.status_code == 500
    assert "not found" in resp.json()["detail"]


def test_post_analyze_returns_tool_results():
    """Cached result should include tool_results from details."""
    db = _make_db(score=90.0, project="github:good/repo")
    c = _client(db)
    resp = c.post("/analyze", json={"repo": "good/repo"})
    data = resp.json()
    assert "tool_results" in data


def test_post_analyze_returns_elapsed():
    """Cached result should return elapsed_seconds = 0."""
    db = _make_db(score=90.0, project="github:good/repo")
    c = _client(db)
    resp = c.post("/analyze", json={"repo": "good/repo"})
    assert resp.json()["elapsed_seconds"] == 0


# ---------------------------------------------------------------------------
# GET /analyze?repo= tests
# ---------------------------------------------------------------------------

def test_get_analyze_query_cached():
    db = _make_db(score=77.0, project="github:query/repo")
    c = _client(db)
    resp = c.get("/analyze?repo=query/repo")
    assert resp.status_code == 200
    assert resp.json()["cached"] is True
    assert resp.json()["score"] == 77.0


def test_get_analyze_query_invalid():
    c = _client()
    resp = c.get("/analyze?repo=badformat")
    assert resp.status_code == 400


def test_get_analyze_query_missing():
    c = _client()
    resp = c.get("/analyze")
    assert resp.status_code == 422  # FastAPI validation error
