"""Tests for agentkit_cli/track_report.py — HTML report generation."""
from __future__ import annotations

from agentkit_cli.pr_tracker import TrackedPRStatus
from agentkit_cli.track_report import generate_html_report


def _make_status(
    id=1,
    repo="owner/repo",
    pr_number=1,
    pr_url="https://github.com/owner/repo/pull/1",
    campaign_id=None,
    submitted_at="2026-03-14T10:00:00+00:00",
    status="open",
    days_open=3,
    review_comments=0,
    is_merged=False,
) -> TrackedPRStatus:
    return TrackedPRStatus(
        id=id, repo=repo, pr_number=pr_number, pr_url=pr_url,
        campaign_id=campaign_id, submitted_at=submitted_at, status=status,
        days_open=days_open, review_comments=review_comments, is_merged=is_merged,
    )


def test_generate_html_report_returns_string():
    statuses = [_make_status()]
    html = generate_html_report(statuses)
    assert isinstance(html, str)
    assert len(html) > 100


def test_html_report_contains_header():
    statuses = [_make_status()]
    html = generate_html_report(statuses, title="My Report")
    assert "My Report" in html


def test_html_report_contains_stats():
    statuses = [
        _make_status(id=1, status="merged", is_merged=True),
        _make_status(id=2, status="open"),
        _make_status(id=3, status="closed"),
    ]
    html = generate_html_report(statuses)
    assert "1" in html  # merged count
    assert "Merge Rate" in html


def test_html_report_contains_repo_names():
    statuses = [
        _make_status(id=1, repo="alpha/one"),
        _make_status(id=2, repo="beta/two"),
    ]
    html = generate_html_report(statuses)
    assert "alpha/one" in html
    assert "beta/two" in html


def test_html_report_campaign_grouping():
    statuses = [
        _make_status(id=1, campaign_id="camp1", repo="a/b"),
        _make_status(id=2, campaign_id="camp2", repo="c/d"),
    ]
    html = generate_html_report(statuses)
    assert "camp1" in html
    assert "camp2" in html


def test_html_report_empty_statuses():
    html = generate_html_report([])
    assert "0%" in html  # 0% merge rate
    assert "<!DOCTYPE html>" in html


def test_html_report_dark_theme():
    html = generate_html_report([_make_status()])
    assert "#0f172a" in html  # dark background


def test_html_report_version_in_footer():
    html = generate_html_report([_make_status()], version="0.40.0")
    assert "0.40.0" in html


def test_html_report_pr_link():
    statuses = [_make_status(pr_url="https://github.com/owner/repo/pull/42", pr_number=42)]
    html = generate_html_report(statuses)
    assert "https://github.com/owner/repo/pull/42" in html


def test_html_report_status_badges():
    statuses = [
        _make_status(id=1, status="merged"),
        _make_status(id=2, status="open"),
        _make_status(id=3, status="closed"),
    ]
    html = generate_html_report(statuses)
    assert "badge-merged" in html
    assert "badge-open" in html
    assert "badge-closed" in html
