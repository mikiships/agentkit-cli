"""Tests for D1: api_server.py FastAPI endpoints."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from starlette.testclient import TestClient

from agentkit_cli.history import HistoryDB
from agentkit_cli.api_server import create_app, _grade, _badge_color, _is_stale


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db_with_record(score: float = 85.0, project: str = "github:testowner/testrepo") -> HistoryDB:
    """Create an in-memory HistoryDB with one record."""
    tmp = tempfile.mktemp(suffix=".db")
    db = HistoryDB(db_path=tmp)
    db.record_run(project=project, tool="overall", score=score, details={"notes": "test"})
    return db


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

def test_grade_A():
    assert _grade(95) == "A"

def test_grade_B():
    assert _grade(82) == "B"

def test_grade_C():
    assert _grade(72) == "C"

def test_grade_D():
    assert _grade(62) == "D"

def test_grade_F():
    assert _grade(40) == "F"

def test_badge_color_brightgreen():
    assert _badge_color(95) == "brightgreen"

def test_badge_color_yellow():
    assert _badge_color(75) == "yellow"

def test_badge_color_orange():
    assert _badge_color(55) == "orange"

def test_badge_color_red():
    assert _badge_color(30) == "red"

def test_is_stale_fresh():
    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).isoformat()
    assert not _is_stale(ts)

def test_is_stale_old():
    assert _is_stale("2000-01-01T00:00:00+00:00")


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health_endpoint():
    db = make_db_with_record()
    client = TestClient(create_app(db=db))
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data


# ---------------------------------------------------------------------------
# /score endpoint
# ---------------------------------------------------------------------------

def test_score_found():
    db = make_db_with_record(score=78.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/score/testowner/testrepo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 78.0
    assert data["grade"] == "C"
    assert data["repo"] == "testowner/testrepo"

def test_score_not_found():
    db = make_db_with_record()
    client = TestClient(create_app(db=db))
    resp = client.get("/score/nobody/missing")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /badge endpoint
# ---------------------------------------------------------------------------

def test_badge_brightgreen():
    db = make_db_with_record(score=92.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/badge/testowner/testrepo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["schemaVersion"] == 1
    assert data["label"] == "agent score"
    assert data["color"] == "brightgreen"
    assert "92" in data["message"]

def test_badge_not_found():
    db = make_db_with_record()
    client = TestClient(create_app(db=db))
    resp = client.get("/badge/nobody/missing")
    assert resp.status_code == 404

def test_badge_red_color():
    db = make_db_with_record(score=20.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/badge/testowner/testrepo")
    assert resp.json()["color"] == "red"

def test_badge_yellow_color():
    db = make_db_with_record(score=75.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/badge/testowner/testrepo")
    assert resp.json()["color"] == "yellow"

def test_badge_orange_color():
    db = make_db_with_record(score=55.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/badge/testowner/testrepo")
    assert resp.json()["color"] == "orange"


# ---------------------------------------------------------------------------
# /trending endpoint
# ---------------------------------------------------------------------------

def test_trending_returns_repos():
    db = make_db_with_record(score=80.0)
    db.record_run("github:other/repo", "overall", 90.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/trending")
    assert resp.status_code == 200
    data = resp.json()
    assert "repos" in data
    assert len(data["repos"]) >= 1

def test_trending_limit():
    db = make_db_with_record(score=80.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/trending?limit=1")
    assert resp.status_code == 200
    assert len(resp.json()["repos"]) <= 1

def test_trending_min_score():
    db = make_db_with_record(score=40.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/trending?min_score=50")
    assert resp.status_code == 200
    # score 40 should be filtered out
    for r in resp.json()["repos"]:
        assert r["score"] >= 50


# ---------------------------------------------------------------------------
# /history endpoint
# ---------------------------------------------------------------------------

def test_history_found():
    db = make_db_with_record(score=85.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/history/testowner/testrepo")
    assert resp.status_code == 200
    data = resp.json()
    assert "history" in data
    assert len(data["history"]) >= 1
    assert "timestamp" in data["history"][0]

def test_history_not_found():
    db = make_db_with_record()
    client = TestClient(create_app(db=db))
    resp = client.get("/history/nobody/missing")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /leaderboard endpoint
# ---------------------------------------------------------------------------

def test_leaderboard():
    db = make_db_with_record(score=88.0)
    db.record_run("github:other/repo", "overall", 95.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "leaderboard" in data
    assert len(data["leaderboard"]) >= 1
    # Sorted by score desc
    scores = [r["score"] for r in data["leaderboard"]]
    assert scores == sorted(scores, reverse=True)

def test_leaderboard_limit():
    db = make_db_with_record(score=80.0)
    client = TestClient(create_app(db=db))
    resp = client.get("/leaderboard?limit=1")
    assert len(resp.json()["leaderboard"]) <= 1


# ---------------------------------------------------------------------------
# /analyze endpoint (mocked subprocess)
# ---------------------------------------------------------------------------

def test_analyze_cached():
    """analyze returns from DB when data is fresh."""
    db = make_db_with_record(score=77.0)
    client = TestClient(create_app(db=db))
    # Patch _is_stale to return False (data is fresh)
    with patch("agentkit_cli.api_server._is_stale", return_value=False):
        resp = client.get("/analyze/testowner/testrepo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 77.0
    assert data["repo"] == "testowner/testrepo"

def test_analyze_triggers_subprocess_when_missing():
    """analyze triggers subprocess when repo not in DB."""
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    client = TestClient(create_app(db=db))
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Analysis failed"
    with patch("subprocess.run", return_value=mock_result):
        resp = client.get("/analyze/nobody/missing")
    assert resp.status_code == 500

def test_analyze_subprocess_success_then_db_miss():
    """When subprocess succeeds but DB still empty, return 404."""
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    client = TestClient(create_app(db=db))
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result):
        resp = client.get("/analyze/nobody/missing")
    assert resp.status_code == 404

def test_analyze_stale_triggers_refresh():
    """When data is stale, subprocess is called."""
    db = make_db_with_record(score=70.0)
    client = TestClient(create_app(db=db))
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    with patch("agentkit_cli.api_server._is_stale", return_value=True), \
         patch("subprocess.run", return_value=mock_result):
        resp = client.get("/analyze/testowner/testrepo")
    # DB still has the old record, should return 200
    assert resp.status_code == 200
