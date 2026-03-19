"""Tests for DigestReportRenderer (D3) — ≥12 tests required."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agentkit_cli.digest import DigestReport, ProjectDigest
from agentkit_cli.digest_report import DigestReportRenderer, _trend_badge, _delta_html


def _make_report(**kwargs) -> DigestReport:
    now = datetime.now(timezone.utc)
    defaults = dict(
        period_start=now - timedelta(days=7),
        period_end=now,
        projects_tracked=2,
        runs_in_period=5,
        overall_trend="stable",
        per_project=[],
        regressions=[],
        improvements=[],
        top_actions=[],
        coverage_pct=75.0,
    )
    defaults.update(kwargs)
    return DigestReport(**defaults)


def test_renderer_returns_html_string():
    renderer = DigestReportRenderer()
    report = _make_report()
    html = renderer.render(report)
    assert isinstance(html, str)
    assert html.strip().startswith("<!DOCTYPE html>")


def test_renderer_has_dark_bg():
    renderer = DigestReportRenderer()
    report = _make_report()
    html = renderer.render(report)
    assert "#0d1117" in html


def test_renderer_accent_color():
    renderer = DigestReportRenderer()
    report = _make_report()
    html = renderer.render(report)
    assert "#58a6ff" in html


def test_renderer_period_in_output():
    renderer = DigestReportRenderer()
    report = _make_report()
    html = renderer.render(report)
    assert report.period_start.strftime("%Y-%m-%d") in html
    assert report.period_end.strftime("%Y-%m-%d") in html


def test_renderer_overall_trend_badge_improving():
    renderer = DigestReportRenderer()
    report = _make_report(overall_trend="improving")
    html = renderer.render(report)
    assert "Improving" in html


def test_renderer_overall_trend_badge_regressing():
    renderer = DigestReportRenderer()
    report = _make_report(overall_trend="regressing")
    html = renderer.render(report)
    assert "Regressing" in html


def test_renderer_overall_trend_badge_stable():
    renderer = DigestReportRenderer()
    report = _make_report(overall_trend="stable")
    html = renderer.render(report)
    assert "Stable" in html


def test_renderer_per_project_cards():
    proj = ProjectDigest(name="myproject", score_start=60.0, score_end=80.0, delta=20.0, runs=3, status="improving")
    renderer = DigestReportRenderer()
    report = _make_report(per_project=[proj])
    html = renderer.render(report)
    assert "myproject" in html
    assert "60.0" in html
    assert "80.0" in html


def test_renderer_delta_positive_green():
    proj = ProjectDigest(name="proj", score_start=60.0, score_end=80.0, delta=20.0, runs=2, status="improving")
    renderer = DigestReportRenderer()
    report = _make_report(per_project=[proj])
    html = renderer.render(report)
    assert "delta-pos" in html or "+20.0" in html


def test_renderer_delta_negative_red():
    proj = ProjectDigest(name="proj", score_start=80.0, score_end=65.0, delta=-15.0, runs=2, status="regressing")
    renderer = DigestReportRenderer()
    report = _make_report(per_project=[proj])
    html = renderer.render(report)
    assert "delta-neg" in html or "-15.0" in html


def test_renderer_regressions_panel():
    renderer = DigestReportRenderer()
    report = _make_report(regressions=[("proj", 80.0, 60.0, "2026-03-10T00:00:00")])
    html = renderer.render(report)
    assert "Regressed" in html or "panel-regression" in html


def test_renderer_improvements_panel():
    renderer = DigestReportRenderer()
    report = _make_report(improvements=[("proj", 60.0, 85.0, "2026-03-10T00:00:00")])
    html = renderer.render(report)
    assert "Improved" in html or "panel-improvement" in html


def test_renderer_top_actions_in_output():
    renderer = DigestReportRenderer()
    report = _make_report(top_actions=["Fix error handling", "Add memory context"])
    html = renderer.render(report)
    assert "Fix error handling" in html
    assert "Add memory context" in html


def test_renderer_stats_section_present():
    renderer = DigestReportRenderer()
    report = _make_report(projects_tracked=5, runs_in_period=12)
    html = renderer.render(report)
    assert "5" in html  # projects tracked
    assert "12" in html  # runs in period


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_trend_badge_improving():
    html = _trend_badge("improving")
    assert "badge-improving" in html
    assert "Improving" in html


def test_trend_badge_regressing():
    html = _trend_badge("regressing")
    assert "badge-regressing" in html
    assert "Regressing" in html


def test_trend_badge_stable():
    html = _trend_badge("stable")
    assert "badge-stable" in html
    assert "Stable" in html


def test_delta_html_positive():
    html = _delta_html(10.0)
    assert "delta-pos" in html
    assert "+10.0" in html


def test_delta_html_negative():
    html = _delta_html(-5.0)
    assert "delta-neg" in html
    assert "-5.0" in html


def test_delta_html_none():
    html = _delta_html(None)
    assert "delta-neutral" in html


def test_renderer_empty_top_actions():
    renderer = DigestReportRenderer()
    report = _make_report(top_actions=[])
    html = renderer.render(report)
    assert "No recurring suggestions" in html
