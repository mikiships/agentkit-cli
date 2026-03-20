"""agentkit user-rank command — rank top GitHub contributors for a topic by agent-readiness."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.user_rank import UserRankEngine
from agentkit_cli.user_rank_html import UserRankHTMLRenderer

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}


def user_rank_command(
    topic: str,
    limit: int = 20,
    json_output: bool = False,
    output: Optional[str] = None,
    share: bool = False,
    quiet: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
) -> None:
    """Discover top GitHub contributors for a topic and rank by agent-readiness."""
    topic = topic.strip()

    if not topic:
        if json_output:
            console.print(json.dumps({"error": "Topic is required."}))
        else:
            console.print("[red]Error:[/red] Topic is required.")
        raise typer.Exit(code=1)

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not resolved_token and not quiet and not json_output:
        console.print("[yellow]Warning:[/yellow] GITHUB_TOKEN not set. Rate limits may apply.")

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit user-rank[/bold] — ranking contributors for topic [bold]{topic}[/bold]")

    engine = UserRankEngine(
        topic=topic,
        limit=limit,
        token=resolved_token,
        timeout=timeout,
    )

    def _progress_cb(idx: int, total: int, username: str) -> None:
        if not quiet and not json_output:
            console.print(f"  [dim][{idx + 1}/{total}] scoring @{username}[/dim]")

    try:
        if not quiet and not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(f"Analyzing contributors for topic [bold]{topic}[/bold]…", total=None)
                result = engine.run(progress_callback=_progress_cb)
        else:
            result = engine.run(progress_callback=_progress_cb)
    except Exception as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Render HTML
    html: Optional[str] = None
    if share or output:
        renderer = UserRankHTMLRenderer()
        html = renderer.render(result)

    # --output: save HTML to file
    if output and html:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        if not quiet and not json_output:
            console.print(f"[dim]HTML saved to {output}[/dim]")

    # --share: publish to here.now
    share_url: Optional[str] = None
    if share:
        if html is None:
            renderer = UserRankHTMLRenderer()
            html = renderer.render(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url and not json_output and not quiet:
                console.print(f"\n[bold green]User-rank report published:[/bold green] {share_url}")
        except Exception as exc:
            if not json_output and not quiet:
                console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    # JSON output
    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        print(json.dumps(out, indent=2))
        return

    # Quiet: only share URL
    if quiet:
        if share_url:
            print(share_url)
        return

    # Rich terminal output
    _print_rich_summary(result, share_url=share_url)


def _print_rich_summary(result, share_url: Optional[str] = None) -> None:
    """Print rich terminal summary of user-rank result."""
    topic = result.topic

    console.print(
        f"\n[bold]🏆 State of Agent Readiness:[/bold] "
        f"[bold cyan]{topic}[/bold cyan]  "
        f"[dim]Mean Score {result.mean_score:.1f}/100[/dim]"
    )
    console.print(
        f"  [dim]{len(result.contributors)} contributors ranked[/dim]\n"
    )

    if not result.contributors:
        console.print("[yellow]No contributors found for this topic.[/yellow]")
        return

    table = Table(title=f"Top Contributors — {topic}", show_header=True, header_style="bold")
    table.add_column("Rank", width=5, justify="center")
    table.add_column("Contributor", style="cyan")
    table.add_column("Score", justify="right", width=8)
    table.add_column("Grade", justify="center", width=6)
    table.add_column("Top Repo", style="dim")

    for entry in result.contributors:
        gc = _GRADE_RICH.get(entry.grade, "white")
        top_mark = " 🏆" if entry.username == result.top_scorer else ""
        table.add_row(
            str(entry.rank),
            f"@{entry.username}{top_mark}",
            f"{entry.score:.1f}",
            f"[{gc}]{entry.grade}[/{gc}]",
            entry.top_repo or "—",
        )

    console.print(table)

    if result.top_scorer:
        console.print(f"\n[bold yellow]🏆 Top Scorer:[/bold yellow] [bold cyan]@{result.top_scorer}[/bold cyan]")

    # Grade distribution
    dist = result.grade_distribution
    dist_parts = [f"{g}:{dist.get(g, 0)}" for g in ("A", "B", "C", "D")]
    console.print(f"\n[dim]Grade distribution: {' | '.join(dist_parts)}[/dim]")

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
