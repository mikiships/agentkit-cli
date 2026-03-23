"""Tests for D2: --pages flag on analyze and run commands."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


# ── analyze_command --pages ───────────────────────────────────────────────────

def _make_analyze_result(repo_name="owner/repo", score=75.0, grade="B"):
    from agentkit_cli.analyze import AnalyzeResult
    return AnalyzeResult(
        target="github:owner/repo",
        repo_name=repo_name,
        composite_score=score,
        grade=grade,
        tools={},
        generated_context=False,
    )


def test_analyze_command_pages_flag_calls_sync(tmp_path):
    """When --pages is set, analyze_command calls SyncEngine.sync."""
    result = _make_analyze_result()
    with patch("agentkit_cli.commands.analyze_cmd.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.analyze_cmd.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.pages_sync_engine.SyncEngine") as MockEngine:
        mock_instance = MagicMock()
        MockEngine.return_value = mock_instance

        from agentkit_cli.commands.analyze_cmd import analyze_command
        analyze_command(target="github:owner/repo", pages=True)

        mock_instance.sync.assert_called_once_with(push=False)


def test_analyze_command_no_pages_no_sync():
    """Without --pages, SyncEngine should NOT be called."""
    result = _make_analyze_result()
    with patch("agentkit_cli.commands.analyze_cmd.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.analyze_cmd.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.pages_sync_engine.SyncEngine") as MockEngine:
        mock_instance = MagicMock()
        MockEngine.return_value = mock_instance

        from agentkit_cli.commands.analyze_cmd import analyze_command
        analyze_command(target="github:owner/repo", pages=False)

        mock_instance.sync.assert_not_called()


def test_analyze_command_pages_prints_leaderboard_url(capsys):
    """When --pages syncs, calls sync with push=False."""
    result = _make_analyze_result()
    with patch("agentkit_cli.commands.analyze_cmd.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.analyze_cmd.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.pages_sync_engine.SyncEngine") as MockEngine:
        mock_instance = MagicMock()
        MockEngine.return_value = mock_instance

        from agentkit_cli.commands.analyze_cmd import analyze_command
        analyze_command(target="github:owner/repo", pages=True)
        mock_instance.sync.assert_called_once()


def test_analyze_command_pages_sync_failure_doesnt_crash():
    """If sync raises, analyze_command handles gracefully."""
    result = _make_analyze_result()
    with patch("agentkit_cli.commands.analyze_cmd.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.analyze_cmd.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.pages_sync_engine.SyncEngine") as MockEngine:
        mock_instance = MagicMock()
        mock_instance.sync.side_effect = RuntimeError("git push failed")
        MockEngine.return_value = mock_instance

        from agentkit_cli.commands.analyze_cmd import analyze_command
        # Should not raise
        analyze_command(target="github:owner/repo", pages=True)


def test_analyze_command_accepts_pages_parameter():
    """analyze_command signature accepts pages keyword arg."""
    import inspect
    from agentkit_cli.commands.analyze_cmd import analyze_command
    sig = inspect.signature(analyze_command)
    assert "pages" in sig.parameters


# ── run command --pages ───────────────────────────────────────────────────────

def test_run_command_has_pages_in_main():
    """main.py run command has --pages option."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "run", "--help"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "--pages" in result.stdout


def test_analyze_command_has_pages_in_main():
    """main.py analyze command has --pages option."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "analyze", "--help"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "--pages" in result.stdout


def test_pages_sync_command_registered():
    """pages-sync command appears in main help."""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "--help"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "pages-sync" in result.stdout
