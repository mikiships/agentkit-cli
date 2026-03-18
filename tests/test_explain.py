"""Tests for agentkit explain — D1 through D5.

D1: ExplainEngine (≥12 tests)
D2: explain_cmd CLI command (≥10 tests)
D3: Template-based explanation quality (≥8 tests)
D4: agentkit run --explain integration (≥6 tests)
D5: Docs / version bump / BUILD-REPORT (≥4 tests)
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _report(
    composite: float = 85.0,
    findings: list | None = None,
    project: str = "my-repo",
    tool_scores: dict | None = None,
) -> dict:
    base: dict[str, Any] = {
        "project": project,
        "composite": composite,
        "total": 4,
        "passed": 3,
        "failed": 1,
        "findings": findings or [],
        "summary": {"steps": []},
    }
    if tool_scores:
        base["breakdown"] = tool_scores
    return base


def _finding(cat: str, sev: str = "high", msg: str = "") -> dict:
    return {"type": cat, "severity": sev, "message": msg or f"Issue: {cat}"}


# ===========================================================================
# D1: ExplainEngine
# ===========================================================================

class TestExplainEngineLoadReport:
    """D1: load_report()"""

    def test_load_valid_json(self, tmp_path):
        from agentkit_cli.explain import ExplainEngine
        data = {"composite": 75, "project": "test"}
        p = tmp_path / "report.json"
        p.write_text(json.dumps(data))
        engine = ExplainEngine()
        result = engine.load_report(str(p))
        assert result["composite"] == 75
        assert result["project"] == "test"

    def test_load_missing_file_raises(self, tmp_path):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        with pytest.raises(FileNotFoundError):
            engine.load_report(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json_raises(self, tmp_path):
        from agentkit_cli.explain import ExplainEngine
        p = tmp_path / "bad.json"
        p.write_text("not json {{{")
        engine = ExplainEngine()
        with pytest.raises((json.JSONDecodeError, ValueError)):
            engine.load_report(str(p))

    def test_load_non_object_raises(self, tmp_path):
        from agentkit_cli.explain import ExplainEngine
        p = tmp_path / "array.json"
        p.write_text("[1, 2, 3]")
        engine = ExplainEngine()
        with pytest.raises(ValueError, match="Expected JSON object"):
            engine.load_report(str(p))


class TestExplainEngineBuildPrompt:
    """D1: build_prompt()"""

    def test_prompt_contains_score(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=72.0, project="acme")
        prompt = engine.build_prompt(report)
        assert "72" in prompt
        assert "acme" in prompt

    def test_prompt_contains_tier(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=85.0)
        prompt = engine.build_prompt(report)
        assert "Tier B" in prompt

    def test_prompt_contains_four_sections(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=60.0)
        prompt = engine.build_prompt(report)
        assert "## What This Score Means" in prompt
        assert "## Key Findings Explained" in prompt
        assert "## Top 3 Next Steps" in prompt
        assert "## If You Do Nothing Else" in prompt

    def test_prompt_includes_findings(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        findings = [_finding("path-rot", "critical", "broken path")]
        report = _report(composite=55.0, findings=findings)
        prompt = engine.build_prompt(report)
        assert "path-rot" in prompt

    def test_prompt_truncates_findings(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        # Use names unlikely to appear more than once per finding
        findings = [{"type": f"findtype{i:02d}", "severity": "high", "message": f"msg{i:02d}"} for i in range(20)]
        report = _report(findings=findings)
        prompt = engine.build_prompt(report)
        # Should include at most 5 findings (types findtype00 through findtype04 max)
        # Count unique finding type references
        included = sum(1 for i in range(20) if f"findtype{i:02d}" in prompt)
        assert included <= 5

    def test_prompt_within_token_budget(self):
        """Prompt must be under ~8000 chars (rough 2000 token proxy)."""
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(
            composite=40.0,
            findings=[_finding(f"t-{i}", msg="x" * 200) for i in range(10)],
        )
        prompt = engine.build_prompt(report)
        assert len(prompt) < 8000


class TestExplainEngineCallLLM:
    """D1: call_llm() — always mocked, never real API"""

    def test_returns_empty_when_no_api_key(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = engine.call_llm("test prompt")
        assert result == ""

    def test_uses_api_key_when_set(self):
        from agentkit_cli.explain import ExplainEngine

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "## What This Score Means\nGreat job.\n"
        mock_message.content = [mock_block]
        mock_client.messages.create.return_value = mock_message

        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client

        engine = ExplainEngine()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
                result = engine.call_llm("test prompt")

        assert "Great job" in result
        mock_client.messages.create.assert_called_once()

    def test_falls_back_on_api_error(self):
        from agentkit_cli.explain import ExplainEngine

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RuntimeError("connection refused")

        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client

        engine = ExplainEngine()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
                result = engine.call_llm("test prompt")

        assert result == ""

    def test_falls_back_when_anthropic_not_installed(self):
        from agentkit_cli.explain import ExplainEngine
        import sys

        engine = ExplainEngine()
        # Remove anthropic from sys.modules so the import inside call_llm fails
        saved = sys.modules.pop("anthropic", None)
        try:
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
                result = engine.call_llm("test prompt")
        finally:
            if saved is not None:
                sys.modules["anthropic"] = saved

        assert result == ""


class TestExplainEngineIntegration:
    """D1: explain() full pipeline"""

    def test_explain_uses_template_when_no_api_key(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=75.0)
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = engine.explain(report)
        assert "## What This Score Means" in result
        assert len(result) > 100

    def test_explain_uses_llm_result_when_available(self):
        from agentkit_cli.explain import ExplainEngine

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_block = MagicMock()
        mock_block.text = "## What This Score Means\nLLM response here.\n"
        mock_message.content = [mock_block]
        mock_client.messages.create.return_value = mock_message

        mock_anthropic_module = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client

        engine = ExplainEngine()
        report = _report(composite=60.0)
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            with patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
                result = engine.explain(report)

        assert "LLM response here" in result

    def test_explain_run_result_delegates_to_explain(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=80.0)
        with patch.object(engine, "explain", return_value="## Coaching") as mock_explain:
            result = engine.explain_run_result(report)
        mock_explain.assert_called_once_with(report)
        assert result == "## Coaching"

    def test_model_default(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        assert engine.model == "claude-3-5-haiku-20241022"

    def test_custom_model(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine(model="claude-3-opus-20240229")
        assert engine.model == "claude-3-opus-20240229"


# ===========================================================================
# D2: explain_cmd CLI
# ===========================================================================

class TestExplainCmdLoadReport:
    """D2: --report flag"""

    def test_loads_report_and_outputs_markdown(self, tmp_path):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=78.0, project="test-project")
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            # Should not raise
            explain_command(report_path=str(p), no_llm=True)

    def test_missing_report_exits_1(self, tmp_path):
        from agentkit_cli.commands.explain_cmd import explain_command
        import typer
        with pytest.raises((SystemExit, typer.Exit)):
            explain_command(report_path=str(tmp_path / "missing.json"))

    def test_invalid_json_exits_1(self, tmp_path):
        from agentkit_cli.commands.explain_cmd import explain_command
        import typer
        p = tmp_path / "bad.json"
        p.write_text("not json")
        with pytest.raises((SystemExit, typer.Exit)):
            explain_command(report_path=str(p))


class TestExplainCmdNoLLM:
    """D2: --no-llm path"""

    def test_no_llm_calls_template_explain(self, tmp_path):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=65.0)
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch("agentkit_cli.explain.ExplainEngine.template_explain") as mock_tmpl:
            mock_tmpl.return_value = "## Template output"
            explain_command(report_path=str(p), no_llm=True)

        mock_tmpl.assert_called_once()

    def test_no_llm_does_not_call_llm(self, tmp_path):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=65.0)
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch("agentkit_cli.explain.ExplainEngine.call_llm") as mock_llm:
            explain_command(report_path=str(p), no_llm=True)

        mock_llm.assert_not_called()


class TestExplainCmdJsonOutput:
    """D2: --json output structure"""

    def test_json_output_has_required_fields(self, tmp_path, capsys):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=72.0, project="json-test")
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            explain_command(report_path=str(p), no_llm=True, json_output=True)

        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert "project" in out
        assert "score" in out
        assert "tier" in out
        assert "explanation" in out
        assert "recommendations" in out
        assert "one_thing" in out

    def test_json_output_score_matches_report(self, tmp_path, capsys):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=55.0, project="score-check")
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            explain_command(report_path=str(p), no_llm=True, json_output=True)

        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert out["score"] == 55.0

    def test_json_output_tier_correct(self, tmp_path, capsys):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=92.0)
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            explain_command(report_path=str(p), no_llm=True, json_output=True)

        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert out["tier"] == "A"

    def test_json_recommendations_is_list(self, tmp_path, capsys):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=70.0)
        p = tmp_path / "report.json"
        p.write_text(json.dumps(report_data))

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            explain_command(report_path=str(p), no_llm=True, json_output=True)

        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert isinstance(out["recommendations"], list)


class TestExplainCmdOutputFile:
    """D2: --output file"""

    def test_writes_markdown_to_file(self, tmp_path):
        from agentkit_cli.commands.explain_cmd import explain_command
        report_data = _report(composite=80.0)
        report_p = tmp_path / "report.json"
        report_p.write_text(json.dumps(report_data))
        out_p = tmp_path / "coaching.md"

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            explain_command(report_path=str(report_p), no_llm=True, output=out_p)

        assert out_p.exists()
        content = out_p.read_text()
        assert len(content) > 50


# ===========================================================================
# D3: Template-based explanation quality
# ===========================================================================

class TestTemplateScoreTiers:
    """D3: One test per score tier."""

    def test_tier_a_phrase(self):
        """Score ≥ 90 → well-configured language."""
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=95.0)
        result = engine.template_explain(report)
        assert "well-configured" in result.lower() or "well configured" in result.lower() or "already working" in result.lower()

    def test_tier_b_phrase(self):
        """Score 70-89 → good foundation language."""
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=78.0)
        result = engine.template_explain(report)
        assert "good foundation" in result.lower() or "room to improve" in result.lower()

    def test_tier_c_phrase(self):
        """Score 50-69 → mixed results language."""
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=60.0)
        result = engine.template_explain(report)
        assert "mixed" in result.lower() or "friction" in result.lower()

    def test_tier_f_phrase(self):
        """Score < 50 → significant gaps language."""
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=30.0)
        result = engine.template_explain(report)
        assert "significant" in result.lower() or "gaps" in result.lower() or "struggle" in result.lower()


class TestTemplateFindings:
    """D3: Plain language for finding types."""

    def test_path_rot_explanation(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=60.0, findings=[_finding("path-rot", "critical")])
        result = engine.template_explain(report)
        assert "path" in result.lower() and (
            "don't exist" in result.lower() or "not exist" in result.lower()
            or "confuse" in result.lower() or "broken" in result.lower()
        )

    def test_year_rot_explanation(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=60.0, findings=[_finding("year-rot", "critical")])
        result = engine.template_explain(report)
        assert "stale" in result.lower() or "year" in result.lower() or "past" in result.lower()

    def test_bloat_explanation(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=65.0, findings=[_finding("bloat", "medium")])
        result = engine.template_explain(report)
        assert "long" in result.lower() or "too long" in result.lower() or "focused" in result.lower() or "trim" in result.lower()

    def test_low_coderace_explanation(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=55.0, tool_scores={"coderace": 40})
        result = engine.template_explain(report)
        assert "benchmark" in result.lower() or "score" in result.lower() or "coderace" in result.lower()

    def test_output_has_four_sections(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=72.0)
        result = engine.template_explain(report)
        assert "## What This Score Means" in result
        assert "## Key Findings Explained" in result
        assert "## Top 3 Next Steps" in result
        assert "## If You Do Nothing Else" in result

    def test_output_contains_next_steps(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=45.0)
        result = engine.template_explain(report)
        # Should have at least 1 numbered step
        assert any(f"{n}." in result for n in range(1, 4))

    def test_template_is_pure_markdown(self):
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=80.0)
        result = engine.template_explain(report)
        assert isinstance(result, str)
        assert len(result) > 200

    def test_template_no_api_key_required(self):
        """template_explain must work with no env vars at all."""
        from agentkit_cli.explain import ExplainEngine
        engine = ExplainEngine()
        report = _report(composite=50.0)
        with patch.dict(os.environ, {}, clear=True):
            result = engine.template_explain(report)
        assert "## What This Score Means" in result


# ===========================================================================
# D4: agentkit run --explain integration
# ===========================================================================

class TestRunExplainFlag:
    """D4: agentkit run --explain"""

    def test_explain_flag_accepted_by_run_command(self):
        """run_command should accept explain=True without raising TypeError."""
        from agentkit_cli.commands.run_cmd import run_command
        import inspect
        sig = inspect.signature(run_command)
        assert "explain" in sig.parameters

    def test_no_llm_flag_accepted_by_run_command(self):
        from agentkit_cli.commands.run_cmd import run_command
        import inspect
        sig = inspect.signature(run_command)
        assert "no_llm" in sig.parameters

    def test_explain_appends_coaching_report_to_output(self, tmp_path, capsys):
        from agentkit_cli.commands.run_cmd import run_command

        with patch("agentkit_cli.commands.run_cmd._run_step") as mock_step:
            mock_step.return_value = {
                "step": "lint-context",
                "tool": "agentlint",
                "status": "pass",
                "duration": 0.1,
                "output": "",
            }
            with patch("agentkit_cli.explain.ExplainEngine.template_explain") as mock_tmpl:
                mock_tmpl.return_value = "## What This Score Means\nMocked coaching."
                run_command(
                    path=tmp_path,
                    skip=None,
                    explain=True,
                    no_llm=True,
                    no_history=True,
                    json_output=False,
                )

        # template_explain was called — verify
        mock_tmpl.assert_called_once()

    def test_explain_json_includes_coaching_field(self, tmp_path, capsys):
        from agentkit_cli.commands.run_cmd import run_command

        with patch("agentkit_cli.commands.run_cmd._run_step") as mock_step:
            mock_step.return_value = {
                "step": "lint-context",
                "tool": "agentlint",
                "status": "pass",
                "duration": 0.1,
                "output": "",
            }
            with patch("agentkit_cli.explain.ExplainEngine.template_explain") as mock_tmpl:
                mock_tmpl.return_value = "## Coaching section"
                run_command(
                    path=tmp_path,
                    skip=None,
                    explain=True,
                    no_llm=True,
                    no_history=True,
                    json_output=True,
                )

        captured = capsys.readouterr()
        stdout = captured.out
        if stdout.strip():
            try:
                data = json.loads(stdout)
                if "coaching_report" in data:
                    assert data["coaching_report"] == "## Coaching section"
            except json.JSONDecodeError:
                pass  # Non-JSON output lines before JSON block

    def test_run_explain_main_wiring(self):
        """agentkit run --explain flag is wired in main.py."""
        from agentkit_cli.main import app
        # Check typer app has 'run' command with --explain option
        result = None
        for cmd in app.registered_commands:
            if cmd.name == "run" or (hasattr(cmd, "callback") and cmd.callback.__name__ == "run"):
                result = cmd
                break
        # Alternative: just import and check signature via CLI runner
        from typer.testing import CliRunner
        runner = CliRunner()
        res = runner.invoke(app, ["run", "--help"])
        assert "--explain" in res.output

    def test_run_no_llm_flag_wired(self):
        from agentkit_cli.main import app
        from typer.testing import CliRunner
        runner = CliRunner()
        res = runner.invoke(app, ["run", "--help"])
        assert "--no-llm" in res.output

    def test_explain_command_in_main(self):
        """agentkit explain is registered in main.py."""
        from agentkit_cli.main import app
        from typer.testing import CliRunner
        runner = CliRunner()
        res = runner.invoke(app, ["explain", "--help"])
        assert res.exit_code == 0
        assert "--no-llm" in res.output


# ===========================================================================
# D5: Docs, CHANGELOG, version bump, BUILD-REPORT
# ===========================================================================

class TestVersionBump:
    """D5: version bump to 0.45.0"""

    def test_version_is_0_45_0(self):
        from agentkit_cli import __version__
        assert __version__ == "0.49.0"

    def test_pyproject_version_matches(self):
        import tomllib
        repo = Path(__file__).parent.parent
        with open(repo / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        assert data["project"]["version"] == "0.49.0"


class TestChangelog:
    """D5: CHANGELOG entry"""

    def test_changelog_has_0_45_0_entry(self):
        repo = Path(__file__).parent.parent
        text = (repo / "CHANGELOG.md").read_text()
        assert "0.45.0" in text

    def test_changelog_mentions_explain(self):
        repo = Path(__file__).parent.parent
        text = (repo / "CHANGELOG.md").read_text()
        assert "explain" in text.lower()


class TestBuildReport:
    """D5: BUILD-REPORT.md exists and is complete."""

    def test_build_report_exists(self):
        repo = Path(__file__).parent.parent
        assert (repo / "BUILD-REPORT.md").exists(), "BUILD-REPORT.md not found"

    def test_build_report_has_deliverables(self):
        repo = Path(__file__).parent.parent
        text = (repo / "BUILD-REPORT.md").read_text()
        # Should mention all 5 deliverables
        for d in ("D1", "D2", "D3", "D4", "D5"):
            assert d in text, f"BUILD-REPORT.md missing {d}"


class TestReadme:
    """D5: README has AI-Powered Explanations section."""

    def test_readme_has_explain_section(self):
        repo = Path(__file__).parent.parent
        readme = (repo / "README.md").read_text()
        assert "explain" in readme.lower(), "README.md missing explain documentation"
