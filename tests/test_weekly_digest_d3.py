"""D3 tests: weekly-digest CLI command — ≥10 tests."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app


runner = CliRunner()


def _make_db(tmp_path: Path) -> Path:
    from agentkit_cli.history import HistoryDB
    db_path = tmp_path / "test.db"
    HistoryDB(db_path=db_path)
    return db_path


class TestWeeklyDigestCmd:
    def test_help(self):
        result = runner.invoke(app, ["weekly-digest", "--help"])
        assert result.exit_code == 0
        assert "weekly" in result.output.lower() or "digest" in result.output.lower()

    def test_basic_runs(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = runner.invoke(app, ["weekly-digest", "--db", str(db_path)])
        assert result.exit_code == 0

    def test_json_output_is_valid(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = runner.invoke(app, ["weekly-digest", "--json", "--db", str(db_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "top_repos" in data
        assert "week_stats" in data
        assert "generated_at" in data

    def test_json_output_required_keys(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = runner.invoke(app, ["weekly-digest", "--json", "--db", str(db_path)])
        data = json.loads(result.output)
        stats = data["week_stats"]
        assert "total_analyses" in stats
        assert "avg_score" in stats
        assert "top_scorer" in stats

    def test_output_file(self, tmp_path):
        db_path = _make_db(tmp_path)
        out_file = tmp_path / "digest.html"
        result = runner.invoke(app, ["weekly-digest", "--output", str(out_file), "--db", str(db_path)])
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert "State of AI Agent Readiness" in content

    def test_quiet_suppresses_rich(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = runner.invoke(app, ["weekly-digest", "--quiet", "--db", str(db_path)])
        assert result.exit_code == 0
        # quiet suppresses table output
        assert "Analyses" not in result.output

    def test_since_param_accepted(self, tmp_path):
        db_path = _make_db(tmp_path)
        result = runner.invoke(app, ["weekly-digest", "--since", "30", "--db", str(db_path)])
        assert result.exit_code == 0

    def test_share_calls_upload(self, tmp_path):
        db_path = _make_db(tmp_path)
        with patch("agentkit_cli.commands.weekly_digest_cmd._share_html", return_value="https://here.now/test") as mock_share:
            result = runner.invoke(app, ["weekly-digest", "--share", "--db", str(db_path)])
        assert result.exit_code == 0
        mock_share.assert_called_once()
        assert "https://here.now/test" in result.output

    def test_cron_mode_enables_share(self, tmp_path):
        db_path = _make_db(tmp_path)
        with patch("agentkit_cli.commands.weekly_digest_cmd._share_html", return_value="https://here.now/cron") as mock_share:
            result = runner.invoke(app, ["weekly-digest", "--cron", "--db", str(db_path)])
        assert result.exit_code == 0
        mock_share.assert_called_once()
        assert "https://here.now/cron" in result.output

    def test_cron_mode_quiet(self, tmp_path):
        db_path = _make_db(tmp_path)
        with patch("agentkit_cli.commands.weekly_digest_cmd._share_html", return_value="https://here.now/cron"):
            result = runner.invoke(app, ["weekly-digest", "--cron", "--db", str(db_path)])
        assert result.exit_code == 0
        # Cron mode should not have rich table output
        assert "Top Repositories" not in result.output

    def test_share_failure_exits_nonzero(self, tmp_path):
        db_path = _make_db(tmp_path)
        with patch("agentkit_cli.commands.weekly_digest_cmd._share_html", return_value=None):
            result = runner.invoke(app, ["weekly-digest", "--share", "--db", str(db_path)])
        assert result.exit_code != 0
