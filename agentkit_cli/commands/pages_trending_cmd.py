"""agentkit pages-trending — fetch trending repos, score them, publish to GitHub Pages."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.engines.trending_pages import TrendingPagesEngine

console = Console()

_VALID_PERIODS = ("today", "week", "month")


def pages_trending_command(
    pages_repo: Optional[str] = None,
    limit: int = 20,
    language: Optional[str] = None,
    period: str = "today",
    dry_run: bool = False,
    quiet: bool = False,
    share: bool = False,
    json_output: bool = False,
    token: Optional[str] = None,
) -> None:
    """Fetch trending GitHub repos, score them with agentkit, publish leaderboard to GitHub Pages."""
    # Validate period
    if period not in _VALID_PERIODS:
        console.print(f"[red]Error:[/red] --period must be one of: {', '.join(_VALID_PERIODS)}")
        raise typer.Exit(code=1)

    # Validate limit
    if limit < 1 or limit > 50:
        console.print("[red]Error:[/red] --limit must be between 1 and 50")
        raise typer.Exit(code=1)

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    # Resolve pages_repo
    if pages_repo is None:
        pages_repo = _detect_pages_repo(resolved_token)

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit pages-trending[/bold]")
        console.print(f"  period: {period}, limit: {limit}" + (f", language: {language}" if language else ""))
        console.print(f"  pages-repo: {pages_repo}")
        if dry_run:
            console.print("[yellow](dry-run: git push will be skipped)[/yellow]")

    engine = TrendingPagesEngine(
        pages_repo=pages_repo,
        limit=limit,
        language=language,
        period=period,
        dry_run=dry_run,
        share=share,
        token=resolved_token,
    )

    if not quiet and not json_output:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Fetching and scoring trending repos…", total=None)
            result = engine.run()
    else:
        result = engine.run()

    # Output
    if json_output:
        out = {
            "pages_repo": pages_repo,
            "pages_url": result.pages_url,
            "repos_scored": result.repos_scored,
            "period": result.period,
            "language": result.language,
            "published": result.published,
        }
        if result.error:
            out["error"] = result.error
        if result.share_url:
            out["share_url"] = result.share_url
        print(json.dumps(out, indent=2))
        return

    if quiet:
        print(result.pages_url)
        return

    # Rich summary
    table = Table(show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Pages Repo", pages_repo)
    table.add_row("Period", period)
    table.add_row("Language", language or "all")
    table.add_row("Repos Scored", str(result.repos_scored))
    if dry_run:
        table.add_row("Status", "[yellow]dry-run (not published)[/yellow]")
    elif result.published:
        table.add_row("Status", "[green]Published[/green]")
    else:
        table.add_row("Status", f"[red]Failed[/red]: {result.error or 'unknown error'}")
    table.add_row("Pages URL", result.pages_url)
    if result.share_url:
        table.add_row("Share URL (24h)", result.share_url)
    console.print(table)

    if result.published and not dry_run:
        console.print(f"\n[bold green]Trending leaderboard (permanent):[/bold green] {result.pages_url}")
        if result.share_url:
            console.print(f"[bold cyan]Preview (24h):[/bold cyan] {result.share_url}")
    elif result.error:
        console.print(f"\n[yellow]Warning: publish failed ({result.error})[/yellow]")
    elif dry_run:
        console.print(f"\n[dim]Dry-run complete. Would publish to: {result.pages_url}[/dim]")


def _detect_pages_repo(token: Optional[str]) -> str:
    """Detect pages repo from current git remote, or fall back to default."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            remote = result.stdout.strip()
            if "github.com" in remote:
                # Parse owner/repo
                if remote.startswith("git@github.com:"):
                    owner_repo = remote[len("git@github.com:"):].rstrip("/")
                else:
                    owner_repo = remote.split("github.com/", 1)[1].rstrip("/")
                owner_repo = owner_repo[:-4] if owner_repo.endswith(".git") else owner_repo
                parts = owner_repo.split("/", 1)
                if parts:
                    owner = parts[0]
                    return f"{owner}/agentkit-trending"
    except Exception:
        pass
    return "mikiships/agentkit-trending"
