"""Tests for agentkit_cli/history.py — HistoryDB class and module helpers."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

import pytest

from agentkit_cli.history import HistoryDB, record_run, get_history, clear_history


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    """Return a fresh HistoryDB backed by a temp file."""
    return HistoryDB(db_path=tmp_path / "history.db")


# ---------------------------------------------------------------------------
# D1.1 — HistoryDB creation and schema
# ---------------------------------------------------------------------------

def test_historydb_creates_file(tmp_path):
    db_path = tmp_path / "sub" / "history.db"
    db = HistoryDB(db_path=db_path)
    assert db_path.exists()


def test_historydb_creates_parent_dir(tmp_path):
    db_path = tmp_path / "nested" / "deep" / "history.db"
    HistoryDB(db_path=db_path)
    assert db_path.parent.exists()


def test_historydb_schema_idempotent(tmp_path):
    """Creating HistoryDB twice on the same file doesn't raise."""
    db_path = tmp_path / "history.db"
    HistoryDB(db_path=db_path)
    HistoryDB(db_path=db_path)  # second init must be safe


def test_historydb_has_runs_table(tmp_path):
    db_path = tmp_path / "history.db"
    HistoryDB(db_path=db_path)
    conn = sqlite3.connect(str(db_path))
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "runs" in tables


# ---------------------------------------------------------------------------
# D1.2 — record_run
# ---------------------------------------------------------------------------

def test_record_run_basic(db):
    db.record_run("myproject", "agentlint", 85.0)
    rows = db.get_history(project="myproject")
    assert len(rows) == 1
    assert rows[0]["project"] == "myproject"
    assert rows[0]["tool"] == "agentlint"
    assert rows[0]["score"] == 85.0


def test_record_run_with_details(db):
    details = {"key": "value", "num": 42}
    db.record_run("proj", "coderace", 72.5, details=details)
    rows = db.get_history(project="proj")
    assert rows[0]["details"] == details


def test_record_run_details_none(db):
    db.record_run("proj", "overall", 90.0)
    rows = db.get_history(project="proj")
    assert rows[0]["details"] is None


def test_record_run_multiple(db):
    db.record_run("p", "agentlint", 80.0)
    db.record_run("p", "coderace", 60.0)
    db.record_run("p", "overall", 70.0)
    rows = db.get_history(project="p")
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# D1.3 — get_history ordering and filtering
# ---------------------------------------------------------------------------

def test_get_history_newest_first(db):
    db.record_run("p", "agentlint", 50.0)
    time.sleep(0.01)
    db.record_run("p", "agentlint", 90.0)
    rows = db.get_history(project="p")
    assert rows[0]["score"] == 90.0
    assert rows[1]["score"] == 50.0


def test_get_history_filter_project(db):
    db.record_run("projA", "agentlint", 70.0)
    db.record_run("projB", "agentlint", 80.0)
    rows = db.get_history(project="projA")
    assert all(r["project"] == "projA" for r in rows)
    assert len(rows) == 1


def test_get_history_filter_tool(db):
    db.record_run("p", "agentlint", 70.0)
    db.record_run("p", "coderace", 80.0)
    db.record_run("p", "overall", 75.0)
    rows = db.get_history(project="p", tool="coderace")
    assert len(rows) == 1
    assert rows[0]["tool"] == "coderace"


def test_get_history_limit(db):
    for i in range(15):
        db.record_run("p", "overall", float(i))
    rows = db.get_history(project="p", limit=5)
    assert len(rows) == 5


def test_get_history_all_projects(db):
    db.record_run("projA", "overall", 70.0)
    db.record_run("projB", "overall", 80.0)
    rows = db.get_history()  # no project filter
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# D1.4 — clear_history
# ---------------------------------------------------------------------------

def test_clear_history_project(db):
    db.record_run("p1", "overall", 80.0)
    db.record_run("p2", "overall", 90.0)
    deleted = db.clear_history(project="p1")
    assert deleted == 1
    rows = db.get_history()
    assert all(r["project"] == "p2" for r in rows)


def test_clear_history_all(db):
    db.record_run("p1", "overall", 80.0)
    db.record_run("p2", "overall", 90.0)
    deleted = db.clear_history()
    assert deleted == 2
    assert db.get_history() == []


def test_clear_history_returns_zero_when_empty(db):
    deleted = db.clear_history(project="nonexistent")
    assert deleted == 0


# ---------------------------------------------------------------------------
# D1.5 — get_all_projects / get_project_summary
# ---------------------------------------------------------------------------

def test_get_all_projects(db):
    db.record_run("alpha", "overall", 70.0)
    db.record_run("beta", "overall", 80.0)
    projects = db.get_all_projects()
    assert "alpha" in projects
    assert "beta" in projects


def test_get_project_summary(db):
    db.record_run("proj", "agentlint", 80.0)
    db.record_run("proj", "overall", 75.0)
    summary = db.get_project_summary()
    assert len(summary) == 1
    assert summary[0]["project"] == "proj"
    assert summary[0]["run_count"] == 2


# ---------------------------------------------------------------------------
# D1.6 — module-level helpers
# ---------------------------------------------------------------------------

def test_module_record_run_uses_db(tmp_path):
    db = HistoryDB(db_path=tmp_path / "h.db")
    record_run("proj", "agentlint", 88.0, db=db)
    rows = db.get_history(project="proj")
    assert len(rows) == 1
    assert rows[0]["score"] == 88.0


def test_module_get_history(tmp_path):
    db = HistoryDB(db_path=tmp_path / "h.db")
    db.record_run("proj", "overall", 77.0)
    rows = get_history(project="proj", db=db)
    assert len(rows) == 1


def test_module_clear_history(tmp_path):
    db = HistoryDB(db_path=tmp_path / "h.db")
    db.record_run("proj", "overall", 77.0)
    n = clear_history(project="proj", db=db)
    assert n == 1
    assert get_history(project="proj", db=db) == []


def test_historydb_get_history_empty(db):
    """get_history on empty DB returns empty list."""
    rows = db.get_history()
    assert rows == []


# ---------------------------------------------------------------------------
# D4 — tracked_prs table and helper functions
# ---------------------------------------------------------------------------

def test_tracked_prs_table_exists(tmp_path):
    """tracked_prs table should exist after DB creation."""
    import sqlite3
    db_path = tmp_path / "history.db"
    HistoryDB(db_path=db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracked_prs'")
    assert cursor.fetchone() is not None
    conn.close()


def test_record_pr_returns_row_id(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    row_id = db.record_pr("owner/repo", 42, "https://github.com/owner/repo/pull/42")
    assert isinstance(row_id, int)
    assert row_id > 0


def test_record_pr_stores_fields(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", 10, "https://github.com/owner/repo/pull/10", campaign_id="camp1")
    prs = db.get_tracked_prs()
    assert len(prs) == 1
    pr = prs[0]
    assert pr["repo"] == "owner/repo"
    assert pr["pr_number"] == 10
    assert pr["pr_url"] == "https://github.com/owner/repo/pull/10"
    assert pr["campaign_id"] == "camp1"
    assert pr["last_status"] == "unknown"
    assert pr["submitted_at"]


def test_record_pr_null_pr_number(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", None, None)
    prs = db.get_tracked_prs()
    assert prs[0]["pr_number"] is None


def test_get_tracked_prs_empty(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    assert db.get_tracked_prs() == []


def test_get_tracked_prs_filter_by_campaign(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("a/b", 1, None, campaign_id="camp1")
    db.record_pr("c/d", 2, None, campaign_id="camp2")
    db.record_pr("e/f", 3, None, campaign_id="camp1")

    camp1 = db.get_tracked_prs(campaign_id="camp1")
    assert len(camp1) == 2
    assert all(p["campaign_id"] == "camp1" for p in camp1)


def test_get_tracked_prs_limit(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    for i in range(10):
        db.record_pr(f"owner/repo{i}", i, None)
    prs = db.get_tracked_prs(limit=3)
    assert len(prs) == 3


def test_update_pr_status(tmp_path):
    db = HistoryDB(db_path=tmp_path / "history.db")
    row_id = db.record_pr("owner/repo", 5, "https://github.com/owner/repo/pull/5")
    db.update_pr_status(row_id, "merged", "2026-03-17T12:00:00+00:00")
    prs = db.get_tracked_prs()
    assert prs[0]["last_status"] == "merged"
    assert prs[0]["last_checked_at"] == "2026-03-17T12:00:00+00:00"


def test_module_level_record_pr(tmp_path):
    from agentkit_cli.history import record_pr, get_tracked_prs
    db = HistoryDB(db_path=tmp_path / "history.db")
    row_id = record_pr("owner/repo", 99, "https://url", db=db)
    assert row_id > 0
    prs = get_tracked_prs(db=db)
    assert len(prs) == 1


def test_module_level_update_pr_status(tmp_path):
    from agentkit_cli.history import record_pr, update_pr_status, get_tracked_prs
    db = HistoryDB(db_path=tmp_path / "history.db")
    row_id = record_pr("owner/repo", 1, None, db=db)
    update_pr_status(row_id, "closed", "2026-03-17T00:00:00+00:00", db=db)
    prs = get_tracked_prs(db=db)
    assert prs[0]["last_status"] == "closed"
