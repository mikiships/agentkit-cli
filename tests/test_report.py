"""Tests for agentkit report command and report_runner module."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.report_cmd import (
    build_html,
    report_command,
    run_all,
    _coverage_score,
    _tool_status,
    _score_color_css,
)
from agentkit_cli import report_runner

runner = CliRunner()

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

SAMPLE_AGENTLINT = {
    "score": 72,
    "issues": [
        {"severity": "warning", "message": "CLAUDE.md missing architecture section"},
        {"severity": "error", "message": "No AGENTS.md found"},
    ],
}

SAMPLE_AGENTMD = {
    "score": 85,
    "files": [
        {"name": "CLAUDE.md", "size": 1024, "tier": "primary"},
        {"name": "AGENTS.md", "size": 512, "tier": "secondary"},
    ],
}

SAMPLE_CODERACE = {
    "results": [
        {"agent": "claude", "score": 88},
        {"agent": "codex", "score": 74},
    ]
}

SAMPLE_AGENTREFLECT = {
    "suggestions_md": "### Suggestion 1\nConsider adding more context files.\n### Suggestion 2\nUpdate AGENTS.md.",
    "count": 2,
}

ALL_RESULTS = {
    "agentlint": SAMPLE_AGENTLINT,
    "agentmd": SAMPLE_AGENTMD,
    "coderace": SAMPLE_CODERACE,
    "agentreflect": SAMPLE_AGENTREFLECT,
}

EMPTY_RESULTS = {
    "agentlint": None,
    "agentmd": None,
    "coderace": None,
    "agentreflect": None,
}

# ---------------------------------------------------------------------------
# T1: --help works
# ---------------------------------------------------------------------------

def test_report_help():
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "report" in result.output.lower()


def test_report_help_shows_json_flag():
    result = runner.invoke(app, ["report", "--help"])
    assert "--json" in result.output


def test_report_help_shows_output_flag():
    result = runner.invoke(app, ["report", "--help"])
    assert "--output" in result.output


def test_report_help_shows_open_flag():
    result = runner.invoke(app, ["report", "--help"])
    assert "--open" in result.output


# ---------------------------------------------------------------------------
# T5-T8: --json with mocked tools
# ---------------------------------------------------------------------------

def test_report_json_all_tools_mocked(tmp_path):
    """--json with all tools returning data produces valid JSON."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        result = runner.invoke(app, ["report", "--json", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["coverage"] == 100
    assert data["agentlint"] == SAMPLE_AGENTLINT
    assert data["agentmd"] == SAMPLE_AGENTMD
    assert data["coderace"] == SAMPLE_CODERACE
    assert data["agentreflect"] == SAMPLE_AGENTREFLECT


def test_report_json_no_tools(tmp_path):
    """--json with no tools installed returns zero coverage."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=EMPTY_RESULTS):
        result = runner.invoke(app, ["report", "--json", "--path", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["coverage"] == 0
    assert data["agentlint"] is None
    assert data["agentmd"] is None


def test_report_json_partial_tools(tmp_path):
    """--json with only some tools returns partial coverage."""
    partial = {**EMPTY_RESULTS, "agentlint": SAMPLE_AGENTLINT, "agentmd": SAMPLE_AGENTMD}
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=partial):
        result = runner.invoke(app, ["report", "--json", "--path", str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["coverage"] == 50


def test_report_json_has_tools_list(tmp_path):
    """--json output includes tool status list."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=EMPTY_RESULTS):
        result = runner.invoke(app, ["report", "--json", "--path", str(tmp_path)])
    data = json.loads(result.output)
    assert "tools" in data
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) == 4


# ---------------------------------------------------------------------------
# T9-T12: HTML output
# ---------------------------------------------------------------------------

def test_report_html_saved_to_output(tmp_path):
    """--output saves HTML to specified path."""
    out = tmp_path / "myreport.html"
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        result = runner.invoke(app, ["report", "--output", str(out), "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert out.exists()


def test_report_html_default_path(tmp_path):
    """Without --output, saves to agentkit-report.html in project dir."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "agentkit-report.html").exists()


def test_report_html_is_self_contained(tmp_path):
    """Generated HTML must not reference external URLs (CDN-free)."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        runner.invoke(app, ["report", "--path", str(tmp_path)])
    html = (tmp_path / "agentkit-report.html").read_text()
    assert "http://" not in html
    assert "https://" not in html


def test_report_html_has_minimum_size(tmp_path):
    """HTML report must be > 5KB."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        runner.invoke(app, ["report", "--path", str(tmp_path)])
    size = (tmp_path / "agentkit-report.html").stat().st_size
    assert size > 4000


def test_report_html_contains_expected_sections(tmp_path):
    """HTML contains key section markers."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        runner.invoke(app, ["report", "--path", str(tmp_path)])
    html = (tmp_path / "agentkit-report.html").read_text()
    assert "agentlint" in html.lower()
    assert "agentmd" in html.lower()
    assert "coderace" in html.lower()
    assert "agentreflect" in html.lower()
    assert "Pipeline Status" in html


def test_report_html_contains_project_name(tmp_path):
    """HTML report includes the project directory name."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=ALL_RESULTS):
        runner.invoke(app, ["report", "--path", str(tmp_path)])
    html = (tmp_path / "agentkit-report.html").read_text()
    assert tmp_path.name in html


def test_report_html_empty_results_still_valid(tmp_path):
    """HTML report with no tools doesn't crash and is still valid."""
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=EMPTY_RESULTS):
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "agentkit-report.html").exists()
    html = (tmp_path / "agentkit-report.html").read_text()
    assert "0%" in html  # 0 coverage


# ---------------------------------------------------------------------------
# T17-T20: build_html unit tests
# ---------------------------------------------------------------------------

def test_build_html_returns_string():
    statuses = _tool_status(ALL_RESULTS)
    html = build_html("myproject", ALL_RESULTS, statuses)
    assert isinstance(html, str)
    assert len(html) > 1000


def test_build_html_score_colors():
    """Score color function returns correct colors."""
    assert _score_color_css(90) == "#4caf50"   # green
    assert _score_color_css(65) == "#ffb300"   # yellow
    assert _score_color_css(30) == "#f44336"   # red
    assert _score_color_css(None) == "#888888" # grey


def test_coverage_score_full():
    assert _coverage_score(ALL_RESULTS) == 100


def test_coverage_score_empty():
    assert _coverage_score(EMPTY_RESULTS) == 0


def test_tool_status_structure():
    statuses = _tool_status(ALL_RESULTS)
    assert len(statuses) == 4
    for s in statuses:
        assert "tool" in s
        assert "installed" in s
        assert "status" in s


# ---------------------------------------------------------------------------
# T22-T28: report_runner unit tests with subprocess mocking
# ---------------------------------------------------------------------------

def _make_proc(stdout: str = "", returncode: int = 0) -> MagicMock:
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = ""
    return proc


def test_runner_agentlint_not_installed():
    with patch("agentkit_cli.report_runner._is_installed", return_value=False):
        result = report_runner.run_agentlint_check("/tmp")
    assert result is None


def test_runner_agentlint_success():
    data = {"score": 80, "issues": []}
    proc = _make_proc(stdout=json.dumps(data))
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_agentlint_check("/tmp")
    assert result == data


def test_runner_agentlint_failure():
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=None):
            result = report_runner.run_agentlint_check("/tmp")
    assert result is None


def test_runner_agentmd_not_installed():
    with patch("agentkit_cli.report_runner._is_installed", return_value=False):
        result = report_runner.run_agentmd_score("/tmp")
    assert result is None


def test_runner_agentmd_success():
    data = {"score": 75, "files": []}
    proc = _make_proc(stdout=json.dumps(data))
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_agentmd_score("/tmp")
    assert result == data


def test_runner_coderace_not_installed():
    with patch("agentkit_cli.report_runner._is_installed", return_value=False):
        result = report_runner.run_coderace_bench("/tmp")
    assert result is None


def test_runner_coderace_success():
    """coderace benchmark history returns parseable JSON → pass it through."""
    data = {"results": [{"agent": "claude", "score": 90}]}
    proc = _make_proc(stdout=json.dumps(data))
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_coderace_bench("/tmp")
    assert result == data


def test_runner_coderace_no_history():
    """coderace benchmark history returns no JSON → graceful no_results dict."""
    proc = _make_proc(stdout="No benchmark history found.")
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_coderace_bench("/tmp")
    assert result is not None
    assert result.get("status") == "no_results"


def test_runner_coderace_run_fails():
    """coderace benchmark history command fails → graceful no_results dict."""
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=None):
            result = report_runner.run_coderace_bench("/tmp")
    assert result is not None
    assert result.get("status") == "no_results"


def test_runner_agentreflect_not_installed():
    with patch("agentkit_cli.report_runner._is_installed", return_value=False):
        result = report_runner.run_agentreflect_analyze("/tmp")
    assert result is None


def test_runner_agentreflect_success():
    """agentreflect returns markdown text; runner wraps in suggestions_md dict."""
    md_text = "### Suggestion 1\nAdd more context.\n### Suggestion 2\nFix AGENTS.md."
    proc = _make_proc(stdout=md_text)
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_agentreflect_analyze("/tmp")
    assert result is not None
    assert "suggestions_md" in result
    assert result["suggestions_md"] == md_text
    assert result["count"] == 2


def test_runner_agentreflect_uses_correct_flags():
    """agentreflect runner must use --from-git --format markdown (not --format json)."""
    calls = []

    def capture_run(cmd, cwd, timeout):
        calls.append(cmd)
        return _make_proc(stdout="### Note\nsome suggestion")

    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", side_effect=capture_run):
            report_runner.run_agentreflect_analyze("/tmp")
    assert calls, "expected _run to be called"
    cmd = calls[0]
    assert "--from-git" in cmd
    assert "--format" in cmd
    assert "markdown" in cmd
    assert "json" not in cmd


def test_runner_invalid_json_returns_none():
    proc = _make_proc(stdout="not valid json at all")
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_agentlint_check("/tmp")
    assert result is None


def test_runner_json_with_prefix():
    """runner can extract JSON that has non-JSON prefix lines."""
    data = {"score": 50}
    raw = "Scanning project...\nDone.\n" + json.dumps(data)
    proc = _make_proc(stdout=raw)
    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", return_value=proc):
            result = report_runner.run_agentlint_check("/tmp")
    assert result == data


def test_runner_agentlint_uses_format_json_flag():
    """agentlint runner must use --format json, not --json."""
    calls = []

    def capture_run(cmd, cwd, timeout):
        calls.append(cmd)
        return _make_proc(stdout=json.dumps({"score": 80}))

    with patch("agentkit_cli.report_runner._is_installed", return_value=True):
        with patch("agentkit_cli.report_runner._run", side_effect=capture_run):
            report_runner.run_agentlint_check("/tmp")
    assert calls, "expected _run to be called"
    cmd = calls[0]
    assert "--format" in cmd
    assert "json" in cmd
    # The old wrong flag must NOT be present as a standalone --json
    assert "--json" not in cmd


# ---------------------------------------------------------------------------
# T-agentmd-list: agentmd list handling in summary card
# ---------------------------------------------------------------------------

def test_agentmd_summary_card_handles_list():
    """_agentmd_summary_card must handle a list of per-file dicts (D4 fix)."""
    from agentkit_cli.commands.report_cmd import _agentmd_summary_card
    data_list = [
        {"file": "CLAUDE.md", "score": 80},
        {"file": "AGENTS.md", "score": 60},
        {"file": "README.md", "score": 70},
    ]
    html = _agentmd_summary_card(data_list)
    assert "files analyzed" in html
    # Average score = 70
    assert "70" in html


def test_agentmd_summary_card_handles_empty_list():
    """_agentmd_summary_card must not crash on empty list."""
    from agentkit_cli.commands.report_cmd import _agentmd_summary_card
    html = _agentmd_summary_card([])
    assert "0 files analyzed" in html


def test_agentmd_summary_card_handles_dict():
    """_agentmd_summary_card still works with a plain dict (existing behavior)."""
    from agentkit_cli.commands.report_cmd import _agentmd_summary_card
    html = _agentmd_summary_card({"score": 85, "files": []})
    assert "85" in html
    assert "agentmd score" in html


def test_report_html_with_agentmd_list(tmp_path):
    """HTML generation doesn't crash when agentmd returns a list."""
    results_with_list = {
        **EMPTY_RESULTS,
        "agentmd": [
            {"file": "CLAUDE.md", "score": 75},
            {"file": "AGENTS.md", "score": 65},
        ],
    }
    with patch("agentkit_cli.commands.report_cmd.run_all", return_value=results_with_list):
        result = runner.invoke(app, ["report", "--path", str(tmp_path)])
    assert result.exit_code == 0
    html = (tmp_path / "agentkit-report.html").read_text()
    assert "files analyzed" in html


def test_agentreflect_section_renders_suggestions_md():
    """_agentreflect_section renders suggestions_md key (D3 fix)."""
    from agentkit_cli.commands.report_cmd import _agentreflect_section
    data = {
        "suggestions_md": "### Tip 1\nDo something.\n### Tip 2\nDo another.",
        "count": 2,
    }
    html = _agentreflect_section(data)
    assert "Tip 1" in html
    assert "Tip 2" in html
