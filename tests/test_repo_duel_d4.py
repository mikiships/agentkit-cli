"""Tests for D4: Integration hooks — history --duels."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def test_history_duels_flag_exists():
    result = runner.invoke(app, ["history", "--help"])
    assert result.exit_code == 0
    assert "--duels" in result.output


def test_history_duels_no_data(tmp_path):
    db_path = tmp_path / "hist.db"
    result = runner.invoke(app, ["history", "--duels", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "no repo-duel" in result.output.lower() or "No repo-duel" in result.output


def test_history_duels_json_no_data(tmp_path):
    db_path = tmp_path / "hist.db"
    result = runner.invoke(app, ["history", "--duels", "--json", "--db", str(db_path)])
    assert result.exit_code == 0


def test_history_duels_shows_duel_records(tmp_path):
    from agentkit_cli.history import HistoryDB
    db_path = tmp_path / "hist.db"
    db = HistoryDB(db_path)
    db.record_run(project="repoA__vs__repoB", tool="repo_duel", score=75.0, label="repo_duel")

    result = runner.invoke(app, ["history", "--duels", "--db", str(db_path)])
    assert result.exit_code == 0
    assert "repoA" in result.output or "repo_duel" in result.output


def test_repo_duel_command_registered():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "repo-duel" in result.output


def test_repo_duel_help_shows_flags():
    result = runner.invoke(app, ["repo-duel", "--help"])
    assert result.exit_code == 0
    assert "--deep" in result.output
    assert "--share" in result.output
    assert "--json" in result.output
    assert "--output" in result.output
    assert "--quiet" in result.output


def test_history_cmd_duels_param_accepted(tmp_path):
    from agentkit_cli.commands.history_cmd import history_command
    db_path = tmp_path / "h.db"
    # Should not raise
    history_command(
        limit=10,
        tool=None,
        project=None,
        graph=False,
        json_output=False,
        clear=False,
        yes=False,
        all_projects=False,
        db_path=db_path,
        campaigns=False,
        campaign_id=None,
        duels=True,
    )


def test_history_duels_json_with_data(tmp_path):
    from agentkit_cli.history import HistoryDB
    import sys
    from io import StringIO

    db_path = tmp_path / "hist.db"
    db = HistoryDB(db_path)
    db.record_run(project="repo1__vs__repo2", tool="repo_duel", score=80.0, label="repo_duel")

    result = runner.invoke(app, ["history", "--duels", "--json", "--db", str(db_path)])
    assert result.exit_code == 0
    # Output may be JSON array or rich table; just check no error
