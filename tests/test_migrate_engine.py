"""Tests for MigrateEngine (D1) — ≥15 tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentkit_cli.migrate import (
    MigrateEngine,
    MigrateResult,
    FORMAT_AGENTS_MD,
    FORMAT_CLAUDE_MD,
    FORMAT_LLMSTXT,
    FORMAT_ALL,
    FORMAT_FILENAMES,
    _detect_format_from_content,
    _detect_format_from_filename,
    _parse_sections,
    _get_top_level_intro,
    _make_gen_stamp,
    _extract_gen_hash,
    _source_hash,
)

ENGINE = MigrateEngine()

# ---------------------------------------------------------------------------
# Sample fixtures
# ---------------------------------------------------------------------------

AGENTS_SAMPLE = """\
# My Project Soul

## Session Startup
Always read this file first.

## Memory Rules
Files survive compaction; mental notes don't.

## Safety
Keep private data inside.

## Autonomy Levels
| Action | Level |
|--------|-------|
| Read | Act freely |
"""

CLAUDE_SAMPLE = """\
# My Project

## Overview
A Python CLI for agent quality assurance.

## Stack
- Python 3.11
- typer, rich

## Commands
```
make test
make lint
```

## Patterns
- Use type hints everywhere
- Rich for terminal output
"""

LLMSTXT_SAMPLE = """\
# My Project

> A great tool for developers.

## Features
Key features of the project.

- https://example.com/docs
"""


# ---------------------------------------------------------------------------
# D1: format detection
# ---------------------------------------------------------------------------

class TestDetectFormatFromFilename:
    def test_agents_md(self):
        assert _detect_format_from_filename("AGENTS.md") == FORMAT_AGENTS_MD

    def test_claude_md(self):
        assert _detect_format_from_filename("CLAUDE.md") == FORMAT_CLAUDE_MD

    def test_llms_txt(self):
        assert _detect_format_from_filename("llms.txt") == FORMAT_LLMSTXT

    def test_unknown_returns_none(self):
        assert _detect_format_from_filename("README.md") is None

    def test_full_path(self):
        assert _detect_format_from_filename("/some/path/AGENTS.md") == FORMAT_AGENTS_MD


class TestDetectFormatFromContent:
    def test_llmstxt_detection(self):
        result = _detect_format_from_content(LLMSTXT_SAMPLE)
        assert result == FORMAT_LLMSTXT

    def test_agents_md_detection(self):
        result = _detect_format_from_content(AGENTS_SAMPLE)
        assert result == FORMAT_AGENTS_MD


class TestDetectFormatFromPath:
    def test_detect_agents_md(self, tmp_path):
        p = tmp_path / "AGENTS.md"
        p.write_text(AGENTS_SAMPLE)
        assert ENGINE.detect_format(p) == FORMAT_AGENTS_MD

    def test_detect_claude_md(self, tmp_path):
        p = tmp_path / "CLAUDE.md"
        p.write_text(CLAUDE_SAMPLE)
        assert ENGINE.detect_format(p) == FORMAT_CLAUDE_MD

    def test_detect_llmstxt(self, tmp_path):
        p = tmp_path / "llms.txt"
        p.write_text(LLMSTXT_SAMPLE)
        assert ENGINE.detect_format(p) == FORMAT_LLMSTXT

    def test_detect_missing_returns_none(self, tmp_path):
        assert ENGINE.detect_format(tmp_path / "nonexistent.md") is None


# ---------------------------------------------------------------------------
# D1: detect_source
# ---------------------------------------------------------------------------

class TestDetectSource:
    def test_finds_agents_md(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
        result = ENGINE.detect_source(tmp_path)
        assert result is not None
        fmt, path = result
        assert fmt == FORMAT_AGENTS_MD

    def test_finds_claude_md_if_no_agents(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(CLAUDE_SAMPLE)
        result = ENGINE.detect_source(tmp_path)
        assert result is not None
        fmt, _ = result
        assert fmt == FORMAT_CLAUDE_MD

    def test_prefers_agents_over_claude(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
        (tmp_path / "CLAUDE.md").write_text(CLAUDE_SAMPLE)
        result = ENGINE.detect_source(tmp_path)
        assert result is not None
        fmt, _ = result
        assert fmt == FORMAT_AGENTS_MD

    def test_empty_dir_returns_none(self, tmp_path):
        assert ENGINE.detect_source(tmp_path) is None


# ---------------------------------------------------------------------------
# D1: parse helpers
# ---------------------------------------------------------------------------

class TestParseSections:
    def test_parses_h2_sections(self):
        secs = _parse_sections(AGENTS_SAMPLE)
        titles = [s.title for s in secs]
        assert "Session Startup" in titles
        assert "Memory Rules" in titles

    def test_section_body(self):
        secs = _parse_sections(AGENTS_SAMPLE)
        startup = next(s for s in secs if s.title == "Session Startup")
        assert "Always read this file first" in startup.body

    def test_get_top_level_intro(self):
        text = "Some intro text.\n\n## Section\n\nBody."
        intro = _get_top_level_intro(text)
        assert "Some intro text" in intro
        assert "Section" not in intro


# ---------------------------------------------------------------------------
# D1: stamp / hash helpers
# ---------------------------------------------------------------------------

class TestStampHelpers:
    def test_make_gen_stamp_contains_marker(self):
        stamp = _make_gen_stamp("hello")
        assert "generated by agentkit migrate" in stamp

    def test_make_gen_stamp_contains_hash(self):
        stamp = _make_gen_stamp("hello")
        assert "hash:" in stamp

    def test_extract_gen_hash_roundtrip(self):
        content = "hello world"
        stamp = _make_gen_stamp(content)
        extracted = _extract_gen_hash(stamp)
        assert extracted == _source_hash(content)

    def test_extract_gen_hash_none_if_missing(self):
        assert _extract_gen_hash("plain content without stamp") is None


# ---------------------------------------------------------------------------
# D1: conversions
# ---------------------------------------------------------------------------

class TestConversions:
    def test_agents_to_claude_returns_result(self):
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        assert isinstance(r, MigrateResult)
        assert r.target_format == FORMAT_CLAUDE_MD
        assert len(r.content) > 50

    def test_agents_to_claude_has_gen_comment(self):
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        assert "generated by agentkit migrate" in r.content

    def test_agents_to_llmstxt(self):
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_LLMSTXT)
        assert r.target_format == FORMAT_LLMSTXT
        assert "generated by agentkit migrate" in r.content

    def test_claude_to_agents(self):
        r = ENGINE.convert(CLAUDE_SAMPLE, FORMAT_CLAUDE_MD, FORMAT_AGENTS_MD)
        assert r.target_format == FORMAT_AGENTS_MD
        assert "generated by agentkit migrate" in r.content

    def test_claude_to_llmstxt(self):
        r = ENGINE.convert(CLAUDE_SAMPLE, FORMAT_CLAUDE_MD, FORMAT_LLMSTXT)
        assert r.target_format == FORMAT_LLMSTXT

    def test_llmstxt_to_claude(self):
        r = ENGINE.convert(LLMSTXT_SAMPLE, FORMAT_LLMSTXT, FORMAT_CLAUDE_MD)
        assert r.target_format == FORMAT_CLAUDE_MD
        assert "generated by agentkit migrate" in r.content

    def test_llmstxt_to_agents(self):
        r = ENGINE.convert(LLMSTXT_SAMPLE, FORMAT_LLMSTXT, FORMAT_AGENTS_MD)
        assert r.target_format == FORMAT_AGENTS_MD

    def test_unsupported_conversion_raises(self):
        with pytest.raises(ValueError, match="Unsupported conversion"):
            ENGINE.convert("content", "unknown-fmt", FORMAT_CLAUDE_MD)

    def test_line_count_populated(self):
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        assert r.line_count > 0

    def test_content_preserves_section_titles(self):
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        # Section titles should appear somewhere in output
        assert "Memory Rules" in r.content or "Context" in r.content

    def test_convert_all_returns_two_results(self):
        results = ENGINE.convert_all(AGENTS_SAMPLE, FORMAT_AGENTS_MD)
        assert len(results) == 2
        target_formats = {r.target_format for r in results}
        assert FORMAT_CLAUDE_MD in target_formats
        assert FORMAT_LLMSTXT in target_formats


# ---------------------------------------------------------------------------
# D1: staleness detection
# ---------------------------------------------------------------------------

class TestStaleness:
    def test_fresh_generated_not_stale(self):
        source = "original content"
        r = ENGINE.convert(source, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        assert not ENGINE.is_stale(source, r.content)

    def test_stale_if_source_changed(self):
        source = "original content"
        r = ENGINE.convert(source, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        new_source = "completely different content now"
        assert ENGINE.is_stale(new_source, r.content)

    def test_unmanaged_file_not_stale(self):
        assert not ENGINE.is_stale("anything", "no generation comment here")

    def test_get_sync_status_all_missing(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
        status = ENGINE.get_sync_status(tmp_path)
        assert status[FORMAT_AGENTS_MD] == "source"
        assert status[FORMAT_CLAUDE_MD] == "missing"
        assert status[FORMAT_LLMSTXT] == "missing"

    def test_get_sync_status_ok_after_generate(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
        # Generate CLAUDE.md
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        (tmp_path / "CLAUDE.md").write_text(r.content)
        status = ENGINE.get_sync_status(tmp_path)
        assert status[FORMAT_CLAUDE_MD] == "ok"

    def test_get_sync_status_stale_after_source_change(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
        r = ENGINE.convert(AGENTS_SAMPLE, FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD)
        (tmp_path / "CLAUDE.md").write_text(r.content)
        # Modify source
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE + "\n## New Section\nNew content.\n")
        status = ENGINE.get_sync_status(tmp_path)
        assert status[FORMAT_CLAUDE_MD] == "stale"

    def test_get_sync_status_unmanaged(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text(AGENTS_SAMPLE)
        (tmp_path / "CLAUDE.md").write_text("# Manual CLAUDE.md\n\nHandwritten, no stamp.\n")
        status = ENGINE.get_sync_status(tmp_path)
        assert status[FORMAT_CLAUDE_MD] == "unmanaged"

    def test_get_sync_status_empty_dir(self, tmp_path):
        status = ENGINE.get_sync_status(tmp_path)
        assert status == {}
