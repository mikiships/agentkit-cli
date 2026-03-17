"""Tests for agentkit_cli/pr_tracker.py — PRTracker class."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from agentkit_cli.pr_tracker import PRTracker, TrackedPRStatus, _compute_days_open
from agentkit_cli.history import HistoryDB


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db(tmp_path):
    return HistoryDB(db_path=tmp_path / "history.db")


@pytest.fixture
def tracker():
    return PRTracker(token="fake-token")


def _make_http_response(data: dict, remaining: str = "60") -> MagicMock:
    """Create a mock urllib response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.headers = {"X-RateLimit-Remaining": remaining}
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


# ---------------------------------------------------------------------------
# TrackedPRStatus dataclass
# ---------------------------------------------------------------------------


def test_tracked_pr_status_to_dict():
    status = TrackedPRStatus(
        id=1,
        repo="owner/repo",
        pr_number=42,
        pr_url="https://github.com/owner/repo/pull/42",
        campaign_id="abc123",
        submitted_at="2026-03-17T10:00:00+00:00",
        status="merged",
        days_open=3,
        review_comments=2,
        is_merged=True,
    )
    d = status.to_dict()
    assert d["repo"] == "owner/repo"
    assert d["pr_number"] == 42
    assert d["status"] == "merged"
    assert d["is_merged"] is True
    assert d["review_comments"] == 2


def test_tracked_pr_status_json_serializable():
    status = TrackedPRStatus(
        id=1, repo="a/b", pr_number=1, pr_url=None, campaign_id=None,
        submitted_at="2026-01-01T00:00:00+00:00", status="open",
        days_open=0, review_comments=0, is_merged=False,
    )
    # Should not raise
    json.dumps(status.to_dict())


# ---------------------------------------------------------------------------
# get_tracked_prs
# ---------------------------------------------------------------------------


def test_get_tracked_prs_empty(tmp_path, tracker):
    prs = tracker.get_tracked_prs(db_path=tmp_path / "history.db")
    assert prs == []


def test_get_tracked_prs_with_data(tmp_path, tracker):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", 10, "https://github.com/owner/repo/pull/10", campaign_id="camp1")
    db.record_pr("owner/other", 20, "https://github.com/owner/other/pull/20", campaign_id="camp2")

    prs = tracker.get_tracked_prs(db_path=tmp_path / "history.db")
    assert len(prs) == 2


def test_get_tracked_prs_filter_campaign(tmp_path, tracker):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", 10, None, campaign_id="camp1")
    db.record_pr("owner/other", 20, None, campaign_id="camp2")

    prs = tracker.get_tracked_prs(db_path=tmp_path / "history.db", campaign_id="camp1")
    assert len(prs) == 1
    assert prs[0]["campaign_id"] == "camp1"


# ---------------------------------------------------------------------------
# fetch_pr_status
# ---------------------------------------------------------------------------


def test_fetch_pr_status_open(tracker):
    api_data = {
        "state": "open",
        "merged": False,
        "merged_at": None,
        "mergeable_state": "clean",
        "created_at": "2026-03-14T10:00:00Z",
        "updated_at": "2026-03-17T10:00:00Z",
        "review_comments": 3,
        "commits": 2,
    }
    mock_resp = _make_http_response(api_data)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = tracker.fetch_pr_status("owner", "repo", 42)
    assert result["state"] == "open"
    assert result["merged"] is False
    assert result["review_comments"] == 3


def test_fetch_pr_status_merged(tracker):
    api_data = {
        "state": "closed",
        "merged": True,
        "merged_at": "2026-03-16T12:00:00Z",
        "review_comments": 5,
        "commits": 1,
    }
    mock_resp = _make_http_response(api_data)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = tracker.fetch_pr_status("owner", "repo", 42)
    assert result["merged"] is True
    assert result["state"] == "closed"


def test_fetch_pr_status_404(tracker):
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
        result = tracker.fetch_pr_status("owner", "repo", 9999)
    assert result["state"] == "unknown"
    assert result["error"] == "not_found"


def test_fetch_pr_status_rate_limited(tracker):
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 403, "Forbidden", {}, None)):
        result = tracker.fetch_pr_status("owner", "repo", 42)
    assert result["error"] == "rate_limited"


def test_fetch_pr_status_network_error(tracker):
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        result = tracker.fetch_pr_status("owner", "repo", 42)
    assert result["state"] == "unknown"
    assert "Connection refused" in result["error"]


def test_fetch_pr_status_low_rate_limit_sleeps(tracker):
    api_data = {"state": "open", "merged": False, "review_comments": 0, "commits": 0}
    mock_resp = _make_http_response(api_data, remaining="5")
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with patch("time.sleep") as mock_sleep:
            tracker.fetch_pr_status("owner", "repo", 42)
            mock_sleep.assert_called_with(5)


# ---------------------------------------------------------------------------
# refresh_statuses
# ---------------------------------------------------------------------------


def test_refresh_statuses_open(tmp_path, tracker):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", 10, "https://github.com/owner/repo/pull/10")
    prs = db.get_tracked_prs()

    api_data = {"state": "open", "merged": False, "review_comments": 1, "commits": 2}
    mock_resp = _make_http_response(api_data)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with patch("time.sleep"):
            statuses = tracker.refresh_statuses(prs, db_path=tmp_path / "history.db")

    assert len(statuses) == 1
    assert statuses[0].status == "open"
    assert statuses[0].is_merged is False


def test_refresh_statuses_merged(tmp_path, tracker):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", 5, "https://github.com/owner/repo/pull/5")
    prs = db.get_tracked_prs()

    api_data = {"state": "closed", "merged": True, "merged_at": "2026-03-15T10:00:00Z", "review_comments": 0, "commits": 1}
    mock_resp = _make_http_response(api_data)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with patch("time.sleep"):
            statuses = tracker.refresh_statuses(prs, db_path=tmp_path / "history.db")

    assert statuses[0].status == "merged"
    assert statuses[0].is_merged is True


def test_refresh_statuses_no_pr_number(tmp_path, tracker):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", None, None)
    prs = db.get_tracked_prs()

    with patch("urllib.request.urlopen") as mock_urlopen:
        with patch("time.sleep"):
            statuses = tracker.refresh_statuses(prs, db_path=tmp_path / "history.db")
        mock_urlopen.assert_not_called()

    assert statuses[0].status == "unknown"


def test_refresh_statuses_updates_db(tmp_path, tracker):
    db = HistoryDB(db_path=tmp_path / "history.db")
    db.record_pr("owner/repo", 7, "https://github.com/owner/repo/pull/7")
    prs = db.get_tracked_prs()

    api_data = {"state": "closed", "merged": True, "merged_at": "2026-03-16T00:00:00Z", "review_comments": 0, "commits": 1}
    mock_resp = _make_http_response(api_data)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        with patch("time.sleep"):
            tracker.refresh_statuses(prs, db_path=tmp_path / "history.db")

    updated = db.get_tracked_prs()
    assert updated[0]["last_status"] == "merged"
    assert updated[0]["last_checked_at"] is not None


# ---------------------------------------------------------------------------
# _compute_days_open
# ---------------------------------------------------------------------------


def test_compute_days_open_today():
    now = datetime.now(timezone.utc).isoformat()
    assert _compute_days_open(now) == 0


def test_compute_days_open_past():
    past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    assert _compute_days_open(past) == 5


def test_compute_days_open_invalid():
    assert _compute_days_open("not-a-date") == 0
