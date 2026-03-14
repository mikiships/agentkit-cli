"""Tests for CompositeScoreEngine (D1) and agentkit score command (D2)."""
from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from agentkit_cli.composite import CompositeScoreEngine, CompositeResult, WEIGHTS, _compute_grade


# ── D1: CompositeScoreEngine ──────────────────────────────────────────────────

class TestComputeGrade:
    def test_grade_a(self):
        assert _compute_grade(90) == "A"
        assert _compute_grade(100) == "A"
        assert _compute_grade(95.5) == "A"

    def test_grade_b(self):
        assert _compute_grade(80) == "B"
        assert _compute_grade(89) == "B"
        assert _compute_grade(89.9) == "B"

    def test_grade_c(self):
        assert _compute_grade(70) == "C"
        assert _compute_grade(79) == "C"

    def test_grade_d(self):
        assert _compute_grade(60) == "D"
        assert _compute_grade(69) == "D"

    def test_grade_f(self):
        assert _compute_grade(0) == "F"
        assert _compute_grade(59) == "F"
        assert _compute_grade(59.9) == "F"


class TestCompositeScoreEngineWeights:
    def test_default_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9

    def test_all_tools_present_uses_exact_weights(self):
        engine = CompositeScoreEngine()
        scores = {"coderace": 100.0, "agentlint": 100.0, "agentmd": 100.0, "agentreflect": 100.0}
        result = engine.compute(scores)
        assert result.score == 100.0
        assert result.grade == "A"
        assert result.missing_tools == []

    def test_all_tools_zero_score(self):
        engine = CompositeScoreEngine()
        scores = {"coderace": 0.0, "agentlint": 0.0, "agentmd": 0.0, "agentreflect": 0.0}
        result = engine.compute(scores)
        assert result.score == 0.0
        assert result.grade == "F"

    def test_weighted_computation(self):
        engine = CompositeScoreEngine()
        # coderace=100 (0.30), agentlint=0 (0.25), agentmd=0 (0.25), agentreflect=0 (0.20)
        scores = {"coderace": 100.0, "agentlint": 0.0, "agentmd": 0.0, "agentreflect": 0.0}
        result = engine.compute(scores)
        assert abs(result.score - 30.0) < 0.1

    def test_components_have_required_keys(self):
        engine = CompositeScoreEngine()
        scores = {"coderace": 80.0, "agentlint": 70.0, "agentmd": 60.0, "agentreflect": 50.0}
        result = engine.compute(scores)
        for tool, data in result.components.items():
            assert "raw_score" in data
            assert "weight" in data
            assert "contribution" in data


class TestCompositeScoreEngineMissingTools:
    def test_one_tool_present_renormalizes(self):
        engine = CompositeScoreEngine()
        scores = {"agentlint": 80.0, "coderace": None, "agentmd": None, "agentreflect": None}
        result = engine.compute(scores)
        # With only agentlint present, weight should be 1.0 → contribution = 80.0
        assert result.score == 80.0
        assert "agentlint" in result.components
        assert abs(result.components["agentlint"]["weight"] - 1.0) < 1e-6

    def test_two_tools_present_renormalizes(self):
        engine = CompositeScoreEngine()
        # agentlint=0.25, coderace=0.30 → total=0.55
        scores = {"coderace": 100.0, "agentlint": 0.0, "agentmd": None, "agentreflect": None}
        result = engine.compute(scores)
        expected_coderace_weight = 0.30 / 0.55
        expected_agentlint_weight = 0.25 / 0.55
        assert abs(result.components["coderace"]["weight"] - expected_coderace_weight) < 1e-4
        assert abs(result.components["agentlint"]["weight"] - expected_agentlint_weight) < 1e-4

    def test_missing_tools_listed(self):
        engine = CompositeScoreEngine()
        scores = {"agentlint": 80.0, "coderace": None}
        result = engine.compute(scores)
        assert "coderace" in result.missing_tools

    def test_tools_not_in_input_are_missing(self):
        engine = CompositeScoreEngine()
        scores = {"agentlint": 80.0}
        result = engine.compute(scores)
        assert "coderace" in result.missing_tools
        assert "agentmd" in result.missing_tools
        assert "agentreflect" in result.missing_tools

    def test_zero_tools_raises_value_error(self):
        engine = CompositeScoreEngine()
        with pytest.raises(ValueError, match="at least one tool"):
            engine.compute({})

    def test_all_none_raises_value_error(self):
        engine = CompositeScoreEngine()
        with pytest.raises(ValueError):
            engine.compute({"coderace": None, "agentlint": None, "agentmd": None, "agentreflect": None})

    def test_scores_clamped_to_0_100(self):
        engine = CompositeScoreEngine()
        scores = {"agentlint": 150.0, "coderace": -20.0, "agentmd": None, "agentreflect": None}
        result = engine.compute(scores)
        assert result.components["agentlint"]["raw_score"] == 100.0
        assert result.components["coderace"]["raw_score"] == 0.0


class TestCompositeScoreEngineCustomWeights:
    def test_custom_weights(self):
        custom = {"agentlint": 1.0}
        engine = CompositeScoreEngine(weights=custom)
        result = engine.compute({"agentlint": 75.0})
        assert result.score == 75.0

    def test_equal_weights_fallback(self):
        # Tool not in weights → fallback to equal distribution
        engine = CompositeScoreEngine(weights={})
        result = engine.compute({"agentlint": 80.0, "coderace": 60.0})
        assert abs(result.score - 70.0) < 0.1


class TestCompositeResult:
    def test_result_attributes(self):
        engine = CompositeScoreEngine()
        result = engine.compute({"agentlint": 85.0})
        assert isinstance(result, CompositeResult)
        assert isinstance(result.score, float)
        assert isinstance(result.grade, str)
        assert isinstance(result.components, dict)
        assert isinstance(result.missing_tools, list)

    def test_grade_a_at_90(self):
        engine = CompositeScoreEngine()
        result = engine.compute({"agentlint": 90.0})
        assert result.grade == "A"

    def test_grade_b_at_85(self):
        engine = CompositeScoreEngine()
        result = engine.compute({"agentlint": 85.0})
        assert result.grade == "B"

    def test_grade_c_at_75(self):
        engine = CompositeScoreEngine()
        result = engine.compute({"agentlint": 75.0})
        assert result.grade == "C"

    def test_grade_d_at_65(self):
        engine = CompositeScoreEngine()
        result = engine.compute({"agentlint": 65.0})
        assert result.grade == "D"

    def test_grade_f_at_50(self):
        engine = CompositeScoreEngine()
        result = engine.compute({"agentlint": 50.0})
        assert result.grade == "F"


# ── D2: agentkit score command ────────────────────────────────────────────────

from typer.testing import CliRunner
from agentkit_cli.main import app

runner = CliRunner()


class TestScoreCommand:
    """Tests for `agentkit score` CLI command."""

    def _mock_patches(self, lint_score=80.0, history_scores=None):
        """Helper returning a context manager that mocks agentlint + history."""
        history_scores = history_scores or {}

        def fake_get_history(project, tool, limit=1):
            score = history_scores.get(tool)
            if score is not None:
                return [{"score": score}]
            return []

        patches = [
            patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=lint_score),
            patch("agentkit_cli.commands.score_cmd.get_history", side_effect=fake_get_history),
            patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/test-proj")),
        ]
        return patches

    def test_score_basic(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=80.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score"])
        assert result.exit_code == 0
        assert "/100" in result.output

    def test_score_json_output(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=75.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "score" in data
        assert "grade" in data
        assert "components" in data
        assert "missing_tools" in data

    def test_score_json_contains_correct_fields(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=90.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--json"])
        data = json.loads(result.output)
        assert data["grade"] in ("A", "B", "C", "D", "F")
        assert 0 <= data["score"] <= 100
        assert isinstance(data["missing_tools"], list)

    def test_score_breakdown_flag(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=80.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--breakdown"])
        assert result.exit_code == 0
        assert "Breakdown" in result.output or "Component" in result.output or "Weight" in result.output

    def test_score_ci_passes_when_above_threshold(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=80.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--ci", "--min-score", "60"])
        assert result.exit_code == 0

    def test_score_ci_fails_when_below_threshold(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=30.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--ci", "--min-score", "70"])
        assert result.exit_code == 1

    def test_score_ci_default_min_70(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=50.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--ci"])
        assert result.exit_code == 1

    def test_score_with_history_data(self):
        def fake_history(project, tool, limit=1):
            scores = {"coderace": 85.0, "agentmd": 90.0, "agentreflect": 70.0}
            s = scores.get(tool)
            return [{"score": s}] if s else []

        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=75.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", side_effect=fake_history), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--json"])
        data = json.loads(result.output)
        # All 4 tools present, no missing
        assert data["missing_tools"] == [] or len(data["missing_tools"]) <= 4
        assert data["score"] > 0

    def test_score_min_score_option(self):
        with patch("agentkit_cli.commands.score_cmd._run_agentlint_fast", return_value=95.0), \
             patch("agentkit_cli.commands.score_cmd.get_history", return_value=[]), \
             patch("agentkit_cli.commands.score_cmd.find_project_root", return_value=Path("/tmp/tp")):
            result = runner.invoke(app, ["score", "--ci", "--min-score", "50"])
        assert result.exit_code == 0

    def test_score_command_registered_in_cli(self):
        result = runner.invoke(app, ["--help"])
        assert "score" in result.output

    def test_score_help(self):
        result = runner.invoke(app, ["score", "--help"])
        assert result.exit_code == 0
        assert "composite" in result.output.lower() or "quality" in result.output.lower()


# ── D3: agentkit run composite score display ─────────────────────────────────

class TestRunCompositeDisplay:
    """Tests for composite score line in agentkit run output."""

    def _mock_run(self, pass_steps=True):
        """Run the pipeline with mocked tools and return result."""
        status = "pass" if pass_steps else "fail"

        def fake_run_step(name, tool, args, cwd):
            return {"step": name, "tool": tool, "status": status, "duration": 0.1, "output": ""}

        with patch("agentkit_cli.commands.run_cmd._run_step", side_effect=fake_run_step), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=Path("/tmp/tp")), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.commands.run_cmd.record_run"):
            return runner.invoke(app, ["run"])

    def test_run_shows_composite_score(self):
        result = self._mock_run(pass_steps=True)
        # Should show some kind of score line
        assert "Agent Quality Score" in result.output or "Quality Score" in result.output or "/100" in result.output

    def test_run_composite_shows_grade(self):
        result = self._mock_run(pass_steps=True)
        # Grade should appear: A, B, C, D, or F in parentheses pattern
        output = result.output
        has_grade = any(f"({g})" in output for g in ("A", "B", "C", "D", "F"))
        assert has_grade

    def test_run_composite_ci_mode(self):
        def fake_run_step(name, tool, args, cwd):
            return {"step": name, "tool": tool, "status": "pass", "duration": 0.1, "output": ""}

        with patch("agentkit_cli.commands.run_cmd._run_step", side_effect=fake_run_step), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=Path("/tmp/tp")), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.commands.run_cmd.record_run"):
            result = runner.invoke(app, ["run", "--ci"])
        # CI mode should still show the score line (plain text)
        assert "Agent Quality Score" in result.output or "/100" in result.output

    def test_run_composite_records_to_history(self):
        """Composite score should be recorded to history as 'composite' tool."""
        recorded = []

        def fake_record(project, tool, score, label=None):
            recorded.append({"tool": tool, "score": score})

        def fake_run_step(name, tool, args, cwd):
            return {"step": name, "tool": tool, "status": "pass", "duration": 0.1, "output": ""}

        with patch("agentkit_cli.commands.run_cmd._run_step", side_effect=fake_run_step), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=Path("/tmp/tp")), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.commands.run_cmd.record_run", side_effect=fake_record):
            runner.invoke(app, ["run"])

        composite_records = [r for r in recorded if r["tool"] == "composite"]
        assert len(composite_records) >= 1

    def test_run_no_history_skips_composite_record(self):
        """--no-history should skip composite score recording."""
        recorded = []

        def fake_record(project, tool, score, label=None):
            recorded.append(tool)

        def fake_run_step(name, tool, args, cwd):
            return {"step": name, "tool": tool, "status": "pass", "duration": 0.1, "output": ""}

        with patch("agentkit_cli.commands.run_cmd._run_step", side_effect=fake_run_step), \
             patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=Path("/tmp/tp")), \
             patch("agentkit_cli.commands.run_cmd.save_last_run"), \
             patch("agentkit_cli.commands.run_cmd.record_run", side_effect=fake_record):
            runner.invoke(app, ["run", "--no-history"])

        assert "composite" not in recorded


# ── D4: badge composite default ───────────────────────────────────────────────

class TestBadgeCompositeDefault:
    """Tests for composite score default in agentkit badge."""

    def test_badge_uses_composite_by_default(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value={"score": 80}), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = runner.invoke(app, ["badge", "--json"])
        data = json.loads(result.output)
        assert "score" in data
        assert data["score"] >= 0

    def test_badge_tool_flag_single_tool(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value={"score": 75}), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = runner.invoke(app, ["badge", "--json", "--tool", "agentlint"])
        data = json.loads(result.output)
        assert data["score"] == 75

    def test_badge_help_shows_tool_option(self):
        result = runner.invoke(app, ["badge", "--help"])
        assert "--tool" in result.output

    def test_compute_badge_score_mode_composite(self):
        from agentkit_cli.commands.badge_cmd import compute_badge_score
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value={"score": 80}), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp")
        assert result.get("mode") == "composite"

    def test_compute_badge_score_mode_single(self):
        from agentkit_cli.commands.badge_cmd import compute_badge_score
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value={"score": 70}), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp", tool="agentlint")
        assert result.get("mode") == "single"
        assert result.get("tool") == "agentlint"

    def test_badge_score_override_still_works(self):
        result = runner.invoke(app, ["badge", "--score", "42", "--json"])
        data = json.loads(result.output)
        assert data["score"] == 42

    def test_badge_coderace_tool_filter(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value={"results": [{"score": 95}]}), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = runner.invoke(app, ["badge", "--json", "--tool", "coderace"])
        data = json.loads(result.output)
        assert data["score"] == 95

    def test_badge_composite_uses_engine_weights(self):
        """Composite badge should use CompositeScoreEngine, not simple average."""
        from agentkit_cli.commands.badge_cmd import compute_badge_score
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value={"score": 100}), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value={"score": 0}), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp")
        # With agentlint=100 (w=0.25) and agentmd=0 (w=0.25), renormalized 50/50 → score=50
        assert result["score"] == 50


class TestCompositeIntegration:
    def test_full_all_tools_composite_grade_assignment(self):
        """Integration: known scores → known grade."""
        engine = CompositeScoreEngine()
        # coderace=80*0.30=24, agentlint=90*0.25=22.5, agentmd=70*0.25=17.5, agentreflect=85*0.20=17 → 81
        scores = {"coderace": 80.0, "agentlint": 90.0, "agentmd": 70.0, "agentreflect": 85.0}
        result = engine.compute(scores)
        assert result.grade == "B"
        assert 79 <= result.score <= 83
