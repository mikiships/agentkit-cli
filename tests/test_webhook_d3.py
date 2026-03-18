"""D3 tests: EventProcessor integration with history, notifications, and PR comments."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from agentkit_cli.webhook.event_processor import EventProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _push_event(full_name: str = "owner/repo") -> dict:
    return {
        "event_type": "push",
        "repository": {"full_name": full_name, "clone_url": ""},
        "ref": "refs/heads/main",
    }


def _pr_event(full_name: str = "owner/repo", pr_number: int = 5) -> dict:
    return {
        "event_type": "pull_request",
        "repository": {"full_name": full_name, "clone_url": ""},
        "ref": f"refs/pull/{pr_number}/head",
        "pull_request": {"number": pr_number, "title": "My PR"},
        "action": "opened",
    }


# ---------------------------------------------------------------------------
# D3.1 EventProcessor.process() runs analysis
# ---------------------------------------------------------------------------

def test_process_calls_run_analysis():
    ep = EventProcessor()
    with patch.object(ep, "_run_analysis", return_value=(70.0, None)) as mock_analyze:
        with patch.object(ep, "_record_history", return_value=True):
            ep.process(_push_event())
    mock_analyze.assert_called_once()


def test_process_records_in_history():
    ep = EventProcessor()
    with patch.object(ep, "_run_analysis", return_value=(70.0, None)):
        with patch.object(ep, "_record_history", return_value=True) as mock_record:
            ep.process(_push_event("acme/widget"))
    mock_record.assert_called_once_with("acme/widget", 70.0)


def test_process_fires_notification_on_regression():
    """Score drops by > threshold — notification fires."""
    ep = EventProcessor(
        notify_channels=["https://hooks.slack.com/x"],
        regression_threshold=5.0,
    )
    with patch.object(ep, "_run_analysis", return_value=(55.0, 70.0)):
        with patch.object(ep, "_record_history", return_value=True):
            with patch.object(ep, "_maybe_notify", return_value=True) as mock_notify:
                result = ep.process(_push_event())
    mock_notify.assert_called_once()
    assert result["notified"] is True


def test_process_no_notification_when_no_regression():
    ep = EventProcessor(
        notify_channels=["https://hooks.slack.com/x"],
        regression_threshold=5.0,
    )
    # score improved — no regression
    with patch.object(ep, "_run_analysis", return_value=(90.0, 70.0)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(_push_event())
    assert result["notified"] is False


def test_process_no_notification_when_no_channels():
    ep = EventProcessor(notify_channels=[], regression_threshold=5.0)
    with patch.object(ep, "_run_analysis", return_value=(40.0, 90.0)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(_push_event())
    assert result["notified"] is False


# ---------------------------------------------------------------------------
# D3.2 PR comment formatting
# ---------------------------------------------------------------------------

def test_pr_event_produces_comment_body():
    ep = EventProcessor()
    with patch.object(ep, "_run_analysis", return_value=(78.0, 75.0)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(_pr_event(pr_number=11))
    assert "comment_body" in result
    body = result["comment_body"]
    assert "agentkit" in body.lower()
    assert "#11" in body


def test_pr_comment_includes_score():
    ep = EventProcessor()
    with patch.object(ep, "_run_analysis", return_value=(92.0, None)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(_pr_event())
    assert "92" in result["comment_body"]


def test_pr_comment_includes_delta_when_prev_known():
    ep = EventProcessor()
    with patch.object(ep, "_run_analysis", return_value=(80.0, 70.0)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(_pr_event())
    body = result["comment_body"]
    # +10.0 pts delta
    assert "+10" in body


def test_push_event_has_no_comment_body():
    ep = EventProcessor()
    with patch.object(ep, "_run_analysis", return_value=(70.0, None)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(_push_event())
    assert "comment_body" not in result


# ---------------------------------------------------------------------------
# D3.3 History record integration (with real in-memory DB)
# ---------------------------------------------------------------------------

def test_record_history_writes_to_db(tmp_path):
    ep = EventProcessor()
    with patch("agentkit_cli.history.record_run") as mock_record:
        ep._record_history("myrepo", 88.5)
    mock_record.assert_called_once_with("myrepo", "composite", 88.5)


def test_get_previous_score_returns_none_when_empty():
    ep = EventProcessor()
    with patch("agentkit_cli.history.HistoryDB") as MockDB:
        MockDB.return_value.get_history.return_value = []
        score = ep._get_previous_score("noexist/repo")
    assert score is None


def test_get_previous_score_returns_float_when_found():
    ep = EventProcessor()
    with patch("agentkit_cli.history.HistoryDB") as MockDB:
        MockDB.return_value.get_history.return_value = [{"score": 77.5}]
        score = ep._get_previous_score("myrepo")
    assert score == 77.5


# ---------------------------------------------------------------------------
# D3.4 maybe_notify threshold
# ---------------------------------------------------------------------------

def test_maybe_notify_threshold_respected():
    ep = EventProcessor(
        notify_channels=["https://hooks.slack.com/x"],
        regression_threshold=10.0,
    )
    # Delta = 9.9 < 10.0 — should NOT notify
    notified = ep._maybe_notify("repo", 70.1, 80.0)
    assert notified is False


def test_maybe_notify_threshold_exceeded():
    ep = EventProcessor(
        notify_channels=["https://hooks.slack.com/x"],
        regression_threshold=5.0,
    )
    # Delta = 15 > 5 — should notify (but fire_notifications will fail silently)
    with patch("agentkit_cli.notifier.fire_notifications"):
        with patch("agentkit_cli.notifier.resolve_notify_configs", return_value=[]):
            notified = ep._maybe_notify("repo", 65.0, 80.0)
    assert notified is True
