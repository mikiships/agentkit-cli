from __future__ import annotations

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()

AGENTS_SAMPLE = """\
# Repo Soul

## Session Startup
Read this first.
"""


def test_init_can_write_projection_targets(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--project-targets", "claude,gemini", "--write-projections"])
    assert result.exit_code == 0
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "GEMINI.md").exists()


def test_init_projection_dry_run_mentions_next_step(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    result = runner.invoke(app, ["init", "--path", str(tmp_path), "--project-targets", "claude"])
    assert result.exit_code == 0
    assert "write-projections" in result.output or "agentkit project --write" in result.output
