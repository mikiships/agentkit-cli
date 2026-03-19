"""agentkit pages-org — publish an org-wide GitHub Pages leaderboard."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.engines.org_pages import OrgPagesEngine

console = Console()


def pages_org_command(
    target: str,
    pages_repo: Optional[str] = None,
    pages_path: str = "docs/",
    pages_branch: str = "main",
    only_below: Optional[int] = None,
    limit: int = 50,
    json_output: bool = False,
    quiet: bool = False,
    dry_run: bool = False,
    token: Optional[str] = None,
) -> None:
    """Score all public repos in a GitHub org and publish an org-wide leaderboard to GitHub Pages."""
    # Parse github:<owner> format
    if target.startswith("github:"):
        org = target[len("github:"):]
    else:
        org = target

    if not org:
        console.print("[red]Error:[/red] Provide a target like 'github:vercel'")
        raise typer.Exit(code=1)

    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    if not resolved_token and not dry_run:
        console.print("[red]Error:[/red] GITHUB_TOKEN is required. Set the env var or use --token.")
        raise typer.Exit(code=1)

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit pages-org[/bold] — org: [bold]{org}[/bold]")
        if dry_run:
            console.print("[yellow](dry-run: git push will be skipped)[/yellow]")

    # Score repos (with optional progress indicator)
    engine = OrgPagesEngine(
        org=org,
        pages_repo=pages_repo,
        pages_path=pages_path,
        pages_branch=pages_branch,
        only_below=only_below,
        limit=limit,
        dry_run=dry_run,
        token=resolved_token,
    )

    if not quiet and not json_output:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Scoring repos in [bold]{org}[/bold]…", total=None)
            result = engine.run()
    else:
        result = engine.run()

    # Output
    if json_output:
        out = {
            "org": org,
            "pages_url": result.pages_url,
            "repos_scored": result.repos_scored,
            "avg_score": result.avg_score,
            "top_repo": result.top_repo,
            "published": result.published,
        }
        if result.error:
            out["error"] = result.error
        print(json.dumps(out, indent=2))
        return

    if quiet:
        print(result.pages_url)
        return

    # Rich summary table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Org", org)
    table.add_row("Repos Scored", str(result.repos_scored))
    table.add_row("Avg Score", f"{result.avg_score:.1f}")
    table.add_row("Top Repo", result.top_repo)
    if dry_run:
        table.add_row("Status", "[yellow]dry-run (not published)[/yellow]")
    elif result.published:
        table.add_row("Status", "[green]Published[/green]")
    else:
        table.add_row("Status", f"[red]Failed[/red]: {result.error or 'unknown error'}")
    table.add_row("Pages URL", result.pages_url)
    console.print(table)

    if result.published and not dry_run:
        console.print(f"\n[bold green]Org leaderboard (permanent):[/bold green] {result.pages_url}")
    elif result.error:
        console.print(f"\n[yellow]Warning: publish failed ({result.error})[/yellow]")
