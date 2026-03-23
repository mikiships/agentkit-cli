"""Tests for D4: --interactive flag, README, quickstart/demo docs."""
from __future__ import annotations

from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# --interactive flag tests
# ---------------------------------------------------------------------------

def test_api_command_accepts_interactive():
    """api_command should accept interactive kwarg without error."""
    from agentkit_cli.commands.api_cmd import api_command
    import inspect
    sig = inspect.signature(api_command)
    assert "interactive" in sig.parameters


def test_api_main_has_interactive_flag():
    """The main.py api command should include --interactive."""
    from agentkit_cli.main import api
    import inspect
    sig = inspect.signature(api)
    assert "interactive" in sig.parameters


# ---------------------------------------------------------------------------
# README tests
# ---------------------------------------------------------------------------

def test_readme_has_interactive_demo_section():
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "## Interactive Demo" in readme


def test_readme_mentions_api_share():
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "agentkit api --share" in readme


def test_readme_mentions_interactive_flag():
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "--interactive" in readme


# ---------------------------------------------------------------------------
# quickstart output tests
# ---------------------------------------------------------------------------

def test_quickstart_mentions_api_share():
    """quickstart_cmd.py should mention agentkit api --share in next steps."""
    src = (Path(__file__).parent.parent / "agentkit_cli" / "commands" / "quickstart_cmd.py").read_text()
    assert "agentkit api --share" in src


# ---------------------------------------------------------------------------
# demo output tests
# ---------------------------------------------------------------------------

def test_demo_mentions_api_share():
    """demo_cmd.py should mention agentkit api --share."""
    src = (Path(__file__).parent.parent / "agentkit_cli" / "commands" / "demo_cmd.py").read_text()
    assert "agentkit api --share" in src


# ---------------------------------------------------------------------------
# docs/api.md tests
# ---------------------------------------------------------------------------

def test_docs_api_has_post_analyze():
    doc = (Path(__file__).parent.parent / "docs" / "api.md").read_text()
    assert "POST /analyze" in doc


def test_docs_api_has_recent():
    doc = (Path(__file__).parent.parent / "docs" / "api.md").read_text()
    assert "/recent" in doc


def test_docs_api_has_interactive_option():
    doc = (Path(__file__).parent.parent / "docs" / "api.md").read_text()
    assert "--interactive" in doc
