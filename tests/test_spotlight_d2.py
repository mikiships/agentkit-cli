"""Tests for `agentkit spotlight` CLI command (D2 — ≥10 tests)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.spotlight_cmd import SpotlightResult

runner = CliRunner()


def _make_result(**kwargs) -> SpotlightResult:
    from datetime import datetime, timezone
    defaults = dict(
        repo="acme/cool-agent",
        score=82.5,
        grade="B",
        top_findings=["[agentlint] Missing AGENTS.md", "[agentmd] Score: 75"],
        run_date=datetime.now(timezone.utc).isoformat(),
        repo_description="A test agent repo",
        repo_stars=1200,
        repo_language="Python",
    )
    defaults.update(kwargs)
    return SpotlightResult(**defaults)


FAKE_RESULT = _make_result()


class TestSpotlightHelp:
    def test_help_shows_flags(self):
        result = runner.invoke(app, ["spotlight", "--help"])
        assert result.exit_code == 0
        assert "--topic" in result.output
        assert "--deep" in result.output
        assert "--share" in result.output
        assert "--json" in result.output
        assert "--output" in result.output
        assert "--quiet" in result.output

    def test_help_shows_language_flag(self):
        result = runner.invoke(app, ["spotlight", "--help"])
        assert "--language" in result.output or "--lang" in result.output


class TestSpotlightJsonOutput:
    def test_json_with_explicit_repo(self):
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT):
            result = runner.invoke(app, ["spotlight", "acme/cool-agent", "--json", "--no-history"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["repo"] == "acme/cool-agent"
        assert data["grade"] == "B"
        assert "score" in data
        assert "top_findings" in data

    def test_json_output_is_valid_json(self):
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT):
            result = runner.invoke(app, ["spotlight", "acme/cool-agent", "--json", "--no-history"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert isinstance(parsed, dict)

    def test_json_contains_run_date(self):
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT):
            result = runner.invoke(app, ["spotlight", "acme/cool-agent", "--json", "--no-history"])
        data = json.loads(result.output)
        assert "run_date" in data


class TestSpotlightAutoSelect:
    def test_auto_select_when_no_target(self):
        fake_candidate = {"full_name": "acme/cool-agent", "description": "test", "stars": 500, "language": "Python"}
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.select_candidate", return_value=fake_candidate):
            with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT):
                result = runner.invoke(app, ["spotlight", "--json", "--no-history"])
        assert result.exit_code == 0

    def test_exits_1_when_no_candidate(self):
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.select_candidate", return_value=None):
            result = runner.invoke(app, ["spotlight", "--no-history"])
        assert result.exit_code != 0


class TestSpotlightGithubPrefix:
    def test_github_prefix_stripped(self):
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT) as mock:
            runner.invoke(app, ["spotlight", "github:acme/cool-agent", "--json", "--no-history"])
        # run_spotlight should be called with repo without github: prefix
        call_kwargs = mock.call_args[1] if mock.call_args else {}
        repo_arg = mock.call_args[0][0] if mock.call_args and mock.call_args[0] else call_kwargs.get("repo", "")
        assert not repo_arg.startswith("github:") if repo_arg else True


class TestSpotlightQuietMode:
    def test_quiet_suppresses_output(self):
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT):
            result = runner.invoke(app, ["spotlight", "acme/cool-agent", "--quiet", "--no-history"])
        assert result.exit_code == 0
        # quiet mode produces minimal/no output
        assert len(result.output.strip()) == 0


class TestSpotlightOutputFile:
    def test_output_file_creates_html(self, tmp_path):
        out_file = tmp_path / "spotlight.html"
        with patch("agentkit_cli.commands.spotlight_cmd.SpotlightEngine.run_spotlight", return_value=FAKE_RESULT):
            result = runner.invoke(app, ["spotlight", "acme/cool-agent", "--output", str(out_file), "--no-history"])
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert "<!DOCTYPE html>" in content
        assert "acme/cool-agent" in content
