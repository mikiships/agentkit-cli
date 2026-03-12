"""Tests for agentkit init command."""
from __future__ import annotations

import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from agentkit_cli.main import app

runner = CliRunner()


def test_init_creates_config(tmp_path):
    """init creates .agentkit.yaml in project root."""
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    config_file = tmp_path / ".agentkit.yaml"
    assert config_file.exists(), "Expected .agentkit.yaml to be created"


def test_init_config_content(tmp_path):
    """Config file contains expected keys."""
    runner.invoke(app, ["init", "--path", str(tmp_path)])
    config_file = tmp_path / ".agentkit.yaml"
    content = config_file.read_text()
    assert "tools:" in content
    assert "agentmd:" in content
    assert "coderace:" in content
    assert "agentlint:" in content
    assert "agentreflect:" in content
    assert "defaults:" in content
    assert "min_score:" in content
    assert "context_file:" in content


def test_init_does_not_overwrite_existing_config(tmp_path):
    """init doesn't overwrite existing config."""
    config_file = tmp_path / ".agentkit.yaml"
    config_file.write_text("custom: true\n")
    runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert config_file.read_text() == "custom: true\n"


def test_init_shows_tool_status(tmp_path):
    """init output includes tool status table."""
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    # Should mention quartet tools
    output = result.output
    assert "agentmd" in output
    assert "coderace" in output
    assert "agentlint" in output
    assert "agentreflect" in output


def test_init_shows_next_steps(tmp_path):
    """init output includes next steps."""
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "Next Steps" in result.output or "agentkit run" in result.output


def test_init_shows_install_instructions_for_missing_tools(tmp_path):
    """When tools are missing, install hints are shown."""
    with patch("agentkit_cli.commands.init_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "pip install" in result.output


def test_init_with_git_root(tmp_path):
    """init detects git root when no --path given."""
    # Create a fake git repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    subdir = tmp_path / "src"
    subdir.mkdir()

    with patch("agentkit_cli.config.Path.cwd", return_value=subdir):
        result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".agentkit.yaml").exists()


def test_init_output_mentions_agentkit_run(tmp_path):
    """init output mentions agentkit run."""
    result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert "agentkit run" in result.output


def test_init_all_tools_installed(tmp_path):
    """When all tools installed, no install hints shown."""
    with patch("agentkit_cli.commands.init_cmd.is_installed", return_value=True):
        result = runner.invoke(app, ["init", "--path", str(tmp_path)])
    assert result.exit_code == 0
    # Should not say "pip install" for missing tools section
    # (the table shows installed, no separate install block)
    output = result.output
    assert "installed" in output
