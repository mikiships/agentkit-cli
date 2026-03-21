"""Tests for agentkit site template HTML output (D2) — v0.83.0."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agentkit_cli.site_engine import SiteConfig, SiteEngine, _CSS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db_with_data(tmp_path):
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=tmp_path / "t.db")
    db.record_run("owner/repo-a", "agentlint", 95.0, label="python")
    db.record_run("owner/repo-b", "agentlint", 70.0, label="typescript")
    db.record_run("owner/repo-a", "agentlint", 93.0, label="python")
    return db


@pytest.fixture
def engine(db_with_data):
    cfg = SiteConfig(base_url="https://test.example.com/", topics=["python", "typescript"])
    return SiteEngine(config=cfg, db=db_with_data)


# ---------------------------------------------------------------------------
# HTML structure tests
# ---------------------------------------------------------------------------

def test_index_html_dark_theme(engine):
    page = engine.generate_index()
    # dark background color present
    assert "#0d1117" in page.html


def test_index_html_has_nav(engine):
    page = engine.generate_index()
    assert "<header>" in page.html or "<nav>" in page.html


def test_index_html_has_footer(engine):
    page = engine.generate_index()
    assert "<footer>" in page.html
    assert "agentkit-cli" in page.html


def test_index_html_has_hero(engine):
    page = engine.generate_index()
    assert "hero" in page.html


def test_index_html_stats_section(engine):
    page = engine.generate_index()
    # Stats section exists
    assert "stat-card" in page.html


def test_index_html_topics_grid(engine):
    page = engine.generate_index()
    assert "topics-grid" in page.html or "topic-card" in page.html


def test_index_html_recent_scores_table(engine):
    page = engine.generate_index()
    assert "<table" in page.html


def test_topic_page_html_structure(engine):
    page = engine.generate_topic_page("python")
    assert "<table" in page.html
    assert "Python" in page.html
    assert "breadcrumb" in page.html


def test_topic_page_score_badges(engine):
    page = engine.generate_topic_page("python")
    assert "badge" in page.html


def test_topic_page_links_to_repo(engine):
    page = engine.generate_topic_page("python")
    assert "repo/" in page.html


def test_repo_page_html_structure(engine):
    page = engine.generate_repo_page("owner", "repo-a")
    assert "owner/repo-a" in page.html
    assert "stat-card" in page.html
    assert "github.com/owner/repo-a" in page.html


def test_repo_page_has_history_chart(engine):
    # repo-a has 2 runs, should get sparkline
    page = engine.generate_repo_page("owner", "repo-a")
    assert "history" in page.html.lower() or "svg" in page.html.lower()


def test_sitemap_xml_valid(engine, tmp_path):
    result = engine.generate_site(tmp_path / "s", topics=["python"], limit=5)
    assert result.sitemap_xml.startswith('<?xml')
    assert 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' in result.sitemap_xml


def test_all_pages_have_canonical(engine):
    for topic in ["python", "typescript"]:
        page = engine.generate_topic_page(topic)
        assert 'rel="canonical"' in page.html
        assert page.meta.canonical_url.startswith("https://")


def test_all_pages_have_json_ld(engine):
    index = engine.generate_index()
    topic = engine.generate_topic_page("python")
    repo = engine.generate_repo_page("owner", "repo-a")
    for page in [index, topic, repo]:
        assert "application/ld+json" in page.html
        assert "@context" in page.html


def test_css_dark_theme_variable():
    # The shared CSS should contain dark-theme colors
    assert "#0d1117" in _CSS
    assert "#161b22" in _CSS
