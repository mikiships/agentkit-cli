"""Tests for WeeklyReportEngine (D1)."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agentkit_cli.weekly_engine import (
    WeeklyReportEngine,
    WeeklyReport,
    WeeklyProjectStat,
    _project_status,
    _overall_trend,
    _extract_top_actions,
    _extract_common_findings,
    _make_tweet,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_db(path: Path) -> sqlite3.Connection:
    """Create a minimal agentkit history DB."""
    conn = sqlite3.connect(str(path))
    conn.execute(
        """CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            project TEXT NOT NULL,
            tool TEXT NOT NULL,
            score REAL NOT NULL,
            details TEXT,
            label TEXT,
            findings TEXT
        )"""
    )
    conn.execute("CREATE TABLE IF NOT EXISTS label_aliases (label TEXT, alias TEXT)")
    conn.commit()
    return conn


def _insert_run(
    conn: sqlite3.Connection,
    project: str,
    score: float,
    days_ago: float = 0.0,
    tool: str = "overall",
    findings: list | None = None,
) -> None:
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    findings_str = json.dumps(findings) if findings is not None else None
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score, findings) VALUES (?, ?, ?, ?, ?)",
        (ts, project, tool, score, findings_str),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Unit tests for pure functions
# ---------------------------------------------------------------------------


def test_project_status_improving():
    assert _project_status(10.0) == "improving"


def test_project_status_regressing():
    assert _project_status(-10.0) == "regressing"


def test_project_status_stable():
    assert _project_status(0.0) == "stable"
    assert _project_status(3.0) == "stable"
    assert _project_status(-3.0) == "stable"


def test_project_status_no_data():
    assert _project_status(None) == "no_data"


def test_overall_trend_improving():
    stats = [
        WeeklyProjectStat("a", 50, 60, 10, 2, "improving"),
        WeeklyProjectStat("b", 40, 50, 10, 2, "improving"),
        WeeklyProjectStat("c", 70, 71, 1, 2, "stable"),
    ]
    assert _overall_trend(stats) == "improving"


def test_overall_trend_regressing():
    stats = [
        WeeklyProjectStat("a", 50, 40, -10, 2, "regressing"),
        WeeklyProjectStat("b", 60, 50, -10, 2, "regressing"),
        WeeklyProjectStat("c", 70, 71, 1, 2, "stable"),
    ]
    assert _overall_trend(stats) == "regressing"


def test_overall_trend_stable():
    stats = [
        WeeklyProjectStat("a", 50, 53, 3, 2, "stable"),
        WeeklyProjectStat("b", 60, 57, -3, 2, "stable"),
    ]
    assert _overall_trend(stats) == "stable"


def test_extract_top_actions_empty():
    assert _extract_top_actions([]) == []


def test_extract_top_actions_counts():
    runs = [
        {"findings": json.dumps([{"action": "Add README"}]), "project": "a"},
        {"findings": json.dumps([{"action": "Add README"}]), "project": "b"},
        {"findings": json.dumps([{"action": "Add CI"}]), "project": "c"},
    ]
    actions = _extract_top_actions(runs, top_n=5)
    assert actions[0] == "Add README"
    assert "Add CI" in actions


def test_extract_common_findings_threshold():
    runs = [
        {"findings": json.dumps([{"title": "Missing docs"}]), "project": "a"},
        {"findings": json.dumps([{"title": "Missing docs"}]), "project": "b"},
        {"findings": json.dumps([{"title": "Unique issue"}]), "project": "a"},
    ]
    common = _extract_common_findings(runs, min_projects=2, top_n=5)
    assert "Missing docs" in common
    assert "Unique issue" not in common


def test_extract_common_findings_empty():
    assert _extract_common_findings([], min_projects=2) == []


def test_make_tweet_length():
    report = WeeklyReport(
        period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2024, 1, 8, tzinfo=timezone.utc),
        projects_tracked=10,
        runs_in_period=25,
        overall_trend="improving",
        avg_score=72.5,
    )
    tweet = _make_tweet(report)
    assert len(tweet) <= 280
    assert "agentkit weekly" in tweet


def test_make_tweet_trend_emoji():
    for trend, emoji in [("improving", "📈"), ("regressing", "📉"), ("stable", "➡️")]:
        report = WeeklyReport(
            period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2024, 1, 8, tzinfo=timezone.utc),
            projects_tracked=5,
            runs_in_period=10,
            overall_trend=trend,
            avg_score=70.0,
        )
        tweet = _make_tweet(report)
        assert emoji in tweet


# ---------------------------------------------------------------------------
# Integration tests (with temp DB)
# ---------------------------------------------------------------------------


def test_engine_empty_db():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        _make_db(db_path)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert report.projects_tracked == 0
        assert report.runs_in_period == 0
        assert report.overall_trend == "stable"


def test_engine_single_project():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "myrepo", score=60.0, days_ago=6)
        _insert_run(conn, "myrepo", score=75.0, days_ago=1)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert report.projects_tracked == 1
        assert report.runs_in_period >= 2
        proj = report.per_project[0]
        assert proj.name == "myrepo"
        assert proj.status == "improving"
        assert proj.delta == 15.0


def test_engine_to_dict():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "repo1", score=50.0, days_ago=5)
        _insert_run(conn, "repo1", score=60.0, days_ago=1)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        d = report.to_dict()
        assert "period_start" in d
        assert "per_project" in d
        assert d["projects_tracked"] == 1


def test_engine_tweet_included():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "proj", score=65.0, days_ago=3)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert report.tweet_text
        assert len(report.tweet_text) <= 280


def test_engine_db_missing():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "nonexistent" / "history.db"
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert report.projects_tracked == 0


def test_engine_top_improvements_sorted():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "big_gainer", score=40.0, days_ago=6)
        _insert_run(conn, "big_gainer", score=80.0, days_ago=1)
        _insert_run(conn, "small_gainer", score=60.0, days_ago=6)
        _insert_run(conn, "small_gainer", score=67.0, days_ago=1)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert report.top_improvements[0].name == "big_gainer"


def test_engine_top_regressions():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "bad_proj", score=80.0, days_ago=6)
        _insert_run(conn, "bad_proj", score=60.0, days_ago=1)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert any(p.name == "bad_proj" for p in report.top_regressions)


def test_engine_avg_score():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "p1", score=60.0, days_ago=1)
        _insert_run(conn, "p2", score=80.0, days_ago=1)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7)
        assert report.avg_score == 70.0


def test_engine_coverage_pct():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "history.db"
        conn = _make_db(db_path)
        _insert_run(conn, "proj_a", score=70.0, days_ago=1)
        # proj_b will have no data in the window (run 10 days ago, window is 7)
        _insert_run(conn, "proj_b", score=70.0, days_ago=10)
        engine = WeeklyReportEngine(db_path=db_path)
        report = engine.generate(days=7, projects=["proj_a", "proj_b"])
        # proj_a has data, proj_b does not → 50% coverage
        assert report.coverage_pct == 50.0
