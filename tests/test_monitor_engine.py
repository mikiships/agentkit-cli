"""Tests for agentkit_cli.monitor_engine (D2)."""
from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.monitor_config import MonitorConfig, MonitorTarget
from agentkit_cli.monitor_engine import MonitorEngine, MonitorResult


def _make_config(tmp_path: Path) -> MonitorConfig:
    return MonitorConfig(toml_path=tmp_path / ".agentkit.toml")


def _make_engine(tmp_path: Path, analyze_fn=None) -> MonitorEngine:
    cfg = _make_config(tmp_path)
    return MonitorEngine(config=cfg, analyze_fn=analyze_fn or (lambda t: 85.0))


# ---------------------------------------------------------------------------
# MonitorResult tests
# ---------------------------------------------------------------------------

class TestMonitorResult:
    def test_passed_no_error(self):
        r = MonitorResult(target="x", score=85.0, prev_score=80.0, delta=5.0, timestamp="ts")
        assert r.passed is True

    def test_passed_with_error(self):
        r = MonitorResult(target="x", score=0.0, prev_score=None, delta=0.0, timestamp="ts", error="fail")
        assert r.passed is False

    def test_fields(self):
        r = MonitorResult(target="github:a/b", score=72.0, prev_score=85.0, delta=-13.0, timestamp="ts")
        assert r.target == "github:a/b"
        assert r.score == 72.0
        assert r.delta == -13.0
        assert r.notify_fired is False


# ---------------------------------------------------------------------------
# check_target tests
# ---------------------------------------------------------------------------

class TestCheckTarget:
    def test_check_returns_score(self, tmp_path):
        engine = _make_engine(tmp_path, lambda t: 90.0)
        mt = MonitorTarget(target="github:owner/repo")
        result = engine.check_target(mt)
        assert result.score == 90.0
        assert result.error is None

    def test_check_computes_delta_from_prev(self, tmp_path):
        engine = _make_engine(tmp_path, lambda t: 90.0)
        mt = MonitorTarget(target="github:owner/repo", last_score=80.0)
        result = engine.check_target(mt)
        assert result.delta == 10.0
        assert result.prev_score == 80.0

    def test_check_delta_zero_on_first_run(self, tmp_path):
        engine = _make_engine(tmp_path, lambda t: 75.0)
        mt = MonitorTarget(target="github:owner/repo")
        result = engine.check_target(mt)
        assert result.prev_score is None
        assert result.delta == 0.0

    def test_check_failure_returns_error(self, tmp_path):
        engine = _make_engine(tmp_path, lambda t: None)
        mt = MonitorTarget(target="github:owner/repo")
        result = engine.check_target(mt)
        assert result.error is not None
        assert result.passed is False

    def test_check_timestamp_is_set(self, tmp_path):
        engine = _make_engine(tmp_path, lambda t: 88.0)
        mt = MonitorTarget(target="github:owner/repo")
        result = engine.check_target(mt)
        assert result.timestamp is not None
        # Should parse as ISO datetime
        datetime.fromisoformat(result.timestamp)


# ---------------------------------------------------------------------------
# should_notify tests
# ---------------------------------------------------------------------------

class TestShouldNotify:
    def _engine(self, tmp_path):
        return _make_engine(tmp_path)

    def test_notify_on_large_drop(self, tmp_path):
        engine = self._engine(tmp_path)
        mt = MonitorTarget(target="x", alert_threshold=10.0)
        result = MonitorResult(target="x", score=70.0, prev_score=85.0, delta=-15.0, timestamp="ts")
        assert engine.should_notify(result, mt) is True

    def test_notify_on_large_rise(self, tmp_path):
        engine = self._engine(tmp_path)
        mt = MonitorTarget(target="x", alert_threshold=10.0)
        result = MonitorResult(target="x", score=95.0, prev_score=80.0, delta=15.0, timestamp="ts")
        assert engine.should_notify(result, mt) is True

    def test_no_notify_small_delta(self, tmp_path):
        engine = self._engine(tmp_path)
        mt = MonitorTarget(target="x", alert_threshold=10.0)
        result = MonitorResult(target="x", score=83.0, prev_score=80.0, delta=3.0, timestamp="ts")
        assert engine.should_notify(result, mt) is False

    def test_notify_when_below_min_score(self, tmp_path):
        engine = self._engine(tmp_path)
        mt = MonitorTarget(target="x", alert_threshold=10.0, min_score=80.0)
        result = MonitorResult(target="x", score=75.0, prev_score=85.0, delta=-10.0, timestamp="ts")
        assert engine.should_notify(result, mt) is True

    def test_no_notify_on_error(self, tmp_path):
        engine = self._engine(tmp_path)
        mt = MonitorTarget(target="x", alert_threshold=5.0)
        result = MonitorResult(target="x", score=0.0, prev_score=None, delta=0.0, timestamp="ts", error="fail")
        assert engine.should_notify(result, mt) is False

    def test_no_notify_at_threshold(self, tmp_path):
        """Exact alert_threshold should trigger notify."""
        engine = self._engine(tmp_path)
        mt = MonitorTarget(target="x", alert_threshold=10.0)
        result = MonitorResult(target="x", score=70.0, prev_score=80.0, delta=-10.0, timestamp="ts")
        assert engine.should_notify(result, mt) is True


# ---------------------------------------------------------------------------
# run_check tests
# ---------------------------------------------------------------------------

class TestRunCheck:
    def test_run_check_updates_config(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo")
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 82.0)
        mt = cfg.get_target("github:owner/repo")
        engine.run_check(mt)
        cfg.load()
        mt_updated = cfg.get_target("github:owner/repo")
        assert mt_updated.last_score == 82.0
        assert mt_updated.last_checked is not None

    def test_run_check_notify_fires(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo", notify_slack="https://slack.example.com")
        mt = cfg.get_target("github:owner/repo")
        mt.last_score = 90.0
        notify_calls = []
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 70.0)
        engine._fire_notification = lambda r, t: notify_calls.append((r, t))
        result = engine.run_check(mt)
        # delta is -20 which exceeds threshold of 10
        assert result.notify_fired is True
        assert len(notify_calls) == 1

    def test_run_check_no_notify_small_delta(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo")
        mt = cfg.get_target("github:owner/repo")
        mt.last_score = 80.0
        notify_calls = []
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 82.0)
        engine._fire_notification = lambda r, t: notify_calls.append((r, t))
        result = engine.run_check(mt)
        assert result.notify_fired is False
        assert len(notify_calls) == 0


# ---------------------------------------------------------------------------
# run_all_due tests
# ---------------------------------------------------------------------------

class TestRunAllDue:
    def test_runs_due_targets(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo1")  # no last_checked → due
        cfg.add_target("github:owner/repo2")  # no last_checked → due
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 80.0)
        results = engine.run_all_due()
        assert len(results) == 2

    def test_skips_recent_targets(self, tmp_path):
        cfg = _make_config(tmp_path)
        now_ts = datetime.now(timezone.utc).isoformat()
        cfg.add_target("github:owner/repo1")
        cfg.update_last_run("github:owner/repo1", 85.0, ts=now_ts)
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 85.0)
        results = engine.run_all_due()
        assert len(results) == 0

    def test_run_target_specific(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo1")
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 77.0)
        result = engine.run_target("github:owner/repo1")
        assert result is not None
        assert result.score == 77.0

    def test_run_target_not_found(self, tmp_path):
        cfg = _make_config(tmp_path)
        engine = MonitorEngine(config=cfg, analyze_fn=lambda t: 77.0)
        result = engine.run_target("github:nonexistent/repo")
        assert result is None
