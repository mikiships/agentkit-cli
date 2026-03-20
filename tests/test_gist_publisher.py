"""Tests for GistPublisher (D1) — all HTTP calls mocked."""
from __future__ import annotations

import json
import os
from io import BytesIO
from unittest.mock import MagicMock, call, patch

import pytest

from agentkit_cli.gist_publisher import (
    GITHUB_API_GISTS,
    GistPublishError,
    GistPublisher,
    GistResult,
    _get_gh_token,
    _post_gist,
    _resolve_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(response_dict: dict):
    """Return a context-manager urlopen mock returning response_dict as JSON."""
    class _CM:
        def __enter__(self):
            m = MagicMock()
            m.read.return_value = json.dumps(response_dict).encode()
            return m

        def __exit__(self, *a):
            pass

    return _CM()


SAMPLE_GIST_RESPONSE = {
    "id": "abc123",
    "html_url": "https://gist.github.com/abc123",
    "created_at": "2026-03-20T12:00:00Z",
    "files": {
        "report.md": {
            "raw_url": "https://gist.githubusercontent.com/raw/abc123/report.md",
        }
    },
}


# ---------------------------------------------------------------------------
# D1: GistPublisher core tests
# ---------------------------------------------------------------------------

class TestGistResult:
    def test_dataclass_fields(self):
        r = GistResult(
            url="https://gist.github.com/x",
            gist_id="x",
            raw_url="https://raw.githubusercontent.com/...",
            created_at="2026-03-20T00:00:00Z",
        )
        assert r.url == "https://gist.github.com/x"
        assert r.gist_id == "x"
        assert r.raw_url.startswith("https://raw")
        assert r.created_at == "2026-03-20T00:00:00Z"


class TestPostGist:
    def test_successful_post_returns_dict(self):
        with patch("agentkit_cli.gist_publisher.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_urlopen(SAMPLE_GIST_RESPONSE)
            result = _post_gist({"files": {}})
        assert result["id"] == "abc123"

    def test_post_with_token_sets_auth_header(self):
        captured_req = []

        def _fake_urlopen(req):
            captured_req.append(req)
            return _mock_urlopen(SAMPLE_GIST_RESPONSE)

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=_fake_urlopen):
            _post_gist({"files": {}}, token="mytoken")

        assert len(captured_req) == 1
        headers = dict(captured_req[0].headers)
        # Header keys are title-cased by urllib
        assert headers.get("Authorization") == "Bearer mytoken"

    def test_post_without_token_no_auth_header(self):
        captured_req = []

        def _fake_urlopen(req):
            captured_req.append(req)
            return _mock_urlopen(SAMPLE_GIST_RESPONSE)

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=_fake_urlopen):
            _post_gist({"files": {}}, token=None)

        assert "Authorization" not in dict(captured_req[0].headers)

    def test_http_error_raises_gist_publish_error(self):
        from urllib.error import HTTPError

        err = HTTPError(GITHUB_API_GISTS, 422, "Unprocessable", {}, BytesIO(b"bad input"))
        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=err):
            with pytest.raises(GistPublishError, match="HTTP 422"):
                _post_gist({"files": {}})

    def test_url_error_raises_gist_publish_error(self):
        from urllib.error import URLError

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=URLError("network down")):
            with pytest.raises(GistPublishError, match="Network error"):
                _post_gist({"files": {}})


class TestResolveToken:
    def test_env_var_takes_precedence(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_token"}, clear=False):
            assert _resolve_token() == "env_token"

    def test_gh_token_env_var(self):
        env = {"GH_TOKEN": "gh_token"}
        with patch.dict(os.environ, env, clear=False):
            # Remove GITHUB_TOKEN if present
            with patch.dict(os.environ, {"GITHUB_TOKEN": ""}, clear=False):
                # GH_TOKEN should be found when GITHUB_TOKEN is empty
                pass
        with patch.dict(os.environ, {"GH_TOKEN": "gh_token"}, clear=False):
            patched_env = {k: v for k, v in os.environ.items() if k != "GITHUB_TOKEN"}
            patched_env["GH_TOKEN"] = "gh_token"
            with patch.dict(os.environ, patched_env, clear=True):
                result = _resolve_token()
                assert result == "gh_token"

    def test_falls_back_to_gh_cli(self):
        clean_env = {}
        with patch.dict(os.environ, clean_env, clear=True):
            with patch("agentkit_cli.gist_publisher._get_gh_token", return_value="cli_token"):
                result = _resolve_token()
        assert result == "cli_token"

    def test_returns_none_when_no_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("agentkit_cli.gist_publisher._get_gh_token", return_value=None):
                result = _resolve_token()
        assert result is None


class TestGetGhToken:
    def test_returns_token_on_success(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  ghp_mytoken  \n"
        with patch("agentkit_cli.gist_publisher.subprocess.run", return_value=mock_result):
            token = _get_gh_token()
        assert token == "ghp_mytoken"

    def test_returns_none_on_nonzero_exit(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        with patch("agentkit_cli.gist_publisher.subprocess.run", return_value=mock_result):
            token = _get_gh_token()
        assert token is None

    def test_returns_none_when_gh_not_found(self):
        with patch("agentkit_cli.gist_publisher.subprocess.run", side_effect=FileNotFoundError):
            token = _get_gh_token()
        assert token is None


class TestGistPublisher:
    def test_publish_public_gist_no_token(self):
        """Public gist succeeds without token."""
        with patch("agentkit_cli.gist_publisher.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_urlopen(SAMPLE_GIST_RESPONSE)
            pub = GistPublisher()
            result = pub.publish("content", filename="report.md", public=True)
        assert result is not None
        assert result.url == "https://gist.github.com/abc123"
        assert result.gist_id == "abc123"

    def test_publish_private_gist_with_token(self):
        """Private gist succeeds with token."""
        with patch("agentkit_cli.gist_publisher.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_urlopen(SAMPLE_GIST_RESPONSE)
            pub = GistPublisher(token="mytoken")
            result = pub.publish("content", public=False)
        assert result is not None
        assert result.gist_id == "abc123"

    def test_publish_private_gist_no_token_returns_none(self, capsys):
        """Private gist without token: prints error, returns None (no crash)."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("agentkit_cli.gist_publisher._get_gh_token", return_value=None):
                pub = GistPublisher()
                result = pub.publish("content", public=False)
        assert result is None
        captured = capsys.readouterr()
        assert "token" in captured.err.lower()

    def test_publish_returns_gist_result_with_all_fields(self):
        with patch("agentkit_cli.gist_publisher.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _mock_urlopen(SAMPLE_GIST_RESPONSE)
            pub = GistPublisher(token="tok")
            result = pub.publish("hello", filename="report.md", description="test", public=False)
        assert result is not None
        assert result.url == "https://gist.github.com/abc123"
        assert result.gist_id == "abc123"
        assert result.raw_url == "https://gist.githubusercontent.com/raw/abc123/report.md"
        assert result.created_at == "2026-03-20T12:00:00Z"

    def test_publish_network_error_returns_none_no_crash(self, capsys):
        from urllib.error import URLError

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=URLError("no network")):
            pub = GistPublisher(token="tok")
            result = pub.publish("content", public=True)
        assert result is None
        captured = capsys.readouterr()
        assert "failed" in captured.err.lower()

    def test_publish_payload_contains_content_and_filename(self):
        captured_payloads = []

        def _fake_urlopen(req):
            captured_payloads.append(json.loads(req.data.decode()))
            return _mock_urlopen(SAMPLE_GIST_RESPONSE)

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=_fake_urlopen):
            pub = GistPublisher(token="tok")
            pub.publish("my content", filename="notes.md", description="desc", public=True)

        assert len(captured_payloads) == 1
        payload = captured_payloads[0]
        assert "notes.md" in payload["files"]
        assert payload["files"]["notes.md"]["content"] == "my content"
        assert payload["description"] == "desc"
        assert payload["public"] is True

    def test_publish_private_default(self):
        """Default public=False creates a private gist."""
        captured_payloads = []

        def _fake_urlopen(req):
            captured_payloads.append(json.loads(req.data.decode()))
            return _mock_urlopen(SAMPLE_GIST_RESPONSE)

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=_fake_urlopen):
            pub = GistPublisher(token="tok")
            pub.publish("content")

        assert captured_payloads[0]["public"] is False

    def test_publish_with_env_token(self):
        """Token resolved from GITHUB_TOKEN env var."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "env_tok"}, clear=False):
            with patch("agentkit_cli.gist_publisher.request.urlopen") as mock_urlopen:
                mock_urlopen.return_value = _mock_urlopen(SAMPLE_GIST_RESPONSE)
                pub = GistPublisher()
                result = pub.publish("content", public=False)
        assert result is not None
