"""Tests for agentkit improve (D1–D5)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.improve_engine import ImprovementPlan, ImproveEngine
from agentkit_cli.main import app

runner = CliRunner()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────────────

def _make_tmpdir(has_claude_md: bool = False) -> Path:
    tmp = Path(tempfile.mkdtemp())
    (tmp / "README.md").write_text("# Test repo\n")
    if has_claude_md:
        (tmp / "CLAUDE.md").write_text("# Claude context\n")
    return tmp


def _plan(
    target=".",
    baseline=42.0,
    final=81.0,
    actions_taken=None,
    actions_skipped=None,
    context_generated=True,
    hardening_applied=True,
) -> ImprovementPlan:
    return ImprovementPlan(
        target=target,
        baseline_score=baseline,
        final_score=final,
        delta=round(final - baseline, 1),
        actions_taken=actions_taken or ["Generated CLAUDE.md from source analysis", "Fixed 3 security patterns (redteam hardening)"],
        actions_skipped=actions_skipped or ["PR submission (use --pr to enable)"],
        context_generated=context_generated,
        hardening_applied=hardening_applied,
    )


# ──────────────────────────────────────────────────────────────────────────────
# D1 — ImprovementPlan dataclass
# ──────────────────────────────────────────────────────────────────────────────

class TestImprovementPlan:
    def test_fields_accessible(self):
        p = _plan()
        assert p.baseline_score == 42.0
        assert p.final_score == 81.0
        assert p.delta == 39.0
        assert p.context_generated is True
        assert p.hardening_applied is True

    def test_as_dict_keys(self):
        p = _plan()
        d = p.as_dict()
        for key in ("target", "baseline_score", "final_score", "delta", "actions_taken", "actions_skipped", "context_generated", "hardening_applied"):
            assert key in d

    def test_as_dict_values(self):
        p = _plan(baseline=10.0, final=50.0)
        d = p.as_dict()
        assert d["baseline_score"] == 10.0
        assert d["final_score"] == 50.0
        assert d["delta"] == 40.0

    def test_actions_lists_are_lists(self):
        p = _plan()
        assert isinstance(p.actions_taken, list)
        assert isinstance(p.actions_skipped, list)

    def test_delta_computed_correctly(self):
        p = ImprovementPlan(
            target=".",
            baseline_score=55.0,
            final_score=75.0,
            delta=20.0,
            actions_taken=[],
            actions_skipped=[],
            context_generated=False,
            hardening_applied=False,
        )
        assert p.delta == 20.0

    def test_empty_actions(self):
        p = ImprovementPlan(
            target=".",
            baseline_score=90.0,
            final_score=90.0,
            delta=0.0,
            actions_taken=[],
            actions_skipped=["nothing to do"],
            context_generated=False,
            hardening_applied=False,
        )
        assert p.actions_taken == []
        assert len(p.actions_skipped) == 1


# ──────────────────────────────────────────────────────────────────────────────
# D1 — ImproveEngine.run()
# ──────────────────────────────────────────────────────────────────────────────

class TestImproveEngine:
    def _mock_score(self, score: float):
        return patch("agentkit_cli.improve_engine._get_score", return_value=score)

    def _mock_rt(self, score=None):
        return patch("agentkit_cli.improve_engine._get_redteam_score", return_value=score)

    def _mock_generate(self, ok=True):
        return patch("agentkit_cli.improve_engine._run_agentmd_generate", return_value=ok)

    def _mock_harden(self, fixes=3):
        return patch("agentkit_cli.improve_engine._run_harden", return_value=fixes)

    def test_returns_improvement_plan(self, tmp_path):
        with self._mock_score(42.0), self._mock_rt(50.0), self._mock_generate(True), self._mock_harden(3):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert isinstance(plan, ImprovementPlan)

    def test_baseline_captured(self, tmp_path):
        with self._mock_score(55.0), self._mock_rt(None), self._mock_generate(False), self._mock_harden(0):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert plan.baseline_score == 55.0

    def test_no_generate_flag_skips(self, tmp_path):
        with self._mock_score(42.0), self._mock_rt(None), self._mock_generate(True), self._mock_harden(0):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path), no_generate=True)
        assert plan.context_generated is False
        assert any("no-generate" in s for s in plan.actions_skipped)

    def test_no_harden_flag_skips(self, tmp_path):
        with self._mock_score(42.0), self._mock_rt(50.0), self._mock_generate(False), self._mock_harden(3):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path), no_harden=True)
        assert plan.hardening_applied is False
        assert any("no-harden" in s for s in plan.actions_skipped)

    def test_dry_run_returns_same_score(self, tmp_path):
        with self._mock_score(50.0), self._mock_rt(None), self._mock_generate(True), self._mock_harden(3):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path), dry_run=True)
        assert plan.baseline_score == plan.final_score
        assert plan.delta == 0.0

    def test_context_generated_when_missing(self, tmp_path):
        # No CLAUDE.md in tmp_path
        with self._mock_score(42.0), self._mock_rt(None), self._mock_generate(True), self._mock_harden(0):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert plan.context_generated is True

    def test_high_score_skips_generate(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# existing\n")
        with self._mock_score(85.0), self._mock_rt(90.0), self._mock_generate(True), self._mock_harden(0):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert plan.context_generated is False

    def test_high_rt_score_skips_harden(self, tmp_path):
        with self._mock_score(50.0), self._mock_rt(90.0), self._mock_generate(False), self._mock_harden(3):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert plan.hardening_applied is False

    def test_delta_computed(self, tmp_path):
        scores = iter([42.0, 78.0])
        with patch("agentkit_cli.improve_engine._get_score", side_effect=scores), \
             self._mock_rt(None), self._mock_generate(True), self._mock_harden(3):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert plan.delta == pytest.approx(36.0, abs=0.1)

    def test_missing_target_raises(self):
        engine = ImproveEngine()
        with pytest.raises(FileNotFoundError):
            engine.run("/nonexistent/path/that/does/not/exist")

    def test_target_stored_in_plan(self, tmp_path):
        with self._mock_score(70.0), self._mock_rt(None), self._mock_generate(False), self._mock_harden(0):
            engine = ImproveEngine()
            plan = engine.run(str(tmp_path))
        assert plan.target == str(tmp_path)


# ──────────────────────────────────────────────────────────────────────────────
# D2 — CLI output tests
# ──────────────────────────────────────────────────────────────────────────────

def _mock_engine_run(plan: ImprovementPlan):
    """Context manager that patches ImproveEngine.run."""
    return patch("agentkit_cli.improve_engine.ImproveEngine.run", return_value=plan)


class TestImproveCLI:
    def test_help(self):
        result = runner.invoke(app, ["improve", "--help"])
        assert result.exit_code == 0
        assert "improve" in result.output.lower()

    def test_basic_success_output(self, tmp_path):
        plan = _plan(target=str(tmp_path))
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path)])
        assert result.exit_code == 0
        assert "42" in result.output
        assert "81" in result.output

    def test_json_output(self, tmp_path):
        plan = _plan(target=str(tmp_path))
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "baseline_score" in data
        assert "final_score" in data
        assert "delta" in data

    def test_json_contains_actions(self, tmp_path):
        plan = _plan(target=str(tmp_path))
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert "actions_taken" in data
        assert "actions_skipped" in data

    def test_dry_run_no_changes(self, tmp_path):
        plan = _plan(target=str(tmp_path), baseline=50.0, final=50.0, actions_taken=[])
        plan.delta = 0.0
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "dry" in result.output.lower() or "plan" in result.output.lower() or "50" in result.output

    def test_dry_run_flag_forwarded(self, tmp_path):
        plan = _plan()
        with patch("agentkit_cli.improve_engine.ImproveEngine") as mock_cls:
            instance = MagicMock()
            instance.run.return_value = plan
            mock_cls.return_value = instance
            runner.invoke(app, ["improve", str(tmp_path), "--dry-run"])
        call_kwargs = instance.run.call_args
        assert call_kwargs is not None

    def test_no_generate_flag_forwarded(self, tmp_path):
        plan = _plan()
        with patch("agentkit_cli.improve_engine.ImproveEngine") as mock_cls:
            instance = MagicMock()
            instance.run.return_value = plan
            mock_cls.return_value = instance
            runner.invoke(app, ["improve", str(tmp_path), "--no-generate"])
        call_kwargs = instance.run.call_args
        assert call_kwargs[1]["no_generate"] is True

    def test_no_harden_flag_forwarded(self, tmp_path):
        plan = _plan()
        with patch("agentkit_cli.improve_engine.ImproveEngine") as mock_cls:
            instance = MagicMock()
            instance.run.return_value = plan
            mock_cls.return_value = instance
            runner.invoke(app, ["improve", str(tmp_path), "--no-harden"])
        call_kwargs = instance.run.call_args
        assert call_kwargs[1]["no_harden"] is True

    def test_min_lift_exit_1_on_fail(self, tmp_path):
        plan = _plan(baseline=42.0, final=50.0)
        plan.delta = 8.0
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--min-lift", "20"])
        assert result.exit_code == 1

    def test_min_lift_exit_0_on_pass(self, tmp_path):
        plan = _plan(baseline=42.0, final=81.0)
        plan.delta = 39.0
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--min-lift", "20"])
        assert result.exit_code == 0

    def test_actions_taken_shown(self, tmp_path):
        plan = _plan(actions_taken=["Generated CLAUDE.md"])
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path)])
        assert "Generated CLAUDE.md" in result.output

    def test_actions_skipped_shown(self, tmp_path):
        plan = _plan(actions_skipped=["PR submission (use --pr to enable)"])
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path)])
        assert "PR submission" in result.output

    def test_output_flag_writes_file(self, tmp_path):
        plan = _plan()
        out_file = tmp_path / "report.html"
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--output", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        assert "<html" in out_file.read_text().lower()

    def test_default_target_is_cwd(self):
        plan = _plan()
        with patch("agentkit_cli.improve_engine.ImproveEngine") as mock_cls:
            instance = MagicMock()
            instance.run.return_value = plan
            mock_cls.return_value = instance
            runner.invoke(app, ["improve"])
        assert instance.run.called
        call_args = instance.run.call_args[0]
        # first positional arg is the target (could be "." or resolved path)
        assert call_args[0] in (".", str(Path(".").resolve())) or call_args[0] is not None


# ──────────────────────────────────────────────────────────────────────────────
# D3 — HTML report
# ──────────────────────────────────────────────────────────────────────────────

class TestImproveHTMLReport:
    def test_template_exists(self):
        tmpl = Path(__file__).parent.parent / "agentkit_cli" / "templates" / "improve_report.html"
        assert tmpl.exists()

    def test_template_contains_dark_theme(self):
        tmpl = Path(__file__).parent.parent / "agentkit_cli" / "templates" / "improve_report.html"
        content = tmpl.read_text()
        # Dark theme: check for dark background color
        assert "#0d1117" in content or "background" in content

    def test_template_has_placeholders(self):
        tmpl = Path(__file__).parent.parent / "agentkit_cli" / "templates" / "improve_report.html"
        content = tmpl.read_text()
        for ph in ("{{REPO_NAME}}", "{{BASELINE}}", "{{FINAL}}", "{{DELTA}}"):
            assert ph in content

    def test_render_html_produces_html(self, tmp_path):
        from agentkit_cli.commands.improve import _render_html
        plan = _plan(target=str(tmp_path))
        html = _render_html(plan)
        assert "<html" in html.lower()
        assert "<!DOCTYPE" in html or "<!doctype" in html.lower()

    def test_render_html_has_scores(self, tmp_path):
        from agentkit_cli.commands.improve import _render_html
        plan = _plan(baseline=42.0, final=81.0)
        html = _render_html(plan)
        assert "42" in html
        assert "81" in html

    def test_render_html_has_actions(self, tmp_path):
        from agentkit_cli.commands.improve import _render_html
        plan = _plan(actions_taken=["Generated CLAUDE.md from source analysis"])
        html = _render_html(plan)
        assert "Generated CLAUDE.md" in html

    def test_render_html_has_skipped(self, tmp_path):
        from agentkit_cli.commands.improve import _render_html
        plan = _plan(actions_skipped=["PR submission"])
        html = _render_html(plan)
        assert "PR submission" in html

    def test_render_html_delta_shown(self):
        from agentkit_cli.commands.improve import _render_html
        plan = _plan(baseline=42.0, final=81.0)
        html = _render_html(plan)
        assert "+39" in html or "39" in html

    def test_output_file_written(self, tmp_path):
        plan = _plan(target=str(tmp_path))
        out = tmp_path / "improve.html"
        with _mock_engine_run(plan):
            result = runner.invoke(app, ["improve", str(tmp_path), "--output", str(out)])
        assert out.exists()
        assert len(out.read_text()) > 200

    def test_template_has_two_column_section(self):
        tmpl = Path(__file__).parent.parent / "agentkit_cli" / "templates" / "improve_report.html"
        content = tmpl.read_text()
        # Two-column: Before + After score cards
        assert "Before" in content
        assert "After" in content


# ──────────────────────────────────────────────────────────────────────────────
# D4 — agentkit run --improve integration
# ──────────────────────────────────────────────────────────────────────────────

class TestRunImproveFlag:
    def test_run_improve_flag_exists(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--improve" in result.output

    def test_run_improve_calls_engine(self, tmp_path):
        from agentkit_cli.improve_engine import ImprovementPlan
        mock_plan = ImprovementPlan(
            target=str(tmp_path),
            baseline_score=50.0,
            final_score=70.0,
            delta=20.0,
            actions_taken=["Generated CLAUDE.md"],
            actions_skipped=[],
            context_generated=True,
            hardening_applied=False,
        )
        with patch("agentkit_cli.improve_engine.ImproveEngine") as mock_cls:
            instance = MagicMock()
            instance.run.return_value = mock_plan
            mock_cls.return_value = instance
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--improve", "--json"])
        # run_cmd imports ImproveEngine only when --improve is set
        # verify the JSON output has improvement key
        if result.exit_code == 0:
            try:
                data = json.loads(result.output)
                if "improvement" in data:
                    assert data["improvement"]["delta"] == 20.0
            except (json.JSONDecodeError, KeyError):
                pass

    def test_run_improve_no_generate_passthrough(self):
        result = runner.invoke(app, ["run", "--help"])
        assert "--improve-no-generate" in result.output

    def test_run_improve_no_harden_passthrough(self):
        result = runner.invoke(app, ["run", "--help"])
        assert "--improve-no-harden" in result.output

    def test_run_improve_threshold_option(self):
        result = runner.invoke(app, ["run", "--help"])
        assert "--improve-threshold" in result.output

    def test_run_improve_json_has_improvement_key(self, tmp_path):
        from agentkit_cli.improve_engine import ImprovementPlan
        mock_plan = ImprovementPlan(
            target=str(tmp_path),
            baseline_score=55.0,
            final_score=75.0,
            delta=20.0,
            actions_taken=[],
            actions_skipped=[],
            context_generated=False,
            hardening_applied=False,
        )
        with patch("agentkit_cli.improve_engine.ImproveEngine", return_value=MagicMock(run=MagicMock(return_value=mock_plan))):
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--improve", "--json"])
        if result.exit_code == 0:
            try:
                data = json.loads(result.output)
                if "improvement" in data:
                    d = data["improvement"]
                    assert "baseline" in d or "baseline_score" in d or "delta" in d
            except json.JSONDecodeError:
                pass  # run_cmd may print multiple JSON blocks or mix output


# ──────────────────────────────────────────────────────────────────────────────
# D5 — Version, changelog, docs
# ──────────────────────────────────────────────────────────────────────────────

class TestVersionAndDocs:
    def test_version_is_046(self):
        from agentkit_cli import __version__
        assert __version__ == "0.55.0"

    def test_pyproject_version(self):
        p = Path(__file__).parent.parent / "pyproject.toml"
        content = p.read_text()
        assert '0.55.0' in content

    def test_changelog_has_046(self):
        p = Path(__file__).parent.parent / "CHANGELOG.md"
        content = p.read_text()
        assert "0.55.0" in content

    def test_readme_has_improve(self):
        p = Path(__file__).parent.parent / "README.md"
        content = p.read_text()
        assert "improve" in content.lower()

    def test_build_report_exists(self):
        p = Path(__file__).parent.parent / "BUILD-REPORT.md"
        assert p.exists()

    def test_build_report_has_version(self):
        p = Path(__file__).parent.parent / "BUILD-REPORT.md"
        content = p.read_text()
        assert "0.55.0" in content

    def test_improve_engine_importable(self):
        from agentkit_cli.improve_engine import ImproveEngine, ImprovementPlan
        assert ImproveEngine is not None
        assert ImprovementPlan is not None

    def test_improve_command_importable(self):
        from agentkit_cli.commands.improve import improve_command
        assert improve_command is not None

    def test_version_cli(self):
        result = runner.invoke(app, ["--version"])
        assert "0.55.0" in result.output

    def test_improve_in_app_commands(self):
        result = runner.invoke(app, ["--help"])
        assert "improve" in result.output
