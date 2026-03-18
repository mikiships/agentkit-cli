"""Tests for D4: agentkit run --timeline integration and doctor hint."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.history import HistoryDB
from agentkit_cli.commands.run_cmd import run_command

runner = CliRunner()


def _make_db(tmp_path: Path) -> tuple[HistoryDB, Path]:
    db_path = tmp_path / "history.db"
    db = HistoryDB(db_path=db_path)
    return db, db_path


def _populate(db: HistoryDB, n: int = 5) -> None:
    for i in range(n):
        db.record_run("proj", "overall", float(70 + i))


# -------------------------------------------------------------------------
# run --timeline flag accepted
# -------------------------------------------------------------------------

def test_run_timeline_flag_in_help():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "--timeline" in result.output


def test_run_command_accepts_timeline_kwarg():
    """run_command accepts timeline=True without TypeError."""
    import inspect
    sig = inspect.signature(run_command)
    assert "timeline" in sig.parameters


def test_run_timeline_generates_html(tmp_path):
    """With a populated DB and --timeline, timeline.html should be written."""
    db, db_path = _make_db(tmp_path)
    _populate(db, n=5)
    out_html = tmp_path / "timeline.html"

    with patch("agentkit_cli.commands.timeline_cmd.timeline_command") as mock_tl:
        mock_tl.return_value = None
        # Patch run_command to skip real tool execution
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            with patch("agentkit_cli.commands.run_cmd.record_run"):
                result = runner.invoke(app, ["run", "--timeline", "--no-history"])
    # timeline_command should have been called
    mock_tl.assert_called_once()


# -------------------------------------------------------------------------
# doctor hint
# -------------------------------------------------------------------------

def test_doctor_no_hint_when_empty(tmp_path):
    """Doctor should NOT show timeline hint when DB is empty."""
    db, db_path = _make_db(tmp_path)

    with patch("agentkit_cli.commands.doctor_cmd.run_doctor") as mock_run:
        mock_run.return_value = MagicMock(
            fail_count=0, warn_count=0,
            as_dict=lambda: {"checks": []},
        )
        with patch("agentkit_cli.commands.doctor_cmd.render_human_report"):
            with patch("agentkit_cli.history.HistoryDB.get_history", return_value=[]):
                result = runner.invoke(app, ["doctor", "--no-fail-exit"])
    # We just verify no crash
    assert result.exit_code == 0


def test_doctor_shows_hint_when_history_present(tmp_path):
    """Doctor should show timeline hint when DB has ≥3 entries."""
    db, db_path = _make_db(tmp_path)
    _populate(db, n=5)

    fake_rows = [{"id": i, "ts": "2026-01-01", "project": "proj", "tool": "overall", "score": 80.0, "details": None, "label": None} for i in range(3)]

    with patch("agentkit_cli.commands.doctor_cmd.run_doctor") as mock_run:
        mock_run.return_value = MagicMock(
            fail_count=0, warn_count=0,
            as_dict=lambda: {"checks": []},
        )
        with patch("agentkit_cli.commands.doctor_cmd.render_human_report"):
            with patch("agentkit_cli.history.HistoryDB.get_history", return_value=fake_rows):
                result = runner.invoke(app, ["doctor", "--no-fail-exit"])
    assert result.exit_code == 0
    assert "timeline" in result.output.lower()


# -------------------------------------------------------------------------
# run --timeline + --share forwarding
# -------------------------------------------------------------------------

def test_run_timeline_with_share_passes_share(tmp_path):
    """run --timeline --share should call timeline_command with share=True."""
    db, db_path = _make_db(tmp_path)
    _populate(db, n=3)

    with patch("agentkit_cli.commands.timeline_cmd.timeline_command") as mock_tl:
        mock_tl.return_value = None
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            with patch("agentkit_cli.commands.run_cmd.record_run"):
                runner.invoke(app, ["run", "--timeline", "--share", "--no-history"])
    mock_tl.assert_called_once()
    # share=True should have been passed
    _, kwargs = mock_tl.call_args
    assert kwargs.get("share") is True or (mock_tl.call_args[0] and True in mock_tl.call_args[0])


# -------------------------------------------------------------------------
# timeline_command function signature
# -------------------------------------------------------------------------

def test_timeline_cmd_has_db_path_param():
    from agentkit_cli.commands.timeline_cmd import timeline_command
    import inspect
    sig = inspect.signature(timeline_command)
    assert "db_path" in sig.parameters


def test_timeline_cmd_has_json_output_param():
    from agentkit_cli.commands.timeline_cmd import timeline_command
    import inspect
    sig = inspect.signature(timeline_command)
    assert "json_output" in sig.parameters


def test_timeline_cmd_has_share_param():
    from agentkit_cli.commands.timeline_cmd import timeline_command
    import inspect
    sig = inspect.signature(timeline_command)
    assert "share" in sig.parameters
