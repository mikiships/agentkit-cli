"""Tests for agentkit site_engine (D1) — v0.83.0."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.site_engine import (
    PageMeta,
    RepoEntry,
    SiteConfig,
    SiteEngine,
    SitePage,
    SiteResult,
    _make_sparkline,
    build_frontdoor_stats,
    score_to_grade,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=tmp_path / "test.db")
    return db


@pytest.fixture
def populated_db(tmp_db):
    tmp_db.record_run("langchain-ai/langchain", "agentlint", 88.0, label="python")
    tmp_db.record_run("fastapi/fastapi", "agentlint", 75.0, label="python")
    tmp_db.record_run("tokio-rs/tokio", "agentlint", 62.0, label="rust")
    tmp_db.record_run("langchain-ai/langchain", "agentlint", 91.0, label="python")
    return tmp_db


@pytest.fixture
def engine(tmp_db):
    return SiteEngine(db=tmp_db)


@pytest.fixture
def populated_engine(populated_db):
    return SiteEngine(db=populated_db)


# ---------------------------------------------------------------------------
# Data model tests
# ---------------------------------------------------------------------------

def test_site_config_defaults():
    cfg = SiteConfig()
    assert "python" in cfg.topics
    assert cfg.limit == 20
    assert cfg.base_url.startswith("https://")


def test_site_page_dataclass():
    meta = PageMeta(title="t", description="d", canonical_url="https://x.com/")
    page = SitePage(path="index.html", html="<html>", meta=meta)
    assert page.path == "index.html"


def test_repo_entry_grade():
    e = RepoEntry(repo="a/b", score=90, grade="A", last_run="2026-01-01")
    assert e.grade == "A"


def test_site_result_empty():
    r = SiteResult()
    assert r.pages == []
    assert r.share_url is None


# ---------------------------------------------------------------------------
# SiteEngine core
# ---------------------------------------------------------------------------

def test_engine_init_default(tmp_path):
    engine = SiteEngine(db_path=tmp_path / "x.db")
    assert engine.config is not None


def test_engine_count_unique_repos_empty(engine):
    assert engine._count_unique_repos() == 0


def test_engine_count_unique_repos_populated(populated_engine):
    count = populated_engine._count_unique_repos()
    assert count == 3


def test_engine_get_all_repos_empty(engine):
    repos = engine._get_all_repos()
    assert repos == []


def test_engine_get_all_repos_populated(populated_engine):
    repos = populated_engine._get_all_repos()
    assert len(repos) >= 2
    # Sorted by score descending
    scores = [r.score for r in repos]
    assert scores == sorted(scores, reverse=True)


def test_engine_get_repos_for_topic(populated_engine):
    repos = populated_engine._get_repos_for_topic("python")
    # langchain-ai/langchain and fastapi/fastapi match "python" label
    repo_names = [r.repo for r in repos]
    assert any("langchain" in n for n in repo_names)


def test_engine_get_repos_for_topic_no_match(populated_engine):
    repos = populated_engine._get_repos_for_topic("elixir")
    assert repos == []


def test_generate_index_empty(engine):
    page = engine.generate_index()
    assert page.path == "index.html"
    assert "<html" in page.html
    assert "agentkit" in page.html.lower()
    assert page.meta.canonical_url.startswith("https://")


def test_generate_index_has_seo_tags(engine):
    page = engine.generate_index()
    assert "<title>" in page.html
    assert 'name="description"' in page.html
    assert 'rel="canonical"' in page.html
    assert "application/ld+json" in page.html


def test_generate_index_shows_current_frontdoor_story(engine):
    page = engine.generate_index()
    assert "v1.3.0" in page.html
    assert "4833" in page.html
    assert "agentkit contract" in page.html
    assert "agentkit contract --init" in page.html


def test_build_frontdoor_stats_derives_version_counter():
    stats = build_frontdoor_stats({"version": "1.2.1"})
    assert stats["version"] == "1.2.1"
    assert stats["versions"] == 102


def test_generate_index_uses_site_data_as_frontdoor_source(engine):
    site_data = {
        "generated_at": "2026-04-19T12:00:00+00:00",
        "frontdoor": {
            "version": "1.2.1",
            "tests": 4901,
            "versions": 102,
            "packages": 7,
        },
        "repos": [
            {
                "name": "openai/openai-python",
                "url": "https://github.com/openai/openai-python",
                "score": 91,
                "grade": "A",
                "ecosystem": "python",
                "source": "ecosystem",
            },
            {
                "name": "pydantic/pydantic",
                "url": "https://github.com/pydantic/pydantic",
                "score": 82,
                "grade": "A",
                "ecosystem": "python",
                "source": "community",
            },
        ],
        "stats": {"total": 2, "median": 86.5, "top_score": 91},
    }

    page = engine.generate_index(site_data=site_data)

    assert "v1.2.1" in page.html
    assert 'data-stat="tests">4901<' in page.html
    assert 'data-stat="versions">102<' in page.html
    assert 'data-stat="packages">7<' in page.html
    assert 'id="repos-scored-stat">2<' in page.html
    assert 'id="community-scored-stat">1<' in page.html
    assert "openai/openai-python" in page.html
    assert "pydantic/pydantic" in page.html


def test_generate_topic_page(populated_engine):
    page = populated_engine.generate_topic_page("python")
    assert "python" in page.path.lower()
    assert "<table" in page.html


def test_generate_topic_page_empty(engine):
    page = engine.generate_topic_page("haskell")
    assert page.path == "topic/haskell.html"
    assert "haskell" in page.html.lower()


def test_generate_repo_page(populated_engine):
    page = populated_engine.generate_repo_page("langchain-ai", "langchain")
    assert "langchain" in page.html
    assert "repo/langchain-ai" in page.path and "langchain.html" in page.path


def test_generate_repo_page_no_history(engine):
    page = engine.generate_repo_page("unknown", "repo")
    assert "unknown/repo" in page.html


def test_generate_sitemap(engine):
    pages = [
        SitePage("index.html", "<html>", PageMeta("t", "d", "https://x/index.html", "2026-01-01")),
        SitePage("topic/python.html", "<html>", PageMeta("t", "d", "https://x/topic/python.html", "2026-01-01")),
    ]
    xml = engine.generate_sitemap(pages)
    assert '<?xml version="1.0"' in xml
    assert "index.html" in xml
    assert "topic/python.html" in xml
    assert "<url>" in xml


def test_generate_site_creates_files(populated_engine, tmp_path):
    result = populated_engine.generate_site(tmp_path / "out", topics=["python"], limit=5)
    assert (tmp_path / "out" / "index.html").exists()
    assert (tmp_path / "out" / "topic" / "python.html").exists()
    assert (tmp_path / "out" / "sitemap.xml").exists()
    assert len(result.pages) >= 2


def test_make_sparkline_empty():
    assert _make_sparkline([]) == ""


def test_make_sparkline_single():
    pts = _make_sparkline([80])
    assert "," in pts


def test_make_sparkline_multi():
    pts = _make_sparkline([50, 60, 70, 80])
    pairs = pts.split()
    assert len(pairs) == 4


def test_engine_config_override(tmp_db):
    cfg = SiteConfig(base_url="https://example.com/", topics=["go"], limit=5)
    engine = SiteEngine(config=cfg, db=tmp_db)
    assert engine.config.base_url == "https://example.com/"
    assert engine.config.topics == ["go"]
