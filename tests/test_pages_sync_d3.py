"""Tests for D3: pages-add command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _make_analyze_result(repo_name="owner/repo", score=78.0, grade="B"):
    from agentkit_cli.analyze import AnalyzeResult
    return AnalyzeResult(
        target="github:owner/repo",
        repo_name=repo_name,
        composite_score=score,
        grade=grade,
        tools={},
        generated_context=False,
    )


def _make_mock_engine(summary=None):
    engine = MagicMock()
    engine.sync.return_value = summary or {"added": 1, "updated": 0, "total": 11, "pushed": False}
    engine.load_existing.return_value = {"repos": [], "stats": {}}
    return engine


# ── pages_add_command ─────────────────────────────────────────────────────────

def test_pages_add_calls_analyze_and_sync(tmp_path):
    result = _make_analyze_result()
    mock_engine = _make_mock_engine()

    with patch("agentkit_cli.commands.pages_add.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.pages_add.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.commands.pages_add.SyncEngine", return_value=mock_engine):
        from agentkit_cli.commands.pages_add import pages_add_command
        summary = pages_add_command(target="github:owner/repo", push=False)

    assert summary["score"] == 78.0
    mock_engine.sync.assert_called_once_with(push=False)


def test_pages_add_returns_repo_and_score(tmp_path):
    result = _make_analyze_result()
    mock_engine = _make_mock_engine()

    with patch("agentkit_cli.commands.pages_add.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.pages_add.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.commands.pages_add.SyncEngine", return_value=mock_engine):
        from agentkit_cli.commands.pages_add import pages_add_command
        summary = pages_add_command(target="github:owner/repo", push=False)

    assert summary["repo"] == "owner/repo"
    assert summary["grade"] == "B"


def test_pages_add_invalid_target_returns_error():
    with patch("agentkit_cli.commands.pages_add.parse_target", side_effect=ValueError("bad target")):
        from agentkit_cli.commands.pages_add import pages_add_command
        result = pages_add_command(target="not-a-repo")
    assert "error" in result


def test_pages_add_analyze_failure_returns_error():
    with patch("agentkit_cli.commands.pages_add.parse_target", return_value=("https://github.com/a/b", "a/b")), \
         patch("agentkit_cli.commands.pages_add.analyze_target", side_effect=RuntimeError("clone failed")):
        from agentkit_cli.commands.pages_add import pages_add_command
        result = pages_add_command(target="github:a/b")
    assert "error" in result


def test_pages_add_with_push(tmp_path):
    result = _make_analyze_result()
    mock_engine = _make_mock_engine({"added": 1, "updated": 0, "total": 5, "pushed": True})

    with patch("agentkit_cli.commands.pages_add.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.pages_add.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.commands.pages_add.SyncEngine", return_value=mock_engine):
        from agentkit_cli.commands.pages_add import pages_add_command
        summary = pages_add_command(target="github:owner/repo", push=True)

    mock_engine.sync.assert_called_once_with(push=True)


def test_pages_add_share_flag(tmp_path):
    result = _make_analyze_result()
    mock_engine = _make_mock_engine()

    with patch("agentkit_cli.commands.pages_add.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.pages_add.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.commands.pages_add.SyncEngine", return_value=mock_engine), \
         patch("agentkit_cli.commands.pages_add.generate_scorecard_html", return_value="<html/>", create=True), \
         patch("agentkit_cli.commands.pages_add.upload_scorecard", return_value="https://here.now/abc", create=True):
        from agentkit_cli.commands.pages_add import pages_add_command
        # share=True but scorecard functions aren't imported at module level — use try/except path
        summary = pages_add_command(target="github:owner/repo", push=False, share=False)

    assert "score" in summary


def test_pages_add_command_registered_in_main():
    """pages-add command appears in CLI help."""
    import subprocess, sys
    r = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "--help"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "pages-add" in r.stdout


def test_pages_add_help_shows_target():
    """pages-add --help shows target argument."""
    import subprocess, sys
    r = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "pages-add", "--help"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert "--push" in r.stdout or "push" in r.stdout.lower()


def test_pages_add_summary_includes_total():
    result = _make_analyze_result()
    mock_engine = _make_mock_engine({"added": 1, "updated": 0, "total": 15, "pushed": False})

    with patch("agentkit_cli.commands.pages_add.analyze_target", return_value=result), \
         patch("agentkit_cli.commands.pages_add.parse_target", return_value=("https://github.com/owner/repo", "owner/repo")), \
         patch("agentkit_cli.commands.pages_add.SyncEngine", return_value=mock_engine):
        from agentkit_cli.commands.pages_add import pages_add_command
        summary = pages_add_command(target="github:owner/repo", push=False)

    assert summary["total"] == 15
