"""agentkit tournament command — round-robin bracket across N repos."""
from __future__ import annotations

import json
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table

from agentkit_cli.tournament import TournamentResult, run_tournament
from agentkit_cli.tournament_report import generate_tournament_html, publish_tournament

console = Console()


def tournament_command(
    repos: list[str],
    share: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    parallel: bool = True,
    min_repos: int = 4,
    max_repos: int = 16,
    output: Optional[str] = None,
    timeout: int = 120,
    keep: bool = False,
) -> None:
    """Run round-robin tournament across N repos."""
    if len(repos) < min_repos:
        console.print(
            f"[red]Error:[/red] Tournament requires at least {min_repos} repos, got {len(repos)}.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if len(repos) > max_repos:
        console.print(
            f"[red]Error:[/red] Tournament supports at most {max_repos} repos, got {len(repos)}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not quiet and not json_output:
        console.print(
            f"\n[bold]agentkit tournament[/bold] — {len(repos)} repos, "
            f"{len(repos) * (len(repos) - 1) // 2} duels\n"
        )

    result = run_tournament(
        repos=repos,
        parallel=parallel,
        keep=keep,
        timeout=timeout,
        quiet=quiet,
    )

    # Generate HTML
    html = generate_tournament_html(result)

    # Write HTML to file if --output
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        if not quiet and not json_output:
            console.print(f"[bold green]Report written:[/bold green] {output}")

    # Share
    share_url: Optional[str] = None
    if share:
        share_url = publish_tournament(result)
        if share_url and not json_output and not quiet:
            console.print(f"\n[bold green]Tournament report published:[/bold green] {share_url}")

    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        console.print(json.dumps(out, indent=2))
        return

    if not quiet:
        _render_standings_table(result)

    if share_url and not json_output:
        console.print(f"\n[bold green]Tournament report:[/bold green] {share_url}")


def _render_standings_table(result: TournamentResult) -> None:
    """Render standings table to console."""
    console.print(f"\n[bold]Tournament Results[/bold] — {result.total_duels} duels\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Repo")
    table.add_column("W-L", justify="center")
    table.add_column("Avg Score", justify="right")
    table.add_column("Grade", justify="center")

    def _grade(avg: float) -> str:
        if avg >= 90:
            return "A"
        if avg >= 80:
            return "B"
        if avg >= 70:
            return "C"
        if avg >= 60:
            return "D"
        return "F"

    for s in result.standings:
        trophy = "🏆 " if s.rank == 1 else ""
        short = s.repo.split("/")[-1]
        g = _grade(s.avg_score)
        table.add_row(
            str(s.rank),
            f"{trophy}{short}",
            f"{s.wins}-{s.losses}",
            f"{s.avg_score:.1f}",
            g,
        )

    console.print(table)

    winner_short = result.winner.split("/")[-1]
    console.print(f"\n[bold green]🏆 Tournament winner: {winner_short}[/bold green]")
