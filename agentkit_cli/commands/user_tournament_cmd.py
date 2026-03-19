"""agentkit user-tournament command — bracket-style developer agent-readiness tournament."""
from __future__ import annotations

import json
import os
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.engines.user_tournament import UserTournamentEngine, TournamentResult
from agentkit_cli.renderers.user_tournament_report import UserTournamentReportRenderer, publish_user_tournament

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red"}


def user_tournament_command(
    participants: List[str],
    share: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    output: Optional[str] = None,
    limit: int = 10,
    timeout: int = 60,
    token: Optional[str] = None,
    _duel_engine_factory=None,
) -> None:
    """Bracket-style agent-readiness tournament for N GitHub users."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if len(participants) < 2:
        if json_output:
            console.print(json.dumps({"error": "Tournament requires at least 2 participants."}))
        else:
            console.print("[red]Error:[/red] Tournament requires at least 2 participants.")
        raise typer.Exit(code=1)

    if not quiet and not json_output:
        console.print(f"\n[bold]🏆  Developer Agent-Readiness Tournament[/bold]")
        console.print(f"  Participants: {', '.join('@' + p for p in participants)}")
        console.print(f"  Mode: {'bracket' if len(participants) > 8 else 'round-robin'}\n")

    match_count = [0]
    total_matches = len(participants) * (len(participants) - 1) // 2

    def _progress(idx: int, total: int, u1: str, u2: str) -> None:
        match_count[0] = idx + 1
        if not quiet and not json_output:
            console.print(f"  [dim][{idx + 1}/{total}] @{u1} vs @{u2}[/dim]")

    engine = UserTournamentEngine(
        limit=limit,
        token=resolved_token,
        timeout=timeout,
        _duel_engine_factory=_duel_engine_factory,
    )

    try:
        result = engine.run(participants=participants, progress_callback=_progress)
    except ValueError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Render HTML if needed
    html: Optional[str] = None
    if share or output:
        html = UserTournamentReportRenderer().render(result)

    share_url: Optional[str] = None
    if share:
        share_url = publish_user_tournament(result)
        if share_url and not json_output and not quiet:
            console.print(f"\n[bold green]Tournament report published:[/bold green] {share_url}")

    if output and html:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        if not quiet and not json_output:
            console.print(f"[dim]HTML saved to {output}[/dim]")

    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        console.print(json.dumps(out, indent=2))
        return

    if quiet:
        print(f"champion: @{result.champion}")
        if share_url:
            print(share_url)
        return

    # Rich standings table
    console.print()
    table = Table(title="🏆 Tournament Standings", show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="bold", width=6)
    table.add_column("Handle", style="cyan")
    table.add_column("W-L", width=8)
    table.add_column("Avg Score", width=10)
    table.add_column("Grade", width=7)

    for s in result.standings:
        grade_color = _GRADE_RICH.get(s.grade, "white")
        table.add_row(
            f"#{s.rank}",
            f"@{s.handle}",
            s.record(),
            f"{s.avg_score:.1f}",
            f"[{grade_color}]{s.grade}[/{grade_color}]",
        )

    console.print(table)
    console.print(f"\n[bold yellow]🏆 Champion:[/bold yellow] [bold cyan]@{result.champion}[/bold cyan]\n")
