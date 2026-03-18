"""Tests for D3: agentkit run --llmstxt, agentkit report --llmstxt, agentkit doctor llmstxt check."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.doctor import check_llmstxt_readiness, run_doctor

runner = CliRunner()


def make_repo(tmp_path: Path, readme: bool = True) -> Path:
    if readme:
        (tmp_path / "README.md").write_text("# TestProject\n\nA test project.")
    return tmp_path


# ---------------------------------------------------------------------------
# Doctor llmstxt readiness check
# ---------------------------------------------------------------------------

class TestDoctorLlmstxtReadiness:
    def test_no_readme_no_llmstxt_warns(self, tmp_path):
        result = check_llmstxt_readiness(tmp_path)
        assert result.status == "warn"
        assert result.id == "context.llmstxt"

    def test_readme_no_llmstxt_passes_with_hint(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project")
        result = check_llmstxt_readiness(tmp_path)
        assert result.status == "pass"
        assert "agentkit llmstxt" in result.fix_hint

    def test_llmstxt_present_passes(self, tmp_path):
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "llms.txt").write_text("# Project\n\n> Desc.\n")
        result = check_llmstxt_readiness(tmp_path)
        assert result.status == "pass"

    def test_llmstxt_check_in_run_doctor(self, tmp_path):
        report = run_doctor(tmp_path)
        check_ids = [c.id for c in report.checks]
        assert "context.llmstxt" in check_ids

    def test_llmstxt_check_category_is_context(self, tmp_path):
        result = check_llmstxt_readiness(tmp_path)
        assert result.category == "context"


# ---------------------------------------------------------------------------
# agentkit run --llmstxt
# ---------------------------------------------------------------------------

class TestRunLlmstxt:
    def test_run_llmstxt_generates_file(self, tmp_path):
        make_repo(tmp_path)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--llmstxt", "--no-history"])
        assert (tmp_path / "llms.txt").exists()

    def test_run_llmstxt_json_includes_llmstxt_fields(self, tmp_path):
        make_repo(tmp_path)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--llmstxt", "--json", "--no-history"])
        out = result.output
        json_start = out.find("{")
        data = json.loads(out[json_start:out.rfind("}") + 1])
        assert "llmstxt_generated" in data
        assert data["llmstxt_generated"] is True
        assert "llmstxt_path" in data
        assert "llmstxt_section_count" in data

    def test_run_without_llmstxt_no_llmstxt_fields(self, tmp_path):
        make_repo(tmp_path)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            result = runner.invoke(app, ["run", "--path", str(tmp_path), "--json", "--no-history"])
        out = result.output
        json_start = out.find("{")
        data = json.loads(out[json_start:out.rfind("}") + 1])
        # llmstxt fields not present when flag not used
        assert "llmstxt_generated" not in data

    def test_run_llmstxt_content_valid(self, tmp_path):
        make_repo(tmp_path)
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            runner.invoke(app, ["run", "--path", str(tmp_path), "--llmstxt", "--no-history"])
        content = (tmp_path / "llms.txt").read_text()
        assert content.startswith("# ")


# ---------------------------------------------------------------------------
# agentkit report --llmstxt
# ---------------------------------------------------------------------------

class TestReportLlmstxt:
    def test_report_llmstxt_generates_llmstxt(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with patch("agentkit_cli.commands.report_cmd.run_all", return_value={}):
            with patch("agentkit_cli.commands.report_cmd._tool_status", return_value=[]):
                result = runner.invoke(app, ["report", "--path", str(tmp_path), "--output", str(out_dir / "report.html"), "--llmstxt"])
        assert result.exit_code == 0
        assert (tmp_path / "llms.txt").exists()

    def test_report_without_llmstxt_no_generation(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        with patch("agentkit_cli.commands.report_cmd.run_all", return_value={}):
            with patch("agentkit_cli.commands.report_cmd._tool_status", return_value=[]):
                result = runner.invoke(app, ["report", "--path", str(tmp_path), "--output", str(out_dir / "report.html")])
        assert result.exit_code == 0
        # llms.txt not created without --llmstxt
        assert not (tmp_path / "llms.txt").exists()
