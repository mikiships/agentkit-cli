"""Tests for integration hooks (D4 — ≥8 tests)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.history import HistoryDB

runner = CliRunner()


def _make_result(**kwargs):
    from datetime import datetime, timezone
    from agentkit_cli.commands.spotlight_cmd import SpotlightResult
    defaults = dict(
        repo="acme/cool-agent",
        score=82.5,
        grade="B",
        top_findings=["[agentlint] Missing AGENTS.md"],
        run_date=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(kwargs)
    return SpotlightResult(**defaults)


class TestHistorySpotlightsFlag:
    def test_spotlights_flag_exists(self):
        result = runner.invoke(app, ["history", "--help"])
        assert "--spotlights" in result.output

    def test_spotlights_shows_empty_when_no_runs(self, tmp_path):
        db_file = tmp_path / "test_history.db"
        result = runner.invoke(app, ["history", "--spotlights", "--db", str(db_file)])
        assert result.exit_code == 0
        assert "No spotlight runs" in result.output

    def test_spotlights_json_output(self, tmp_path):
        db_file = tmp_path / "test_history.db"
        # Insert a spotlight run
        db = HistoryDB(db_file)
        db.record_run(
            project="spotlight:acme/cool-agent",
            tool="spotlight",
            score=82.5,
            details={"grade": "B", "share_url": None},
            label="spotlight",
        )
        result = runner.invoke(app, ["history", "--spotlights", "--json", "--db", str(db_file)])
        assert result.exit_code == 0
        rows = json.loads(result.output)
        assert isinstance(rows, list)
        assert len(rows) >= 1
        assert rows[0]["project"] == "spotlight:acme/cool-agent"

    def test_spotlights_table_shows_repo(self, tmp_path):
        db_file = tmp_path / "test_history.db"
        db = HistoryDB(db_file)
        db.record_run(
            project="spotlight:acme/cool-agent",
            tool="spotlight",
            score=82.5,
            details={"grade": "B", "share_url": None},
            label="spotlight",
        )
        result = runner.invoke(app, ["history", "--spotlights", "--db", str(db_file)])
        assert result.exit_code == 0
        assert "acme/cool-agent" in result.output


class TestReportSpotlightFeed:
    def test_spotlight_feed_flag_exists(self):
        result = runner.invoke(app, ["report", "--help"])
        assert "--spotlight-feed" in result.output

    def test_spotlight_feed_empty_db(self, tmp_path):
        db_file = tmp_path / "test_history.db"
        result = runner.invoke(app, ["report", "--spotlight-feed", "--db", str(db_file)])
        assert result.exit_code == 0
        assert "No spotlight runs" in result.output

    def test_spotlight_feed_shows_repos(self, tmp_path):
        db_file = tmp_path / "test_history.db"
        db = HistoryDB(db_file)
        for i in range(3):
            db.record_run(
                project=f"spotlight:owner/repo{i}",
                tool="spotlight",
                score=70.0 + i,
                details={"grade": "C", "share_url": None},
                label="spotlight",
            )
        result = runner.invoke(app, ["report", "--spotlight-feed", "--db", str(db_file)])
        assert result.exit_code == 0
        assert "repo0" in result.output or "repo1" in result.output or "repo2" in result.output

    def test_spotlight_feed_json(self, tmp_path):
        db_file = tmp_path / "test_history.db"
        db = HistoryDB(db_file)
        db.record_run(
            project="spotlight:test/repo",
            tool="spotlight",
            score=75.0,
            details={"grade": "C", "share_url": None},
            label="spotlight",
        )
        result = runner.invoke(app, ["report", "--spotlight-feed", "--json", "--db", str(db_file)])
        assert result.exit_code == 0
        rows = json.loads(result.output)
        assert isinstance(rows, list)
        assert any(r["repo"] == "test/repo" for r in rows)


class TestSpotlightHistoryRecord:
    def test_run_spotlight_records_to_db(self, tmp_path):
        import json as _json
        db_file = tmp_path / "test.db"
        db = HistoryDB(db_file)

        with patch("agentkit_cli.analyze.analyze_target") as mock_analyze:
            mock_result = MagicMock()
            mock_result.composite_score = 80.0
            mock_result.tools = {}
            mock_analyze.return_value = mock_result

            # Patch urlopen to return fake GitHub repo metadata
            fake_resp_data = _json.dumps({"description": "test", "stargazers_count": 500, "language": "Python"}).encode()

            class FakeResp:
                def read(self):
                    return fake_resp_data
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    return False

            with patch("urllib.request.urlopen", return_value=FakeResp()):
                from agentkit_cli.commands.spotlight_cmd import SpotlightEngine
                engine = SpotlightEngine(db=db)
                result = engine.run_spotlight("acme/cool-agent")

        # Check DB was written
        rows = db.get_history(project="spotlight:acme/cool-agent", tool="spotlight", limit=5)
        assert len(rows) >= 1
        assert rows[0]["label"] == "spotlight"
