"""Tests for D1: OrgPagesEngine core."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from agentkit_cli.engines.org_pages import (
    OrgPagesEngine,
    OrgPagesResult,
    _parse_pages_url,
    _score_to_grade,
    generate_org_html,
    generate_leaderboard_json,
    _strip_dot_git,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repos(n: int = 3) -> list[dict]:
    return [
        {
            "rank": i + 1,
            "full_name": f"myorg/repo-{i}",
            "repo": f"repo-{i}",
            "score": 85.0 - i * 5,
            "grade": _score_to_grade(85.0 - i * 5),
            "top_finding": f"Finding {i}",
            "analyzed_at": "2026-03-19",
            "status": "ok",
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


# ---------------------------------------------------------------------------
# _parse_pages_url
# ---------------------------------------------------------------------------

def test_parse_https_url():
    url = _parse_pages_url("https://github.com/myorg/agentkit-scores.git", "docs/")
    assert url == "https://myorg.github.io/agentkit-scores/"

def test_parse_ssh_url():
    url = _parse_pages_url("git@github.com:myorg/agentkit-scores.git", "docs/")
    assert url == "https://myorg.github.io/agentkit-scores/"

def test_parse_no_dot_git():
    url = _parse_pages_url("https://github.com/myorg/agentkit-scores", "docs/")
    assert url == "https://myorg.github.io/agentkit-scores/"


# ---------------------------------------------------------------------------
# generate_org_html
# ---------------------------------------------------------------------------

def test_html_contains_org_name():
    repos = _make_repos(2)
    html = generate_org_html("myorg", "2026-03-19", repos, 82.5, "myorg/repo-0")
    assert "myorg" in html

def test_html_contains_scan_date():
    repos = _make_repos(2)
    html = generate_org_html("myorg", "2026-03-19", repos, 82.5, "myorg/repo-0")
    assert "2026-03-19" in html

def test_html_contains_repo_link():
    repos = _make_repos(2)
    html = generate_org_html("myorg", "2026-03-19", repos, 82.5, "myorg/repo-0")
    assert "github.com/myorg/repo-0" in html

def test_html_contains_grade():
    repos = _make_repos(1)
    html = generate_org_html("myorg", "2026-03-19", repos, 85.0, "myorg/repo-0")
    assert "B" in html  # 85 = B

def test_html_contains_stats_bar():
    repos = _make_repos(3)
    html = generate_org_html("myorg", "2026-03-19", repos, 80.0, "myorg/repo-0")
    assert "stats-bar" in html
    assert "Repos Scored" in html
    assert "Avg Score" in html
    assert "Top Scorer" in html


# ---------------------------------------------------------------------------
# generate_leaderboard_json
# ---------------------------------------------------------------------------

def test_leaderboard_json_structure():
    repos = _make_repos(3)
    data = generate_leaderboard_json("myorg", "2026-03-19", repos)
    assert data["org"] == "myorg"
    assert data["scan_date"] == "2026-03-19"
    assert len(data["repos"]) == 3

def test_leaderboard_json_repo_fields():
    repos = _make_repos(2)
    data = generate_leaderboard_json("myorg", "2026-03-19", repos)
    r = data["repos"][0]
    assert "name" in r
    assert "score" in r
    assert "grade" in r
    assert "top_finding" in r


# ---------------------------------------------------------------------------
# OrgPagesEngine — dry_run
# ---------------------------------------------------------------------------

def test_engine_dry_run_returns_result():
    repos = _make_repos(3)
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=repos)
    result = engine.run()
    assert isinstance(result, OrgPagesResult)
    assert result.repos_scored == 3
    assert result.published is False

def test_engine_dry_run_avg_score():
    repos = _make_repos(3)
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=repos)
    result = engine.run()
    expected_avg = (85.0 + 80.0 + 75.0) / 3
    assert abs(result.avg_score - expected_avg) < 0.1

def test_engine_dry_run_top_repo():
    repos = _make_repos(3)
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=repos)
    result = engine.run()
    assert result.top_repo == "myorg/repo-0"

def test_engine_dry_run_pages_url():
    repos = _make_repos(2)
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=repos)
    result = engine.run()
    assert "myorg" in result.pages_url

def test_engine_dry_run_leaderboard_json():
    repos = _make_repos(2)
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=repos)
    result = engine.run()
    assert result.leaderboard_json is not None
    assert result.leaderboard_json["org"] == "myorg"

def test_engine_only_below_filter():
    repos = _make_repos(5)  # scores 85, 80, 75, 70, 65
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=repos, only_below=80)
    result = engine.run()
    # Only repos with score < 80: 75, 70, 65 = 3
    assert result.repos_scored == 3

def test_engine_default_pages_repo():
    engine = OrgPagesEngine(org="myorg", dry_run=True, _org_results=[])
    assert engine.pages_repo == "myorg/agentkit-scores"

def test_engine_custom_pages_repo():
    engine = OrgPagesEngine(org="myorg", pages_repo="myorg/custom-scores", dry_run=True, _org_results=[])
    assert engine.pages_repo == "myorg/custom-scores"


# ---------------------------------------------------------------------------
# OrgPagesEngine — with mocked git
# ---------------------------------------------------------------------------

def test_engine_publish_success(tmp_path):
    repos = _make_repos(2)
    engine = OrgPagesEngine(org="myorg", dry_run=False, _org_results=repos, token="fake-token")

    mock_run = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

    with patch("agentkit_cli.engines.org_pages.subprocess.run", mock_run):
        # Simulate clone by pre-creating .git dir
        clone_dir = tmp_path / "pages-clone"
        clone_dir.mkdir()
        (clone_dir / ".git").mkdir()
        result = engine.run(clone_dir=clone_dir)

    assert isinstance(result, OrgPagesResult)

def test_engine_publish_writes_index_html(tmp_path):
    repos = _make_repos(2)
    engine = OrgPagesEngine(org="myorg", dry_run=False, _org_results=repos)

    mock_run = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

    with patch("agentkit_cli.engines.org_pages.subprocess.run", mock_run):
        clone_dir = tmp_path / "pages-clone"
        clone_dir.mkdir()
        (clone_dir / ".git").mkdir()
        engine.run(clone_dir=clone_dir)

    assert (clone_dir / "docs" / "index.html").exists()

def test_engine_publish_writes_leaderboard_json(tmp_path):
    repos = _make_repos(2)
    engine = OrgPagesEngine(org="myorg", dry_run=False, _org_results=repos)

    mock_run = MagicMock()
    mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

    with patch("agentkit_cli.engines.org_pages.subprocess.run", mock_run):
        clone_dir = tmp_path / "pages-clone"
        clone_dir.mkdir()
        (clone_dir / ".git").mkdir()
        engine.run(clone_dir=clone_dir)

    json_path = clone_dir / "docs" / "leaderboard.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert data["org"] == "myorg"

def test_engine_publish_clone_failure_returns_unpublished(tmp_path):
    repos = _make_repos(2)
    engine = OrgPagesEngine(org="myorg", dry_run=False, _org_results=repos)

    mock_run = MagicMock()
    mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"clone failed")

    with patch("agentkit_cli.engines.org_pages.subprocess.run", mock_run):
        clone_dir = tmp_path / "never-cloned"
        result = engine.run(clone_dir=clone_dir)

    assert result.published is False
    assert result.error is not None
