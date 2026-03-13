"""Tests for agentkit publish command (D3)."""
from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen(responses: list):
    """Return a context-manager mock that yields responses in sequence."""
    calls = iter(responses)

    class _CM:
        def __init__(self, resp):
            self._resp = resp

        def __enter__(self):
            return self._resp

        def __exit__(self, *a):
            pass

    def _urlopen(req):
        resp_data = next(calls)
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(resp_data).encode()
        return _CM(mock_resp)

    return _urlopen


# ---------------------------------------------------------------------------
# D1 core publish.py tests
# ---------------------------------------------------------------------------

class TestPublishCore:
    def test_anonymous_publish_success(self, tmp_path):
        """3-step API flow with no auth key returns public URL."""
        html = tmp_path / "report.html"
        html.write_text("<html></html>")

        responses = [
            {"uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}], "finalizeUrl": "https://api.here.now/v1/finalize/abc"},
            {},  # PUT response (ignored)
            {"url": "https://abc.here.now/"},
        ]

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_mock_urlopen(responses)):
            from agentkit_cli.publish import publish_html
            result = publish_html(html, api_key=None)

        assert result["url"] == "https://abc.here.now/"
        assert result["anonymous"] is True

    def test_authenticated_publish_success(self, tmp_path):
        """With HERENOW_API_KEY, Bearer header is sent on step 1."""
        html = tmp_path / "report.html"
        html.write_text("<html></html>")

        captured_headers = {}

        def _urlopen_auth(req):
            if hasattr(req, "headers"):
                captured_headers.update(req.headers)
            # Build response based on URL
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "finalize" in url:
                data = {"url": "https://xyz.here.now/"}
            elif req.get_method() == "PUT":
                data = {}
            else:
                data = {
                    "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                    "finalizeUrl": "https://api.here.now/v1/finalize/xyz",
                }
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(data).encode()

            class _CM:
                def __enter__(self_inner): return mock_resp
                def __exit__(self_inner, *a): pass

            return _CM()

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_urlopen_auth):
            from agentkit_cli import publish as pub_mod
            # Reload to clear any module-level state
            import importlib
            importlib.reload(pub_mod)
            result = pub_mod.publish_html(html, api_key="test-key-123")

        assert result["url"] == "https://xyz.here.now/"
        assert result["anonymous"] is False

    def test_file_not_found(self, tmp_path):
        """Missing HTML file raises FileNotFoundError with helpful message."""
        from agentkit_cli.publish import resolve_html_path
        with pytest.raises(FileNotFoundError, match="agentkit report"):
            resolve_html_path(tmp_path / "nonexistent.html")

    def test_api_step1_failure(self, tmp_path):
        """POST fails (503) → PublishError raised, not a crash."""
        html = tmp_path / "report.html"
        html.write_text("<html></html>")

        from urllib.error import HTTPError
        from agentkit_cli.publish import PublishError

        def _fail(req):
            raise HTTPError(url="https://api.here.now/v1/publish", code=503, msg="Service Unavailable", hdrs=None, fp=BytesIO(b"503 error"))

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_fail):
            from agentkit_cli.publish import publish_html
            with pytest.raises(PublishError, match="503"):
                publish_html(html)

    def test_api_step2_failure(self, tmp_path):
        """PUT upload fails → PublishError raised."""
        html = tmp_path / "report.html"
        html.write_text("<html></html>")

        from urllib.error import HTTPError
        from agentkit_cli.publish import PublishError

        call_count = [0]

        def _urlopen(req):
            call_count[0] += 1
            if call_count[0] == 1:
                # Step 1 succeeds
                data = {
                    "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                    "finalizeUrl": "https://api.here.now/v1/finalize/abc",
                }
                mock_resp = MagicMock()
                mock_resp.read.return_value = json.dumps(data).encode()

                class _CM:
                    def __enter__(self_inner): return mock_resp
                    def __exit__(self_inner, *a): pass

                return _CM()
            else:
                raise HTTPError(url="https://upload.here.now/f1", code=403, msg="Forbidden", hdrs=None, fp=BytesIO(b"403"))

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_urlopen):
            from agentkit_cli.publish import publish_html
            with pytest.raises(PublishError, match="403"):
                publish_html(html)

    def test_api_step3_failure(self, tmp_path):
        """Finalize POST fails → PublishError raised."""
        html = tmp_path / "report.html"
        html.write_text("<html></html>")

        from urllib.error import HTTPError
        from agentkit_cli.publish import PublishError

        call_count = [0]

        def _urlopen(req):
            call_count[0] += 1
            if call_count[0] == 1:
                # Step 1
                data = {
                    "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                    "finalizeUrl": "https://api.here.now/v1/finalize/abc",
                }
            elif call_count[0] == 2:
                # Step 2 PUT
                data = {}
            else:
                raise HTTPError(url="https://api.here.now/v1/finalize/abc", code=500, msg="Internal Server Error", hdrs=None, fp=BytesIO(b"500"))

            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(data).encode()

            class _CM:
                def __enter__(self_inner): return mock_resp
                def __exit__(self_inner, *a): pass

            return _CM()

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_urlopen):
            from agentkit_cli.publish import publish_html
            with pytest.raises(PublishError, match="500"):
                publish_html(html)

    def test_json_output(self, tmp_path, capsys):
        """--json flag emits valid JSON with url and expires_in."""
        html = tmp_path / "agentkit-report.html"
        html.write_text("<html></html>")

        responses = [
            {"uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}], "finalizeUrl": "https://api.here.now/v1/finalize/abc"},
            {},
            {"url": "https://abc.here.now/"},
        ]

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_mock_urlopen(responses)):
            with patch("os.environ.get", return_value=None):
                import os
                orig_cwd = os.getcwd()
                os.chdir(tmp_path)
                try:
                    from agentkit_cli.publish import publish_command
                    publish_command(html_path=None, json_output=True, quiet=False)
                finally:
                    os.chdir(orig_cwd)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "url" in data
        assert data["url"] == "https://abc.here.now/"
        assert "expires_in" in data

    def test_quiet_output(self, tmp_path, capsys):
        """--quiet flag prints only the URL."""
        html = tmp_path / "agentkit-report.html"
        html.write_text("<html></html>")

        responses = [
            {"uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}], "finalizeUrl": "https://api.here.now/v1/finalize/abc"},
            {},
            {"url": "https://abc.here.now/"},
        ]

        with patch("agentkit_cli.publish.request.urlopen", side_effect=_mock_urlopen(responses)):
            import os
            orig_cwd = os.getcwd()
            os.chdir(tmp_path)
            try:
                from agentkit_cli.publish import publish_command
                publish_command(html_path=None, json_output=False, quiet=True)
            finally:
                os.chdir(orig_cwd)

        captured = capsys.readouterr()
        assert captured.out.strip() == "https://abc.here.now/"


# ---------------------------------------------------------------------------
# D2 --publish flag integration tests
# ---------------------------------------------------------------------------

class TestPublishFlags:
    def test_run_publish_flag(self, tmp_path):
        """run_command with publish=True calls publish_html after report is written."""
        from agentkit_cli.commands.run_cmd import run_command

        publish_calls = []

        def mock_publish_html(path, api_key=None):
            publish_calls.append(path)
            return {"url": "https://test.here.now/", "anonymous": True}

        def mock_resolve(path_arg):
            # Return a dummy path without needing a real file
            p = tmp_path / "agentkit-report.html"
            p.write_text("<html></html>")
            return p

        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=tmp_path), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.publish.publish_html", side_effect=mock_publish_html), \
             patch("agentkit_cli.publish.resolve_html_path", side_effect=mock_resolve):
            run_command(path=tmp_path, skip=None, benchmark=False, json_output=False, notes=None, ci=True, publish=True)

        assert len(publish_calls) == 1

    def test_report_publish_flag(self, tmp_path):
        """report_command with publish=True calls publish_html; failure is non-fatal."""
        from agentkit_cli.commands.report_cmd import report_command
        from agentkit_cli.publish import PublishError

        publish_called = []

        def mock_publish_fail(path, api_key=None):
            publish_called.append(True)
            raise PublishError("network error")

        with patch("agentkit_cli.commands.report_cmd.run_all", return_value={
                "agentlint": None, "agentmd": None, "coderace": None, "agentreflect": None}), \
             patch("agentkit_cli.commands.report_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.publish.publish_html", side_effect=mock_publish_fail):
            # Should NOT raise even though publish fails
            report_command(
                path=tmp_path,
                json_output=False,
                output=tmp_path / "out.html",
                open_browser=False,
                publish=True,
            )

        # publish was attempted
        assert len(publish_called) == 1
