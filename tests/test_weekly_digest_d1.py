"""D1 tests: WeeklyDigestEngine — ≥10 tests."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from agentkit_cli.weekly_digest_engine import (
    WeeklyDigestEngine,
    DigestReport,
    _score_to_grade,
    _PLACEHOLDER_REPOS,
)
from agentkit_cli.history import HistoryDB


def _make_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    db = HistoryDB(db_path=db_path)
    return db_path


def _insert_run(db_path: Path, project: str, score: float, ts: str | None = None) -> None:
    db = HistoryDB(db_path=db_path)
    if ts is None:
        ts = datetime.now(timezone.utc).isoformat()
    with db._connect() as conn:
        conn.execute(
            "INSERT INTO runs (ts, project, tool, score) VALUES (?, ?, 'overall', ?)",
            (ts, project, score),
        )


class TestScoreToGrade:
    def test_a_plus(self):
        assert _score_to_grade(95) == "A+"

    def test_a(self):
        assert _score_to_grade(87) == "A"

    def test_a_minus(self):
        assert _score_to_grade(81) == "A-"

    def test_b_plus(self):
        assert _score_to_grade(77) == "B+"

    def test_d(self):
        assert _score_to_grade(40) == "D"


class TestWeeklyDigestEngineEmptyState:
    def test_empty_returns_digest_report(self, tmp_path):
        db_path = _make_db(tmp_path)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert isinstance(report, DigestReport)

    def test_empty_uses_placeholder_repos(self, tmp_path):
        db_path = _make_db(tmp_path)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert len(report.top_repos) == len(_PLACEHOLDER_REPOS)
        assert report.top_repos[0]["repo"] == _PLACEHOLDER_REPOS[0]["repo"]

    def test_empty_week_stats_zeros(self, tmp_path):
        db_path = _make_db(tmp_path)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert report.week_stats["total_analyses"] == 0
        assert report.week_stats["avg_score"] == 0.0
        assert report.week_stats["top_scorer"] == ""

    def test_generated_at_is_iso_string(self, tmp_path):
        db_path = _make_db(tmp_path)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        # should parse without error
        datetime.fromisoformat(report.generated_at.replace("Z", "+00:00"))


class TestWeeklyDigestEngineWithData:
    def test_top_repos_sorted_by_score(self, tmp_path):
        db_path = _make_db(tmp_path)
        _insert_run(db_path, "low-repo", 50.0)
        _insert_run(db_path, "high-repo", 90.0)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert report.top_repos[0]["repo"] == "high-repo"

    def test_week_stats_total(self, tmp_path):
        db_path = _make_db(tmp_path)
        _insert_run(db_path, "repo-a", 80.0)
        _insert_run(db_path, "repo-b", 60.0)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert report.week_stats["total_analyses"] == 2

    def test_week_stats_avg(self, tmp_path):
        db_path = _make_db(tmp_path)
        _insert_run(db_path, "repo-a", 80.0)
        _insert_run(db_path, "repo-a", 60.0)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert report.week_stats["avg_score"] == 70.0

    def test_week_stats_top_scorer(self, tmp_path):
        db_path = _make_db(tmp_path)
        _insert_run(db_path, "best-repo", 95.0)
        _insert_run(db_path, "ok-repo", 60.0)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert report.week_stats["top_scorer"] == "best-repo"

    def test_since_days_filters_old_data(self, tmp_path):
        db_path = _make_db(tmp_path)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        _insert_run(db_path, "old-repo", 99.0, ts=old_ts)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate(since_days=7)
        # old data excluded => empty => placeholders
        assert report.week_stats["total_analyses"] == 0
        assert report.top_repos == list(_PLACEHOLDER_REPOS)

    def test_grade_in_top_repos(self, tmp_path):
        db_path = _make_db(tmp_path)
        _insert_run(db_path, "graded-repo", 88.0)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        repo = report.top_repos[0]
        assert "grade" in repo
        assert repo["grade"] == "A"

    def test_digest_report_dataclass_fields(self, tmp_path):
        db_path = _make_db(tmp_path)
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert hasattr(report, "top_repos")
        assert hasattr(report, "week_stats")
        assert hasattr(report, "generated_at")

    def test_top_repos_limit(self, tmp_path):
        db_path = _make_db(tmp_path)
        for i in range(10):
            _insert_run(db_path, f"repo-{i}", float(50 + i))
        engine = WeeklyDigestEngine(db_path=db_path)
        report = engine.generate()
        assert len(report.top_repos) <= 5

    def test_since_30_includes_more(self, tmp_path):
        db_path = _make_db(tmp_path)
        ts_20_days_ago = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        _insert_run(db_path, "older-repo", 75.0, ts=ts_20_days_ago)
        engine_7 = WeeklyDigestEngine(db_path=db_path)
        engine_30 = WeeklyDigestEngine(db_path=db_path)
        report_7 = engine_7.generate(since_days=7)
        report_30 = engine_30.generate(since_days=30)
        assert report_30.week_stats["total_analyses"] > report_7.week_stats["total_analyses"]
