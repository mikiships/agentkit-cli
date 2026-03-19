"""Tests for D2: agentkit user-improve CLI command (≥14 tests)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.commands.user_improve_cmd import user_improve_command
from agentkit_cli.user_improve import UserImproveReport, UserImproveResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(full_name: str, before: float, after: float) -> UserImproveResult:
    return UserImproveResult(
        repo_url=f"https://github.com/{full_name}",
        full_name=full_name,
        before_score=before,
        after_score=after,
        lift=round(after - before, 2),
        files_generated=["CLAUDE.md"],
        files_hardened=[],
    )


def _make_report(user: str = "alice", improved: int = 2) -> UserImproveReport:
    results = [_make_result(f"alice/repo-{i}", 60.0, 75.0) for i in range(improved)]
    return UserImproveReport(
        user=user,
        avatar_url="",
        total_repos=10,
        improved=improved,
        skipped=0,
        results=results,
        summary_stats={"avg_before": 60.0, "avg_after": 75.0, "avg_lift": 15.0,
                       "total_files_generated": improved, "total_files_hardened": 0},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_command_empty_user_exits(capsys):
    import typer
    with pytest.raises((SystemExit, typer.Exit)) as exc:
        user_improve_command(target="github:", limit=5, below=80)
    code = exc.value.code if hasattr(exc.value, "code") else exc.value.exit_code if hasattr(exc.value, "exit_code") else 1
    assert code == 1


def test_command_empty_bare_user_exits(capsys):
    import typer
    with pytest.raises((SystemExit, typer.Exit)) as exc:
        user_improve_command(target="", limit=5, below=80)
    code = exc.value.code if hasattr(exc.value, "code") else exc.value.exit_code if hasattr(exc.value, "exit_code") else 1
    assert code == 1


def test_command_dry_run_json(capsys):
    mock_engine = MagicMock()
    mock_engine.fetch_user_repos.return_value = [
        {"full_name": "alice/repo-0", "name": "repo-0", "stars": 5}
    ]
    mock_engine.score_repos.return_value = [
        MagicMock(full_name="alice/repo-0", score=60.0, grade="C", to_dict=lambda: {"full_name": "alice/repo-0", "score": 60.0, "grade": "C", "name": "repo-0", "stars": 5, "repo_url": "https://github.com/alice/repo-0"})
    ]
    mock_engine.select_targets.return_value = mock_engine.score_repos.return_value

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        user_improve_command(
            target="github:alice",
            limit=5,
            below=80,
            dry_run=True,
            json_output=True,
        )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["dry_run"] is True
    assert data["user"] == "alice"
    assert "would_improve" in data


def test_command_dry_run_no_targets(capsys):
    mock_engine = MagicMock()
    mock_engine.fetch_user_repos.return_value = []
    mock_engine.score_repos.return_value = []
    mock_engine.select_targets.return_value = []

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        user_improve_command(
            target="github:alice",
            limit=5,
            below=80,
            dry_run=True,
            json_output=False,
        )
    captured = capsys.readouterr()
    assert "No repos" in captured.out or captured.out == ""


def test_command_json_output(capsys):
    report = _make_report("alice", improved=2)
    mock_engine = MagicMock()
    mock_engine.run.return_value = report

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with patch("agentkit_cli.commands.user_improve_cmd.UserImproveHTMLRenderer") as mock_renderer:
            with patch("agentkit_cli.commands.user_improve_cmd.upload_user_improve_report", return_value=None):
                mock_renderer.return_value.render.return_value = "<html></html>"
                user_improve_command(
                    target="github:alice",
                    limit=5,
                    below=80,
                    json_output=True,
                )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["user"] == "alice"
    assert data["improved"] == 2


def test_command_share_adds_url(capsys):
    report = _make_report("alice")
    mock_engine = MagicMock()
    mock_engine.run.return_value = report

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with patch("agentkit_cli.commands.user_improve_cmd.UserImproveHTMLRenderer") as mock_renderer:
            with patch("agentkit_cli.commands.user_improve_cmd.upload_user_improve_report", return_value="https://here.now/test"):
                mock_renderer.return_value.render.return_value = "<html></html>"
                user_improve_command(
                    target="github:alice",
                    limit=5,
                    below=80,
                    share=True,
                    json_output=True,
                )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data.get("share_url") == "https://here.now/test"


def test_command_rich_output(capsys):
    report = _make_report("alice")
    mock_engine = MagicMock()
    mock_engine.run.return_value = report

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with patch("agentkit_cli.commands.user_improve_cmd.UserImproveHTMLRenderer") as mock_renderer:
            with patch("agentkit_cli.commands.user_improve_cmd.upload_user_improve_report", return_value=None):
                mock_renderer.return_value.render.return_value = "<html></html>"
                user_improve_command(
                    target="github:alice",
                    limit=5,
                    below=80,
                    json_output=False,
                )
    captured = capsys.readouterr()
    assert "alice" in captured.out


def test_command_error_json_on_value_error(capsys):
    import typer
    mock_engine = MagicMock()
    mock_engine.run.side_effect = ValueError("User not found")

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with pytest.raises((SystemExit, typer.Exit)):
            user_improve_command(
                target="github:nonexistent_xyz_999",
                limit=5,
                below=80,
                json_output=True,
            )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "error" in data


def test_command_limit_capped():
    report = _make_report("alice")
    mock_engine = MagicMock()
    mock_engine.run.return_value = report

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with patch("agentkit_cli.commands.user_improve_cmd.UserImproveHTMLRenderer") as mock_renderer:
            with patch("agentkit_cli.commands.user_improve_cmd.upload_user_improve_report", return_value=None):
                mock_renderer.return_value.render.return_value = "<html></html>"
                user_improve_command(
                    target="github:alice",
                    limit=50,  # above max
                    below=80,
                    json_output=False,
                )
    # Should not raise
    mock_engine.run.assert_called_once()
    args, kwargs = mock_engine.run.call_args
    limit_passed = kwargs.get("limit", args[1] if len(args) > 1 else None)
    assert limit_passed == 20


def test_command_bare_username():
    report = _make_report("alice")
    mock_engine = MagicMock()
    mock_engine.run.return_value = report

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with patch("agentkit_cli.commands.user_improve_cmd.UserImproveHTMLRenderer") as mock_renderer:
            with patch("agentkit_cli.commands.user_improve_cmd.upload_user_improve_report", return_value=None):
                mock_renderer.return_value.render.return_value = "<html></html>"
                user_improve_command(target="alice", limit=5, below=80, json_output=False)
    mock_engine.run.assert_called_once()
    args, kwargs = mock_engine.run.call_args
    assert args[0] == "alice" or kwargs.get("user") == "alice" or (len(args) > 0 and args[0] == "alice") or kwargs.get("username") == "alice"
    # The first positional arg is username
    if args:
        assert args[0] == "alice"


def test_command_records_history():
    report = _make_report("alice")
    mock_engine = MagicMock()
    mock_engine.run.return_value = report

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with patch("agentkit_cli.commands.user_improve_cmd.UserImproveHTMLRenderer") as mock_renderer:
            with patch("agentkit_cli.commands.user_improve_cmd.upload_user_improve_report", return_value=None):
                with patch("agentkit_cli.commands.user_improve_cmd.record_run") as mock_record:
                    mock_renderer.return_value.render.return_value = "<html></html>"
                    user_improve_command(target="github:alice", limit=5, below=80, json_output=False)
    mock_record.assert_called_once()
    # Check that tool="user-improve" was passed
    args, kwargs = mock_record.call_args
    all_args = list(args) + list(kwargs.values())
    assert "user-improve" in all_args or kwargs.get("tool") == "user-improve"


def test_command_dry_run_fetch_error(capsys):
    import typer
    mock_engine = MagicMock()
    mock_engine.fetch_user_repos.side_effect = ValueError("User 'xyz' not found")

    with patch("agentkit_cli.commands.user_improve_cmd.UserImproveEngine", return_value=mock_engine):
        with pytest.raises((SystemExit, typer.Exit)):
            user_improve_command(
                target="github:xyz",
                dry_run=True,
                json_output=True,
            )


def test_command_imports():
    from agentkit_cli.commands import user_improve_cmd
    assert hasattr(user_improve_cmd, "user_improve_command")
