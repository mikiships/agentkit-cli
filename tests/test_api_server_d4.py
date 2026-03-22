"""Tests for D4: /ui HTML endpoint."""
from __future__ import annotations

import tempfile

import pytest
from starlette.testclient import TestClient

from agentkit_cli.history import HistoryDB
from agentkit_cli.api_server import create_app


def make_db():
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    db.record_run("github:foo/bar", "overall", 88.0)
    db.record_run("github:baz/qux", "overall", 72.0)
    return db


def test_ui_returns_200():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    assert resp.status_code == 200


def test_ui_content_type_html():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    assert "text/html" in resp.headers["content-type"]


def test_ui_contains_version():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    from agentkit_cli import __version__
    assert __version__ in resp.text


def test_ui_dark_theme():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    # Dark theme uses dark background color
    assert "#0d1117" in resp.text or "background" in resp.text


def test_ui_shows_repos_count():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    assert "Repos" in resp.text or "repos" in resp.text.lower()


def test_ui_shows_recent_analyses():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    assert "Recent" in resp.text or "foo/bar" in resp.text or "baz/qux" in resp.text


def test_ui_badge_embed_snippet():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    assert "badge" in resp.text.lower()


def test_ui_trending_link():
    client = TestClient(create_app(db=make_db()))
    resp = client.get("/ui")
    assert "/trending" in resp.text


def test_ui_empty_db():
    db = HistoryDB(db_path=tempfile.mktemp(suffix=".db"))
    client = TestClient(create_app(db=db))
    resp = client.get("/ui")
    assert resp.status_code == 200
    assert "No data yet" in resp.text or "0" in resp.text
