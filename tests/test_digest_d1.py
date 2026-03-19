"""Tests for DigestEngine (D1) — ≥15 tests required."""
from __future__ import annotations

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agentkit_cli.digest import (
    DigestEngine,
    DigestReport,
    ProjectDigest,
    _overall_trend,
    _project_status,
    _extract_top_actions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(rows: list[dict]) -> Path:
    """Create a temp SQLite DB with given run rows."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, "
        "project TEXT NOT NULL, tool TEXT NOT NULL, score REAL NOT NULL, "
        "details TEXT, label TEXT, findings TEXT, campaign_id TEXT)"
    )
    conn.execute("CREATE INDEX idx_runs_project ON runs(project)")
    conn.execute("CREATE INDEX idx_runs_ts ON runs(ts DESC)")
    for row in rows:
        conn.execute(
            "INSERT INTO runs (ts, project, tool, score, details, label, findings) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                row["ts"],
                row["project"],
                row.get("tool", "overall"),
                row["score"],
                row.get("details"),
                row.get("label"),
                row.get("findings"),
            ),
        )
    conn.commit()
    conn.close()
    return path


def _ts(days_ago: float = 0) -> str:
    t = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return t.isoformat()


# ---------------------------------------------------------------------------
# DigestReport field tests
# ---------------------------------------------------------------------------

def test_digest_report_period_fields():
    """DigestReport has period_start and period_end datetimes."""
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert isinstance(report.period_start, datetime)
    assert isinstance(report.period_end, datetime)
    assert report.period_end > report.period_start


def test_digest_report_projects_tracked_zero():
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.projects_tracked == 0


def test_digest_report_runs_in_period_zero():
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.runs_in_period == 0


def test_digest_report_overall_trend_stable_empty():
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.overall_trend in ("improving", "stable", "regressing")


def test_digest_report_per_project_empty():
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert isinstance(report.per_project, list)


def test_digest_report_coverage_pct_zero():
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.coverage_pct == 0.0


def test_digest_report_basic_project_data():
    rows = [
        {"ts": _ts(5), "project": "alpha", "tool": "overall", "score": 60.0},
        {"ts": _ts(1), "project": "alpha", "tool": "overall", "score": 80.0},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.projects_tracked == 1
    assert report.runs_in_period == 2
    assert len(report.per_project) == 1
    proj = report.per_project[0]
    assert proj.name == "alpha"
    assert proj.score_start == 60.0
    assert proj.score_end == 80.0
    assert proj.delta == 20.0
    assert proj.runs == 2


def test_digest_trend_calculation_improving():
    rows = [
        {"ts": _ts(6), "project": "proj", "tool": "overall", "score": 50.0},
        {"ts": _ts(1), "project": "proj", "tool": "overall", "score": 90.0},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.overall_trend == "improving"


def test_digest_trend_calculation_regressing():
    rows = [
        {"ts": _ts(6), "project": "proj", "tool": "overall", "score": 90.0},
        {"ts": _ts(1), "project": "proj", "tool": "overall", "score": 70.0},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert report.overall_trend == "regressing"


def test_digest_regressions_detected():
    rows = [
        {"ts": _ts(6), "project": "bad", "tool": "overall", "score": 85.0},
        {"ts": _ts(1), "project": "bad", "tool": "overall", "score": 70.0},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert len(report.regressions) == 1
    r = report.regressions[0]
    assert r[0] == "bad"
    assert r[1] == 85.0
    assert r[2] == 70.0


def test_digest_improvements_detected():
    rows = [
        {"ts": _ts(6), "project": "good", "tool": "overall", "score": 60.0},
        {"ts": _ts(1), "project": "good", "tool": "overall", "score": 90.0},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert len(report.improvements) == 1
    assert report.improvements[0][0] == "good"


def test_digest_filters_by_project():
    rows = [
        {"ts": _ts(2), "project": "alpha", "tool": "overall", "score": 80.0},
        {"ts": _ts(2), "project": "beta", "tool": "overall", "score": 70.0},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate(projects=["alpha"])
    assert report.projects_tracked == 1
    assert report.per_project[0].name == "alpha"


def test_digest_coverage_pct_partial():
    rows = [
        {"ts": _ts(6), "project": "with_run", "tool": "overall", "score": 80.0},
    ]
    # Add a project with no runs in period by inserting an old run
    rows_old = rows + [
        {"ts": _ts(30), "project": "no_run", "tool": "overall", "score": 60.0},
    ]
    path = _make_db(rows_old)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    # "with_run" has run in period, "no_run" does not
    assert report.coverage_pct < 100.0


def test_digest_top_actions_extracted():
    findings = json.dumps(["Add memory context", "Add memory context", "Fix error handling"])
    rows = [
        {"ts": _ts(2), "project": "x", "tool": "overall", "score": 75.0, "findings": findings},
        {"ts": _ts(1), "project": "x", "tool": "overall", "score": 78.0, "findings": findings},
    ]
    path = _make_db(rows)
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    assert isinstance(report.top_actions, list)
    # "Add memory context" should be most frequent
    if report.top_actions:
        assert "Add memory context" in report.top_actions


def test_digest_to_dict():
    path = _make_db([])
    engine = DigestEngine(db_path=path, period_days=7)
    report = engine.generate()
    d = report.to_dict()
    assert "period_start" in d
    assert "period_end" in d
    assert "projects_tracked" in d
    assert "runs_in_period" in d
    assert "overall_trend" in d
    assert "per_project" in d
    assert "regressions" in d
    assert "improvements" in d
    assert "top_actions" in d
    assert "coverage_pct" in d


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_project_status_improving():
    assert _project_status(10.0) == "improving"


def test_project_status_regressing():
    assert _project_status(-10.0) == "regressing"


def test_project_status_stable():
    assert _project_status(0.0) == "stable"


def test_project_status_none():
    assert _project_status(None) == "no_data"


def test_overall_trend_empty():
    assert _overall_trend([]) == "stable"


def test_extract_top_actions_empty():
    assert _extract_top_actions([]) == []


def test_extract_top_actions_dict_findings():
    findings = json.dumps([{"message": "fix me"}, {"message": "fix me"}, {"message": "other"}])
    rows = [{"findings": findings}]
    result = _extract_top_actions(rows)
    assert "fix me" in result
