"""Tests for agentkit_cli.monitor_config (D1)."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agentkit_cli.monitor_config import MonitorConfig, MonitorTarget, _dict_to_toml


# ---------------------------------------------------------------------------
# MonitorTarget unit tests
# ---------------------------------------------------------------------------

class TestMonitorTarget:
    def test_defaults(self):
        mt = MonitorTarget(target="github:owner/repo")
        assert mt.schedule == "daily"
        assert mt.alert_threshold == 10.0
        assert mt.last_checked is None
        assert mt.last_score is None
        assert mt.notify_slack is None

    def test_invalid_schedule_raises(self):
        with pytest.raises(ValueError, match="schedule must be one of"):
            MonitorTarget(target="x", schedule="monthly")

    def test_negative_threshold_raises(self):
        with pytest.raises(ValueError, match="alert_threshold"):
            MonitorTarget(target="x", alert_threshold=-1.0)

    def test_schedule_seconds_hourly(self):
        mt = MonitorTarget(target="x", schedule="hourly")
        assert mt.schedule_seconds() == 3600

    def test_schedule_seconds_daily(self):
        mt = MonitorTarget(target="x", schedule="daily")
        assert mt.schedule_seconds() == 86400

    def test_schedule_seconds_weekly(self):
        mt = MonitorTarget(target="x", schedule="weekly")
        assert mt.schedule_seconds() == 604800

    def test_is_due_no_last_checked(self):
        mt = MonitorTarget(target="x")
        assert mt.is_due() is True

    def test_is_due_recent(self):
        now = datetime.now(timezone.utc).isoformat()
        mt = MonitorTarget(target="x", schedule="daily", last_checked=now)
        assert mt.is_due() is False

    def test_is_due_overdue(self):
        old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        mt = MonitorTarget(target="x", schedule="daily", last_checked=old)
        assert mt.is_due() is True

    def test_has_notify_false(self):
        mt = MonitorTarget(target="x")
        assert mt.has_notify() is False

    def test_has_notify_slack(self):
        mt = MonitorTarget(target="x", notify_slack="https://hooks.slack.com/test")
        assert mt.has_notify() is True

    def test_has_notify_discord(self):
        mt = MonitorTarget(target="x", notify_discord="https://discord.com/api/webhooks/test")
        assert mt.has_notify() is True

    def test_to_dict_round_trip(self):
        mt = MonitorTarget(
            target="github:owner/repo",
            schedule="weekly",
            notify_slack="https://slack.example.com",
            min_score=80.0,
            alert_threshold=5.0,
            last_checked="2025-01-01T00:00:00+00:00",
            last_score=85.5,
        )
        d = mt.to_dict()
        mt2 = MonitorTarget.from_dict("github:owner/repo", d)
        assert mt2.schedule == mt.schedule
        assert mt2.notify_slack == mt.notify_slack
        assert mt2.min_score == mt.min_score
        assert mt2.alert_threshold == mt.alert_threshold
        assert mt2.last_score == mt.last_score

    def test_from_dict_defaults(self):
        mt = MonitorTarget.from_dict("x", {})
        assert mt.schedule == "daily"
        assert mt.alert_threshold == 10.0


# ---------------------------------------------------------------------------
# MonitorConfig unit tests
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path) -> MonitorConfig:
    return MonitorConfig(toml_path=tmp_path / ".agentkit.toml")


class TestMonitorConfig:
    def test_empty_config(self, tmp_path):
        cfg = _make_config(tmp_path)
        assert cfg.list_targets() == []

    def test_add_target(self, tmp_path):
        cfg = _make_config(tmp_path)
        mt = cfg.add_target("github:owner/repo")
        assert mt.target == "github:owner/repo"
        assert len(cfg.list_targets()) == 1

    def test_add_target_with_options(self, tmp_path):
        cfg = _make_config(tmp_path)
        mt = cfg.add_target(
            "github:owner/repo",
            schedule="weekly",
            notify_slack="https://slack.example.com",
            min_score=75.0,
            alert_threshold=5.0,
        )
        assert mt.schedule == "weekly"
        assert mt.notify_slack == "https://slack.example.com"
        assert mt.min_score == 75.0
        assert mt.alert_threshold == 5.0

    def test_remove_target_existing(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo")
        removed = cfg.remove_target("github:owner/repo")
        assert removed is True
        assert cfg.list_targets() == []

    def test_remove_target_nonexistent(self, tmp_path):
        cfg = _make_config(tmp_path)
        removed = cfg.remove_target("github:nonexistent/repo")
        assert removed is False

    def test_list_targets_multiple(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo1")
        cfg.add_target("github:owner/repo2")
        targets = cfg.list_targets()
        names = [t.target for t in targets]
        assert "github:owner/repo1" in names
        assert "github:owner/repo2" in names

    def test_persistence_round_trip(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo", schedule="hourly")
        # Reload from disk
        cfg2 = _make_config(tmp_path)
        targets = cfg2.list_targets()
        assert len(targets) == 1
        assert targets[0].schedule == "hourly"

    def test_update_last_run(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo")
        cfg.update_last_run("github:owner/repo", score=88.5)
        mt = cfg.get_target("github:owner/repo")
        assert mt is not None
        assert mt.last_score == 88.5
        assert mt.last_checked is not None

    def test_update_last_run_nonexistent(self, tmp_path):
        """update_last_run on nonexistent target should not raise."""
        cfg = _make_config(tmp_path)
        cfg.update_last_run("nonexistent", score=50.0)

    def test_save_preserves_other_sections(self, tmp_path):
        toml_path = tmp_path / ".agentkit.toml"
        toml_path.write_text('[gate]\nmin_score = 75\n\n[run]\noutput_dir = ".agentkit"\n')
        cfg = MonitorConfig(toml_path=toml_path)
        cfg.add_target("github:owner/repo")
        # Reload and verify gate section still exists
        content = toml_path.read_text()
        assert "min_score" in content or "gate" in content

    def test_get_target_found(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo")
        mt = cfg.get_target("github:owner/repo")
        assert mt is not None
        assert mt.target == "github:owner/repo"

    def test_get_target_not_found(self, tmp_path):
        cfg = _make_config(tmp_path)
        assert cfg.get_target("github:owner/nope") is None

    def test_add_target_overwrite(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo", schedule="daily")
        cfg.add_target("github:owner/repo", schedule="weekly")
        targets = cfg.list_targets()
        assert len(targets) == 1
        assert targets[0].schedule == "weekly"

    def test_update_last_run_custom_ts(self, tmp_path):
        cfg = _make_config(tmp_path)
        cfg.add_target("github:owner/repo")
        ts = "2025-06-01T12:00:00+00:00"
        cfg.update_last_run("github:owner/repo", score=77.0, ts=ts)
        mt = cfg.get_target("github:owner/repo")
        assert mt.last_checked == ts

    def test_add_invalid_schedule_raises(self, tmp_path):
        cfg = _make_config(tmp_path)
        with pytest.raises(ValueError):
            cfg.add_target("github:owner/repo", schedule="monthly")
