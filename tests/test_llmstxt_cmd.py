"""Tests for agentkit llmstxt CLI command (D2)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def make_repo(tmp_path: Path, readme: bool = True, docs: bool = False) -> Path:
    if readme:
        (tmp_path / "README.md").write_text("# TestProject\n\nA great test project description.")
    if docs:
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide\n\nDetails.")
    return tmp_path


class TestLlmsTxtCommand:
    def test_basic_invocation(self, tmp_path):
        make_repo(tmp_path)
        result = runner.invoke(app, ["llmstxt", str(tmp_path)])
        assert result.exit_code == 0

    def test_writes_llmstxt_file(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--output", str(out_dir)])
        assert result.exit_code == 0
        assert (out_dir / "llms.txt").exists()

    def test_full_flag_writes_llms_full(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--full", "--output", str(out_dir)])
        assert result.exit_code == 0
        assert (out_dir / "llms-full.txt").exists()

    def test_json_output(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--json", "--output", str(out_dir)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "project" in data
        assert "files" in data
        assert "section_count" in data

    def test_json_output_has_size(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--json", "--output", str(out_dir)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["llmstxt_size"] > 0

    def test_score_flag(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--json", "--score", "--output", str(out_dir)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "score" in data
        assert 0 <= data["score"] <= 100

    def test_invalid_path_exits_1(self, tmp_path):
        result = runner.invoke(app, ["llmstxt", "/nonexistent/path/xyz"])
        assert result.exit_code == 1

    def test_validate_no_llmstxt_exits_1(self, tmp_path):
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--validate"])
        assert result.exit_code == 1

    def test_validate_with_existing_llmstxt(self, tmp_path):
        (tmp_path / "llms.txt").write_text("# MyProject\n\n> A great project.\n\n## Docs\n\n- [README](README.md)\n- [Guide](docs/guide.md)\n- [API](api.md)\n")
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--validate"])
        assert result.exit_code == 0

    def test_validate_json_output(self, tmp_path):
        (tmp_path / "llms.txt").write_text("# MyProject\n\n> Description.\n\n## Docs\n\n- [A](a.md)\n- [B](b.md)\n- [C](c.md)\n\n## API\n\n- [X](x.py)\n")
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--validate", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "checks" in data
        assert "score" in data

    def test_default_output_dir_is_cwd(self, tmp_path):
        make_repo(tmp_path)
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["llmstxt", str(tmp_path)])
            assert result.exit_code == 0
            assert Path("llms.txt").exists()

    def test_full_json_includes_full_size(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--json", "--full", "--output", str(out_dir)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["llms_full_size"] > 0

    def test_share_flag_calls_upload(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        with patch("agentkit_cli.commands.llmstxt_cmd._upload_llmstxt", return_value="https://here.now/abc"):
            result = runner.invoke(app, ["llmstxt", str(tmp_path), "--json", "--share", "--output", str(out_dir)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("share_url") == "https://here.now/abc"

    def test_github_clone_failure_exits_1(self):
        with patch("agentkit_cli.commands.llmstxt_cmd._clone_repo",
                   side_effect=RuntimeError("Clone failed")):
            result = runner.invoke(app, ["llmstxt", "github:bad/repo"])
        assert result.exit_code == 1

    def test_github_clone_and_generate(self, tmp_path):
        make_repo(tmp_path)
        out_dir = tmp_path / "out"
        with patch("agentkit_cli.commands.llmstxt_cmd._clone_repo",
                   return_value=(str(tmp_path), "testrepo")):
            result = runner.invoke(app, ["llmstxt", "github:owner/testrepo", "--json", "--output", str(out_dir)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "project" in data
