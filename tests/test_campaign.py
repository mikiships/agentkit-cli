"""Tests for agentkit_cli/campaign.py (D1)."""
from __future__ import annotations

import json
import os
import tempfile
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.campaign import (
    CampaignEngine,
    CampaignResult,
    PRResult,
    RepoSpec,
)


# ---------------------------------------------------------------------------
# RepoSpec tests
# ---------------------------------------------------------------------------

def test_repo_spec_full_name():
    r = RepoSpec(owner="pallets", repo="flask")
    assert r.full_name == "pallets/flask"


def test_repo_spec_defaults():
    r = RepoSpec(owner="x", repo="y")
    assert r.stars == 0
    assert r.language is None
    assert r.description is None


# ---------------------------------------------------------------------------
# PRResult tests
# ---------------------------------------------------------------------------

def test_pr_result_to_dict():
    r = PRResult(repo=RepoSpec("pallets", "flask", stars=1000), pr_url="https://github.com/pallets/flask/pull/1")
    d = r.to_dict()
    assert d["repo"] == "pallets/flask"
    assert d["pr_url"] == "https://github.com/pallets/flask/pull/1"


# ---------------------------------------------------------------------------
# CampaignResult tests
# ---------------------------------------------------------------------------

def test_campaign_result_to_dict():
    cr = CampaignResult(campaign_id="abc123", target_spec="github:pallets", file="CLAUDE.md")
    cr.submitted.append(PRResult(repo=RepoSpec("pallets", "flask"), pr_url="https://github.com/pallets/flask/pull/1"))
    cr.skipped.append(RepoSpec("pallets", "click", stars=500))
    cr.failed.append((RepoSpec("pallets", "jinja"), "timeout"))
    d = cr.to_dict()
    assert d["campaign_id"] == "abc123"
    assert len(d["submitted"]) == 1
    assert len(d["skipped"]) == 1
    assert len(d["failed"]) == 1
    assert d["totals"]["prs"] == 1


def test_campaign_result_auto_id():
    cr = CampaignResult()
    assert len(cr.campaign_id) == 8


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(response_data: dict):
    """Return a context manager mock that reads JSON."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def _org_repos_data():
    return [
        {"owner": {"login": "pallets"}, "name": "flask", "stargazers_count": 68000, "language": "Python", "description": "Web framework"},
        {"owner": {"login": "pallets"}, "name": "click", "stargazers_count": 15000, "language": "Python", "description": "CLI toolkit"},
        {"owner": {"login": "pallets"}, "name": "jinja", "stargazers_count": 10000, "language": "Python", "description": "Templating"},
    ]


# ---------------------------------------------------------------------------
# CampaignEngine.find_repos tests
# ---------------------------------------------------------------------------

def test_find_repos_github_org(monkeypatch):
    engine = CampaignEngine(token="fake")
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(_org_repos_data())
        repos = engine.find_repos("github:pallets", limit=5)
    assert len(repos) == 3
    assert repos[0].owner == "pallets"
    assert repos[0].repo == "flask"
    assert repos[0].stars == 68000


def test_find_repos_topic(monkeypatch):
    engine = CampaignEngine(token="fake")
    items = [
        {"owner": {"login": "a"}, "name": "repo1", "stargazers_count": 500, "language": "Python", "description": ""},
        {"owner": {"login": "b"}, "name": "repo2", "stargazers_count": 200, "language": "TypeScript", "description": ""},
    ]
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen({"items": items})
        repos = engine.find_repos("topic:ai-agents", limit=5)
    assert len(repos) == 2


def test_find_repos_file(tmp_path):
    repos_file = tmp_path / "repos.txt"
    repos_file.write_text("pallets/flask\npallets/click\n# comment\n\n")
    engine = CampaignEngine()
    repos = engine.find_repos(f"repos-file:{repos_file}", limit=10)
    assert len(repos) == 2
    assert repos[0].owner == "pallets"
    assert repos[0].repo == "flask"


def test_find_repos_unknown_spec_raises():
    engine = CampaignEngine()
    with pytest.raises(ValueError):
        engine.find_repos("unknown:spec")


def test_find_repos_limit(monkeypatch):
    engine = CampaignEngine(token="fake")
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(_org_repos_data())
        repos = engine.find_repos("github:pallets", limit=2)
    assert len(repos) == 2


def test_find_repos_language_filter(monkeypatch):
    engine = CampaignEngine(token="fake")
    data = [
        {"owner": {"login": "a"}, "name": "py-repo", "stargazers_count": 100, "language": "Python", "description": ""},
        {"owner": {"login": "b"}, "name": "js-repo", "stargazers_count": 50, "language": "JavaScript", "description": ""},
    ]
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(data)
        repos = engine.find_repos("github:someorg", limit=10, language="python")
    assert all(r.language.lower() == "python" for r in repos)


def test_find_repos_min_stars_filter(monkeypatch):
    engine = CampaignEngine(token="fake")
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(_org_repos_data())
        repos = engine.find_repos("github:pallets", limit=10, min_stars=12000)
    assert all(r.stars >= 12000 for r in repos)


def test_find_repos_org_fallback_to_users(monkeypatch):
    """When /orgs/ returns 404, falls back to /users/."""
    engine = CampaignEngine(token="fake")
    calls = []

    def fake_urlopen(req, *args, **kwargs):
        calls.append(req.full_url if hasattr(req, 'full_url') else req.get_full_url())
        if "orgs" in calls[-1]:
            raise urllib.error.HTTPError(calls[-1], 404, "Not Found", {}, None)
        return _mock_urlopen(_org_repos_data())

    with patch("urllib.request.urlopen", fake_urlopen):
        repos = engine.find_repos("github:pallets", limit=5)
    assert any("users" in url for url in calls)
    assert len(repos) == 3


# ---------------------------------------------------------------------------
# has_context_file tests
# ---------------------------------------------------------------------------

def test_has_context_file_found(monkeypatch):
    engine = CampaignEngine(token="fake")
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen({"name": "CLAUDE.md"})
        result = engine.has_context_file("pallets", "flask")
    assert result is True


def test_has_context_file_not_found(monkeypatch):
    engine = CampaignEngine(token="fake")

    def raise_404(req, *args, **kwargs):
        raise urllib.error.HTTPError(req.get_full_url(), 404, "Not Found", {}, None)

    with patch("urllib.request.urlopen", raise_404):
        result = engine.has_context_file("pallets", "flask")
    assert result is False


def test_has_context_file_agents_md(monkeypatch):
    """Should return True when AGENTS.md exists (second check)."""
    engine = CampaignEngine(token="fake")
    call_count = [0]

    def fake_urlopen(req, *args, **kwargs):
        call_count[0] += 1
        if "CLAUDE.md" in req.get_full_url():
            raise urllib.error.HTTPError(req.get_full_url(), 404, "Not Found", {}, None)
        return _mock_urlopen({"name": "AGENTS.md"})

    with patch("urllib.request.urlopen", fake_urlopen):
        result = engine.has_context_file("pallets", "flask")
    assert result is True


# ---------------------------------------------------------------------------
# filter_missing_context tests
# ---------------------------------------------------------------------------

def test_filter_missing_context(monkeypatch):
    engine = CampaignEngine(token="fake")
    repos = [
        RepoSpec("a", "has-claude"),
        RepoSpec("b", "missing"),
        RepoSpec("c", "also-missing"),
    ]

    def mock_has(owner, repo, token=None):
        return repo == "has-claude"

    engine.has_context_file = mock_has
    filtered = engine.filter_missing_context(repos)
    assert len(filtered) == 2
    assert all(r.repo != "has-claude" for r in filtered)


# ---------------------------------------------------------------------------
# run_campaign tests
# ---------------------------------------------------------------------------

def test_run_campaign_success(monkeypatch):
    engine = CampaignEngine(token="fake")
    repos = [RepoSpec("pallets", "flask", stars=68000)]

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({"pr_url": "https://github.com/pallets/flask/pull/99", "score_before": None, "score_after": None})
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc):
        result = engine.run_campaign(repos, file="CLAUDE.md")

    assert len(result.submitted) == 1
    assert result.submitted[0].pr_url == "https://github.com/pallets/flask/pull/99"
    assert len(result.skipped) == 0
    assert len(result.failed) == 0


def test_run_campaign_skip_on_existing(monkeypatch):
    engine = CampaignEngine(token="fake")
    repos = [RepoSpec("pallets", "click")]

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = ""
    mock_proc.stderr = "Skipping: CLAUDE.md already exists"

    with patch("subprocess.run", return_value=mock_proc):
        result = engine.run_campaign(repos)

    assert len(result.skipped) == 1
    assert len(result.submitted) == 0


def test_run_campaign_failure(monkeypatch):
    engine = CampaignEngine(token="fake")
    repos = [RepoSpec("pallets", "markupsafe")]

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stdout = ""
    mock_proc.stderr = "Fork creation failed: 403"

    with patch("subprocess.run", return_value=mock_proc):
        result = engine.run_campaign(repos)

    assert len(result.failed) == 1
    assert "403" in result.failed[0][1]


def test_run_campaign_dry_run(monkeypatch):
    engine = CampaignEngine(token="fake")
    repos = [RepoSpec("pallets", "flask")]

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = json.dumps({"dry_run": True, "repo": "pallets/flask", "file": "CLAUDE.md"})
    mock_proc.stderr = ""

    with patch("subprocess.run", return_value=mock_proc) as mock_run:
        result = engine.run_campaign(repos, dry_run=True)

    cmd = mock_run.call_args[0][0]
    assert "--dry-run" in cmd
    assert result.submitted[0].pr_url == "[DRY RUN]"


def test_run_campaign_timeout(monkeypatch):
    import subprocess
    engine = CampaignEngine(token="fake")
    repos = [RepoSpec("slow", "repo")]

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="agentkit", timeout=120)):
        result = engine.run_campaign(repos)

    assert len(result.failed) == 1
    assert "Timeout" in result.failed[0][1]
