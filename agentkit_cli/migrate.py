"""agentkit migrate compatibility layer backed by context projections."""
from __future__ import annotations

from pathlib import Path

from agentkit_cli.context_projections import (
    ContextProjectionEngine,
    ProjectionResult as MigrateResult,
    Section,
    FORMAT_AGENTS_MD,
    FORMAT_CLAUDE_MD,
    FORMAT_AGENT_MD,
    FORMAT_GEMINI_MD,
    FORMAT_COPILOT_MD,
    FORMAT_LLMSTXT,
    FORMAT_ALL,
    FORMAT_FILENAMES,
    FILENAME_FORMATS,
    _detect_format_from_content,
    _detect_format_from_filename,
    _parse_sections,
    _get_top_level_intro,
    _make_gen_stamp,
    _extract_gen_hash,
    _source_hash,
)

KNOWN_FORMATS = (FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD, FORMAT_LLMSTXT)


class MigrateEngine(ContextProjectionEngine):
    """Legacy migrate engine that preserves the original public surface."""

    def convert(self, source_content: str, source_format: str, target_format: str, source_path: str = "<source>", output_path: str = "<output>") -> MigrateResult:
        if source_format not in {FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD, FORMAT_LLMSTXT} or target_format not in {
            FORMAT_AGENTS_MD,
            FORMAT_CLAUDE_MD,
            FORMAT_LLMSTXT,
        }:
            raise ValueError(f"Unsupported conversion: {source_format} → {target_format}")
        return super().convert(source_content, source_format, target_format, source_path, output_path)

    def convert_all(self, source_content: str, source_format: str, source_path: str = "<source>", directory: str = ".") -> list[MigrateResult]:
        if source_format not in {FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD, FORMAT_LLMSTXT}:
            raise ValueError(f"Unsupported conversion: {source_format} → {FORMAT_ALL}")
        return [
            self.convert(source_content, source_format, target, source_path, str(Path(directory) / FORMAT_FILENAMES[target]))
            for target in KNOWN_FORMATS
            if target != source_format
        ]


__all__ = [
    "MigrateEngine",
    "MigrateResult",
    "Section",
    "FORMAT_AGENTS_MD",
    "FORMAT_CLAUDE_MD",
    "FORMAT_AGENT_MD",
    "FORMAT_GEMINI_MD",
    "FORMAT_COPILOT_MD",
    "FORMAT_LLMSTXT",
    "FORMAT_ALL",
    "KNOWN_FORMATS",
    "FORMAT_FILENAMES",
    "FILENAME_FORMATS",
    "_detect_format_from_content",
    "_detect_format_from_filename",
    "_parse_sections",
    "_get_top_level_intro",
    "_make_gen_stamp",
    "_extract_gen_hash",
    "_source_hash",
]
