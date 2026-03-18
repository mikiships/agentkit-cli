"""Tests for TimelineEngine — D1 (≥12 tests)."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentkit_cli.history import HistoryDB
from agentkit_cli.timeline import TimelineEngine, STREAK_THRESHOLD


def _make_engine(tmp_path: Path) -> tuple[TimelineEngine, HistoryDB]:
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path=db_path)
    engine = TimelineEngine(db_path=db_path)
    return engine, db


def _populate(db: HistoryDB, project: str = "proj", n: int = 5) -> None:
    for i in range(n):
        db.record_run(project, "overall", float(60 + i * 5))
        db.record_run(project, "agentlint", float(55 + i * 4))
        db.record_run(project, "coderace", float(50 + i * 6))


# -------------------------------------------------------------------------
# load_runs
# -------------------------------------------------------------------------

def test_load_runs_empty(tmp_path):
    engine, _ = _make_engine(tmp_path)
    runs = engine.load_runs()
    assert runs == []


def test_load_runs_returns_list(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db)
    runs = engine.load_runs(project="proj")
    assert isinstance(runs, list)
    assert len(runs) > 0


def test_load_runs_sorted_oldest_first(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, n=3)
    runs = engine.load_runs(project="proj")
    timestamps = [r["ts"] for r in runs]
    assert timestamps == sorted(timestamps)


def test_load_runs_respects_limit(tmp_path):
    engine, db = _make_engine(tmp_path)
    for i in range(10):
        db.record_run("proj", "overall", float(70 + i))
    runs = engine.load_runs(project="proj", limit=5)
    assert len(runs) <= 5


def test_load_runs_project_filter(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "alpha", n=3)
    _populate(db, "beta", n=3)
    runs = engine.load_runs(project="alpha")
    for r in runs:
        assert r["project"] == "alpha"


def test_load_runs_all_projects(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "alpha", n=2)
    _populate(db, "beta", n=2)
    runs = engine.load_runs()
    projects = {r["project"] for r in runs}
    assert "alpha" in projects
    assert "beta" in projects


# -------------------------------------------------------------------------
# build_chart_data
# -------------------------------------------------------------------------

def test_build_chart_data_empty():
    engine = TimelineEngine.__new__(TimelineEngine)
    result = engine.build_chart_data([])
    assert result["dates"] == []
    assert result["scores"] == []
    assert result["projects"] == []
    assert result["by_project"] == {}


def test_build_chart_data_structure(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "proj", n=3)
    runs = engine.load_runs(project="proj")
    chart = engine.build_chart_data(runs)
    assert "dates" in chart
    assert "scores" in chart
    assert "per_tool" in chart
    assert "projects" in chart
    assert "by_project" in chart


def test_build_chart_data_by_project(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "proj", n=3)
    runs = engine.load_runs(project="proj")
    chart = engine.build_chart_data(runs)
    assert "proj" in chart["by_project"]
    pdata = chart["by_project"]["proj"]
    assert "dates" in pdata
    assert "scores" in pdata


def test_build_chart_data_per_tool_keys(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "proj", n=3)
    runs = engine.load_runs(project="proj")
    chart = engine.build_chart_data(runs)
    for tool in ["agentlint", "coderace", "agentmd", "agentreflect"]:
        assert tool in chart["per_tool"]


# -------------------------------------------------------------------------
# compute_stats
# -------------------------------------------------------------------------

def test_compute_stats_empty():
    engine = TimelineEngine.__new__(TimelineEngine)
    stats = engine.compute_stats([])
    assert stats["run_count"] == 0
    assert stats["trend"] == "stable"
    assert stats["min"] is None


def test_compute_stats_values(tmp_path):
    engine, db = _make_engine(tmp_path)
    for score in [60.0, 70.0, 80.0, 90.0]:
        db.record_run("proj", "overall", score)
    runs = engine.load_runs(project="proj")
    stats = engine.compute_stats(runs)
    assert stats["min"] == 60.0
    assert stats["max"] == 90.0
    assert stats["avg"] is not None
    assert stats["run_count"] == 4


def test_compute_stats_trend_improving(tmp_path):
    engine, db = _make_engine(tmp_path)
    for score in [60.0, 65.0, 70.0, 80.0, 85.0, 90.0]:
        db.record_run("proj", "overall", score)
    runs = engine.load_runs(project="proj")
    stats = engine.compute_stats(runs)
    assert stats["trend"] == "improving"
    assert stats["trend_delta"] > 0


def test_compute_stats_trend_declining(tmp_path):
    engine, db = _make_engine(tmp_path)
    for score in [90.0, 85.0, 80.0, 70.0, 65.0, 60.0]:
        db.record_run("proj", "overall", score)
    runs = engine.load_runs(project="proj")
    stats = engine.compute_stats(runs)
    assert stats["trend"] == "declining"


def test_compute_stats_streak(tmp_path):
    engine, db = _make_engine(tmp_path)
    # 3 below threshold, then 4 above
    for score in [50.0, 55.0, 60.0, 85.0, 87.0, 90.0, 88.0]:
        db.record_run("proj", "overall", score)
    runs = engine.load_runs(project="proj")
    stats = engine.compute_stats(runs)
    assert stats["streak"] == 4


def test_build_full_payload(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "proj", n=4)
    payload = engine.build_full_payload(project="proj", limit=50)
    assert "chart" in payload
    assert "stats" in payload
    assert "runs" in payload


def test_build_full_payload_since_filter(tmp_path):
    engine, db = _make_engine(tmp_path)
    _populate(db, "proj", n=5)
    # A far-future since should return empty runs
    payload = engine.build_full_payload(project="proj", limit=50, since="2099-01-01")
    assert payload["stats"]["run_count"] == 0
