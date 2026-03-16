"""agentkit duel command — head-to-head agent-readiness comparison."""
from __future__ import annotations

import json
from typing import Optional

from rich.console import Console
from rich.table import Table

from agentkit_cli.duel import run_duel, DuelResult
from agentkit_cli.duel_report import generate_duel_html, publish_duel

console = Console()


def duel_command(
    target1: str,
    target2: str,
    share: bool = False,
    json_output: bool = False,
    timeout: int = 120,
    keep: bool = False,
) -> None:
    """Run head-to-head agent-readiness comparison of two targets."""
    result = run_duel(target1, target2, keep=keep, timeout=timeout)

    share_url: Optional[str] = None
    if share:
        share_url = publish_duel(result)
        if share_url and not json_output:
            console.print(f"\n[bold green]Duel report published:[/bold green] {share_url}")

    if json_output:
        output = result.to_dict()
        if share_url:
            output["share_url"] = share_url
        console.print(json.dumps(output, indent=2))
        return

    _render_duel_table(result)

    if share_url:
        console.print(f"\n[bold green]Duel report:[/bold green] {share_url}")


def _render_duel_table(result: DuelResult) -> None:
    """Render side-by-side duel table to console."""
    left_name = result.left_repo_name or result.left_target.split("/")[-1]
    right_name = result.right_repo_name or result.right_target.split("/")[-1]

    console.print(f"\n[bold]agentkit duel[/bold] — {left_name} vs {right_name}\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric", style="dim")
    table.add_column(left_name, justify="right")
    table.add_column(right_name, justify="right")

    # Score row
    left_score_str = f"{result.left_score:.0f}" if result.left_score is not None else "—"
    right_score_str = f"{result.right_score:.0f}" if result.right_score is not None else "—"
    table.add_row("Score", left_score_str, right_score_str)

    # Grade row
    table.add_row("Grade", result.left_grade or "—", result.right_grade or "—")

    # Per-tool rows
    tools = ["agentmd", "agentlint", "coderace", "agentreflect"]
    for tool in tools:
        left_info = result.left_breakdown.get(tool)
        right_info = result.right_breakdown.get(tool)

        def _fmt(info: Optional[dict]) -> str:
            if info is None:
                return "—"
            score = info.get("score")
            if score is not None:
                try:
                    return str(int(round(float(score))))
                except (TypeError, ValueError):
                    pass
            status = info.get("status", "")
            return "✓" if status == "pass" else ("–" if status == "skipped" else "✗")

        table.add_row(tool, _fmt(left_info), _fmt(right_info))

    console.print(table)

    # Winner announcement
    if result.winner == "left":
        delta_str = f" by {int(round(result.delta))} pts" if result.delta is not None else ""
        console.print(f"\n[bold green]🏆 {left_name} wins{delta_str}[/bold green]")
    elif result.winner == "right":
        delta_str = f" by {int(round(result.delta))} pts" if result.delta is not None else ""
        console.print(f"\n[bold green]🏆 {right_name} wins{delta_str}[/bold green]")
    elif result.winner == "tie":
        delta_str = f" (delta: {result.delta:.1f})" if result.delta is not None else ""
        console.print(f"\n[bold yellow]🤝 Tie{delta_str} — within 5 points[/bold yellow]")
    else:
        console.print("\n[bold red]Both sides failed to analyze[/bold red]")

    if result.left_error:
        console.print(f"[red]Left error:[/red] {result.left_error}")
    if result.right_error:
        console.print(f"[red]Right error:[/red] {result.right_error}")
