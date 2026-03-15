"""Tests for --share flag on agentkit analyze (D1, D3 new params)."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.analyze import AnalyzeResult
from agentkit_cli.main import app
from agentkit_cli.share import generate_scorecard_html, generate_sweep_scorecard_html

runner = CliRunner()


def _make_analyze_result(score: float = 75.0) -> AnalyzeResult:
    return AnalyzeResult(
        target="github:owner/repo",
        repo_name="repo",
        composite_score=score,
        grade="C",
        tools={"agentmd": {"tool": "agentmd", "status": "pass", "score": score, "finding": "ok"}},
        generated_context=False,
    )


# ---------------------------------------------------------------------------
# D1: --share on analyze — rich output
# ---------------------------------------------------------------------------

class TestAnalyzeShareFlag:
    @patch("agentkit_cli.commands.analyze_cmd.upload_scorecard", return_value="https://abc.here.now/")
    @patch("agentkit_cli.commands.analyze_cmd.analyze_target")
    def test_share_prints_url(self, mock_analyze, mock_upload):
        mock_analyze.return_value = _make_analyze_result(75.0)
        result = runner.invoke(app, ["analyze", "github:owner/repo", "--share"])
        assert result.exit_code == 0
        assert "https://abc.here.now/" in result.output

    @patch("agentkit_cli.commands.analyze_cmd.upload_scorecard", return_value="https://abc.here.now/")
    @patch("agentkit_cli.commands.analyze_cmd.analyze_target")
    def test_share_json_includes_share_url(self, mock_analyze, mock_upload):
        mock_analyze.return_value = _make_analyze_result(80.0)
        result = runner.invoke(app, ["analyze", "github:owner/repo", "--share", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["share_url"] == "https://abc.here.now/"

    @patch("agentkit_cli.commands.analyze_cmd.upload_scorecard", return_value=None)
    @patch("agentkit_cli.commands.analyze_cmd.analyze_target")
    def test_share_upload_failure_nonfatal(self, mock_analyze, mock_upload):
        """Upload failure should not crash analyze; still exits 0."""
        mock_analyze.return_value = _make_analyze_result(70.0)
        result = runner.invoke(app, ["analyze", "github:owner/repo", "--share"])
        assert result.exit_code == 0

    @patch("agentkit_cli.commands.analyze_cmd.analyze_target")
    def test_no_share_flag_no_upload(self, mock_analyze):
        mock_analyze.return_value = _make_analyze_result(80.0)
        with patch("agentkit_cli.commands.analyze_cmd.upload_scorecard") as mock_upload:
            runner.invoke(app, ["analyze", "github:owner/repo"])
            mock_upload.assert_not_called()

    @patch("agentkit_cli.commands.analyze_cmd.upload_scorecard", return_value="https://x.here.now/")
    @patch("agentkit_cli.commands.analyze_cmd.analyze_target")
    def test_share_json_no_share_url_when_no_flag(self, mock_analyze, mock_upload):
        """Without --share, JSON output should NOT include share_url."""
        mock_analyze.return_value = _make_analyze_result(80.0)
        result = runner.invoke(app, ["analyze", "github:owner/repo", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "share_url" not in data

    def test_analyze_help_has_share_option(self):
        result = runner.invoke(app, ["analyze", "--help"])
        assert "--share" in result.output


# ---------------------------------------------------------------------------
# D3: generate_scorecard_html new params (repo_url, repo_name)
# ---------------------------------------------------------------------------

class TestScorecardHtmlD3:
    def test_repo_url_github_prefix_rendered_as_link(self):
        html = generate_scorecard_html(
            {"composite": 80},
            project_name="repo",
            repo_url="github:owner/repo",
            repo_name="repo",
        )
        assert "github.com/owner/repo" in html
        assert "<a href=" in html

    def test_repo_url_https_rendered_as_link(self):
        html = generate_scorecard_html(
            {"composite": 80},
            project_name="repo",
            repo_url="https://github.com/owner/repo.git",
            repo_name="myrepo",
        )
        assert "myrepo" in html
        assert "<a href=" in html

    def test_repo_name_overrides_project_name_in_header(self):
        html = generate_scorecard_html(
            {"composite": 80},
            project_name="fallback",
            repo_url="github:owner/myrepo",
            repo_name="myrepo",
        )
        assert "myrepo" in html

    def test_backward_compat_no_repo_params(self):
        """Existing callers without repo_url/repo_name still work."""
        html = generate_scorecard_html({"composite": 80}, project_name="proj", ref="main")
        assert "proj" in html
        assert "<!DOCTYPE html>" in html

    def test_timestamp_shown_in_footer(self):
        html = generate_scorecard_html(
            {"composite": 80},
            project_name="p",
            timestamp="2026-03-15 08:00 UTC",
        )
        assert "2026-03-15" in html

    def test_analyzed_by_footer(self):
        html = generate_scorecard_html({"composite": 80}, project_name="p")
        assert "Analyzed by" in html
        assert "agentkit-cli" in html


# ---------------------------------------------------------------------------
# D2: generate_sweep_scorecard_html
# ---------------------------------------------------------------------------

class TestGenerateSweepScorecardHtml:
    def _make_results(self):
        return [
            {"target": "github:owner/repo1", "score": 85.0, "grade": "B", "status": "succeeded", "error": None},
            {"target": "github:owner/repo2", "score": 42.0, "grade": "F", "status": "failed", "error": "clone failed"},
        ]

    def test_generates_html(self):
        html = generate_sweep_scorecard_html(self._make_results())
        assert "<!DOCTYPE html>" in html
        assert "agentkit sweep" in html

    def test_contains_targets(self):
        html = generate_sweep_scorecard_html(self._make_results())
        assert "repo1" in html
        assert "repo2" in html

    def test_contains_scores(self):
        html = generate_sweep_scorecard_html(self._make_results())
        assert "85" in html
        assert "42" in html

    def test_contains_timestamp(self):
        html = generate_sweep_scorecard_html(self._make_results(), timestamp="2026-03-15 09:00 UTC")
        assert "2026-03-15" in html

    def test_contains_footer(self):
        html = generate_sweep_scorecard_html(self._make_results())
        assert "agentkit-cli" in html
        assert "Analyzed by" in html

    def test_target_count_shown(self):
        html = generate_sweep_scorecard_html(self._make_results())
        assert "2" in html  # 2 targets

    def test_empty_results(self):
        html = generate_sweep_scorecard_html([])
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# D2: --share on sweep CLI
# ---------------------------------------------------------------------------

from agentkit_cli.sweep import SweepRunResult, SweepTargetResult


def _make_sweep_result(targets=None, scores=None):
    if targets is None:
        targets = ["github:owner/repo1", "github:owner/repo2"]
    if scores is None:
        scores = [85.0, 42.0]
    results = [
        SweepTargetResult(
            target=t,
            status="succeeded",
            repo_name=t.split("/")[-1],
            composite_score=s,
            grade="B",
            error=None,
            successful_tools=3,
            total_tools=3,
        )
        for t, s in zip(targets, scores)
    ]
    return SweepRunResult(targets=targets, results=results)


class TestSweepShareFlag:
    @patch("agentkit_cli.commands.sweep_cmd.upload_scorecard", return_value="https://sweep.here.now/")
    @patch("agentkit_cli.commands.sweep_cmd.run_sweep")
    def test_share_prints_url(self, mock_sweep, mock_upload):
        mock_sweep.return_value = _make_sweep_result()
        result = runner.invoke(app, ["sweep", "github:owner/repo1", "github:owner/repo2", "--share"])
        assert result.exit_code == 0
        assert "https://sweep.here.now/" in result.output

    @patch("agentkit_cli.commands.sweep_cmd.upload_scorecard", return_value="https://sweep.here.now/")
    @patch("agentkit_cli.commands.sweep_cmd.run_sweep")
    def test_share_single_upload(self, mock_sweep, mock_upload):
        mock_sweep.return_value = _make_sweep_result()
        runner.invoke(app, ["sweep", "github:owner/repo1", "github:owner/repo2", "--share"])
        mock_upload.assert_called_once()

    @patch("agentkit_cli.commands.sweep_cmd.upload_scorecard", return_value="https://sweep.here.now/")
    @patch("agentkit_cli.commands.sweep_cmd.run_sweep")
    def test_share_json_includes_share_url(self, mock_sweep, mock_upload):
        mock_sweep.return_value = _make_sweep_result()
        result = runner.invoke(app, ["sweep", "github:owner/repo1", "--share", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["share_url"] == "https://sweep.here.now/"

    @patch("agentkit_cli.commands.sweep_cmd.upload_scorecard", return_value=None)
    @patch("agentkit_cli.commands.sweep_cmd.run_sweep")
    def test_share_upload_failure_nonfatal(self, mock_sweep, mock_upload):
        mock_sweep.return_value = _make_sweep_result()
        result = runner.invoke(app, ["sweep", "github:owner/repo1", "--share"])
        assert result.exit_code == 0

    @patch("agentkit_cli.commands.sweep_cmd.run_sweep")
    def test_no_share_no_upload(self, mock_sweep):
        mock_sweep.return_value = _make_sweep_result()
        with patch("agentkit_cli.commands.sweep_cmd.upload_scorecard") as mock_upload:
            runner.invoke(app, ["sweep", "github:owner/repo1"])
            mock_upload.assert_not_called()

    def test_sweep_help_has_share_option(self):
        result = runner.invoke(app, ["sweep", "--help"])
        assert "--share" in result.output
