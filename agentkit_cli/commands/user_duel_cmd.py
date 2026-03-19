"""agentkit user-duel command — head-to-head agent-readiness comparison for two GitHub users."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.user_duel import UserDuelEngine, UserDuelResult, publish_user_duel

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red"}


def user_duel_command(
    user1: str,
    user2: str,
    limit: int = 10,
    json_output: bool = False,
    share: bool = False,
    quiet: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    _engine_factory=None,
) -> None:
    """Head-to-head agent-readiness comparison of two GitHub users."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not quiet and not json_output:
        console.print(f"\n[bold]⚔️  Agent Readiness Duel[/bold] — [bold cyan]@{user1}[/bold cyan] vs [bold cyan]@{user2}[/bold cyan]")
        console.print(f"  [dim]Analyzing up to {limit} repos per user…[/dim]\n")

    engine = UserDuelEngine(
        limit=limit,
        token=resolved_token,
        timeout=timeout,
        _engine_factory=_engine_factory,
    )

    def _progress_cb(username: str, full_name: str, score_str: str) -> None:
        if not quiet and not json_output:
            console.print(f"  [dim][@{username}] {full_name} → {score_str}/100[/dim]")

    try:
        result = engine.run(user1=user1, user2=user2, progress_callback=_progress_cb)
    except ValueError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    share_url: Optional[str] = None
    if share:
        share_url = publish_user_duel(result)
        if share_url and not json_output and not quiet:
            console.print(f"\n[bold green]Duel report published:[/bold green] {share_url}")

    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        console.print(json.dumps(out, indent=2))
        return

    if quiet:
        if result.tied:
            print(f"tie: @{user1} and @{user2} are tied")
        elif result.overall_winner == "user1":
            print(f"winner: @{user1}")
        else:
            print(f"winner: @{user2}")
        if share_url:
            print(share_url)
        return

    _render_rich_table(result)
    if share_url:
        console.print(f"\n[bold green]Duel report:[/bold green] {share_url}")


def _render_rich_table(result: UserDuelResult) -> None:
    """Render the side-by-side duel table."""
    u1 = result.user1
    u2 = result.user2
    s1 = result.user1_scorecard
    s2 = result.user2_scorecard

    table = Table(show_header=True, header_style="bold", title="⚔️  Agent Readiness Duel")
    table.add_column("Dimension", style="dim")
    table.add_column(f"@{u1}", justify="right")
    table.add_column(f"@{u2}", justify="right")
    table.add_column("Winner", justify="center")

    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red"}

    for dim in result.dimensions:
        from agentkit_cli.user_duel import _fmt_dim_value
        v1 = _fmt_dim_value(dim.name, dim.user1_value)
        v2 = _fmt_dim_value(dim.name, dim.user2_value)
        if dim.winner == "user1":
            v1_str = f"[bold green]{v1}[/bold green]"
            v2_str = f"[dim]{v2}[/dim]"
            winner_str = f"[green]@{u1}[/green]"
        elif dim.winner == "user2":
            v1_str = f"[dim]{v1}[/dim]"
            v2_str = f"[bold green]{v2}[/bold green]"
            winner_str = f"[green]@{u2}[/green]"
        else:
            v1_str = f"[yellow]{v1}[/yellow]"
            v2_str = f"[yellow]{v2}[/yellow]"
            winner_str = "[yellow]tie[/yellow]"
        table.add_row(dim.name.replace("_", " ").title(), v1_str, v2_str, winner_str)

    console.print(table)

    # Verdict banner
    if result.tied:
        console.print(f"\n[bold yellow]🤝 Tied![/bold yellow]  @{u1} and @{u2} are evenly matched.\n")
    elif result.overall_winner == "user1":
        gc = grade_colors.get(s1.grade, "white")
        console.print(f"\n[bold green]🏆 @{u1} wins![/bold green]  Grade [{gc}]{s1.grade}[/{gc}] · avg {s1.avg_score:.1f}\n")
    else:
        gc = grade_colors.get(s2.grade, "white")
        console.print(f"\n[bold green]🏆 @{u2} wins![/bold green]  Grade [{gc}]{s2.grade}[/{gc}] · avg {s2.avg_score:.1f}\n")
