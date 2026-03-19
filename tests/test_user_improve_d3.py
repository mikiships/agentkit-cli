"""Tests for D3: Dark-theme HTML report renderer (≥10 tests)."""
from __future__ import annotations

import pytest

from agentkit_cli.renderers.user_improve_html import UserImproveHTMLRenderer, upload_user_improve_report
from agentkit_cli.user_improve import UserImproveReport, UserImproveResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(
    full_name: str = "alice/repo",
    before: float = 60.0,
    after: float = 75.0,
    skipped: bool = False,
    errors: list[str] | None = None,
) -> UserImproveResult:
    return UserImproveResult(
        repo_url=f"https://github.com/{full_name}",
        full_name=full_name,
        before_score=before,
        after_score=after,
        lift=round(after - before, 2),
        files_generated=["CLAUDE.md"] if not skipped else [],
        files_hardened=["hardening"] if not skipped else [],
        errors=errors or [],
        skipped=skipped,
    )


def _make_report(user: str = "alice", results: list | None = None) -> UserImproveReport:
    if results is None:
        results = [_make_result("alice/repo-0", 60.0, 75.0), _make_result("alice/repo-1", 45.0, 58.0)]
    return UserImproveReport(
        user=user,
        avatar_url="https://avatars.githubusercontent.com/u/12345",
        total_repos=10,
        improved=len([r for r in results if not r.skipped]),
        skipped=len([r for r in results if r.skipped]),
        results=results,
        summary_stats={
            "avg_before": 52.5,
            "avg_after": 66.5,
            "avg_lift": 14.0,
            "total_files_generated": 2,
            "total_files_hardened": 2,
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_renderer_returns_html():
    renderer = UserImproveHTMLRenderer()
    report = _make_report()
    html = renderer.render(report)
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html


def test_renderer_dark_theme():
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(_make_report())
    assert "#0d1117" in html or "background: #0d1117" in html


def test_renderer_user_handle_in_header():
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(_make_report("tiangolo"))
    assert "@tiangolo" in html


def test_renderer_avatar_img_tag():
    renderer = UserImproveHTMLRenderer()
    report = _make_report()
    report.avatar_url = "https://github.com/alice.png"
    html = renderer.render(report)
    assert '<img' in html
    assert "alice.png" in html


def test_renderer_avatar_placeholder_when_no_url():
    renderer = UserImproveHTMLRenderer()
    report = _make_report()
    report.avatar_url = ""
    html = renderer.render(report)
    assert "avatar-placeholder" in html or "👤" in html


def test_renderer_summary_bar_stats():
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(_make_report())
    assert "Repos Improved" in html
    assert "Avg Lift" in html


def test_renderer_per_repo_cards():
    renderer = UserImproveHTMLRenderer()
    report = _make_report()
    html = renderer.render(report)
    assert "alice/repo-0" in html
    assert "alice/repo-1" in html


def test_renderer_score_bars_present():
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(_make_report())
    assert "score-bar" in html
    assert "Before" in html
    assert "After" in html


def test_renderer_lift_badge_positive():
    renderer = UserImproveHTMLRenderer()
    result = _make_result("alice/repo", 60.0, 80.0)
    report = _make_report(results=[result])
    html = renderer.render(report)
    assert "+20" in html or "20.0" in html


def test_renderer_skipped_badge():
    renderer = UserImproveHTMLRenderer()
    result = _make_result("alice/repo", 50.0, 50.0, skipped=True)
    report = _make_report(results=[result])
    html = renderer.render(report)
    assert "skipped" in html


def test_renderer_error_shown():
    renderer = UserImproveHTMLRenderer()
    result = _make_result("alice/repo", 50.0, 50.0, errors=["Clone failed"])
    report = _make_report(results=[result])
    html = renderer.render(report)
    assert "Clone failed" in html


def test_renderer_links_to_repos():
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(_make_report())
    assert "https://github.com/alice/repo-0" in html


def test_renderer_version_in_footer():
    from agentkit_cli import __version__
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(_make_report())
    assert __version__ in html


def test_upload_user_improve_report_uses_upload_scorecard():
    from unittest.mock import patch
    with patch("agentkit_cli.renderers.user_improve_html.upload_scorecard", return_value="https://here.now/test") as mock_upload:
        url = upload_user_improve_report("<html>test</html>", api_key=None)
    assert url == "https://here.now/test"
    mock_upload.assert_called_once()
    # Verify it passed html as first arg
    args, kwargs = mock_upload.call_args
    assert args[0] == "<html>test</html>"
