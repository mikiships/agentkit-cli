"""Integration tests for D4 — agentkit run --populate, doctor history check."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def _make_db(tmp_path, records=None):
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=tmp_path / "test.db")
    for rec in (records or []):
        db.record_run(*rec)
    return db


class TestDoctorHistoryDBCheck:
    def test_empty_db_returns_warn(self, tmp_path):
        from agentkit_cli.doctor import check_history_db_has_data
        with patch("agentkit_cli.doctor.HistoryDB") as MockDB:
            mock_instance = MagicMock()
            mock_instance.get_all_projects.return_value = []
            MockDB.return_value = mock_instance
            result = check_history_db_has_data()
        assert result.status == "warn"
        assert "populate" in result.fix_hint.lower() or "agentkit populate" in result.fix_hint

    def test_populated_db_returns_pass(self, tmp_path):
        from agentkit_cli.doctor import check_history_db_has_data
        with patch("agentkit_cli.doctor.HistoryDB") as MockDB:
            mock_instance = MagicMock()
            mock_instance.get_all_projects.return_value = ["owner/repo1", "owner/repo2"]
            MockDB.return_value = mock_instance
            result = check_history_db_has_data()
        assert result.status == "pass"
        assert "2" in result.summary

    def test_history_check_in_doctor_report(self, tmp_path):
        """check_history_db_has_data is included in run_doctor output."""
        from agentkit_cli.doctor import run_doctor
        with patch("agentkit_cli.doctor.HistoryDB") as MockDB:
            mock_instance = MagicMock()
            mock_instance.get_all_projects.return_value = ["owner/repo"]
            MockDB.return_value = mock_instance
            report = run_doctor(root=tmp_path)
        ids = [c.id for c in report.checks]
        assert "history.data" in ids

    def test_db_error_returns_warn(self):
        from agentkit_cli.doctor import check_history_db_has_data
        with patch("agentkit_cli.doctor.HistoryDB") as MockDB:
            MockDB.side_effect = RuntimeError("DB error")
            result = check_history_db_has_data()
        assert result.status == "warn"


class TestRunCommandPopulateFlag:
    def test_run_command_accepts_populate_flag(self, tmp_path):
        """run_command --populate=False should work without errors (smoke test)."""
        from agentkit_cli.commands.run_cmd import run_command
        # Just verify the signature accepts populate without error
        import inspect
        sig = inspect.signature(run_command)
        assert "populate" in sig.parameters

    def test_populate_flag_triggers_populate_engine(self, tmp_path):
        """When --populate is passed via CLI, PopulateEngine.populate is called."""
        from typer.testing import CliRunner
        from agentkit_cli.main import app

        with patch("agentkit_cli.commands.run_cmd.PopulateEngine") as MockEngine:
            mock_engine = MagicMock()
            mock_result = MagicMock()
            mock_result.total_scored = 5
            mock_result.to_dict.return_value = {"total_scored": 5}
            mock_engine.populate.return_value = mock_result
            MockEngine.return_value = mock_engine

            runner = CliRunner()
            runner.invoke(app, ["run", "--path", str(tmp_path), "--populate", "--json", "--no-history"])

            assert mock_engine.populate.called


class TestPopulateCommandIntegration:
    def test_populate_command_dry_run_json(self, tmp_path, capsys):
        from agentkit_cli.commands.populate_cmd import populate_command
        from agentkit_cli.populate_engine import PopulateEngine
        engine = PopulateEngine(
            db_path=tmp_path / "db.db",
            _analyze_fn=lambda r: 70.0,
            _search_fn=lambda t, l, la, to: [{"full_name": f"owner/{t}-0"}],
        )
        populate_command(
            topics="python",
            limit=1,
            dry_run=True,
            json_output=True,
            quiet=True,
            _engine=engine,
        )
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["dry_run"] is True
