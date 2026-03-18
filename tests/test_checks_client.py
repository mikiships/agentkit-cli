"""Tests for agentkit_cli.checks_client — all HTTP mocked."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.checks_client import (
    ChecksEnv,
    GitHubChecksClient,
    detect_github_env,
)


# ---------------------------------------------------------------------------
# detect_github_env
# ---------------------------------------------------------------------------

class TestDetectGithubEnv:
    def test_returns_none_outside_actions(self, monkeypatch):
        monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
        assert detect_github_env() is None

    def test_returns_none_when_actions_not_true(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "false")
        assert detect_github_env() is None

    def test_returns_none_missing_repo(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITHUB_REPOSITORY", "noslash")
        monkeypatch.setenv("GITHUB_SHA", "abc123")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_xxx")
        assert detect_github_env() is None

    def test_returns_none_missing_sha(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_SHA", "")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_xxx")
        assert detect_github_env() is None

    def test_returns_none_missing_token(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
        monkeypatch.setenv("GITHUB_SHA", "abc123")
        monkeypatch.setenv("GITHUB_TOKEN", "")
        assert detect_github_env() is None

    def test_returns_env_when_all_present(self, monkeypatch):
        monkeypatch.setenv("GITHUB_ACTIONS", "true")
        monkeypatch.setenv("GITHUB_REPOSITORY", "myorg/myrepo")
        monkeypatch.setenv("GITHUB_SHA", "deadbeef")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_token123")
        env = detect_github_env()
        assert env is not None
        assert env.owner == "myorg"
        assert env.repo == "myrepo"
        assert env.sha == "deadbeef"
        assert env.token == "ghp_token123"
        assert env.full_repo == "myorg/myrepo"


# ---------------------------------------------------------------------------
# ChecksEnv
# ---------------------------------------------------------------------------

class TestChecksEnv:
    def test_full_repo(self):
        env = ChecksEnv(owner="org", repo="project", sha="abc", token="tok")
        assert env.full_repo == "org/project"


# ---------------------------------------------------------------------------
# GitHubChecksClient — no-op when env is None
# ---------------------------------------------------------------------------

class TestClientNoOp:
    def test_active_false_without_env(self):
        client = GitHubChecksClient(env=None)
        assert client.active is False

    def test_create_returns_none_without_env(self):
        client = GitHubChecksClient(env=None)
        assert client.create_check_run() is None

    def test_update_returns_false_without_env(self):
        client = GitHubChecksClient(env=None)
        assert client.update_check_run(123) is False


# ---------------------------------------------------------------------------
# GitHubChecksClient — create / update with mocked HTTP
# ---------------------------------------------------------------------------

def _mock_env() -> ChecksEnv:
    return ChecksEnv(owner="org", repo="repo", sha="abc123", token="ghp_test")


def _make_response(body: dict, status: int = 201):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(body).encode("utf-8")
    mock_resp.status = status
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestClientCreate:
    def test_create_returns_id(self):
        client = GitHubChecksClient(env=_mock_env())
        resp = _make_response({"id": 42})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp):
            result = client.create_check_run(name="agentkit")
        assert result == 42

    def test_create_posts_correct_url(self):
        client = GitHubChecksClient(env=_mock_env())
        resp = _make_response({"id": 1})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            client.create_check_run()
        req = mock_open.call_args[0][0]
        assert "/repos/org/repo/check-runs" in req.full_url
        assert req.method == "POST"

    def test_create_sends_auth_header(self):
        client = GitHubChecksClient(env=_mock_env())
        resp = _make_response({"id": 1})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            client.create_check_run()
        req = mock_open.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer ghp_test"

    def test_create_returns_none_on_http_error(self):
        from urllib.error import HTTPError
        client = GitHubChecksClient(env=_mock_env())
        err = HTTPError("url", 422, "Unprocessable", {}, None)
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", side_effect=err):
            result = client.create_check_run()
        assert result is None


class TestClientUpdate:
    def test_update_returns_true_on_success(self):
        client = GitHubChecksClient(env=_mock_env())
        resp = _make_response({"id": 42})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp):
            result = client.update_check_run(42, conclusion="success")
        assert result is True

    def test_update_uses_patch_method(self):
        client = GitHubChecksClient(env=_mock_env())
        resp = _make_response({"id": 42})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp) as mock_open:
            client.update_check_run(42, conclusion="failure", output={"title": "t", "summary": "s"})
        req = mock_open.call_args[0][0]
        assert req.method == "PATCH"
        body = json.loads(req.data)
        assert body["conclusion"] == "failure"
        assert body["output"]["title"] == "t"

    def test_update_returns_false_on_network_error(self):
        from urllib.error import URLError
        client = GitHubChecksClient(env=_mock_env())
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", side_effect=URLError("timeout")):
            result = client.update_check_run(42)
        assert result is False

    def test_update_returns_false_on_unexpected_error(self):
        client = GitHubChecksClient(env=_mock_env())
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", side_effect=RuntimeError("boom")):
            result = client.update_check_run(42)
        assert result is False
