"""Tests for weekly HTML renderer (D3)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agentkit_cli.weekly_engine import WeeklyProjectStat, WeeklyReport
from agentkit_cli.weekly_html import render_weekly_html, _delta_str, _status_color


def _make_report(**kwargs) -> WeeklyReport:
    defaults = dict(
        period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2024, 1, 8, tzinfo=timezone.utc),
        projects_tracked=2,
        runs_in_period=10,
        overall_trend="improving",
        avg_score=72.5,
        coverage_pct=100.0,
        tweet_text="agentkit weekly Jan 01 📈\n2 projects · avg score 72.5 · 10 runs",
    )
    defaults.update(kwargs)
    return WeeklyReport(**defaults)


def test_render_returns_string():
    report = _make_report()
    html = render_weekly_html(report)
    assert isinstance(html, str)
    assert len(html) > 100


def test_render_has_doctype():
    report = _make_report()
    html = render_weekly_html(report)
    assert "<!DOCTYPE html>" in html or "<!doctype html" in html.lower()


def test_render_dark_background():
    report = _make_report()
    html = render_weekly_html(report)
    assert "#0d1117" in html


def test_render_includes_version():
    report = _make_report()
    html = render_weekly_html(report)
    from agentkit_cli import __version__
    assert __version__ in html


def test_render_includes_week_label():
    report = _make_report()
    html = render_weekly_html(report)
    assert "Jan 01" in html


def test_render_includes_stats():
    report = _make_report(projects_tracked=5, runs_in_period=42, avg_score=68.0)
    html = render_weekly_html(report)
    assert "5" in html
    assert "42" in html
    assert "68.0" in html


def test_render_project_rows():
    p = WeeklyProjectStat(
        name="myrepo",
        score_start=60.0,
        score_end=75.0,
        delta=15.0,
        runs=3,
        status="improving",
    )
    report = _make_report(per_project=[p])
    html = render_weekly_html(report)
    assert "myrepo" in html
    assert "+15.0" in html


def test_render_regression_color():
    p = WeeklyProjectStat(
        name="sinking",
        score_start=80.0,
        score_end=65.0,
        delta=-15.0,
        runs=2,
        status="regressing",
    )
    report = _make_report(per_project=[p], overall_trend="regressing", top_regressions=[p])
    html = render_weekly_html(report)
    assert "sinking" in html
    assert "#f85149" in html  # regression red


def test_render_tweet_block():
    tweet = "agentkit weekly Jan 01 📈\n5 projects"
    report = _make_report(tweet_text=tweet)
    html = render_weekly_html(report)
    assert "tweet-block" in html
    assert "agentkit weekly" in html


def test_delta_str_positive():
    assert _delta_str(5.0) == "+5.0"


def test_delta_str_negative():
    assert _delta_str(-3.0) == "-3.0"


def test_delta_str_none():
    assert _delta_str(None) == "—"


def test_status_color_improving():
    assert _status_color("improving") == "#3fb950"


def test_status_color_regressing():
    assert _status_color("regressing") == "#f85149"


def test_status_color_unknown():
    c = _status_color("unknown_status")
    assert c.startswith("#")


def test_render_custom_timestamp():
    report = _make_report()
    html = render_weekly_html(report, timestamp="2024-01-08 12:00 UTC")
    assert "2024-01-08 12:00 UTC" in html
