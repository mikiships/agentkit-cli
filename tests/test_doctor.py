"""Tests for agentkit doctor command."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from agentkit_cli.main import app
from agentkit_cli.commands.doctor_cmd import check_tool

runner = CliRunner()


# --- check_tool unit tests ---

def test_check_tool_installed():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="1.0.0"):
        r = check_tool("coderace")
    assert r["installed"] is True
    assert r["version"] == "1.0.0"
    assert r["name"] == "coderace"


def test_check_tool_not_installed():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=False):
        r = check_tool("coderace")
    assert r["installed"] is False
    assert r["version"] == "NOT FOUND"
    assert "pip install" in r["install_hint"]


def test_check_tool_installed_no_version():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value=None):
        r = check_tool("agentmd")
    assert r["installed"] is True
    assert r["version"] == "NOT FOUND"


def test_check_tool_install_hint_present():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=False):
        r = check_tool("agentmd")
    assert r["install_hint"] == "pip install agentmd"


# --- CLI integration tests ---

def _all_installed(tool):
    return True

def _none_installed(tool):
    return False


def test_doctor_all_installed_exit_0():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", side_effect=_all_installed), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="1.0.0"):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0


def test_doctor_missing_tool_exit_1():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1


def test_doctor_shows_table_output():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="0.5.0"):
        result = runner.invoke(app, ["doctor"])
    assert "coderace" in result.output
    assert "agentmd" in result.output
    assert "agentlint" in result.output
    assert "agentreflect" in result.output


def test_doctor_json_all_installed():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", side_effect=_all_installed), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="2.0.0"):
        result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "coderace" in data
    assert "agentmd" in data
    assert "agentkit-cli" in data


def test_doctor_json_missing_exit_1():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["coderace"] == "NOT FOUND"


def test_doctor_json_partial_install():
    def partial(tool):
        return tool in ("coderace", "agentmd")

    with patch("agentkit_cli.commands.doctor_cmd.is_installed", side_effect=partial), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="1.0.0"):
        result = runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["coderace"] == "1.0.0"
    assert data["agentlint"] == "NOT FOUND"


def test_doctor_shows_missing_message():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=False):
        result = runner.invoke(app, ["doctor"])
    assert "missing" in result.output.lower() or "NOT FOUND" in result.output


def test_doctor_shows_installed_checkmark():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="1.0.0"):
        result = runner.invoke(app, ["doctor"])
    assert "installed" in result.output


def test_doctor_shows_agentkit_cli_version():
    with patch("agentkit_cli.commands.doctor_cmd.is_installed", return_value=True), \
         patch("agentkit_cli.commands.doctor_cmd.get_version", return_value="1.0.0"):
        result = runner.invoke(app, ["doctor"])
    assert "agentkit-cli" in result.output
