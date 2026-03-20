"""Tests for D3: UserCardHTMLRenderer (≥10 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from agentkit_cli.user_card import UserCardResult
from agentkit_cli.renderers.user_card_html import UserCardHTMLRenderer, upload_user_card


def _make_result(username="alice", grade="B", avg_score=72.0):
    return UserCardResult(
        username=username,
        avatar_url=f"https://github.com/{username}.png",
        grade=grade,
        avg_score=avg_score,
        total_repos=10,
        analyzed_repos=8,
        context_coverage_pct=60.0,
        top_repo_name="best-repo",
        top_repo_score=90.0,
        agent_ready_count=3,
        summary_line=f"3/8 repos agent-ready · Grade {grade}",
    )


# ---------------------------------------------------------------------------
# HTML structure
# ---------------------------------------------------------------------------

def test_render_returns_string():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result())
    assert isinstance(html, str)


def test_render_has_doctype():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result())
    assert "<!DOCTYPE html>" in html


def test_render_has_username():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result(username="alice"))
    assert "@alice" in html


def test_render_has_grade():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result(grade="A"))
    assert "A" in html


def test_render_dark_background():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result())
    assert "#0d1117" in html


def test_render_avatar_img_tag():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result(username="alice"))
    assert "https://github.com/alice.png" in html


def test_render_top_repo_name():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result())
    assert "best-repo" in html


def test_render_has_agentkit_footer():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result())
    assert "agentkit" in html.lower()


def test_render_with_share_url_includes_embed_comment():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result(), share_url="https://here.now/card123")
    assert "Agent-Readiness Card" in html
    assert "here.now/card123" in html


def test_render_grade_A_green_color():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result(grade="A"))
    assert "#3fb950" in html


def test_render_grade_D_red_color():
    r = UserCardHTMLRenderer()
    html = r.render(_make_result(grade="D"))
    assert "#f85149" in html


def test_upload_user_card_calls_upload_scorecard():
    with patch("agentkit_cli.renderers.user_card_html.upload_scorecard", return_value="https://here.now/x") as mock:
        url = upload_user_card("<html>test</html>")
    assert url == "https://here.now/x"
    mock.assert_called_once_with("<html>test</html>")
