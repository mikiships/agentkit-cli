"""Render optimize results as markdown or plain text."""
from __future__ import annotations

from difflib import unified_diff

from agentkit_cli.models import OptimizeResult


class OptimizeRenderer:
    def render(self, result: OptimizeResult, *, fmt: str = "text") -> str:
        if fmt == "markdown":
            return self._markdown(result)
        return self._text(result)

    def _text(self, result: OptimizeResult) -> str:
        lines = [
            f"agentkit optimize: {result.source_file}",
            f"Lines: {result.original_stats.lines} -> {result.optimized_stats.lines} ({result.line_delta:+d})",
            f"Tokens: {result.original_stats.estimated_tokens} -> {result.optimized_stats.estimated_tokens} ({result.token_delta:+d})",
            "",
            "Preserved:",
            *[f"- {item}" for item in (result.preserved_sections or ["None"])],
            "",
            "Top removed bloat:",
            *[f"- {item}" for item in (result.removed_bloat or ["None"])],
            "",
            "Warnings:",
            *[f"- {item}" for item in (result.warnings or ["None"])],
            "",
            "Diff:",
            self._diff_block(result),
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _markdown(self, result: OptimizeResult) -> str:
        lines = [
            f"# agentkit optimize",
            "",
            f"**File:** `{result.source_file}`",
            "",
            "## Stats",
            "",
            "| Metric | Original | Optimized | Delta |",
            "|---|---:|---:|---:|",
            f"| Lines | {result.original_stats.lines} | {result.optimized_stats.lines} | {result.line_delta:+d} |",
            f"| Estimated tokens | {result.original_stats.estimated_tokens} | {result.optimized_stats.estimated_tokens} | {result.token_delta:+d} |",
            "",
            "## Preserved high-signal sections",
            *[f"- {item}" for item in (result.preserved_sections or ["None"])],
            "",
            "## Top removed bloat",
            *[f"- {item}" for item in (result.removed_bloat or ["None"])],
            "",
            "## Warnings",
            *[f"- {item}" for item in (result.warnings or ["None"])],
            "",
            "## Unified diff",
            "",
            "```diff",
            self._diff(result),
            "```",
            "",
        ]
        return "\n".join(lines)

    def _diff_block(self, result: OptimizeResult) -> str:
        return self._diff(result)

    def _diff(self, result: OptimizeResult) -> str:
        diff = unified_diff(
            result.original_text.splitlines(),
            result.optimized_text.splitlines(),
            fromfile="original",
            tofile="optimized",
            lineterm="",
        )
        text = "\n".join(diff)
        return text or "(no changes)"
