"""Tests for D1: publish_to_pages() in DailyLeaderboardEngine."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from agentkit_cli.engines.daily_leaderboard import (
    DailyLeaderboard,
    RankedRepo,
    _parse_github_pages_url,
    publish_to_pages,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_leaderboard(n: int = 3) -> DailyLeaderboard:
    repos = [
        RankedRepo(
            rank=i + 1,
            full_name=f"org/repo-{i}",
            description=f"Repo {i}",
            stars=1000 * (i + 1),
            language="Python",
            url=f"https://github.com/org/repo-{i}",
            composite_score=80.0 - i,
            top_finding=f"Finding {i}",
        )
        for i in range(n)
    ]
    return DailyLeaderboard(
        date=date(2026, 3, 19),
        repos=repos,
        generated_at=datetime(2026, 3, 19, 8, 0, 0, tzinfo=timezone.utc),
        total_fetched=n,
    )


# ---------------------------------------------------------------------------
# _parse_github_pages_url
# ---------------------------------------------------------------------------

def test_parse_https_url():
    url = _parse_github_pages_url("https://github.com/mikiships/agentkit-cli.git", "docs/leaderboard.html")
    assert url == "https://mikiships.github.io/agentkit-cli/leaderboard.html"


def test_parse_ssh_url():
    url = _parse_github_pages_url("git@github.com:mikiships/agentkit-cli.git", "docs/leaderboard.html")
    assert url == "https://mikiships.github.io/agentkit-cli/leaderboard.html"


def test_parse_https_no_dot_git():
    url = _parse_github_pages_url("https://github.com/owner/my-repo", "docs/leaderboard.html")
    assert url == "https://owner.github.io/my-repo/leaderboard.html"


def test_parse_custom_pages_path():
    url = _parse_github_pages_url("https://github.com/owner/repo.git", "docs/subdir/page.html")
    assert "owner.github.io" in url
    assert "page.html" in url


# ---------------------------------------------------------------------------
# publish_to_pages — success path
# ---------------------------------------------------------------------------

def test_publish_to_pages_writes_html(tmp_path):
    lb = _make_leaderboard()
    html = "<html><body>hello</body></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/mikiships/agentkit-cli.git\n"

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = publish_to_pages(html, lb, repo_path=str(tmp_path))

    html_file = tmp_path / "docs" / "leaderboard.html"
    assert html_file.exists()
    assert html_file.read_text() == html


def test_publish_to_pages_writes_json_data(tmp_path):
    lb = _make_leaderboard(3)
    html = "<html></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/owner/repo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        publish_to_pages(html, lb, repo_path=str(tmp_path))

    data_file = tmp_path / "docs" / "leaderboard-data.json"
    assert data_file.exists()
    data = json.loads(data_file.read_text())
    assert data["generated"] == "2026-03-19"
    assert "repos" in data
    assert len(data["repos"]) <= 10


def test_publish_to_pages_json_has_required_fields(tmp_path):
    lb = _make_leaderboard(2)
    html = "<html></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/owner/repo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        publish_to_pages(html, lb, repo_path=str(tmp_path))

    data = json.loads((tmp_path / "docs" / "leaderboard-data.json").read_text())
    repo = data["repos"][0]
    for field in ("rank", "full_name", "composite_score", "stars", "language", "top_finding"):
        assert field in repo, f"JSON data missing field: {field}"


def test_publish_to_pages_returns_committed_true(tmp_path):
    lb = _make_leaderboard()
    html = "<html></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/mikiships/agentkit-cli.git\n"

    with patch("subprocess.run", return_value=mock_result):
        result = publish_to_pages(html, lb, repo_path=str(tmp_path))

    assert result["committed"] is True
    assert "pages_url" in result
    assert result["pages_url"].startswith("https://")


def test_publish_to_pages_returns_correct_url(tmp_path):
    lb = _make_leaderboard()
    html = "<html></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/mikiships/agentkit-cli.git\n"

    with patch("subprocess.run", return_value=mock_result):
        result = publish_to_pages(html, lb, repo_path=str(tmp_path))

    assert "mikiships.github.io" in result["pages_url"]
    assert "agentkit-cli" in result["pages_url"]


# ---------------------------------------------------------------------------
# publish_to_pages — git not found
# ---------------------------------------------------------------------------

def test_publish_to_pages_no_git_returns_error(tmp_path):
    lb = _make_leaderboard()
    html = "<html></html>"

    with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
        result = publish_to_pages(html, lb, repo_path=str(tmp_path))

    assert result["committed"] is False
    assert "error" in result
    assert "git" in result["error"].lower()


# ---------------------------------------------------------------------------
# publish_to_pages — git CalledProcessError
# ---------------------------------------------------------------------------

def test_publish_to_pages_git_push_failure_returns_error(tmp_path):
    lb = _make_leaderboard()
    html = "<html></html>"

    import subprocess

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call is git --version check
            r = MagicMock()
            r.returncode = 0
            r.stdout = b"git version 2.0"
            return r
        if "get-url" in (args[0] if args else []):
            r = MagicMock()
            r.returncode = 0
            r.stdout = "https://github.com/owner/repo.git\n"
            return r
        raise subprocess.CalledProcessError(1, "git push", stderr=b"Authentication failed")

    with patch("subprocess.run", side_effect=side_effect):
        result = publish_to_pages(html, lb, repo_path=str(tmp_path))

    assert result["committed"] is False


# ---------------------------------------------------------------------------
# publish_to_pages — custom pages_path
# ---------------------------------------------------------------------------

def test_publish_to_pages_custom_path(tmp_path):
    lb = _make_leaderboard()
    html = "<html>custom</html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/owner/repo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        publish_to_pages(html, lb, repo_path=str(tmp_path), pages_path="docs/subdir/report.html")

    assert (tmp_path / "docs" / "subdir" / "report.html").exists()


def test_publish_to_pages_creates_parent_dirs(tmp_path):
    lb = _make_leaderboard()
    html = "<html></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/owner/repo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        publish_to_pages(html, lb, repo_path=str(tmp_path), pages_path="deeply/nested/dir/leaderboard.html")

    assert (tmp_path / "deeply" / "nested" / "dir" / "leaderboard.html").exists()


def test_publish_to_pages_json_top10_limit(tmp_path):
    """JSON data file should contain at most 10 repos."""
    lb = _make_leaderboard(15)
    html = "<html></html>"

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://github.com/owner/repo.git\n"

    with patch("subprocess.run", return_value=mock_result):
        publish_to_pages(html, lb, repo_path=str(tmp_path))

    data = json.loads((tmp_path / "docs" / "leaderboard-data.json").read_text())
    assert len(data["repos"]) <= 10
