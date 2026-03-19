"""Tests for D1: TrendingPagesEngine core."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import subprocess

import pytest

from agentkit_cli.engines.trending_pages import (
    TrendingPagesEngine,
    TrendingPagesResult,
    _score_to_grade,
    _grade_color,
    _score_repo,
    _parse_pages_url,
    _strip_dot_git,
    generate_trending_html,
    generate_leaderboard_json,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repos(n: int = 3) -> list[dict]:
    return [
        {
            "full_name": f"owner/repo-{i}",
            "description": f"An agent LLM repo {i}",
            "stars": 5000 * (i + 1),
            "language": "Python",
            "url": f"https://github.com/owner/repo-{i}",
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# _score_to_grade
# ---------------------------------------------------------------------------

def test_grade_A():
    assert _score_to_grade(95) == "A"

def test_grade_B():
    assert _score_to_grade(85) == "B"

def test_grade_C():
    assert _score_to_grade(75) == "C"

def test_grade_D():
    assert _score_to_grade(65) == "D"

def test_grade_F():
    assert _score_to_grade(55) == "F"

def test_grade_none():
    assert _score_to_grade(None) == "F"

def test_grade_exactly_90():
    assert _score_to_grade(90) == "A"


# ---------------------------------------------------------------------------
# _grade_color
# ---------------------------------------------------------------------------

def test_grade_color_A():
    assert "#" in _grade_color("A")

def test_grade_color_unknown():
    assert _grade_color("Z") == "#d1d5db"


# ---------------------------------------------------------------------------
# _score_repo
# ---------------------------------------------------------------------------

def test_score_repo_base():
    score, finding = _score_repo({"full_name": "x/y", "stars": 0, "language": "", "description": ""})
    assert score >= 50.0

def test_score_repo_high_stars():
    score, finding = _score_repo({"full_name": "x/y", "stars": 15000, "language": "", "description": ""})
    assert score > 60.0

def test_score_repo_python_bonus():
    score_py, _ = _score_repo({"full_name": "x/y", "stars": 100, "language": "Python", "description": ""})
    score_other, _ = _score_repo({"full_name": "x/y", "stars": 100, "language": "Go", "description": ""})
    assert score_py > score_other

def test_score_repo_agent_keyword():
    score, finding = _score_repo({"full_name": "x/y", "stars": 100, "language": "", "description": "LLM agent toolkit"})
    assert score >= 65.0
    assert "keyword" in finding.lower() or "agent" in finding.lower() or "llm" in finding.lower()

def test_score_repo_capped_at_100():
    score, _ = _score_repo({"full_name": "x/y", "stars": 100000, "language": "Python", "description": "agent llm gpt"})
    assert score <= 100.0


# ---------------------------------------------------------------------------
# _parse_pages_url
# ---------------------------------------------------------------------------

def test_parse_pages_url_standard():
    url = _parse_pages_url("mikiships/agentkit-trending", "trending.html")
    assert url == "https://mikiships.github.io/agentkit-trending/trending.html"

def test_parse_pages_url_custom_file():
    url = _parse_pages_url("owner/repo", "leaderboard.html")
    assert "leaderboard.html" in url


# ---------------------------------------------------------------------------
# generate_trending_html
# ---------------------------------------------------------------------------

def test_html_contains_title():
    html = generate_trending_html([], "today", None, "2026-03-19")
    assert "AI-Ready Repos Today" in html

def test_html_contains_repos():
    repos = [{"rank": 1, "full_name": "owner/cool-repo", "stars": 1234, "language": "Python",
               "url": "https://github.com/owner/cool-repo", "agentkit_score": 78.5,
               "grade": "C", "top_finding": "Python repo", "description": "test"}]
    html = generate_trending_html(repos, "today", None, "2026-03-19")
    assert "owner/cool-repo" in html
    assert "78.5" in html

def test_html_dark_theme():
    html = generate_trending_html([], "today", None, "2026-03-19")
    assert "#111827" in html

def test_html_seo_meta():
    html = generate_trending_html([], "today", None, "2026-03-19")
    assert 'og:title' in html or 'og:description' in html or 'description' in html

def test_html_subscribe_cta():
    html = generate_trending_html([], "today", None, "2026-03-19")
    assert "Subscribe" in html or "subscribe" in html or "agentkit-trending" in html


# ---------------------------------------------------------------------------
# generate_leaderboard_json
# ---------------------------------------------------------------------------

def test_leaderboard_json_structure():
    repos = [{"rank": 1, "full_name": "a/b", "stars": 100, "language": "Python",
               "agentkit_score": 80.0, "grade": "B", "top_finding": "x", "url": "https://github.com/a/b"}]
    result = generate_leaderboard_json(repos, "today", "python", "2026-03-19")
    assert result["period"] == "today"
    assert result["language"] == "python"
    assert len(result["repos"]) == 1
    assert result["repos"][0]["agentkit_score"] == 80.0

def test_leaderboard_json_empty():
    result = generate_leaderboard_json([], "week", None, "2026-03-19")
    assert result["repos"] == []


# ---------------------------------------------------------------------------
# TrendingPagesEngine dry_run
# ---------------------------------------------------------------------------

def test_engine_dry_run_no_push():
    repos = _make_repos(3)
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        limit=5,
        period="today",
        dry_run=True,
        _prefetched_repos=repos,
    )
    result = engine.run()
    assert isinstance(result, TrendingPagesResult)
    assert result.published is False
    assert result.repos_scored == 3

def test_engine_dry_run_returns_leaderboard_json():
    repos = _make_repos(2)
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        dry_run=True,
        _prefetched_repos=repos,
    )
    result = engine.run()
    assert result.leaderboard_json is not None
    assert "repos" in result.leaderboard_json

def test_engine_empty_repos_dry_run():
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        dry_run=True,
        _prefetched_repos=[],
    )
    result = engine.run()
    assert result.repos_scored == 0
    assert result.published is False

def test_engine_scores_and_ranks():
    repos = _make_repos(4)
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        dry_run=True,
        _prefetched_repos=repos,
    )
    result = engine.run()
    assert result.repos_scored == 4
    # JSON repos should be sorted by score
    json_repos = result.leaderboard_json["repos"]
    scores = [r["agentkit_score"] for r in json_repos if r["agentkit_score"] is not None]
    assert scores == sorted(scores, reverse=True)

def test_engine_skips_repos_without_full_name():
    repos = [{"full_name": "", "stars": 100, "language": "Python", "description": ""}]
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        dry_run=True,
        _prefetched_repos=repos,
    )
    result = engine.run()
    assert result.repos_scored == 0


# ---------------------------------------------------------------------------
# TrendingPagesEngine publish (mocked git)
# ---------------------------------------------------------------------------

def test_engine_publish_mocked(tmp_path):
    repos = _make_repos(2)
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        limit=5,
        dry_run=False,
        _prefetched_repos=repos,
    )

    def fake_clone(pages_repo, clone_dir, pages_branch, token=None):
        clone_dir.mkdir(parents=True, exist_ok=True)
        (clone_dir / ".git").mkdir()
        return True, ""

    def fake_commit(repo_root, files, commit_msg, pages_branch):
        return True, ""

    with patch("agentkit_cli.engines.trending_pages._clone_or_pull_pages_repo", side_effect=fake_clone), \
         patch("agentkit_cli.engines.trending_pages._commit_and_push", side_effect=fake_commit):
        result = engine.run(clone_dir=tmp_path / "pages")

    assert result.published is True
    assert result.error is None

def test_engine_publish_clone_failure(tmp_path):
    repos = _make_repos(2)
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        dry_run=False,
        _prefetched_repos=repos,
    )

    def fake_clone_fail(pages_repo, clone_dir, pages_branch, token=None):
        clone_dir.mkdir(parents=True, exist_ok=True)
        return False, "clone failed"

    with patch("agentkit_cli.engines.trending_pages._clone_or_pull_pages_repo", side_effect=fake_clone_fail):
        result = engine.run(clone_dir=tmp_path / "pages")

    assert result.published is False
    assert result.error is not None

def test_engine_limit_clamped():
    engine = TrendingPagesEngine(pages_repo="owner/repo", limit=200)
    assert engine.limit == 50

def test_engine_limit_min():
    engine = TrendingPagesEngine(pages_repo="owner/repo", limit=0)
    assert engine.limit >= 1

def test_engine_writes_html_and_json(tmp_path):
    repos = _make_repos(2)
    engine = TrendingPagesEngine(
        pages_repo="owner/agentkit-trending",
        pages_path="docs/",
        dry_run=False,
        _prefetched_repos=repos,
    )

    def fake_clone(pages_repo, clone_dir, pages_branch, token=None):
        clone_dir.mkdir(parents=True, exist_ok=True)
        (clone_dir / ".git").mkdir()
        return True, ""

    def fake_commit(repo_root, files, commit_msg, pages_branch):
        # Verify files were written
        for f in files:
            assert Path(f).exists()
        return True, ""

    with patch("agentkit_cli.engines.trending_pages._clone_or_pull_pages_repo", side_effect=fake_clone), \
         patch("agentkit_cli.engines.trending_pages._commit_and_push", side_effect=fake_commit):
        result = engine.run(clone_dir=tmp_path / "pages")

    assert result.published is True
    html_file = tmp_path / "pages" / "docs" / "trending.html"
    json_file = tmp_path / "pages" / "docs" / "leaderboard.json"
    assert html_file.exists()
    assert json_file.exists()
    data = json.loads(json_file.read_text())
    assert "repos" in data
