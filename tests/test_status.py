"""Tests for agentkit status command."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from agentkit_cli.main import app

runner = CliRunner()


def _fake_tool_status_none():
    return {
        "agentmd": {"installed": False, "path": None, "version": None},
        "coderace": {"installed": False, "path": None, "version": None},
        "agentlint": {"installed": False, "path": None, "version": None},
        "agentreflect": {"installed": False, "path": None, "version": None},
    }


def _fake_tool_status_all():
    return {
        "agentmd": {"installed": True, "path": "/usr/local/bin/agentmd", "version": "agentmd 1.0.0"},
        "coderace": {"installed": True, "path": "/usr/local/bin/coderace", "version": "coderace 1.0.0"},
        "agentlint": {"installed": True, "path": "/usr/local/bin/agentlint", "version": "agentlint 1.0.0"},
        "agentreflect": {"installed": True, "path": "/usr/local/bin/agentreflect", "version": "agentreflect 1.0.0"},
    }


def test_status_runs_without_error(tmp_path):
    """status command exits cleanly."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert result.exit_code == 0


def test_status_shows_quartet_tools(tmp_path):
    """status output mentions all quartet tools."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    output = result.output
    assert "agentmd" in output
    assert "coderace" in output
    assert "agentlint" in output
    assert "agentreflect" in output


def test_status_shows_missing_tools(tmp_path):
    """status shows tools as missing when not installed."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert "missing" in result.output


def test_status_shows_installed_tools(tmp_path):
    """status shows tools as installed when present."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_all()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert "installed" in result.output


def test_status_shows_config_missing(tmp_path):
    """status shows when .agentkit.yaml is missing."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert ".agentkit.yaml" in result.output


def test_status_shows_config_exists(tmp_path):
    """status shows when .agentkit.yaml exists."""
    (tmp_path / ".agentkit.yaml").write_text("tools:\n  agentmd: true\n")
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert "exists" in result.output


def test_status_shows_claude_md_missing(tmp_path):
    """status shows when CLAUDE.md is absent."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert "CLAUDE.md" in result.output


def test_status_shows_claude_md_exists(tmp_path):
    """status shows CLAUDE.md as present when it exists."""
    (tmp_path / "CLAUDE.md").write_text("# Context\n")
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    output = result.output
    assert "CLAUDE.md" in output


def test_status_json_output_valid(tmp_path):
    """--json flag produces parseable JSON."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0
    output = result.output
    json_start = output.find("{")
    assert json_start != -1
    json_str = output[json_start:output.rfind("}") + 1]
    data = json.loads(json_str)
    assert "tools" in data
    assert "files" in data


def test_status_json_has_tool_keys(tmp_path):
    """JSON output contains all quartet tool keys."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path), "--json"])
    output = result.output
    json_start = output.find("{")
    json_str = output[json_start:output.rfind("}") + 1]
    data = json.loads(json_str)
    tools = data["tools"]
    assert "agentmd" in tools
    assert "coderace" in tools
    assert "agentlint" in tools
    assert "agentreflect" in tools


def test_status_shows_last_run_when_present(tmp_path):
    """status shows last run summary when .agentkit-last-run.json exists."""
    last_run_data = {
        "timestamp": "2026-03-12T10:00:00Z",
        "passed": 3,
        "failed": 0,
        "skipped": 2,
        "steps": [],
    }
    (tmp_path / ".agentkit-last-run.json").write_text(json.dumps(last_run_data))
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert "Last Run" in result.output or "2026-03-12" in result.output


def test_status_no_crash_without_last_run(tmp_path):
    """status doesn't crash when no last run file."""
    with patch("agentkit_cli.commands.status_cmd.tool_status", return_value=_fake_tool_status_none()):
        result = runner.invoke(app, ["status", "--path", str(tmp_path)])
    assert result.exit_code == 0
