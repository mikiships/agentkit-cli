from __future__ import annotations

from agentkit_cli.models import (
    OptimizeFinding,
    OptimizeResult,
    OptimizeStats,
    OptimizationAction,
    OptimizeSweepResult,
    OptimizeSweepSummary,
)
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
        protected_sections=["Project", "Safety"],
        removed_bloat=["Workflow"],
        warnings=["medium: Repeated line"],
        no_op=False,
    )


def test_markdown_renderer_includes_diff_and_sections():
    output = OptimizeRenderer().render(_result(), fmt="markdown")
    assert "## Verdict" in output
    assert "## Protected sections preserved" in output
    assert "## Unified diff" in output
    assert "```diff" in output
    assert "-old line" in output
    assert "+new line" in output
    assert "## Top removed bloat" in output


def test_text_renderer_is_reviewable():
    output = OptimizeRenderer().render(_result(), fmt="text")
    assert "agentkit optimize:" in output
    assert "Verdict: Meaningful rewrite available" in output
    assert "Protected sections preserved:" in output
    assert "Preserved:" in output
    assert "Top removed bloat:" in output
    assert "Warnings:" in output


def test_renderer_truncates_large_diffs():
    result = _result()
    result.original_text = "\n".join([f"line {i}" for i in range(120)]) + "\n"
    result.optimized_text = "\n".join([f"line {i} updated" for i in range(120)]) + "\n"

    output = OptimizeRenderer().render(result, fmt="text")

    assert "diff truncated, omitted" in output


def test_sweep_renderer_includes_aggregate_sections():
    sweep = OptimizeSweepResult(
        root="/tmp/repo",
        results=[_result()],
        summary=OptimizeSweepSummary(
            total_files=1,
            rewritable_files=1,
            noop_files=0,
            total_line_delta=-1,
            total_token_delta=-1,
            protected_signal_files=1,
            warnings_count=1,
        ),
    )

    text_output = OptimizeRenderer().render(sweep, fmt="text")
    markdown_output = OptimizeRenderer().render(sweep, fmt="markdown")

    assert "agentkit optimize sweep:" in text_output
    assert "Per-file summary:" in text_output
    assert "# agentkit optimize sweep" in markdown_output
    assert "## Totals" in markdown_output
    assert "## `/tmp/CLAUDE.md`" in markdown_output
