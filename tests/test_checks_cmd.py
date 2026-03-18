"""Tests for agentkit checks CLI command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_github_env(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "testorg/testrepo")
    monkeypatch.setenv("GITHUB_SHA", "abc123def456")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")


def _clear_github_env(monkeypatch):
    for var in ("GITHUB_ACTIONS", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_TOKEN"):
        monkeypatch.delenv(var, raising=False)


def _mock_urlopen_response(body: dict):
    resp = MagicMock()
    resp.read.return_value = json.dumps(body).encode()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

class TestVerify:
    def test_verify_all_present(self, monkeypatch):
        _set_github_env(monkeypatch)
        result = runner.invoke(app, ["checks", "verify"])
        assert result.exit_code == 0
        assert "ready" in result.output.lower()

    def test_verify_missing_token(self, monkeypatch):
        _set_github_env(monkeypatch)
        monkeypatch.setenv("GITHUB_TOKEN", "")
        result = runner.invoke(app, ["checks", "verify"])
        assert result.exit_code == 1
        assert "GITHUB_TOKEN" in result.output

    def test_verify_missing_actions(self, monkeypatch):
        _clear_github_env(monkeypatch)
        result = runner.invoke(app, ["checks", "verify"])
        assert result.exit_code == 1
        assert "GITHUB_ACTIONS" in result.output

    def test_verify_missing_repo(self, monkeypatch):
        _set_github_env(monkeypatch)
        monkeypatch.setenv("GITHUB_REPOSITORY", "noslash")
        result = runner.invoke(app, ["checks", "verify"])
        assert result.exit_code == 1
        assert "GITHUB_REPOSITORY" in result.output

    def test_verify_missing_sha(self, monkeypatch):
        _set_github_env(monkeypatch)
        monkeypatch.setenv("GITHUB_SHA", "")
        result = runner.invoke(app, ["checks", "verify"])
        assert result.exit_code == 1
        assert "GITHUB_SHA" in result.output


# ---------------------------------------------------------------------------
# post
# ---------------------------------------------------------------------------

class TestPost:
    def test_post_success(self, monkeypatch, tmp_path):
        _set_github_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        resp = _mock_urlopen_response({"id": 123})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp):
            result = runner.invoke(app, ["checks", "post", "--score", "87", "--conclusion", "success"])
        assert result.exit_code == 0
        assert "123" in result.output

    def test_post_not_in_actions(self, monkeypatch):
        _clear_github_env(monkeypatch)
        result = runner.invoke(app, ["checks", "post", "--score", "80"])
        assert result.exit_code == 1
        assert "Not in GitHub Actions" in result.output

    def test_post_api_failure(self, monkeypatch, tmp_path):
        _set_github_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        from urllib.error import HTTPError
        with patch("agentkit_cli.checks_client.urllib_request.urlopen",
                    side_effect=HTTPError("url", 500, "err", {}, None)):
            result = runner.invoke(app, ["checks", "post", "--score", "80"])
        assert result.exit_code == 1

    def test_post_saves_status_file(self, monkeypatch, tmp_path):
        _set_github_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        resp = _mock_urlopen_response({"id": 456})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp):
            result = runner.invoke(app, ["checks", "post", "--score", "92", "--grade", "A"])
        assert result.exit_code == 0
        status_path = tmp_path / ".agentkit-checks.json"
        assert status_path.exists()
        data = json.loads(status_path.read_text())
        assert data["check_run_id"] == 456
        assert data["score"] == 92.0
        assert data["grade"] == "A"

    def test_post_auto_grade(self, monkeypatch, tmp_path):
        """Grade is auto-computed when not provided."""
        _set_github_env(monkeypatch)
        monkeypatch.chdir(tmp_path)
        resp = _mock_urlopen_response({"id": 789})
        with patch("agentkit_cli.checks_client.urllib_request.urlopen", return_value=resp):
            result = runner.invoke(app, ["checks", "post", "--score", "55"])
        assert result.exit_code == 0
        assert "F" in result.output or "55" in result.output


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

class TestStatus:
    def test_status_no_file(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["checks", "status"])
        assert result.exit_code == 0
        assert "No check runs" in result.output

    def test_status_with_file(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        status_data = {
            "check_run_id": 42,
            "score": 88.0,
            "grade": "B",
            "conclusion": "success",
            "repo": "org/repo",
            "sha": "deadbeef",
        }
        (tmp_path / ".agentkit-checks.json").write_text(json.dumps(status_data))
        result = runner.invoke(app, ["checks", "status"])
        assert result.exit_code == 0
        assert "42" in result.output
        assert "88" in result.output
        assert "B" in result.output
