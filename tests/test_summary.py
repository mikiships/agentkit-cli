"""Tests for agentkit summary command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.summary_cmd import build_summary_markdown

runner = CliRunner()


SAMPLE_RESULTS = {
    "project": "demo-project",
    "tools": [
        {"tool": "agentlint", "installed": True, "status": "success"},
        {"tool": "agentmd", "installed": True, "status": "success"},
        {"tool": "coderace", "installed": False, "status": "not_installed"},
        {"tool": "agentreflect", "installed": True, "status": "success"},
    ],
    "agentlint": {"score": 82, "issues": [{"severity": "warning", "message": "Missing roadmap"}]},
    "agentmd": {"score": 76, "files": [{"name": "CLAUDE.md"}, {"name": "AGENTS.md"}]},
    "coderace": None,
    "agentreflect": {"count": 2, "suggestions_md": "### Fix one\n### Fix two"},
}


def test_summary_help():
    result = runner.invoke(app, ["summary", "--help"])
    assert result.exit_code == 0
    assert "--json-input" in result.output
    assert "--path" in result.output


def test_summary_build_markdown_is_deterministic():
    rendered_once = build_summary_markdown(SAMPLE_RESULTS)
    rendered_twice = build_summary_markdown(SAMPLE_RESULTS)
    assert rendered_once == rendered_twice
    assert "# agentkit summary" in rendered_once
    assert "Overall score: 79/100" in rendered_once
    assert "| agentlint | success | 82 | 1 issue(s) |" in rendered_once


def test_summary_reads_existing_json_input(tmp_path: Path):
    json_path = tmp_path / "report.json"
    json_path.write_text(json.dumps(SAMPLE_RESULTS), encoding="utf-8")

    result = runner.invoke(app, ["summary", "--json-input", str(json_path)])

    assert result.exit_code == 0, result.output
    assert "# agentkit summary" in result.output
    assert "Overall score: 79/100" in result.output


def test_summary_runs_local_analysis_for_path_mode(tmp_path: Path):
    mocked_results = {
        "agentlint": SAMPLE_RESULTS["agentlint"],
        "agentmd": SAMPLE_RESULTS["agentmd"],
        "coderace": SAMPLE_RESULTS["coderace"],
        "agentreflect": SAMPLE_RESULTS["agentreflect"],
    }

    with patch("agentkit_cli.commands.summary_cmd.run_all", return_value=mocked_results), patch(
        "agentkit_cli.commands.summary_cmd._tool_status",
        return_value=SAMPLE_RESULTS["tools"],
    ):
        result = runner.invoke(app, ["summary", "--path", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "# agentkit summary" in result.output
    assert "| agentmd | success | 76 | 2 file(s) analyzed |" in result.output
