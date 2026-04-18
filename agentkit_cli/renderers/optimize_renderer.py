"""Render optimize results as markdown or plain text."""
from __future__ import annotations

from difflib import unified_diff

from agentkit_cli.models import OptimizeResult, OptimizeSweepResult


class OptimizeRenderer:
    MAX_DIFF_LINES = 80

    def render(self, result: OptimizeResult | OptimizeSweepResult, *, fmt: str = "text") -> str:
        if isinstance(result, OptimizeSweepResult):
            if fmt == "markdown":
                return self._markdown_sweep(result)
            return self._text_sweep(result)
        if fmt == "markdown":
            return self._markdown(result)
        return self._text(result)

    def _text(self, result: OptimizeResult) -> str:
        lines = [
            f"agentkit optimize: {result.source_file}",
            f"Verdict: {result.verdict}",
            f"Lines: {result.original_stats.lines} -> {result.optimized_stats.lines} ({result.line_delta:+d})",
            f"Tokens: {result.original_stats.estimated_tokens} -> {result.optimized_stats.estimated_tokens} ({result.token_delta:+d})",
            "",
            "Protected sections preserved:",
            *[f"- {item}" for item in (result.protected_sections or ["None"])],
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
            self._diff(result),
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _markdown(self, result: OptimizeResult) -> str:
        lines = [
            "# agentkit optimize",
            "",
            f"**File:** `{result.source_file}`",
            "",
            "## Verdict",
            "",
            f"**{result.verdict}**",
            "",
            "## Stats",
            "",
            "| Metric | Original | Optimized | Delta |",
            "|---|---:|---:|---:|",
            f"| Lines | {result.original_stats.lines} | {result.optimized_stats.lines} | {result.line_delta:+d} |",
            f"| Estimated tokens | {result.original_stats.estimated_tokens} | {result.optimized_stats.estimated_tokens} | {result.token_delta:+d} |",
            "",
            "## Protected sections preserved",
            *[f"- {item}" for item in (result.protected_sections or ["None"])],
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

    def _text_sweep(self, result: OptimizeSweepResult) -> str:
        lines = [
            f"agentkit optimize sweep: {result.root}",
            f"Verdict: {result.verdict}",
            f"Files: {result.summary.total_files} total, {result.summary.rewritable_files} rewritable, {result.summary.noop_files} no-op",
            f"Totals: lines {result.summary.total_line_delta:+d}, tokens {result.summary.total_token_delta:+d}, warnings {result.summary.warnings_count}",
            "",
            "Per-file summary:",
        ]
        if not result.results:
            lines.append("- No CLAUDE.md or AGENTS.md files found")
        for item in result.results:
            rel = item.source_file
            lines.extend([
                f"- {rel}",
                f"  Verdict: {item.verdict}",
                f"  Delta: lines {item.line_delta:+d}, tokens {item.token_delta:+d}",
                f"  Protected: {', '.join(item.protected_sections) if item.protected_sections else 'None'}",
                f"  Removed bloat: {', '.join(item.removed_bloat) if item.removed_bloat else 'None'}",
                f"  Warnings: {', '.join(item.warnings) if item.warnings else 'None'}",
            ])
        return "\n".join(lines).rstrip() + "\n"

    def _markdown_sweep(self, result: OptimizeSweepResult) -> str:
        lines = [
            "# agentkit optimize sweep",
            "",
            f"**Root:** `{result.root}`",
            "",
            "## Verdict",
            "",
            f"**{result.verdict}**",
            "",
            "## Totals",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Files scanned | {result.summary.total_files} |",
            f"| Rewritable files | {result.summary.rewritable_files} |",
            f"| Safe no-op files | {result.summary.noop_files} |",
            f"| Total line delta | {result.summary.total_line_delta:+d} |",
            f"| Total token delta | {result.summary.total_token_delta:+d} |",
            f"| Warning count | {result.summary.warnings_count} |",
            "",
        ]
        for item in result.results:
            lines.extend([
                f"## `{item.source_file}`",
                "",
                f"- Verdict: **{item.verdict}**",
                f"- Line delta: {item.line_delta:+d}",
                f"- Token delta: {item.token_delta:+d}",
                f"- Protected sections: {', '.join(item.protected_sections) if item.protected_sections else 'None'}",
                f"- Top removed bloat: {', '.join(item.removed_bloat) if item.removed_bloat else 'None'}",
                f"- Warnings: {', '.join(item.warnings) if item.warnings else 'None'}",
                "",
            ])
        if not result.results:
            lines.extend(["No CLAUDE.md or AGENTS.md files found.", ""])
        return "\n".join(lines)

    def _diff(self, result: OptimizeResult) -> str:
        diff = unified_diff(
            result.original_text.splitlines(),
            result.optimized_text.splitlines(),
            fromfile="original",
            tofile="optimized",
            lineterm="",
        )
        text = "\n".join(diff)
        if not text:
            return "(no changes)"
        diff_lines = text.splitlines()
        if len(diff_lines) <= self.MAX_DIFF_LINES:
            return text
        head = diff_lines[:50]
        tail = diff_lines[-20:]
        omitted = len(diff_lines) - len(head) - len(tail)
        return "\n".join(head + [f"... diff truncated, omitted {omitted} lines ..."] + tail)
