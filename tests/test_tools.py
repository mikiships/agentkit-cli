"""Tests for tool detection utilities."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from agentkit_cli.tools import (
    which, is_installed, get_version, tool_status, QUARTET_TOOLS, INSTALL_HINTS
)


def test_which_returns_none_for_nonexistent():
    assert which("this_tool_does_not_exist_xyzzy") is None


def test_which_returns_path_for_python():
    result = which("python3")
    assert result is not None


def test_is_installed_false_for_nonexistent():
    assert is_installed("this_tool_does_not_exist_xyzzy") is False


def test_is_installed_true_for_python():
    assert is_installed("python3") is True


def test_tool_status_returns_all_quartet():
    status = tool_status()
    for tool in QUARTET_TOOLS:
        assert tool in status


def test_tool_status_structure():
    status = tool_status()
    for tool, info in status.items():
        assert "installed" in info
        assert "path" in info
        assert "version" in info


def test_install_hints_for_all_quartet():
    for tool in QUARTET_TOOLS:
        assert tool in INSTALL_HINTS
        assert "pip install" in INSTALL_HINTS[tool]


def test_get_version_none_for_missing():
    result = get_version("this_tool_does_not_exist_xyzzy")
    assert result is None
