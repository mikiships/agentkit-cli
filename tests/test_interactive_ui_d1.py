"""Tests for D1: Interactive /ui form in api_server.py."""
from __future__ import annotations

import tempfile

import pytest
from starlette.testclient import TestClient

from agentkit_cli.history import HistoryDB
from agentkit_cli.api_server import create_app, _grade_badge_css, _parse_repo_input


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
# /ui page tests
# ---------------------------------------------------------------------------

def test_ui_returns_200():
    c = _client()
    resp = c.get("/ui")
    assert resp.status_code == 200


def test_ui_contains_form():
    c = _client()
    resp = c.get("/ui")
    assert "analyze-form" in resp.text


def test_ui_contains_repo_input():
    c = _client()
    resp = c.get("/ui")
    assert 'id="repo-input"' in resp.text


def test_ui_contains_analyze_button():
    c = _client()
    resp = c.get("/ui")
    assert "Analyze</button>" in resp.text


def test_ui_contains_spinner():
    c = _client()
    resp = c.get("/ui")
    assert "analyze-spinner" in resp.text


def test_ui_contains_result_panel():
    c = _client()
    resp = c.get("/ui")
    assert "analyze-result" in resp.text


def test_ui_contains_error_panel():
    c = _client()
    resp = c.get("/ui")
    assert "analyze-error" in resp.text


def test_ui_contains_recent_table():
    c = _client()
    resp = c.get("/ui")
    assert 'id="recent-table"' in resp.text


def test_ui_contains_auto_refresh_script():
    c = _client()
    resp = c.get("/ui")
    assert "setInterval(refreshRecent, 30000)" in resp.text


def test_ui_contains_version():
    from agentkit_cli import __version__
    c = _client()
    resp = c.get("/ui")
    assert __version__ in resp.text


def test_ui_dark_theme():
    c = _client()
    resp = c.get("/ui")
    assert "#0d1117" in resp.text


def test_ui_shows_recent_data():
    db = _make_db(score=92.0, project="github:acme/cool")
    c = _client(db)
    resp = c.get("/ui")
    assert "acme/cool" in resp.text


def test_ui_no_data_message():
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    c = _client(db)
    resp = c.get("/ui")
    assert "No data yet" in resp.text


# ---------------------------------------------------------------------------
# _grade_badge_css tests
# ---------------------------------------------------------------------------

def test_grade_badge_css_A():
    assert _grade_badge_css("A") == "#238636"


def test_grade_badge_css_F():
    assert _grade_badge_css("F") == "#f85149"


def test_grade_badge_css_unknown():
    assert _grade_badge_css("X") == "#8b949e"


# ---------------------------------------------------------------------------
# _parse_repo_input tests
# ---------------------------------------------------------------------------

def test_parse_repo_owner_slash_repo():
    assert _parse_repo_input("psf/requests") == ("psf", "requests")


def test_parse_repo_github_prefix():
    assert _parse_repo_input("github:psf/requests") == ("psf", "requests")


def test_parse_repo_github_url():
    owner, repo = _parse_repo_input("https://github.com/psf/requests")
    assert owner == "psf"
    assert repo == "requests"


def test_parse_repo_github_url_trailing_slash():
    owner, repo = _parse_repo_input("https://github.com/psf/requests/")
    assert owner == "psf"
    assert repo == "requests"


def test_parse_repo_invalid():
    with pytest.raises(ValueError, match="Invalid repo format"):
        _parse_repo_input("not-a-repo")


def test_parse_repo_empty():
    with pytest.raises(ValueError):
        _parse_repo_input("")


def test_parse_repo_whitespace_stripped():
    assert _parse_repo_input("  psf/requests  ") == ("psf", "requests")
