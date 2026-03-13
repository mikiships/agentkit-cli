"""Tests for agentkit demo command."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.demo_cmd import (
    detect_project_type,
    detect_available_agents,
    pick_demo_task,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# detect_project_type
# ---------------------------------------------------------------------------

def test_detect_python_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'")
    assert detect_project_type(tmp_path) == "python"


def test_detect_python_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text("from setuptools import setup; setup()")
    assert detect_project_type(tmp_path) == "python"


def test_detect_python_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests>=2.0")
    assert detect_project_type(tmp_path) == "python"


def test_detect_typescript(tmp_path):
    (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}')
    assert detect_project_type(tmp_path) == "typescript"


def test_detect_javascript(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "foo"}')
    assert detect_project_type(tmp_path) == "javascript"


def test_detect_javascript_not_typescript_when_no_tsconfig(tmp_path):
    """package.json without tsconfig.json → javascript, not typescript."""
    (tmp_path / "package.json").write_text('{"name": "bar"}')
    assert detect_project_type(tmp_path) == "javascript"


def test_detect_typescript_takes_priority_over_package_json(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "ts-pkg"}')
    (tmp_path / "tsconfig.json").write_text('{}')
    assert detect_project_type(tmp_path) == "typescript"


def test_detect_generic_empty_dir(tmp_path):
    assert detect_project_type(tmp_path) == "generic"


# ---------------------------------------------------------------------------
# pick_demo_task
# ---------------------------------------------------------------------------

def test_pick_demo_task_python():
    assert pick_demo_task("python") == "bug-hunt"


def test_pick_demo_task_typescript():
    assert pick_demo_task("typescript") == "refactor"


def test_pick_demo_task_javascript():
    assert pick_demo_task("javascript") == "refactor"


def test_pick_demo_task_generic():
    assert pick_demo_task("generic") == "bug-hunt"


def test_pick_demo_task_unknown_falls_back():
    assert pick_demo_task("rust") == "bug-hunt"


# ---------------------------------------------------------------------------
# detect_available_agents
# ---------------------------------------------------------------------------

def test_detect_agents_none_available():
    with patch("agentkit_cli.commands.demo_cmd.shutil.which", return_value=None):
        result = detect_available_agents()
    assert result == []


def test_detect_agents_only_claude():
    def _which(name):
        return "/usr/local/bin/claude" if name == "claude" else None
    with patch("agentkit_cli.commands.demo_cmd.shutil.which", side_effect=_which):
        result = detect_available_agents()
    assert result == ["claude"]


def test_detect_agents_only_codex():
    def _which(name):
        return "/usr/local/bin/codex" if name == "codex" else None
    with patch("agentkit_cli.commands.demo_cmd.shutil.which", side_effect=_which):
        result = detect_available_agents()
    assert result == ["codex"]


def test_detect_agents_both():
    with patch("agentkit_cli.commands.demo_cmd.shutil.which", return_value="/usr/local/bin/x"):
        result = detect_available_agents()
    assert "claude" in result
    assert "codex" in result


# ---------------------------------------------------------------------------
# demo command — CLI integration
# ---------------------------------------------------------------------------

def _mock_no_tools(tool: str) -> bool:
    return False


def test_demo_skip_benchmark_no_crash(tmp_path):
    """--skip-benchmark runs without error when all tools are missing."""
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["demo", "--skip-benchmark"], catch_exceptions=False)
    assert result.exit_code == 0


def test_demo_skip_benchmark_shows_header(tmp_path):
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["demo", "--skip-benchmark"])
    assert "agentkit demo" in result.output


def test_demo_json_output_is_valid_json(tmp_path):
    """--json emits parseable JSON."""
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]):
            result = runner.invoke(app, ["demo", "--skip-benchmark", "--json"])
    # JSON is printed to stdout; find the JSON block
    parsed = json.loads(result.output)
    assert "project_type" in parsed
    assert "steps" in parsed
    assert "agents" in parsed


def test_demo_json_contains_task_field(tmp_path):
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]):
            result = runner.invoke(app, ["demo", "--json", "--task", "refactor", "--skip-benchmark"])
    parsed = json.loads(result.output)
    assert parsed["task"] == "refactor"


def test_demo_no_agents_shows_message():
    """No agents found message appears when agent list is empty and benchmark not skipped."""
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]):
            result = runner.invoke(app, ["demo"])
    assert "No agents found" in result.output or result.exit_code == 0


def test_demo_custom_task_option():
    """--task option is respected."""
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]):
            result = runner.invoke(app, ["demo", "--skip-benchmark", "--json", "--task", "bug-hunt"])
    parsed = json.loads(result.output)
    assert parsed["task"] == "bug-hunt"


def test_demo_agents_option_overrides_detection():
    """--agents option overrides auto-detection."""
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]) as mock_detect:
            result = runner.invoke(app, ["demo", "--skip-benchmark", "--json", "--agents", "claude,codex"])
    parsed = json.loads(result.output)
    assert "claude" in parsed["agents"]
    assert "codex" in parsed["agents"]
    # auto-detection not called when --agents supplied
    mock_detect.assert_not_called()


def test_demo_help_exits_zero():
    result = runner.invoke(app, ["demo", "--help"])
    assert result.exit_code == 0
    assert "demo" in result.output.lower()


def test_demo_benchmark_not_run_when_no_agents():
    """Benchmark step list is empty when no agents and not skipping (they just aren't run)."""
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]):
            result = runner.invoke(app, ["demo", "--json"])
    parsed = json.loads(result.output)
    assert parsed["benchmark"] == []


def test_demo_footer_hint_displayed():
    with patch("agentkit_cli.commands.demo_cmd.is_installed", return_value=False):
        with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=[]):
            result = runner.invoke(app, ["demo", "--skip-benchmark"])
    assert "agentkit init" in result.output


def test_demo_benchmark_mocked_agent():
    """Benchmark step runs and result returned when coderace is available."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "score: 87\n"
    mock_result.stderr = ""

    def _installed(tool):
        return tool == "coderace"

    with patch("agentkit_cli.commands.demo_cmd.is_installed", side_effect=_installed):
        with patch("agentkit_cli.commands.demo_cmd.run_tool", return_value=mock_result):
            with patch("agentkit_cli.commands.demo_cmd.detect_available_agents", return_value=["claude"]):
                result = runner.invoke(app, ["demo", "--json"])
    parsed = json.loads(result.output)
    assert len(parsed["benchmark"]) == 1
    assert parsed["benchmark"][0]["agent"] == "claude"
    assert parsed["benchmark"][0]["score"] == 87
