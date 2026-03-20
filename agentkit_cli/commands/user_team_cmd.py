"""agentkit user-team command — analyze a GitHub org's top contributors for agent-readiness."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.user_team import TeamScorecardEngine
from agentkit_cli.user_team_html import TeamScorecardHTMLRenderer

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}


def user_team_command(
    target: str,
    limit: int = 10,
    json_output: bool = False,
    output: Optional[str] = None,
    share: bool = False,
    quiet: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
) -> None:
    """Analyze a GitHub org's top contributors and produce a ranked team scorecard."""
    # Parse github:<org> prefix
    if target.startswith("github:"):
        org = target[len("github:"):]
    else:
        org = target

    org = org.strip("/").strip()

    if not org:
        if json_output:
            console.print(json.dumps({"error": "Org name is required. Use github:<org> or bare <org>."}))
        else:
            console.print("[red]Error:[/red] Org name is required. Use github:<org> or bare <org>.")
        raise typer.Exit(code=1)

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not resolved_token and not quiet and not json_output:
        console.print("[yellow]Warning:[/yellow] GITHUB_TOKEN not set. Rate limits may apply.")

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit user-team[/bold] — team scorecard for [bold]{org}[/bold]")

    engine = TeamScorecardEngine(
        org=org,
        limit=limit,
        token=resolved_token,
        timeout=timeout,
    )

    contributor_idx = [0]

    def _progress_cb(idx: int, total: int, username: str) -> None:
        contributor_idx[0] = idx + 1
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
                progress.add_task(f"Analyzing contributors for [bold]{org}[/bold]…", total=None)
                result = engine.run(progress_callback=_progress_cb)
        else:
            result = engine.run(progress_callback=_progress_cb)
    except ValueError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Render HTML
    html: Optional[str] = None
    if share or output:
        renderer = TeamScorecardHTMLRenderer()
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
            renderer = TeamScorecardHTMLRenderer()
            html = renderer.render(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url and not json_output and not quiet:
                console.print(f"\n[bold green]Team scorecard published:[/bold green] {share_url}")
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
    """Print rich terminal summary of team scorecard result."""
    org = result.org
    grade = result.aggregate_grade
    grade_color = _GRADE_RICH.get(grade, "white")

    console.print(
        f"\n[bold]🏢 Team Agent-Readiness Scorecard:[/bold] "
        f"[bold cyan]{org}[/bold cyan]  "
        f"[bold {grade_color}]Grade {grade}[/bold {grade_color}]  "
        f"[dim]Score {result.aggregate_score:.1f}/100[/dim]"
    )
    console.print(
        f"  [dim]{result.contributor_count} contributors analyzed[/dim]\n"
    )

    if not result.contributor_results:
        console.print("[yellow]No contributors found.[/yellow]")
        return

    # Ranked contributor table
    sorted_results = sorted(result.contributor_results, key=lambda r: r.avg_score, reverse=True)
    table = Table(title="Team Rankings", show_header=True, header_style="bold")
    table.add_column("Rank", width=5, justify="center")
    table.add_column("Contributor", style="cyan")
    table.add_column("Score", justify="right", width=8)
    table.add_column("Grade", justify="center", width=6)
    table.add_column("Repos", justify="right", width=6)

    for rank, r in enumerate(sorted_results, 1):
        gc = _GRADE_RICH.get(r.grade, "white")
        top_mark = " 🏆" if r.username == result.top_scorer else ""
        table.add_row(
            str(rank),
            f"@{r.username}{top_mark}",
            f"{r.avg_score:.1f}",
            f"[{gc}]{r.grade}[/{gc}]",
            str(r.analyzed_repos),
        )

    console.print(table)

    if result.top_scorer:
        console.print(f"\n[bold yellow]🏆 Top Scorer:[/bold yellow] [bold cyan]@{result.top_scorer}[/bold cyan]")

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
