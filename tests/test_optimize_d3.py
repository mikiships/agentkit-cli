from __future__ import annotations

from pathlib import Path

from agentkit_cli.models import OptimizeFinding, OptimizeResult, OptimizeStats, OptimizationAction
from agentkit_cli.renderers.optimize_renderer import OptimizeRenderer


def _result() -> OptimizeResult:
    return OptimizeResult(
        source_file="/tmp/CLAUDE.md",
        original_text="# Project\n\nold line\n",
        optimized_text="# Project\n\nnew line\n",
        original_stats=OptimizeStats(lines=3, estimated_tokens=4),
        optimized_stats=OptimizeStats(lines=3, estimated_tokens=3),
        findings=[OptimizeFinding(kind="bloat", severity="medium", message="Repeated line")],
        actions=[OptimizationAction(kind="compress-section", description="Compressed workflow", lines_affected=2)],
        preserved_sections=["Project"],
        removed_bloat=["Workflow"],
        warnings=["medium: Repeated line"],
    )


def test_markdown_renderer_includes_diff_and_sections():
    output = OptimizeRenderer().render(_result(), fmt="markdown")
    assert "## Unified diff" in output
    assert "```diff" in output
    assert "-old line" in output
    assert "+new line" in output
    assert "## Top removed bloat" in output


def test_text_renderer_is_reviewable():
    output = OptimizeRenderer().render(_result(), fmt="text")
    assert "agentkit optimize:" in output
    assert "Preserved:" in output
    assert "Top removed bloat:" in output
    assert "Warnings:" in output
