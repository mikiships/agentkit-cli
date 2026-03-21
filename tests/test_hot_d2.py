"""Tests for agentkit hot D2 — HTML report rendering."""
from __future__ import annotations

import pytest

from agentkit_cli.hot import (
    HotEngine,
    HotRepoResult,
    HotResult,
    render_hot_html,
)


def _make_result(repos=None, most_surprising=None):
    if repos is None:
        repos = [
            HotRepoResult(full_name="owner/repo1", rank=1, score=85.0, grade="B",
                          description="A cool repo", stars=500, language="Python"),
            HotRepoResult(full_name="owner/repo2", rank=2, score=20.0, grade="F",
                          description="Another repo", stars=200, language="JavaScript"),
        ]
    if most_surprising is None:
        most_surprising = repos[1]  # low score = surprising
    return HotResult(
        repos=repos,
        most_surprising=most_surprising,
        tweet_text="owner/repo2 is #2 trending but scores 20/100.",
        run_date="2026-03-21T12:00:00+00:00",
        language_filter=None,
        trending_available=True,
    )


def test_render_hot_html_returns_string():
    result = _make_result()
    html = render_hot_html(result)
    assert isinstance(html, str)


def test_render_hot_html_contains_doctype():
    result = _make_result()
    html = render_hot_html(result)
    assert "<!DOCTYPE html>" in html


def test_render_hot_html_dark_theme():
    result = _make_result()
    html = render_hot_html(result)
    assert "background: #0d1117" in html or "#0d1117" in html


def test_render_hot_html_contains_repo_names():
    result = _make_result()
    html = render_hot_html(result)
    assert "owner/repo1" in html
    assert "owner/repo2" in html


def test_render_hot_html_contains_scores():
    result = _make_result()
    html = render_hot_html(result)
    assert "85" in html
    assert "20" in html


def test_render_hot_html_contains_surprise_block():
    result = _make_result()
    html = render_hot_html(result)
    assert "Most Surprising" in html


def test_render_hot_html_contains_tweet():
    result = _make_result()
    html = render_hot_html(result)
    assert "owner/repo2 is #2 trending" in html


def test_render_hot_html_star_marker():
    result = _make_result()
    html = render_hot_html(result)
    # The most surprising repo should have a star marker
    assert "⭐" in html


def test_render_hot_html_github_links():
    result = _make_result()
    html = render_hot_html(result)
    assert "https://github.com/owner/repo1" in html


def test_render_hot_html_language_filter():
    repos = [
        HotRepoResult(full_name="owner/r1", rank=1, score=70.0, grade="C",
                      description="", stars=100, language="Python"),
    ]
    result = HotResult(
        repos=repos,
        most_surprising=repos[0],
        tweet_text="test tweet",
        run_date="2026-03-21T12:00:00+00:00",
        language_filter="python",
        trending_available=True,
    )
    html = render_hot_html(result)
    assert "python" in html


def test_render_hot_html_no_repos():
    result = HotResult(
        repos=[],
        most_surprising=None,
        tweet_text="fallback tweet",
        run_date="2026-03-21T12:00:00+00:00",
        language_filter=None,
        trending_available=False,
    )
    html = render_hot_html(result)
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
