"""Tests for D1: pages-sync command and SyncEngine."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.pages_sync_engine import SyncEngine
from agentkit_cli.history import HistoryDB


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_db(tmp_path: Path, entries: list[dict]) -> HistoryDB:
    db = HistoryDB(db_path=tmp_path / "history.db")
    for e in entries:
        db.record_run(
            project=e["project"],
            tool=e.get("tool", "overall"),
            score=e["score"],
            details=e.get("details"),
        )
    return db


def _make_engine(tmp_path: Path, entries: list[dict]) -> SyncEngine:
    db = _make_db(tmp_path, entries)
    docs = tmp_path / "docs"
    docs.mkdir()
    return SyncEngine(db=db, docs_dir=docs)


# ── SyncEngine.read_history ───────────────────────────────────────────────────

def test_read_history_returns_latest_per_repo(tmp_path):
    engine = _make_engine(tmp_path, [
        {"project": "github:owner/repo1", "score": 70.0},
        {"project": "github:owner/repo1", "score": 80.0},  # newer
        {"project": "github:owner/repo2", "score": 60.0},
    ])
    rows = engine.read_history()
    names = [r["project"] for r in rows]
    assert "github:owner/repo1" in names
    assert "github:owner/repo2" in names
    assert names.count("github:owner/repo1") == 1


def test_read_history_latest_score_wins(tmp_path):
    engine = _make_engine(tmp_path, [
        {"project": "github:owner/repo1", "score": 70.0},
        {"project": "github:owner/repo1", "score": 80.0},
    ])
    rows = engine.read_history()
    repo_row = next(r for r in rows if r["project"] == "github:owner/repo1")
    assert repo_row["score"] == 80.0


def test_read_history_filters_non_github(tmp_path):
    engine = _make_engine(tmp_path, [
        {"project": "github:owner/repo1", "score": 70.0},
        {"project": "./local-path", "score": 90.0},
    ])
    rows = engine.read_history()
    assert all(r["project"].startswith("github:") for r in rows)


def test_read_history_empty_db(tmp_path):
    engine = _make_engine(tmp_path, [])
    rows = engine.read_history()
    assert rows == []


def test_read_history_limit(tmp_path):
    entries = [{"project": f"github:owner/repo{i}", "score": float(i)} for i in range(10)]
    engine = _make_engine(tmp_path, entries)
    rows = engine.read_history(limit=5)
    assert len(rows) == 5


def test_read_history_sorted_by_score_desc(tmp_path):
    engine = _make_engine(tmp_path, [
        {"project": "github:a/low", "score": 40.0},
        {"project": "github:a/high", "score": 90.0},
        {"project": "github:a/mid", "score": 60.0},
    ])
    rows = engine.read_history()
    scores = [r["score"] for r in rows]
    assert scores == sorted(scores, reverse=True)


# ── SyncEngine.build_entries ──────────────────────────────────────────────────

def test_build_entries_community_source(tmp_path):
    engine = _make_engine(tmp_path, [])
    rows = [{"project": "github:owner/repo", "score": 75.0, "ts": "2026-01-01", "details": None}]
    entries = engine.build_entries(rows)
    assert entries[0]["source"] == "community"


def test_build_entries_name_format(tmp_path):
    engine = _make_engine(tmp_path, [])
    rows = [{"project": "github:openai/openai-python", "score": 85.0, "ts": "2026-01-01", "details": None}]
    entries = engine.build_entries(rows)
    assert entries[0]["name"] == "openai/openai-python"
    assert entries[0]["url"] == "https://github.com/openai/openai-python"


def test_build_entries_grade_computed(tmp_path):
    engine = _make_engine(tmp_path, [])
    rows = [{"project": "github:owner/repo", "score": 82.0, "ts": "2026-01-01", "details": None}]
    entries = engine.build_entries(rows)
    assert entries[0]["grade"] == "A"


def test_build_entries_ecosystem_from_details(tmp_path):
    engine = _make_engine(tmp_path, [])
    rows = [{"project": "github:owner/repo", "score": 75.0, "ts": "2026-01-01", "details": {"ecosystem": "python"}}]
    entries = engine.build_entries(rows)
    assert entries[0]["ecosystem"] == "python"


# ── SyncEngine.merge_entries ──────────────────────────────────────────────────

def test_merge_entries_add_new(tmp_path):
    engine = _make_engine(tmp_path, [])
    existing = {"repos": [], "stats": {}}
    new = [{"name": "a/repo", "url": "https://github.com/a/repo", "score": 70.0, "grade": "B", "ecosystem": "", "source": "community", "synced_at": "2026-01-02"}]
    merged, added, updated = engine.merge_entries(existing, new)
    assert added == 1
    assert updated == 0
    assert len(merged["repos"]) == 1


def test_merge_entries_update_community(tmp_path):
    engine = _make_engine(tmp_path, [])
    existing = {"repos": [{"name": "a/repo", "url": "https://github.com/a/repo", "score": 60.0, "grade": "C", "ecosystem": "", "source": "community", "synced_at": "2026-01-01"}], "stats": {}}
    new = [{"name": "a/repo", "url": "https://github.com/a/repo", "score": 75.0, "grade": "B", "ecosystem": "", "source": "community", "synced_at": "2026-01-02"}]
    merged, added, updated = engine.merge_entries(existing, new)
    assert added == 0
    assert updated == 1
    repo = next(r for r in merged["repos"] if r["name"] == "a/repo")
    assert repo["score"] == 75.0


def test_merge_entries_ecosystem_source_preserved(tmp_path):
    engine = _make_engine(tmp_path, [])
    existing = {"repos": [{"name": "a/repo", "url": "", "score": 85.0, "grade": "A", "ecosystem": "python", "source": "ecosystem", "synced_at": "2026-01-01"}], "stats": {}}
    new = [{"name": "a/repo", "url": "", "score": 70.0, "grade": "B", "ecosystem": "", "source": "community", "synced_at": "2026-01-01"}]
    merged, added, updated = engine.merge_entries(existing, new)
    repo = next(r for r in merged["repos"] if r["name"] == "a/repo")
    assert repo["source"] == "ecosystem"


def test_merge_adds_source_to_existing_without_source(tmp_path):
    engine = _make_engine(tmp_path, [])
    existing = {"repos": [{"name": "a/repo", "url": "", "score": 85.0, "grade": "A", "ecosystem": "python"}], "stats": {}}
    merged, added, updated = engine.merge_entries(existing, [])
    repo = next(r for r in merged["repos"] if r["name"] == "a/repo")
    assert repo["source"] == "ecosystem"


def test_merge_entries_sorted_by_score(tmp_path):
    engine = _make_engine(tmp_path, [])
    existing = {"repos": [], "stats": {}}
    new_entries = [
        {"name": "a/low", "url": "", "score": 40.0, "grade": "D", "ecosystem": "", "source": "community", "synced_at": ""},
        {"name": "a/high", "url": "", "score": 90.0, "grade": "A", "ecosystem": "", "source": "community", "synced_at": ""},
    ]
    merged, _, _ = engine.merge_entries(existing, new_entries)
    scores = [r["score"] for r in merged["repos"]]
    assert scores == sorted(scores, reverse=True)


def test_merge_entries_stats(tmp_path):
    engine = _make_engine(tmp_path, [])
    existing = {"repos": [], "stats": {}}
    new_entries = [
        {"name": "a/r1", "url": "", "score": 80.0, "grade": "A", "ecosystem": "", "source": "community", "synced_at": ""},
        {"name": "a/r2", "url": "", "score": 60.0, "grade": "C", "ecosystem": "", "source": "community", "synced_at": ""},
    ]
    merged, _, _ = engine.merge_entries(existing, new_entries)
    assert merged["stats"]["total"] == 2
    assert merged["stats"]["top_score"] == 80.0


# ── SyncEngine.write_data_json ────────────────────────────────────────────────

def test_write_data_json(tmp_path):
    engine = _make_engine(tmp_path, [])
    data = {"generated_at": "now", "repos": [], "stats": {"total": 0}}
    engine.write_data_json(data)
    written = json.loads((tmp_path / "docs" / "data.json").read_text())
    assert written["stats"]["total"] == 0


# ── SyncEngine.sync (no push) ─────────────────────────────────────────────────

def test_sync_dry_run_no_file_written(tmp_path):
    engine = _make_engine(tmp_path, [{"project": "github:owner/repo", "score": 75.0}])
    summary = engine.sync(push=False, dry_run=True)
    assert summary["dry_run"] is True
    assert not (tmp_path / "docs" / "data.json").exists()


def test_sync_writes_file(tmp_path):
    engine = _make_engine(tmp_path, [{"project": "github:owner/repo", "score": 75.0}])
    engine.sync(push=False, dry_run=False)
    assert (tmp_path / "docs" / "data.json").exists()


def test_sync_summary_keys(tmp_path):
    engine = _make_engine(tmp_path, [{"project": "github:owner/repo", "score": 75.0}])
    summary = engine.sync(push=False)
    assert "added" in summary
    assert "updated" in summary
    assert "total" in summary
    assert "pushed" in summary


# ── pages_sync_command ────────────────────────────────────────────────────────

def test_pages_sync_command_json_output(tmp_path, capsys):
    engine = _make_engine(tmp_path, [{"project": "github:owner/repo", "score": 75.0}])
    from agentkit_cli.commands.pages_sync import pages_sync_command
    pages_sync_command(push=False, json_output=True, _engine=engine)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total" in data
    assert "added" in data


def test_pages_sync_command_no_push_returns_summary(tmp_path):
    engine = _make_engine(tmp_path, [{"project": "github:owner/repo", "score": 75.0}])
    from agentkit_cli.commands.pages_sync import pages_sync_command
    summary = pages_sync_command(push=False, _engine=engine)
    assert summary["total"] >= 1
