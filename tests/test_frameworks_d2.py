"""D2 tests for agentkit frameworks CLI command."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def write_file(root: Path, name: str, content: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


class TestFrameworksCLI:
    def test_help_exits_zero(self):
        result = runner.invoke(app, ["frameworks", "--help"])
        assert result.exit_code == 0
        assert "frameworks" in result.output.lower()

    def test_empty_project(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path)])
        assert result.exit_code == 0
        assert "No frameworks detected" in result.output

    def test_json_output_has_detected_frameworks_key(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "detected_frameworks" in data

    def test_json_output_version_key(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "version" in data

    def test_json_output_project_path(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "project_path" in data

    def test_json_output_overall_score(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "overall_score" in data

    def test_json_output_below_threshold(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "below_threshold" in data

    def test_quiet_output_is_one_line(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--quiet"])
        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if l.strip()]
        assert len(lines) == 1

    def test_quiet_mentions_count(self, tmp_path):
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--quiet"])
        assert "frameworks detected" in result.output

    def test_default_min_score_60(self, tmp_path):
        # With no context file, a detected framework scores 0, below default 60
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert "FastAPI" in data["below_threshold"]

    def test_custom_min_score(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        # With --min-score 0, nothing is below threshold (even score 0 is not < 0)
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json", "--min-score", "0"])
        data = json.loads(result.output)
        assert data["below_threshold"] == []

    def test_context_file_option(self, tmp_path):
        ctx = tmp_path / "MY_AGENTS.md"
        ctx.write_text("## FastAPI Notes\nSetup.\nCommon patterns.\nKnown gotchas.\n")
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        result = runner.invoke(app, [
            "frameworks", str(tmp_path), "--json",
            "--context-file", str(ctx),
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["context_file"] == str(ctx)

    def test_rich_table_output_default(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        result = runner.invoke(app, ["frameworks", str(tmp_path)])
        assert result.exit_code == 0
        assert "Flask" in result.output

    def test_detected_frameworks_have_score(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--json"])
        data = json.loads(result.output)
        assert len(data["detected_frameworks"]) > 0
        for fw in data["detected_frameworks"]:
            assert "score" in fw
            assert isinstance(fw["score"], int)
