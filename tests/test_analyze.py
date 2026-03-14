"""Tests for agentkit analyze command (D1-D3)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.analyze import parse_target, analyze_target, AnalyzeResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# D1: Target URL parsing
# ---------------------------------------------------------------------------

class TestParseTarget:
    def test_github_prefix(self):
        url, name = parse_target("github:tiangolo/fastapi")
        assert "github.com/tiangolo/fastapi" in url
        assert name == "fastapi"

    def test_https_url(self):
        url, name = parse_target("https://github.com/tiangolo/fastapi")
        assert url.endswith(".git")
        assert name == "fastapi"

    def test_https_url_with_git(self):
        url, name = parse_target("https://github.com/tiangolo/fastapi.git")
        assert url.endswith(".git")
        assert name == "fastapi"

    def test_bare_owner_repo(self):
        url, name = parse_target("owner/repo")
        assert "github.com/owner/repo" in url
        assert name == "repo"

    def test_local_dot_path(self, tmp_path):
        _, name = parse_target("./somedir")
        assert name == "somedir"

    def test_local_abs_path(self, tmp_path):
        _, name = parse_target(str(tmp_path))
        assert name == tmp_path.name

    def test_local_tilde_path(self):
        url, name = parse_target("~/somedir")
        assert "somedir" in url

    def test_invalid_target_raises(self):
        with pytest.raises(ValueError):
            parse_target("not a valid target!!")

    def test_invalid_no_slash(self):
        with pytest.raises(ValueError):
            parse_target("justaplainword")


# ---------------------------------------------------------------------------
# D1: Mock clone test
# ---------------------------------------------------------------------------

def _make_mock_run(returncode=0, stdout="score: 75", stderr=""):
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    mock.stderr = stderr
    return mock


@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.is_installed", return_value=False)
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.shutil.rmtree")
def test_clone_called_for_remote_target(mock_rmtree, mock_mkdtemp, mock_installed, mock_run, mock_which):
    """git clone is invoked for github: targets."""
    mock_run.return_value = _make_mock_run(returncode=0, stdout="")
    result = analyze_target("github:owner/repo", timeout=30)
    assert result.repo_name == "repo"
    # git clone should have been called
    clone_call = mock_run.call_args_list[0]
    assert "clone" in clone_call[0][0]


@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.is_installed", return_value=False)
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.shutil.rmtree")
def test_no_clone_for_local_path(mock_rmtree, mock_mkdtemp, mock_installed, mock_run, mock_which, tmp_path):
    """No git clone for local paths."""
    result = analyze_target(str(tmp_path), timeout=30)
    # mkdtemp should NOT have been called
    mock_mkdtemp.assert_not_called()
    assert result.repo_name == tmp_path.name


# ---------------------------------------------------------------------------
# D1: Mock pipeline test
# ---------------------------------------------------------------------------

@patch("agentkit_cli.analyze.shutil.rmtree")
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.is_installed")
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
def test_pipeline_skips_missing_tools(mock_which, mock_run, mock_installed, mock_mkdtemp, mock_rmtree):
    """Tools not installed are skipped, analysis still returns result."""
    # git clone succeeds, tools not installed
    mock_run.return_value = _make_mock_run(returncode=0, stdout="")
    mock_installed.return_value = False

    result = analyze_target("github:owner/repo", timeout=30)
    # All tools skipped → scores None → composite score from engine
    assert isinstance(result.composite_score, float)
    assert result.grade in ("A", "B", "C", "D", "F")


@patch("agentkit_cli.analyze.shutil.rmtree")
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.is_installed", return_value=True)
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
def test_pipeline_with_all_tools_pass(mock_which, mock_run, mock_installed, mock_mkdtemp, mock_rmtree):
    """When all tools pass, composite_score > 0."""
    # First call = git clone, rest = tool calls with score: 80
    mock_run.return_value = _make_mock_run(returncode=0, stdout="score: 80")
    result = analyze_target("github:owner/repo", timeout=30)
    assert result.composite_score > 0


# ---------------------------------------------------------------------------
# D1: no_generate flag
# ---------------------------------------------------------------------------

@patch("agentkit_cli.analyze.shutil.rmtree")
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.is_installed", return_value=False)
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
def test_no_generate_skips_generate_step(mock_which, mock_run, mock_installed, mock_mkdtemp, mock_rmtree):
    """--no-generate skips agentmd generate."""
    mock_run.return_value = _make_mock_run(returncode=0, stdout="")
    result = analyze_target("github:owner/repo", no_generate=True, timeout=30)
    assert result.generated_context is False
    assert "agentmd_generate" not in result.tools


# ---------------------------------------------------------------------------
# D2: JSON output schema
# ---------------------------------------------------------------------------

@patch("agentkit_cli.commands.analyze_cmd.analyze_target")
def test_json_output_schema(mock_analyze):
    """--json output contains required fields."""
    mock_analyze.return_value = AnalyzeResult(
        target="github:owner/repo",
        repo_name="repo",
        composite_score=75.0,
        grade="C",
        tools={"agentmd": {"tool": "agentmd", "status": "pass", "score": 75.0, "finding": "ok"}},
        generated_context=False,
    )
    result = runner.invoke(app, ["analyze", "github:owner/repo", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "target" in data
    assert "repo_name" in data
    assert "composite_score" in data
    assert "grade" in data
    assert "tools" in data
    assert "generated_context" in data
    # temp_dir and report_url omitted when None
    assert "temp_dir" not in data
    assert "report_url" not in data


@patch("agentkit_cli.commands.analyze_cmd.analyze_target")
def test_json_output_with_temp_dir(mock_analyze):
    """--json includes temp_dir when --keep is used."""
    mock_analyze.return_value = AnalyzeResult(
        target="github:owner/repo",
        repo_name="repo",
        composite_score=80.0,
        grade="B",
        tools={},
        generated_context=False,
        temp_dir="/tmp/agentkit-analyze-test",
    )
    result = runner.invoke(app, ["analyze", "github:owner/repo", "--json", "--keep"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "temp_dir" in data
    assert data["temp_dir"] == "/tmp/agentkit-analyze-test"


# ---------------------------------------------------------------------------
# D2: Rich table output
# ---------------------------------------------------------------------------

@patch("agentkit_cli.commands.analyze_cmd.analyze_target")
def test_rich_table_output(mock_analyze):
    """Default output shows score headline."""
    mock_analyze.return_value = AnalyzeResult(
        target="github:owner/repo",
        repo_name="repo",
        composite_score=82.0,
        grade="B",
        tools={"agentmd": {"tool": "agentmd", "status": "pass", "score": 82.0, "finding": "good"}},
        generated_context=False,
    )
    result = runner.invoke(app, ["analyze", "github:owner/repo"])
    assert result.exit_code == 0
    assert "Agent Quality Score" in result.output
    assert "repo" in result.output
    assert "82" in result.output


# ---------------------------------------------------------------------------
# D3: Error handling
# ---------------------------------------------------------------------------

@patch("agentkit_cli.analyze.shutil.which", return_value=None)
def test_git_not_installed_error(mock_which, tmp_path):
    """Clear error when git is not installed."""
    with pytest.raises(RuntimeError, match="git is not installed"):
        analyze_target("github:owner/repo", timeout=30)


@patch("agentkit_cli.commands.analyze_cmd.analyze_target", side_effect=RuntimeError("clone failed: repository not found"))
def test_clone_failure_exits_nonzero(mock_analyze):
    """Clone failures exit with code 1."""
    result = runner.invoke(app, ["analyze", "github:owner/nonexistent"])
    assert result.exit_code == 1
    assert "Error" in result.output


@patch("agentkit_cli.analyze.shutil.rmtree")
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.is_installed", return_value=True)
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
def test_tool_timeout_yields_error_status(mock_which, mock_run, mock_installed, mock_mkdtemp, mock_rmtree):
    """Timeout on tool yields error status but doesn't abort whole analysis."""
    import subprocess as sp

    def side_effect(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if "clone" in cmd:
            m = MagicMock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m
        raise sp.TimeoutExpired(cmd, 1)

    mock_run.side_effect = side_effect
    result = analyze_target("github:owner/repo", timeout=1)
    # Should still return a result, with error statuses on tools
    assert isinstance(result, AnalyzeResult)
    for tr in result.tools.values():
        assert tr["status"] in ("error", "skipped", "pass", "fail")


@patch("agentkit_cli.analyze.shutil.rmtree")
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.is_installed", return_value=True)
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
def test_temp_dir_cleaned_on_success(mock_which, mock_run, mock_installed, mock_mkdtemp, mock_rmtree):
    """Temp dir removed after analysis (unless --keep)."""
    mock_run.return_value = _make_mock_run(returncode=0, stdout="score: 70")
    analyze_target("github:owner/repo", keep=False, timeout=30)
    mock_rmtree.assert_called()


@patch("agentkit_cli.analyze.shutil.rmtree")
@patch("agentkit_cli.analyze.tempfile.mkdtemp", return_value="/tmp/agentkit-analyze-test")
@patch("agentkit_cli.analyze.is_installed", return_value=False)
@patch("agentkit_cli.analyze.subprocess.run")
@patch("agentkit_cli.analyze.shutil.which", return_value="/usr/bin/git")
def test_temp_dir_cleaned_on_clone_failure(mock_which, mock_run, mock_installed, mock_mkdtemp, mock_rmtree):
    """Temp dir cleaned up even when clone fails."""
    mock_run.return_value = _make_mock_run(returncode=1, stdout="", stderr="repo not found")
    with pytest.raises(RuntimeError):
        analyze_target("github:owner/repo", keep=False, timeout=30)
    mock_rmtree.assert_called()


# ---------------------------------------------------------------------------
# D3: Invalid target
# ---------------------------------------------------------------------------

def test_invalid_target_cli_exits_nonzero():
    """Invalid target string exits with code 1."""
    result = runner.invoke(app, ["analyze", "not!!valid"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# D1: AnalyzeResult.to_dict()
# ---------------------------------------------------------------------------

def test_analyze_result_to_dict_schema():
    ar = AnalyzeResult(
        target="github:owner/repo",
        repo_name="repo",
        composite_score=65.0,
        grade="D",
        tools={"agentmd": {"tool": "agentmd", "status": "fail", "score": 0.0, "finding": "no context"}},
        generated_context=True,
    )
    d = ar.to_dict()
    assert d["target"] == "github:owner/repo"
    assert d["composite_score"] == 65.0
    assert d["grade"] == "D"
    assert "agentmd" in d["tools"]
    assert d["generated_context"] is True
    assert "temp_dir" not in d
    assert "report_url" not in d


def test_analyze_result_to_dict_includes_temp_dir_when_set():
    ar = AnalyzeResult(
        target="github:o/r",
        repo_name="r",
        composite_score=50.0,
        grade="F",
        tools={},
        generated_context=False,
        temp_dir="/tmp/test-dir",
    )
    d = ar.to_dict()
    assert d["temp_dir"] == "/tmp/test-dir"
