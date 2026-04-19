from __future__ import annotations

from typer.testing import CliRunner

from agentkit_cli.context_projections import ContextProjectionEngine, FORMAT_AGENTKIT_SOURCE, FORMAT_AGENTS_MD, FORMAT_GEMINI_MD, dedicated_source_path
from agentkit_cli.main import app

runner = CliRunner()
engine = ContextProjectionEngine()

AGENTS_SAMPLE = """\
# Repo Soul

## Session Startup
Read this first.

## Safety
Keep data private.
"""


def test_sync_fix_creates_new_projection_targets(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["sync", str(tmp_path), "--fix"])
    assert result.exit_code == 0
    assert (tmp_path / "GEMINI.md").exists()
    assert (tmp_path / "COPILOT.md").exists()


def test_sync_check_detects_drift_in_new_projection_target(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    gemini = engine.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_GEMINI_MD)
    (tmp_path / "GEMINI.md").write_text(gemini.content.replace("Repo Soul", "Different"))
    result = runner.invoke(app, ["sync", str(tmp_path), "--check"])
    assert result.exit_code == 1


def test_sync_check_uses_dedicated_source_when_present(tmp_path):
    dedicated = dedicated_source_path(tmp_path)
    dedicated.parent.mkdir()
    source = "# Repo Soul\n\n## Overview\nCanonical.\n"
    dedicated.write_text(source)
    agents = engine.convert(source, FORMAT_AGENTKIT_SOURCE, FORMAT_AGENTS_MD)
    (tmp_path / "AGENTS.md").write_text(agents.content)
    result = runner.invoke(app, ["sync", str(tmp_path), "--check"])
    assert result.exit_code == 1
    assert ".agentkit/source.md" in result.output


def test_sync_fix_projects_from_dedicated_source(tmp_path):
    dedicated = dedicated_source_path(tmp_path)
    dedicated.parent.mkdir()
    dedicated.write_text("# Repo Soul\n\n## Overview\nCanonical.\n")
    result = runner.invoke(app, ["sync", str(tmp_path), "--fix"])
    assert result.exit_code == 0
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
