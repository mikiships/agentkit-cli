"""Tests for D3: GET /recent endpoint and recent analyses panel."""
from __future__ import annotations

import tempfile

import pytest
from starlette.testclient import TestClient

from agentkit_cli.history import HistoryDB
from agentkit_cli.api_server import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db_multi() -> HistoryDB:
    tmp = tempfile.mktemp(suffix=".db")
    db = HistoryDB(db_path=tmp)
    db.record_run(project="github:alpha/one", tool="overall", score=90.0)
    db.record_run(project="github:beta/two", tool="overall", score=75.0)
    db.record_run(project="github:gamma/three", tool="overall", score=60.0)
    return db


def _client(db: HistoryDB | None = None) -> TestClient:
    if db is None:
        db = _make_db_multi()
    return TestClient(create_app(db=db))


# ---------------------------------------------------------------------------
# GET /recent tests
# ---------------------------------------------------------------------------

def test_recent_returns_200():
    c = _client()
    resp = c.get("/recent")
    assert resp.status_code == 200


def test_recent_returns_analyses():
    c = _client()
    data = c.get("/recent").json()
    assert "analyses" in data
    assert "total" in data


def test_recent_default_limit():
    c = _client()
    data = c.get("/recent").json()
    assert len(data["analyses"]) == 3  # we have 3 repos


def test_recent_custom_limit():
    c = _client()
    data = c.get("/recent?limit=2").json()
    assert len(data["analyses"]) <= 2


def test_recent_entry_has_fields():
    c = _client()
    data = c.get("/recent").json()
    entry = data["analyses"][0]
    assert "repo" in entry
    assert "score" in entry
    assert "grade" in entry
    assert "last_analyzed" in entry


def test_recent_deduplicates():
    """Multiple runs for same project should only appear once."""
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    db.record_run(project="github:dup/repo", tool="overall", score=80.0)
    db.record_run(project="github:dup/repo", tool="overall", score=85.0)
    c = _client(db)
    data = c.get("/recent").json()
    repos = [a["repo"] for a in data["analyses"]]
    assert repos.count("dup/repo") == 1


def test_recent_empty_db():
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    c = _client(db)
    data = c.get("/recent").json()
    assert data["analyses"] == []
    assert data["total"] == 0


def test_recent_includes_grade():
    c = _client()
    data = c.get("/recent").json()
    grades = {a["grade"] for a in data["analyses"]}
    assert grades.issubset({"A", "B", "C", "D", "F"})


def test_recent_score_is_float():
    c = _client()
    data = c.get("/recent").json()
    for a in data["analyses"]:
        assert isinstance(a["score"], float)


# ---------------------------------------------------------------------------
# /ui recent panel tests
# ---------------------------------------------------------------------------

def test_ui_recent_panel_exists():
    c = _client()
    resp = c.get("/ui")
    assert "Recent Analyses" in resp.text


def test_ui_recent_link():
    c = _client()
    resp = c.get("/ui")
    assert "/recent" in resp.text
