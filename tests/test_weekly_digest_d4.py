"""D4 tests: README section and integration — ≥5 tests."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()
REPO_ROOT = Path(__file__).parent.parent


class TestReadmeSection:
    def test_readme_has_weekly_digest_section(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "## Weekly Digest" in readme

    def test_readme_has_example_usage(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "agentkit weekly-digest" in readme

    def test_readme_has_share_flag(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "--share" in readme

    def test_readme_has_since_flag(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "--since" in readme


class TestJsonIntegration:
    def test_json_output_valid(self, tmp_path):
        from agentkit_cli.history import HistoryDB
        db_path = tmp_path / "test.db"
        HistoryDB(db_path=db_path)
        result = runner.invoke(app, ["weekly-digest", "--json", "--db", str(db_path)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "top_repos" in data
        assert "week_stats" in data
        assert "generated_at" in data

    def test_cron_with_mock_share(self, tmp_path):
        from agentkit_cli.history import HistoryDB
        db_path = tmp_path / "test.db"
        HistoryDB(db_path=db_path)
        with patch("agentkit_cli.commands.weekly_digest_cmd._share_html", return_value="https://here.now/xyz"):
            result = runner.invoke(app, ["weekly-digest", "--cron", "--db", str(db_path)])
        assert result.exit_code == 0
        assert "https://here.now/xyz" in result.output

    def test_since_30_uses_30_day_window(self, tmp_path):
        """Test that --since 30 passes 30 to engine."""
        from agentkit_cli.history import HistoryDB
        from agentkit_cli.weekly_digest_engine import WeeklyDigestEngine
        db_path = tmp_path / "test.db"
        HistoryDB(db_path=db_path)
        with patch.object(WeeklyDigestEngine, "generate", wraps=None) as mock_gen:
            mock_gen.return_value = __import__(
                "agentkit_cli.weekly_digest_engine", fromlist=["DigestReport"]
            ).DigestReport(
                top_repos=[],
                week_stats={"total_analyses": 0, "avg_score": 0.0, "top_scorer": ""},
                generated_at="2026-03-22T10:00:00+00:00",
            )
            result = runner.invoke(app, ["weekly-digest", "--since", "30", "--db", str(db_path)])
        assert result.exit_code == 0
        mock_gen.assert_called_once_with(since_days=30)
