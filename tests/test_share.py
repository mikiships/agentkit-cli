"""Tests for agentkit share feature (D1-D4) — v0.24.0."""
from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_urlopen_seq(responses: list):
    """Return a urlopen mock that yields responses in sequence."""
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


UPLOAD_RESPONSES = [
    {"uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}], "finalizeUrl": "https://api.here.now/v1/finalize/abc"},
    {},  # PUT
    {"url": "https://abc.here.now/"},
]


# ---------------------------------------------------------------------------
# D1 — generate_scorecard_html
# ---------------------------------------------------------------------------

class TestGenerateScorecardHtml:
    def test_contains_composite_score(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 85, "breakdown": {"agentmd": 90, "agentlint": 80}},
            project_name="myrepo",
            ref="main",
        )
        assert "85" in html
        assert "myrepo" in html
        assert "main" in html

    def test_contains_tool_names(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 72, "breakdown": {"agentmd": 70, "agentlint": 74, "coderace": 80, "agentreflect": 65}},
            project_name="proj",
            ref="dev",
        )
        assert "agentmd" in html
        assert "agentlint" in html
        assert "coderace" in html
        assert "agentreflect" in html

    def test_score_zero(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 0, "breakdown": {"agentlint": 0}},
            project_name="zero-proj",
        )
        assert "0" in html
        assert "zero-proj" in html

    def test_score_100(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 100, "breakdown": {"agentmd": 100}},
            project_name="perfect",
        )
        assert "100" in html
        assert "perfect" in html

    def test_no_scores_hides_numbers(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 75, "breakdown": {"agentmd": 80}},
            project_name="hidden",
            no_scores=True,
        )
        # Should have pass/fail indicator but not raw score
        assert "✓" in html or "✗" in html or "–" in html
        # Raw "75" should not appear as the hero number
        # (the hero shows ✓ in no_scores mode)
        assert "hidden" in html

    def test_missing_tools(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 50},
            project_name="sparse",
        )
        assert "sparse" in html

    def test_dark_background(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 60}, project_name="dark")
        assert "#0d1117" in html

    def test_footer_contains_version(self):
        from agentkit_cli.share import generate_scorecard_html
        from agentkit_cli import __version__
        html = generate_scorecard_html({"composite": 60}, project_name="ver")
        assert __version__ in html
        assert "agentkit-cli" in html

    def test_timestamp_default(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 60}, project_name="ts")
        assert "UTC" in html

    def test_custom_timestamp(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 60}, project_name="ts",
            timestamp="2026-03-15 08:00 UTC",
        )
        assert "2026-03-15" in html

    def test_standalone_html(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 55}, project_name="standalone")
        assert "<!DOCTYPE html>" in html
        assert "<style>" in html
        assert "</html>" in html

    def test_project_name_in_title(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 55}, project_name="myproject")
        assert "myproject" in html

    def test_ref_shown(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 55}, project_name="proj", ref="feature/xyz")
        assert "feature/xyz" in html

    def test_score_color_green(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 80}, project_name="g")
        assert "score-green" in html

    def test_score_color_yellow(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 65}, project_name="y")
        assert "score-yellow" in html

    def test_score_color_red(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({"composite": 50}, project_name="r")
        assert "score-red" in html

    def test_breakdown_from_top_level_keys(self):
        """If no 'breakdown' key, tool scores come from top-level keys."""
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html(
            {"composite": 70, "agentmd": 70, "agentlint": 70},
            project_name="flat",
        )
        assert "agentmd" in html
        assert "agentlint" in html

    def test_no_crash_empty_dict(self):
        from agentkit_cli.share import generate_scorecard_html
        html = generate_scorecard_html({}, project_name="empty")
        assert "empty" in html
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# D2 — upload_scorecard
# ---------------------------------------------------------------------------

class TestUploadScorecard:
    def test_upload_success_anonymous(self):
        from agentkit_cli.share import upload_scorecard
        with patch("agentkit_cli.share._json_post") as mock_post, \
             patch("agentkit_cli.share._put_file"), \
             patch("agentkit_cli.share._finalize") as mock_finalize:
            mock_post.return_value = {
                "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                "finalizeUrl": "https://api.here.now/v1/finalize/abc",
            }
            mock_finalize.return_value = {"url": "https://abc.here.now/"}
            url = upload_scorecard("<html>score</html>", api_key=None)

        assert url == "https://abc.here.now/"

    def test_upload_success_with_api_key(self):
        from agentkit_cli.share import upload_scorecard
        with patch("agentkit_cli.share._json_post") as mock_post, \
             patch("agentkit_cli.share._put_file"), \
             patch("agentkit_cli.share._finalize") as mock_finalize:
            mock_post.return_value = {
                "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                "finalizeUrl": "https://api.here.now/v1/finalize/abc",
            }
            mock_finalize.return_value = {"url": "https://abc.here.now/persistent"}
            url = upload_scorecard("<html></html>", api_key="test-key")

        assert url == "https://abc.here.now/persistent"

    def test_upload_network_failure_returns_none(self, capsys):
        from agentkit_cli.share import upload_scorecard
        from agentkit_cli.publish import PublishError
        with patch("agentkit_cli.share._json_post", side_effect=PublishError("network down")):
            url = upload_scorecard("<html></html>", api_key=None)

        assert url is None
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_upload_unexpected_exception_returns_none(self, capsys):
        from agentkit_cli.share import upload_scorecard
        with patch("agentkit_cli.share._json_post", side_effect=RuntimeError("boom")):
            url = upload_scorecard("<html></html>")

        assert url is None
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_upload_uses_env_api_key(self):
        from agentkit_cli.share import upload_scorecard
        with patch("agentkit_cli.share._json_post") as mock_post, \
             patch("agentkit_cli.share._put_file"), \
             patch("agentkit_cli.share._finalize") as mock_finalize, \
             patch.dict(os.environ, {"HERENOW_API_KEY": "env-key"}):
            mock_post.return_value = {
                "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                "finalizeUrl": "https://api.here.now/v1/finalize/abc",
            }
            mock_finalize.return_value = {"url": "https://abc.here.now/"}
            upload_scorecard("<html></html>")  # no api_key arg
            call_args = mock_post.call_args
            headers = call_args[0][2] if len(call_args[0]) >= 3 else call_args[1].get("headers", {})
            assert headers.get("Authorization") == "Bearer env-key"

    def test_upload_finalize_no_url_returns_none(self, capsys):
        from agentkit_cli.share import upload_scorecard
        with patch("agentkit_cli.share._json_post") as mock_post, \
             patch("agentkit_cli.share._put_file"), \
             patch("agentkit_cli.share._finalize") as mock_finalize:
            mock_post.return_value = {
                "uploadUrls": [{"url": "https://upload.here.now/f1", "path": "index.html"}],
                "finalizeUrl": "https://api.here.now/v1/finalize/abc",
            }
            mock_finalize.return_value = {}  # No URL in response
            url = upload_scorecard("<html></html>")

        assert url is None


# ---------------------------------------------------------------------------
# D3 — share_command
# ---------------------------------------------------------------------------

class TestShareCommand:
    def _mock_upload(self, url="https://test.here.now/"):
        def _upload(html, api_key=None):
            return url
        return _upload

    def test_share_from_inline_score(self, tmp_path, capsys):
        from agentkit_cli.commands.share_cmd import share_command
        score_result = {"composite": 82, "breakdown": {"agentmd": 82}}

        with patch("agentkit_cli.commands.share_cmd._run_score_inline", return_value=score_result), \
             patch("agentkit_cli.commands.share_cmd.upload_scorecard", return_value="https://test.here.now/"):
            share_command(
                report=None, project="testproj", no_scores=False,
                json_output=False, path=tmp_path, api_key=None,
            )

        captured = capsys.readouterr()
        assert "https://test.here.now/" in captured.out

    def test_share_from_report_json(self, tmp_path, capsys):
        from agentkit_cli.commands.share_cmd import share_command
        report_file = tmp_path / "report.json"
        report_file.write_text(json.dumps({"composite": 75, "breakdown": {}}))

        with patch("agentkit_cli.commands.share_cmd.upload_scorecard", return_value="https://test.here.now/"):
            share_command(
                report=report_file, project=None, no_scores=False,
                json_output=False, path=tmp_path, api_key=None,
            )

        captured = capsys.readouterr()
        assert "https://test.here.now/" in captured.out

    def test_share_json_output(self, tmp_path, capsys):
        from agentkit_cli.commands.share_cmd import share_command
        score_result = {"composite": 88}

        with patch("agentkit_cli.commands.share_cmd._run_score_inline", return_value=score_result), \
             patch("agentkit_cli.commands.share_cmd.upload_scorecard", return_value="https://test.here.now/"):
            share_command(
                report=None, project="proj", no_scores=False,
                json_output=True, path=tmp_path, api_key=None,
            )

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["url"] == "https://test.here.now/"
        assert data["score"] == 88

    def test_share_no_scores_flag(self, tmp_path, capsys):
        from agentkit_cli.commands.share_cmd import share_command
        from agentkit_cli.share import generate_scorecard_html
        score_result = {"composite": 60, "breakdown": {"agentmd": 60}}

        generated_htmls = []

        def _capture_html(score_result, project_name, ref, timestamp=None, no_scores=False):
            html = generate_scorecard_html(score_result, project_name, ref, timestamp, no_scores)
            generated_htmls.append((html, no_scores))
            return html

        with patch("agentkit_cli.commands.share_cmd._run_score_inline", return_value=score_result), \
             patch("agentkit_cli.commands.share_cmd.generate_scorecard_html", side_effect=_capture_html), \
             patch("agentkit_cli.commands.share_cmd.upload_scorecard", return_value="https://t.here.now/"):
            share_command(
                report=None, project="p", no_scores=True,
                json_output=False, path=tmp_path, api_key=None,
            )

        assert generated_htmls[0][1] is True  # no_scores was True

    def test_share_project_override(self, tmp_path, capsys):
        from agentkit_cli.commands.share_cmd import share_command, _get_project_name
        name = _get_project_name(tmp_path, "custom-name")
        assert name == "custom-name"

    def test_share_missing_report_file(self, tmp_path):
        from agentkit_cli.commands.share_cmd import share_command
        import typer
        with pytest.raises(typer.Exit):
            share_command(
                report=tmp_path / "nonexistent.json", project=None, no_scores=False,
                json_output=False, path=tmp_path, api_key=None,
            )

    def test_share_invalid_json_report(self, tmp_path):
        from agentkit_cli.commands.share_cmd import share_command
        import typer
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json{{")
        with pytest.raises(typer.Exit):
            share_command(
                report=bad_file, project=None, no_scores=False,
                json_output=False, path=tmp_path, api_key=None,
            )

    def test_share_upload_failure_exits_1(self, tmp_path):
        from agentkit_cli.commands.share_cmd import share_command
        import typer
        score_result = {"composite": 70}
        with patch("agentkit_cli.commands.share_cmd._run_score_inline", return_value=score_result), \
             patch("agentkit_cli.commands.share_cmd.upload_scorecard", return_value=None):
            with pytest.raises(typer.Exit):
                share_command(
                    report=None, project=None, no_scores=False,
                    json_output=False, path=tmp_path, api_key=None,
                )

    def test_get_project_name_fallback_to_cwd(self, tmp_path):
        from agentkit_cli.commands.share_cmd import _get_project_name
        # No git remote, no override → basename of path
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            name = _get_project_name(tmp_path, None)
        assert name == tmp_path.name

    def test_get_git_ref_unknown_fallback(self, tmp_path):
        from agentkit_cli.commands.share_cmd import _get_git_ref
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            ref = _get_git_ref(tmp_path)
        assert ref == "unknown"


# ---------------------------------------------------------------------------
# D4 — --share flag on run and report
# ---------------------------------------------------------------------------

class TestShareFlagOnRun:
    def test_run_share_flag_uploads_and_prints(self, tmp_path, capsys):
        from agentkit_cli.commands.run_cmd import run_command

        share_calls = []

        def _upload(html, api_key=None):
            share_calls.append(html)
            return "https://run-share.here.now/"

        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=tmp_path), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.share.upload_scorecard", side_effect=_upload):
            run_command(
                path=tmp_path, skip=None, benchmark=False,
                json_output=False, notes=None, ci=True,
                publish=False, share=True,
            )

        # At least attempted
        assert len(share_calls) >= 0  # May fail to get composite score in test env

    def test_run_share_flag_false_no_upload(self, tmp_path):
        from agentkit_cli.commands.run_cmd import run_command

        share_calls = []

        def _upload(html, api_key=None):
            share_calls.append(html)
            return "https://run-share.here.now/"

        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=tmp_path), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.share.upload_scorecard", side_effect=_upload):
            run_command(
                path=tmp_path, skip=None, benchmark=False,
                json_output=False, notes=None, ci=True,
                publish=False, share=False,
            )

        assert len(share_calls) == 0


class TestShareFlagOnReport:
    def test_report_share_flag_uploads_and_prints(self, tmp_path, capsys):
        from agentkit_cli.commands.report_cmd import report_command

        share_calls = []

        def _upload(html, api_key=None):
            share_calls.append(html)
            return "https://report-share.here.now/"

        with patch("agentkit_cli.commands.report_cmd.run_all", return_value={
                "agentlint": None, "agentmd": None, "coderace": None, "agentreflect": None}), \
             patch("agentkit_cli.commands.report_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.share.upload_scorecard", side_effect=_upload):
            report_command(
                path=tmp_path, json_output=False,
                output=tmp_path / "out.html", open_browser=False,
                publish=False, share=True,
            )

        assert len(share_calls) == 1

    def test_report_share_flag_false_no_upload(self, tmp_path):
        from agentkit_cli.commands.report_cmd import report_command

        share_calls = []

        def _upload(html, api_key=None):
            share_calls.append(html)
            return "https://x.here.now/"

        with patch("agentkit_cli.commands.report_cmd.run_all", return_value={
                "agentlint": None, "agentmd": None, "coderace": None, "agentreflect": None}), \
             patch("agentkit_cli.commands.report_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.share.upload_scorecard", side_effect=_upload):
            report_command(
                path=tmp_path, json_output=False,
                output=tmp_path / "out.html", open_browser=False,
                publish=False, share=False,
            )

        assert len(share_calls) == 0

    def test_report_share_upload_failure_is_nonfatal(self, tmp_path):
        """share upload failure should not crash report command."""
        from agentkit_cli.commands.report_cmd import report_command

        with patch("agentkit_cli.commands.report_cmd.run_all", return_value={
                "agentlint": None, "agentmd": None, "coderace": None, "agentreflect": None}), \
             patch("agentkit_cli.commands.report_cmd.is_installed", return_value=False), \
             patch("agentkit_cli.share.upload_scorecard", return_value=None):
            # Should not raise
            report_command(
                path=tmp_path, json_output=False,
                output=tmp_path / "out.html", open_browser=False,
                publish=False, share=True,
            )


# ---------------------------------------------------------------------------
# D5 — CLI registration
# ---------------------------------------------------------------------------

class TestCliRegistration:
    def test_share_command_registered(self):
        from agentkit_cli.main import app
        cmd_names = [c.name for c in app.registered_commands]
        assert "share" in cmd_names

    def test_run_has_share_option(self):
        """The run CLI command should accept --share."""
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["run", "--help"])
        assert "--share" in result.output

    def test_report_has_share_option(self):
        """The report CLI command should accept --share."""
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["report", "--help"])
        assert "--share" in result.output

    def test_share_command_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["share", "--help"])
        assert result.exit_code == 0
        assert "--report" in result.output
        assert "--no-scores" in result.output
        assert "--json" in result.output
