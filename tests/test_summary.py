"""Tests for agentkit summary command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.commands.summary_cmd import (
    build_summary_markdown,
    build_summary_payload,
)
from agentkit_cli.main import app

runner = CliRunner()


SAMPLE_RESULTS = {
    "project": "demo-project",
    "tools": [
        {"tool": "agentlint", "installed": True, "status": "success"},
        {"tool": "agentmd", "installed": True, "status": "success"},
        {"tool": "coderace", "installed": False, "status": "not_installed"},
        {"tool": "agentreflect", "installed": True, "status": "success"},
    ],
    "agentlint": {
        "score": 82,
        "issues": [
            {
                "type": "path-rot",
                "severity": "critical",
                "message": "Broken docs path",
                "file": "CLAUDE.md",
            }
        ],
    },
    "agentmd": {"score": 76, "files": [{"name": "CLAUDE.md"}, {"name": "AGENTS.md"}]},
    "coderace": None,
    "agentreflect": {"count": 2, "suggestions_md": "### Fix stale roadmap\n### Trim duplicate examples"},
}


WARNING_HEAVY_RESULTS = {
    "project": "warn-project",
    "tools": [
        {"tool": "agentlint", "installed": True, "status": "success"},
        {"tool": "agentmd", "installed": True, "status": "success"},
        {"tool": "coderace", "installed": True, "status": "success"},
        {"tool": "agentreflect", "installed": True, "status": "success"},
    ],
    "agentlint": {
        "score": 71,
        "issues": [
            {"type": "cosmetic", "severity": "warning", "message": "Heading order is inconsistent", "file": "AGENTS.md"},
            {"type": "cosmetic", "severity": "warning", "message": "Long paragraph in CLAUDE.md", "file": "CLAUDE.md"},
        ],
    },
    "agentmd": {"score": 73, "files": [{"name": "CLAUDE.md"}]},
    "coderace": {"score": 75, "results": [{"agent": "codex", "score": 75}]},
    "agentreflect": {"count": 0, "suggestions_md": ""},
}


NO_FINDINGS_RESULTS = {
    "project": "clean-project",
    "tools": [
        {"tool": "agentlint", "installed": True, "status": "success"},
        {"tool": "agentmd", "installed": True, "status": "success"},
        {"tool": "coderace", "installed": True, "status": "success"},
        {"tool": "agentreflect", "installed": True, "status": "success"},
    ],
    "agentlint": {"score": 92, "issues": []},
    "agentmd": {"score": 90, "files": [{"name": "CLAUDE.md"}]},
    "coderace": {"score": 91, "results": [{"agent": "codex", "score": 91}]},
    "agentreflect": {"count": 0, "suggestions_md": ""},
}


COMPARE_RESULTS = {
    **SAMPLE_RESULTS,
    "compare": {
        "ref1": "main",
        "ref2": "HEAD",
        "verdict": "DEGRADED",
        "net_delta": -6.5,
        "tools": [
            {"tool": "agentlint", "score_ref1": 88, "score_ref2": 82, "delta": -6.0},
            {"tool": "agentmd", "score_ref1": 77, "score_ref2": 76, "delta": -1.0},
        ],
    },
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
    assert "## Overview" in rendered_once
    assert "Verdict: Action Required" in rendered_once
    assert "| agentlint | success | 82 | 1 critical |" in rendered_once
    assert "## Top fixes" in rendered_once
    assert "[critical] Broken docs path (CLAUDE.md) — path-rot" in rendered_once


def test_summary_payload_uses_warning_verdict_for_warning_heavy_results():
    payload = build_summary_payload(WARNING_HEAVY_RESULTS)

    assert payload["verdict"] == "WARNINGS_PRESENT"
    assert payload["tool_status"][0]["notes"] == "2 warning(s)"
    assert payload["top_fixes"][0]["summary"] == "Heading order is inconsistent"


def test_summary_markdown_shows_no_findings_state():
    rendered = build_summary_markdown(NO_FINDINGS_RESULTS)

    assert "Verdict: Passing" in rendered
    assert "No actionable fixes found." in rendered
    assert "| agentlint | success | 92 | No issues found |" in rendered


def test_summary_markdown_includes_compare_section_for_regressions():
    rendered = build_summary_markdown(COMPARE_RESULTS)

    assert "Verdict: Regression Detected" in rendered
    assert "## Compare" in rendered
    assert "- Base ref: main" in rendered
    assert "- Head ref: HEAD" in rendered
    assert "| agentlint | 88 | 82 | -6.0 |" in rendered


def test_summary_reads_existing_json_input(tmp_path: Path):
    json_path = tmp_path / "report.json"
    json_path.write_text(json.dumps(SAMPLE_RESULTS), encoding="utf-8")

    result = runner.invoke(app, ["summary", "--json-input", str(json_path)])

    assert result.exit_code == 0, result.output
    assert "# agentkit summary" in result.output
    assert "Verdict: Action Required" in result.output


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
