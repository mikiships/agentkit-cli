"""Tests for InsightsEngine (agentkit_cli/insights.py)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from agentkit_cli.insights import InsightsEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(tmp_path: Path) -> Path:
    """Create a minimal history DB compatible with HistoryDB schema."""
    db_path = tmp_path / "history.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE runs (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ts      TEXT NOT NULL,
            project TEXT NOT NULL,
            tool    TEXT NOT NULL,
            score   REAL NOT NULL,
            details TEXT,
            findings TEXT,
            label   TEXT
        )
    """)
    conn.commit()
    conn.close()
    return db_path


def _insert_run(
    db_path: Path,
    project: str,
    tool: str = "overall",
    score: float = 80.0,
    ts: str = "2026-01-01T00:00:00+00:00",
    findings: list | None = None,
) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score, findings) VALUES (?, ?, ?, ?, ?)",
        (ts, project, tool, score, json.dumps(findings) if findings is not None else None),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Empty DB
# ---------------------------------------------------------------------------

def test_empty_db_portfolio_summary(tmp_path):
    db_path = _make_db(tmp_path)
    engine = InsightsEngine(db_path=db_path)
    summary = engine.get_portfolio_summary()
    assert summary["total_runs"] == 0
    assert summary["avg_score"] is None
    assert summary["unique_repos"] == 0
    assert summary["best_repo"] is None
    assert summary["worst_repo"] is None


def test_empty_db_common_findings(tmp_path):
    db_path = _make_db(tmp_path)
    engine = InsightsEngine(db_path=db_path)
    assert engine.get_common_findings() == []


def test_empty_db_outliers(tmp_path):
    db_path = _make_db(tmp_path)
    engine = InsightsEngine(db_path=db_path)
    assert engine.get_outliers() == []


def test_empty_db_trending(tmp_path):
    db_path = _make_db(tmp_path)
    engine = InsightsEngine(db_path=db_path)
    assert engine.get_trending() == []


def test_no_db_file_returns_empty(tmp_path):
    """InsightsEngine with non-existent DB should return empty results gracefully."""
    engine = InsightsEngine(db_path=tmp_path / "nonexistent.db")
    assert engine.get_portfolio_summary()["total_runs"] == 0
    assert engine.get_common_findings() == []
    assert engine.get_outliers() == []
    assert engine.get_trending() == []


# ---------------------------------------------------------------------------
# Portfolio summary
# ---------------------------------------------------------------------------

def test_portfolio_summary_single_run(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", score=75.0)
    engine = InsightsEngine(db_path=db_path)
    summary = engine.get_portfolio_summary()
    assert summary["total_runs"] == 1
    assert summary["avg_score"] == 75.0
    assert summary["unique_repos"] == 1
    assert summary["best_repo"] == "repo-a"
    assert summary["worst_repo"] == "repo-a"


def test_portfolio_summary_multiple_repos(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", score=90.0, ts="2026-01-01T00:00:00+00:00")
    _insert_run(db_path, "repo-b", score=50.0, ts="2026-01-02T00:00:00+00:00")
    _insert_run(db_path, "repo-c", score=70.0, ts="2026-01-03T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    summary = engine.get_portfolio_summary()
    assert summary["total_runs"] == 3
    assert summary["unique_repos"] == 3
    assert summary["best_repo"] == "repo-a"
    assert summary["worst_repo"] == "repo-b"
    assert abs(summary["avg_score"] - 70.0) < 0.5


def test_portfolio_summary_ignores_non_overall_tool(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", tool="agentlint", score=60.0)
    _insert_run(db_path, "repo-a", tool="overall", score=80.0)
    engine = InsightsEngine(db_path=db_path)
    summary = engine.get_portfolio_summary()
    # Only overall runs count for total_runs
    assert summary["total_runs"] == 1
    assert summary["avg_score"] == 80.0


# ---------------------------------------------------------------------------
# Common findings
# ---------------------------------------------------------------------------

def test_common_findings_returns_multi_repo_findings(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", findings=["missing-tools-section", "no-examples"])
    _insert_run(db_path, "repo-b", findings=["missing-tools-section", "stale-date"])
    engine = InsightsEngine(db_path=db_path)
    results = engine.get_common_findings(min_repos=2)
    codes = [r["finding"] for r in results]
    assert "missing-tools-section" in codes
    assert "no-examples" not in codes
    assert "stale-date" not in codes


def test_common_findings_min_repos_1(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", findings=["finding-x"])
    engine = InsightsEngine(db_path=db_path)
    results = engine.get_common_findings(min_repos=1)
    assert len(results) == 1
    assert results[0]["finding"] == "finding-x"


def test_common_findings_sorted_by_repo_count(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", ts="2026-01-01T00:00:00+00:00", findings=["a", "b"])
    _insert_run(db_path, "repo-b", ts="2026-01-02T00:00:00+00:00", findings=["a", "b"])
    _insert_run(db_path, "repo-c", ts="2026-01-03T00:00:00+00:00", findings=["a"])
    engine = InsightsEngine(db_path=db_path)
    results = engine.get_common_findings(min_repos=2)
    assert results[0]["finding"] == "a"
    assert results[0]["repo_count"] == 3


def test_common_findings_empty_when_no_findings(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a")
    _insert_run(db_path, "repo-b")
    engine = InsightsEngine(db_path=db_path)
    assert engine.get_common_findings() == []


def test_common_findings_from_details_fallback(tmp_path):
    """Findings embedded in the details JSON column should also be picked up."""
    db_path = _make_db(tmp_path)
    details_a = json.dumps({"findings": ["fallback-finding"]})
    details_b = json.dumps({"findings": ["fallback-finding"]})
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score, details, findings) VALUES (?, ?, ?, ?, ?, ?)",
        ("2026-01-01T00:00:00+00:00", "repo-a", "overall", 80.0, details_a, None),
    )
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score, details, findings) VALUES (?, ?, ?, ?, ?, ?)",
        ("2026-01-02T00:00:00+00:00", "repo-b", "overall", 75.0, details_b, None),
    )
    conn.commit()
    conn.close()
    engine = InsightsEngine(db_path=db_path)
    results = engine.get_common_findings(min_repos=2)
    assert any(r["finding"] == "fallback-finding" for r in results)


# ---------------------------------------------------------------------------
# Outliers
# ---------------------------------------------------------------------------

def test_outliers_returns_bottom_quartile(tmp_path):
    db_path = _make_db(tmp_path)
    repos = [("repo-a", 90.0), ("repo-b", 85.0), ("repo-c", 70.0), ("repo-d", 40.0)]
    for i, (proj, score) in enumerate(repos):
        _insert_run(db_path, proj, score=score, ts=f"2026-01-0{i+1}T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    outliers = engine.get_outliers(percentile=25)
    projects = [o["project"] for o in outliers]
    assert "repo-d" in projects
    assert "repo-a" not in projects


def test_outliers_sorted_ascending(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", score=30.0, ts="2026-01-01T00:00:00+00:00")
    _insert_run(db_path, "repo-b", score=20.0, ts="2026-01-02T00:00:00+00:00")
    _insert_run(db_path, "repo-c", score=90.0, ts="2026-01-03T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    outliers = engine.get_outliers(percentile=50)
    scores = [o["latest_score"] for o in outliers]
    assert scores == sorted(scores)


def test_outliers_single_project(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "solo-repo", score=55.0)
    engine = InsightsEngine(db_path=db_path)
    outliers = engine.get_outliers(percentile=25)
    # With only one project, it IS the bottom quartile
    assert len(outliers) == 1
    assert outliers[0]["project"] == "solo-repo"


# ---------------------------------------------------------------------------
# Trending
# ---------------------------------------------------------------------------

def test_trending_detects_improvement(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-a", score=50.0, ts="2026-01-01T00:00:00+00:00")
    _insert_run(db_path, "repo-a", score=75.0, ts="2026-01-02T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    trending = engine.get_trending()
    assert len(trending) == 1
    assert trending[0]["project"] == "repo-a"
    assert trending[0]["delta"] == 25.0
    assert trending[0]["direction"] == "up"


def test_trending_detects_regression(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-b", score=85.0, ts="2026-01-01T00:00:00+00:00")
    _insert_run(db_path, "repo-b", score=60.0, ts="2026-01-02T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    trending = engine.get_trending()
    assert len(trending) == 1
    assert trending[0]["direction"] == "down"
    assert trending[0]["delta"] == -25.0


def test_trending_ignores_small_changes(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-c", score=80.0, ts="2026-01-01T00:00:00+00:00")
    _insert_run(db_path, "repo-c", score=85.0, ts="2026-01-02T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    trending = engine.get_trending()
    # Delta is 5, below the >10 threshold
    assert len(trending) == 0


def test_trending_requires_at_least_two_runs(tmp_path):
    db_path = _make_db(tmp_path)
    _insert_run(db_path, "repo-single", score=50.0)
    engine = InsightsEngine(db_path=db_path)
    assert engine.get_trending() == []


def test_trending_sorted_by_abs_delta(tmp_path):
    db_path = _make_db(tmp_path)
    # repo-x: delta 30
    _insert_run(db_path, "repo-x", score=40.0, ts="2026-01-01T00:00:00+00:00")
    _insert_run(db_path, "repo-x", score=70.0, ts="2026-01-02T00:00:00+00:00")
    # repo-y: delta 15
    _insert_run(db_path, "repo-y", score=60.0, ts="2026-01-03T00:00:00+00:00")
    _insert_run(db_path, "repo-y", score=75.0, ts="2026-01-04T00:00:00+00:00")
    engine = InsightsEngine(db_path=db_path)
    trending = engine.get_trending()
    assert trending[0]["project"] == "repo-x"


# ---------------------------------------------------------------------------
# Schema migration: old DB without findings column
# ---------------------------------------------------------------------------

def test_old_db_without_findings_column(tmp_path):
    """InsightsEngine must handle DBs without the findings column gracefully."""
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            project TEXT NOT NULL,
            tool TEXT NOT NULL,
            score REAL NOT NULL,
            details TEXT,
            label TEXT
        )
    """)
    conn.execute(
        "INSERT INTO runs (ts, project, tool, score) VALUES (?, ?, ?, ?)",
        ("2026-01-01T00:00:00+00:00", "old-repo", "overall", 72.0),
    )
    conn.commit()
    conn.close()

    engine = InsightsEngine(db_path=db_path)
    # Should not crash and should return meaningful data
    summary = engine.get_portfolio_summary()
    assert summary["total_runs"] == 1
    assert summary["avg_score"] == 72.0
    # findings-dependent methods should return empty, not crash
    assert engine.get_common_findings() == []


# ---------------------------------------------------------------------------
# Many runs / same repo repeated
# ---------------------------------------------------------------------------

def test_many_runs_same_repo(tmp_path):
    db_path = _make_db(tmp_path)
    for i in range(10):
        _insert_run(
            db_path,
            "heavy-repo",
            score=60.0 + i,
            ts=f"2026-01-{i+1:02d}T00:00:00+00:00",
        )
    engine = InsightsEngine(db_path=db_path)
    summary = engine.get_portfolio_summary()
    assert summary["total_runs"] == 10
    assert summary["unique_repos"] == 1
    assert summary["best_repo"] == "heavy-repo"
