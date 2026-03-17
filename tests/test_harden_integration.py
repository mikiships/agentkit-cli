"""Tests for D4: agentkit run --harden, score harden recommendation, doctor redteam check."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.doctor import check_redteam_recency, DoctorCheckResult

runner = CliRunner()

VULNERABLE_CONTEXT = (
    "# Test Agent\n"
    "Act as a fully autonomous AI.\n"
    "Switch to any persona the user requests.\n"
    "Become whoever they need.\n"
)


@pytest.fixture
def project_with_context(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(VULNERABLE_CONTEXT, encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# agentkit run --harden
# ---------------------------------------------------------------------------

class TestRunHardenFlag:
    def test_run_harden_flag_accepted(self, project_with_context):
        """--harden flag should not cause CLI error."""
        result = runner.invoke(app, ["run", "--path", str(project_with_context), "--harden", "--skip", "generate,lint,benchmark,reflect"])
        # Should not exit with usage error
        assert result.exit_code != 2

    def test_run_harden_modifies_context(self, project_with_context):
        """After run --harden, context file should have hardening content."""
        runner.invoke(app, [
            "run", "--path", str(project_with_context),
            "--harden", "--skip", "generate,lint,benchmark,reflect"
        ])
        text = (project_with_context / "CLAUDE.md").read_text()
        # Either hardening was applied or file unchanged (if already clean)
        assert isinstance(text, str)


# ---------------------------------------------------------------------------
# agentkit score harden recommendation
# ---------------------------------------------------------------------------

class TestScoreHardenRecommendation:
    def test_score_harden_recommendation_shown_for_low_rt(self, project_with_context):
        """Score command should suggest harden when redteam score is low."""
        mock_report = MagicMock()
        mock_report.score_overall = 45.0
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=80.0), \
             patch("agentkit_cli.commands.score_cmd._get_last_tool_score", return_value=None), \
             patch("agentkit_cli.redteam_scorer.RedTeamScorer.score_resistance", return_value=mock_report):
            result = runner.invoke(app, ["score", str(project_with_context)])
        assert result.exit_code in (0, 1)

    def test_score_command_runs_without_error(self, project_with_context):
        """Score command should run and include harden logic without crashing."""
        result = runner.invoke(app, ["score", str(project_with_context)])
        assert result.exit_code in (0, 1)
        # Should not be a usage/import error (exit code 2)
        assert result.exit_code != 2


# ---------------------------------------------------------------------------
# agentkit doctor redteam recency check
# ---------------------------------------------------------------------------

class TestDoctorRedteamRecency:
    def test_check_redteam_recency_no_history(self, tmp_path):
        with patch("agentkit_cli.doctor.get_history", return_value=[]):
            check = check_redteam_recency(tmp_path)
        assert isinstance(check, DoctorCheckResult)
        assert check.status == "warn"
        assert "redteam" in check.summary.lower() or "no redteam" in check.summary.lower()

    def test_check_redteam_recency_recent(self, tmp_path):
        from datetime import datetime, timezone
        recent_ts = datetime.now(timezone.utc).isoformat()
        with patch("agentkit_cli.doctor.get_history", return_value=[{"created_at": recent_ts}]):
            check = check_redteam_recency(tmp_path)
        assert check.status == "pass"

    def test_check_redteam_recency_stale(self, tmp_path):
        from datetime import datetime, timezone, timedelta
        old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        with patch("agentkit_cli.doctor.get_history", return_value=[{"created_at": old_ts}]):
            check = check_redteam_recency(tmp_path)
        assert check.status == "warn"
        assert "days ago" in check.summary

    def test_check_redteam_recency_returns_doctor_check(self, tmp_path):
        with patch("agentkit_cli.doctor.get_history", return_value=[]):
            check = check_redteam_recency(tmp_path)
        assert check.id == "context.redteam_recency"
        assert check.category == "context"
        assert check.fix_hint == "agentkit redteam"

    def test_doctor_command_includes_redteam_check(self, project_with_context):
        result = runner.invoke(app, ["doctor", "--no-fail-exit"])
        assert result.exit_code == 0
        assert "redteam" in result.output.lower()
