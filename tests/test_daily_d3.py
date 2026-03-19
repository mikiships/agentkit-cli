"""Tests for D3: Dark-theme HTML leaderboard renderer."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from agentkit_cli.engines.daily_leaderboard import DailyLeaderboard, RankedRepo
from agentkit_cli.renderers.daily_leaderboard_renderer import (
    render_leaderboard_html,
    _format_date,
    _score_class,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_leaderboard(n: int = 5, for_date: date = date(2026, 3, 19)) -> DailyLeaderboard:
    repos = [
        RankedRepo(
            rank=i,
            full_name=f"org/repo-{i}",
            description=f"Repo {i} description",
            stars=10000 // i,
            language="Python",
            url=f"https://github.com/org/repo-{i}",
            composite_score=float(95 - i * 5),
            top_finding=f"Top finding {i}",
        )
        for i in range(1, n + 1)
    ]
    return DailyLeaderboard(
        date=for_date,
        repos=repos,
        generated_at=datetime(2026, 3, 19, 9, 0, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# _format_date
# ---------------------------------------------------------------------------

class TestFormatDate:
    def test_march_19(self):
        assert _format_date(date(2026, 3, 19)) == "March 19, 2026"

    def test_january_1(self):
        assert _format_date(date(2026, 1, 1)) == "January 1, 2026"

    def test_december_31(self):
        assert _format_date(date(2025, 12, 31)) == "December 31, 2025"


# ---------------------------------------------------------------------------
# _score_class
# ---------------------------------------------------------------------------

class TestScoreClass:
    def test_high_score(self):
        assert _score_class(90.0) == "score-high"

    def test_mid_score(self):
        assert _score_class(65.0) == "score-mid"

    def test_low_score(self):
        assert _score_class(40.0) == "score-low"

    def test_none_score(self):
        assert _score_class(None) == "score-na"

    def test_boundary_80(self):
        assert _score_class(80.0) == "score-high"

    def test_boundary_60(self):
        assert _score_class(60.0) == "score-mid"


# ---------------------------------------------------------------------------
# render_leaderboard_html
# ---------------------------------------------------------------------------

class TestRenderLeaderboardHtml:
    def test_returns_string(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert isinstance(html, str)

    def test_is_valid_html(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_title_contains_date(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "March 19, 2026" in html

    def test_dark_background(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "#0d1117" in html

    def test_repo_names_present(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "org/repo-1" in html
        assert "org/repo-2" in html

    def test_top3_medals_present(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "🥇" in html
        assert "🥈" in html
        assert "🥉" in html

    def test_github_links_present(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "https://github.com/org/repo-1" in html

    def test_footer_contains_cta(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "agentkit daily --share" in html

    def test_scores_displayed(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        # rank 1 has score 90
        assert "90" in html

    def test_findings_displayed(self):
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert "Top finding 1" in html

    def test_empty_leaderboard_renders(self):
        lb = DailyLeaderboard(
            date=date(2026, 3, 19),
            repos=[],
            generated_at=datetime(2026, 3, 19, 9, 0, 0, tzinfo=timezone.utc),
        )
        html = render_leaderboard_html(lb)
        assert "Agent-Ready Repos" in html

    def test_version_in_html(self):
        from agentkit_cli import __version__
        lb = _make_leaderboard()
        html = render_leaderboard_html(lb)
        assert __version__ in html
