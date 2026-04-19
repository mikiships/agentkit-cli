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


def test_source_init_creates_dedicated_template(tmp_path):
    result = runner.invoke(app, ["source", str(tmp_path), "--init", "--title", "Repo Soul"])
    assert result.exit_code == 0
    content = dedicated_source_path(tmp_path).read_text()
    assert "# Repo Soul" in content
    assert "## Overview" in content


def test_source_promote_copies_best_detected_legacy_source(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["source", str(tmp_path), "--promote"])
    assert result.exit_code == 0
    assert dedicated_source_path(tmp_path).read_text() == AGENTS_SAMPLE


def test_source_promote_can_use_explicit_from_format(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Repo Soul\n")
    result = runner.invoke(app, ["source", str(tmp_path), "--promote", "--from", "claude"])
    assert result.exit_code == 0
    assert dedicated_source_path(tmp_path).read_text() == "# Repo Soul\n"


def test_source_existing_destination_fails_without_force(tmp_path):
    dedicated = dedicated_source_path(tmp_path)
    dedicated.parent.mkdir()
    dedicated.write_text("existing\n")
    result = runner.invoke(app, ["source", str(tmp_path), "--init"])
    assert result.exit_code == 1
    assert "Dedicated source already exists" in result.output


def test_source_json_reports_promoted_metadata(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["source", str(tmp_path), "--promote", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["action"] == "promote"
    assert payload["source_format"] == "agentkit-source"
    assert payload["promoted_from_format"] == "agents-md"
    assert payload["destination_display"] == ".agentkit/source.md"
