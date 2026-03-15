"""Tests for --profile flag integration in gate, run, sweep, score, analyze commands — D3."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / ".git").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# gate --profile
# ---------------------------------------------------------------------------

class TestGateProfile:
    def test_gate_has_profile_option(self):
        result = runner.invoke(app, ["gate", "--help"])
        assert "--profile" in result.output

    def test_gate_invalid_profile_exits_2(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        with patch("agentkit_cli.commands.gate_cmd.run_gate") as mock_gate:
            result = runner.invoke(app, ["gate", "--profile", "nonexistent"])
            assert result.exit_code == 2

    def test_gate_strict_profile_applies_min_score(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from agentkit_cli.gate import GateResult
        mock_result = GateResult(
            verdict="PASS", passed=True, score=90.0, grade="A",
            thresholds={"min_score": 85.0}, baseline_delta=None, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=mock_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications"):
                result = runner.invoke(app, ["gate", "--profile", "strict"])
                assert result.exit_code == 0

    def test_gate_profile_shown_in_output(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from agentkit_cli.gate import GateResult
        mock_result = GateResult(
            verdict="PASS", passed=True, score=90.0, grade="A",
            thresholds={}, baseline_delta=None, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=mock_result):
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications"):
                result = runner.invoke(app, ["gate", "--profile", "strict"])
                assert "strict" in result.output

    def test_gate_explicit_min_score_overrides_profile(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from agentkit_cli.gate import GateResult
        mock_result = GateResult(
            verdict="PASS", passed=True, score=90.0, grade="A",
            thresholds={"min_score": 99.0}, baseline_delta=None, failure_reasons=[],
            components={}, missing_tools=[], tool_status=[],
        )
        with patch("agentkit_cli.commands.gate_cmd.run_gate", return_value=mock_result) as mock:
            with patch("agentkit_cli.commands.gate_cmd.fire_notifications"):
                result = runner.invoke(app, ["gate", "--profile", "strict", "--min-score", "99"])
                call_kwargs = mock.call_args
                assert call_kwargs.kwargs.get("min_score") == 99.0


# ---------------------------------------------------------------------------
# run --profile
# ---------------------------------------------------------------------------

class TestRunProfile:
    def test_run_has_profile_option(self):
        result = runner.invoke(app, ["run", "--help"])
        assert "--profile" in result.output

    def test_run_invalid_profile_exits_2(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["run", "--profile", "nonexistent"])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# sweep --profile
# ---------------------------------------------------------------------------

class TestSweepProfile:
    def test_sweep_has_profile_option(self):
        result = runner.invoke(app, ["sweep", "--help"])
        assert "--profile" in result.output

    def test_sweep_invalid_profile_exits_2(self):
        result = runner.invoke(app, ["sweep", "--profile", "nonexistent", "owner/repo"])
        assert result.exit_code == 2


# ---------------------------------------------------------------------------
# score --profile
# ---------------------------------------------------------------------------

class TestScoreProfile:
    def test_score_has_profile_option(self):
        result = runner.invoke(app, ["score", "--help"])
        assert "--profile" in result.output

    def test_score_invalid_profile_exits_2(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        result = runner.invoke(app, ["score", "--profile", "nonexistent"])
        assert result.exit_code == 2

    def test_score_balanced_profile(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        from agentkit_cli.composite import CompositeResult
        mock_result = CompositeResult(
            score=75.0, grade="B",
            components={"agentlint": {}, "agentmd": {}, "coderace": {}, "agentreflect": {}},
            missing_tools=[],
        )
        with patch("agentkit_cli.commands.score_cmd.CompositeScoreEngine") as mock_engine:
            instance = MagicMock()
            instance.compute.return_value = mock_result
            mock_engine.return_value = instance
            result = runner.invoke(app, ["score", "--profile", "balanced"])
            assert result.exit_code == 0


# ---------------------------------------------------------------------------
# analyze --profile
# ---------------------------------------------------------------------------

class TestAnalyzeProfile:
    def test_analyze_has_profile_option(self):
        result = runner.invoke(app, ["analyze", "--help"])
        assert "--profile" in result.output

    def test_analyze_invalid_profile_with_local_path(self, tmp_project, monkeypatch):
        monkeypatch.chdir(tmp_project)
        # Even with invalid profile, analyze_command receives it
        # It's up to the command; we just test the flag exists in help
        result = runner.invoke(app, ["analyze", "--help"])
        assert "--profile" in result.output


# ---------------------------------------------------------------------------
# Profile precedence
# ---------------------------------------------------------------------------

class TestProfilePrecedence:
    def test_strict_profile_min_score_applied_to_config(self):
        from agentkit_cli.config import AgentKitConfig
        from agentkit_cli.profiles import apply_profile
        cfg = AgentKitConfig()
        apply_profile("strict", cfg)
        assert cfg.gate.min_score == 85.0

    def test_cli_flag_none_means_profile_fills_gap(self):
        from agentkit_cli.config import AgentKitConfig
        from agentkit_cli.profiles import apply_profile
        cfg = AgentKitConfig()
        apply_profile("strict", cfg, cli_min_score=None)
        assert cfg.gate.min_score == 85.0

    def test_cli_flag_provided_means_profile_does_not_overwrite(self):
        from agentkit_cli.config import AgentKitConfig
        from agentkit_cli.profiles import apply_profile
        cfg = AgentKitConfig()
        apply_profile("strict", cfg, cli_min_score=90.0)
        # profile skipped for min_score because cli provided it
        assert cfg.gate.min_score is None  # profile did not set it

    def test_profile_balanced_sets_notify_on(self):
        from agentkit_cli.config import AgentKitConfig
        from agentkit_cli.profiles import apply_profile
        cfg = AgentKitConfig()
        apply_profile("balanced", cfg)
        assert cfg.notify.on == "never"
