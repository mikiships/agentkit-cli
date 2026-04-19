from __future__ import annotations

from agentkit_cli.context_projections import (
    ContextProjectionEngine,
    FORMAT_AGENT_MD,
    FORMAT_AGENTS_MD,
    FORMAT_CLAUDE_MD,
    FORMAT_COPILOT_MD,
    FORMAT_GEMINI_MD,
    FORMAT_LLMSTXT,
    FORMAT_FILENAMES,
)

ENGINE = ContextProjectionEngine()

AGENTS_SAMPLE = """\
# Project Soul

## Session Startup
Read this first.

## Safety
Keep data private.

## Commands
make test
"""


def test_detect_source_priority_prefers_agents_over_other_targets(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# Repo\n")
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    (tmp_path / "GEMINI.md").write_text("# Repo\n")
    fmt, path = ENGINE.detect_source(tmp_path)  # type: ignore[misc]
    assert fmt == FORMAT_AGENTS_MD
    assert path.name == "AGENTS.md"


def test_convert_all_includes_new_projection_targets():
    results = ENGINE.convert_all(AGENTS_SAMPLE, FORMAT_AGENTS_MD)
    targets = {r.target_format for r in results}
    assert {FORMAT_CLAUDE_MD, FORMAT_AGENT_MD, FORMAT_GEMINI_MD, FORMAT_COPILOT_MD, FORMAT_LLMSTXT}.issubset(targets)


def test_agent_projection_normalizes_heading_without_wrong_filename_swap():
    result = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_AGENT_MD)
    assert result.content.startswith("# AGENT.md for Project Soul")
    assert "AGENTS.md for" not in result.content.splitlines()[0]


def test_gemini_projection_keeps_project_heading():
    result = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_GEMINI_MD)
    assert result.content.splitlines()[0] == "# Project Soul"
    assert "Projected target: GEMINI.md" in result.content


def test_sync_status_tracks_new_projection_targets(tmp_path):
    (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
    fresh = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_COPILOT_MD)
    (tmp_path / "COPILOT.md").write_text(fresh.content)
    status = ENGINE.get_sync_status(tmp_path)
    assert status[FORMAT_AGENTS_MD] == "source"
    assert status[FORMAT_COPILOT_MD] == "ok"
    assert status[FORMAT_AGENT_MD] == "missing"


def test_llmstxt_projection_contains_source_metadata():
    result = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_LLMSTXT)
    assert "## Source" in result.content
    assert "Generated from: agents-md" in result.content


def test_filenames_cover_supported_targets():
    assert FORMAT_FILENAMES[FORMAT_AGENT_MD] == "AGENT.md"
    assert FORMAT_FILENAMES[FORMAT_GEMINI_MD] == "GEMINI.md"
    assert FORMAT_FILENAMES[FORMAT_COPILOT_MD] == "COPILOT.md"
