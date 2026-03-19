"""Tests for D4: docs/index.html update for pages-trending."""
from __future__ import annotations

from pathlib import Path

import pytest

INDEX_PATH = Path(__file__).parent.parent / "docs" / "index.html"
QUICKSTART_CMD_PATH = Path(__file__).parent.parent / "agentkit_cli" / "commands" / "quickstart_cmd.py"


def _load_index() -> str:
    return INDEX_PATH.read_text(encoding="utf-8")

def _load_quickstart() -> str:
    return QUICKSTART_CMD_PATH.read_text(encoding="utf-8")


def test_index_has_trending_nav_link():
    content = _load_index()
    assert "trending.html" in content

def test_index_has_daily_trending_text():
    content = _load_index()
    assert "Daily Trending" in content or "daily trending" in content.lower()

def test_index_has_subscribe_cta():
    content = _load_index()
    assert "subscribe" in content.lower() or "Subscribe" in content

def test_index_has_pages_trending_feature_card():
    content = _load_index()
    assert "pages-trending" in content

def test_quickstart_mentions_pages_trending():
    content = _load_quickstart()
    assert "pages-trending" in content

def test_index_trending_link_points_to_correct_file():
    content = _load_index()
    assert 'href="trending.html"' in content
