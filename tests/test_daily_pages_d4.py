"""Tests for D4: docs/index.html nav and feature card updates."""
from __future__ import annotations

from pathlib import Path

INDEX_HTML = Path(__file__).parent.parent / "docs" / "index.html"


def _html() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_index_html_exists():
    assert INDEX_HTML.exists()


def test_nav_has_leaderboard_link():
    html = _html()
    assert "leaderboard.html" in html, "Nav should link to leaderboard.html"


def test_nav_link_text():
    html = _html()
    assert "Daily Leaderboard" in html or "Leaderboard" in html


def test_feature_card_leaderboard_present():
    html = _html()
    assert "Daily Leaderboard" in html or "daily leaderboard" in html.lower()


def test_feature_card_mentions_pages_flag():
    html = _html()
    assert "--pages" in html or "agentkit daily" in html


def test_stat_test_count_updated():
    html = _html()
    # Should have a test count >= 2000 in the stats bar
    assert any(str(n) in html for n in range(2000, 9999)), "Stats bar test count not updated"
