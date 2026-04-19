from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.context_projections import dedicated_source_path
from agentkit_cli.main import app

runner = CliRunner()

AGENTS_SAMPLE = """\
# Repo Soul

## Session Startup
Read this first.

## Safety
Keep data private.
"""


def test_project_write_all_creates_supported_targets(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["project", str(tmp_path), "--targets", "all", "--write"])
    assert result.exit_code == 0
    for name in ("CLAUDE.md", "AGENT.md", "GEMINI.md", "COPILOT.md", "llms.txt"):
        assert (tmp_path / name).exists()


def test_project_check_exits_non_zero_on_missing_targets(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["project", str(tmp_path), "--targets", "claude,gemini", "--check"])
    assert result.exit_code == 1


def test_project_json_reports_expected_fields(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["project", str(tmp_path), "--targets", "claude,agent", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) >= {"canonical_source", "requested_targets", "written_targets", "drifted_targets", "skipped_targets"}
    assert payload["requested_targets"] == ["claude-md", "agent-md"]


def test_project_output_dir_writes_into_custom_directory(tmp_path):
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    out_dir = tmp_path / "out"
    (source_dir / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["project", str(source_dir), "--targets", "claude", "--output-dir", str(out_dir), "--write"])
    assert result.exit_code == 0
    assert (out_dir / "CLAUDE.md").exists()


def test_project_unknown_target_fails(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["project", str(tmp_path), "--targets", "bogus"])
    assert result.exit_code == 1


def test_project_prefers_dedicated_source_when_present(tmp_path):
    dedicated = dedicated_source_path(tmp_path)
    dedicated.parent.mkdir()
    dedicated.write_text("# Dedicated Soul\n\n## Overview\nCanonical.\n")
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["project", str(tmp_path), "--targets", "claude", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["canonical_source_format"] == "agentkit-source"
    assert payload["canonical_source"].endswith(".agentkit/source.md")
