"""agentkit repo-duel command — head-to-head agent-readiness comparison for two GitHub repos."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.repo_duel import RepoDuelEngine, RepoDuelResult

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}


def repo_duel_command(
    repo1: str,
    repo2: str,
    deep: bool = False,
    json_output: bool = False,
    share: bool = False,
    output: Optional[str] = None,
    quiet: bool = False,
    timeout: int = 120,
    token: Optional[str] = None,
    _analyze_factory=None,
) -> None:
    """Head-to-head agent-readiness comparison of two GitHub repos."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not quiet and not json_output:
        console.print(
            f"\n[bold]⚔️  Repo Duel[/bold] — "
            f"[bold cyan]{repo1}[/bold cyan] vs [bold cyan]{repo2}[/bold cyan]"
        )
        if deep:
            console.print("  [dim]Deep mode: redteam dimension included[/dim]")
        console.print()

    engine = RepoDuelEngine(
        token=resolved_token,
        timeout=timeout,
        _analyze_factory=_analyze_factory,
    )

    try:
        result = engine.run_duel(repo1=repo1, repo2=repo2, deep=deep)
    except Exception as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Render HTML for --output / --share
    html: Optional[str] = None
    if share or output:
        from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html
        html = render_repo_duel_html(result)

    if output and html:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        if not quiet and not json_output:
            console.print(f"[dim]HTML saved to {output}[/dim]")

    share_url: Optional[str] = None
    if share:
        if html is None:
            from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html
            html = render_repo_duel_html(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            result.share_url = share_url
            if share_url and not json_output and not quiet:
                console.print(f"\n[bold green]Repo duel report published:[/bold green] {share_url}")
        except Exception as exc:
            if not json_output and not quiet:
                console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    # Save to history DB
    try:
        from agentkit_cli.history import HistoryDB
        db = HistoryDB()
        db.record_run(
            project=f"{repo1}__vs__{repo2}",
            tool="repo_duel",
            score=result.repo1_score,
            label="repo_duel",
        )
    except Exception:
        pass  # history is best-effort

    if json_output:
        out = result.to_dict()
        print(json.dumps(out, indent=2))
        return

    if quiet:
        if result.winner == "draw":
            print(f"draw: {repo1} and {repo2} are evenly matched")
        elif result.winner == "repo1":
            print(f"winner: {repo1}")
        else:
            print(f"winner: {repo2}")
        if share_url:
            print(share_url)
        return

    _render_rich_table(result)
    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")


def _render_rich_table(result: RepoDuelResult) -> None:
    """Render the side-by-side duel table in the terminal."""
    r1 = result.repo1
    r2 = result.repo2
    gc1 = _GRADE_RICH.get(result.repo1_grade, "white")
    gc2 = _GRADE_RICH.get(result.repo2_grade, "white")

    # Header summary
    console.print(
        f"  [{gc1}]{r1}[/{gc1}]  [{gc1}]{result.repo1_grade}[/{gc1}] · {result.repo1_score:.1f}"
    )
    console.print(
        f"  [{gc2}]{r2}[/{gc2}]  [{gc2}]{result.repo2_grade}[/{gc2}] · {result.repo2_score:.1f}"
    )
    console.print()

    table = Table(show_header=True, header_style="bold", title="⚔️  Repo Duel Dimensions")
    table.add_column("Dimension", style="dim")
    table.add_column(r1, justify="right")
    table.add_column("Winner", justify="center")
    table.add_column(r2, justify="right")

    for dim in result.dimension_results:
        v1 = f"{dim.repo1_value:.1f}"
        v2 = f"{dim.repo2_value:.1f}"
        if dim.winner == "repo1":
            v1_str = f"[bold green]{v1}[/bold green]"
            v2_str = f"[dim]{v2}[/dim]"
            w_str = f"[green]{r1}[/green]"
        elif dim.winner == "repo2":
            v1_str = f"[dim]{v1}[/dim]"
            v2_str = f"[bold green]{v2}[/bold green]"
            w_str = f"[green]{r2}[/green]"
        else:
            v1_str = f"[yellow]{v1}[/yellow]"
            v2_str = f"[yellow]{v2}[/yellow]"
            w_str = "[yellow]draw[/yellow]"
        table.add_row(dim.name.replace("_", " ").title(), v1_str, w_str, v2_str)

    console.print(table)

    # Verdict banner
    if result.winner == "draw":
        console.print(f"\n[bold yellow]🤝 Draw![/bold yellow]  {r1} and {r2} are evenly matched.\n")
    elif result.winner == "repo1":
        gc = _GRADE_RICH.get(result.repo1_grade, "white")
        console.print(
            f"\n[bold green]🏆 {r1} wins![/bold green]  "
            f"Grade [{gc}]{result.repo1_grade}[/{gc}] · {result.repo1_score:.1f}\n"
        )
    else:
        gc = _GRADE_RICH.get(result.repo2_grade, "white")
        console.print(
            f"\n[bold green]🏆 {r2} wins![/bold green]  "
            f"Grade [{gc}]{result.repo2_grade}[/{gc}] · {result.repo2_score:.1f}\n"
        )
