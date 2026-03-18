"""Tests for dark-theme HTML timeline report — D3 (≥10 tests)."""
from __future__ import annotations

from agentkit_cli.timeline_report import render_html_timeline, CHART_JS_CDN


def _make_payload(n: int = 4, project: str = "proj") -> dict:
    """Build a minimal but valid timeline payload."""
    import datetime
    dates = [f"2026-01-{i+1:02d}" for i in range(n)]
    scores = [float(70 + i * 3) for i in range(n)]
    per_tool = {
        "agentlint": [float(65 + i * 2) for i in range(n)],
        "coderace": [float(60 + i * 3) for i in range(n)],
        "agentmd": [None] * n,
        "agentreflect": [None] * n,
    }
    return {
        "project": project,
        "chart": {
            "dates": dates,
            "scores": scores,
            "per_tool": per_tool,
            "projects": [project],
            "by_project": {
                project: {
                    "dates": dates,
                    "scores": scores,
                    "per_tool": per_tool,
                }
            },
        },
        "stats": {
            "min": 70.0,
            "max": 79.0,
            "avg": 74.5,
            "trend": "improving",
            "trend_delta": 9.0,
            "streak": 3,
            "run_count": n,
        },
        "runs": [],
    }


def test_render_returns_string():
    payload = _make_payload()
    html = render_html_timeline(payload)
    assert isinstance(html, str)
    assert len(html) > 100


def test_render_has_doctype():
    html = render_html_timeline(_make_payload())
    assert "<!DOCTYPE html>" in html


def test_render_has_html_tag():
    html = render_html_timeline(_make_payload())
    assert "<html" in html
    assert "</html>" in html


def test_render_has_header_text():
    html = render_html_timeline(_make_payload())
    assert "Agent Quality Timeline" in html


def test_render_has_chart_js_cdn():
    html = render_html_timeline(_make_payload())
    assert CHART_JS_CDN in html or "chart.js" in html.lower()


def test_render_has_project_name():
    html = render_html_timeline(_make_payload(project="my-agent"), project_name="my-agent")
    assert "my-agent" in html


def test_render_has_footer():
    html = render_html_timeline(_make_payload())
    assert "agentkit-cli v0.44.0" in html


def test_render_has_stats_section():
    html = render_html_timeline(_make_payload())
    assert "Stats" in html


def test_render_has_per_tool_section():
    html = render_html_timeline(_make_payload())
    assert "Per-Tool" in html or "Breakdown" in html


def test_render_streak_badge():
    payload = _make_payload()
    html = render_html_timeline(payload)
    # streak=3, should show badge
    assert "runs above 80" in html or "streak" in html.lower() or "badge" in html.lower()


def test_render_empty_payload_no_crash():
    empty = {
        "project": None,
        "chart": {"dates": [], "scores": [], "per_tool": {}, "projects": [], "by_project": {}},
        "stats": {
            "min": None, "max": None, "avg": None,
            "trend": "stable", "trend_delta": 0.0, "streak": 0, "run_count": 0,
        },
        "runs": [],
    }
    html = render_html_timeline(empty)
    assert "No history found" in html


def test_render_trend_arrow_improving():
    html = render_html_timeline(_make_payload())
    assert "↑" in html


def test_render_chart_data_injected():
    payload = _make_payload()
    html = render_html_timeline(payload)
    # Chart.js datasets should be injected as JSON
    assert "datasets" in html


def test_render_multiproject():
    payload = _make_payload()
    payload["chart"]["by_project"]["other-proj"] = {
        "dates": ["2026-01-01", "2026-01-02"],
        "scores": [75.0, 80.0],
        "per_tool": {},
    }
    payload["chart"]["projects"].append("other-proj")
    html = render_html_timeline(payload)
    assert "other-proj" in html
