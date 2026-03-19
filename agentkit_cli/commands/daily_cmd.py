"""agentkit daily — generate and optionally share a daily agent-readiness leaderboard."""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.engines.daily_leaderboard import fetch_trending_repos, publish_to_pages
from agentkit_cli.renderers.daily_leaderboard_renderer import render_leaderboard_html
from agentkit_cli.trending_report import publish_report

console = Console()

_DATE_FORMAT = "%Y-%m-%d"


def _parse_date(date_str: Optional[str]) -> date:
    if not date_str:
        return date.today()
    try:
        return datetime.strptime(date_str, _DATE_FORMAT).date()
    except ValueError:
        console.print(f"[red]Error: invalid date '{date_str}' — expected YYYY-MM-DD[/red]", err=True)
        raise typer.Exit(1)


def _detect_repo_path_from_remote() -> Optional[str]:
    """Detect the current git repo path."""
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def daily_command(
    date_str: Optional[str] = None,
    limit: int = 20,
    min_score: float = 0.0,
    share: bool = False,
    json_output: bool = False,
    output: Optional[Path] = None,
    quiet: bool = False,
    token: Optional[str] = None,
    pages: bool = False,
    pages_repo: Optional[str] = None,
    pages_path: str = "docs/leaderboard.html",
) -> None:
    """Fetch today's trending GitHub repos scored for agent-readiness and render a leaderboard."""
    for_date = _parse_date(date_str)
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit daily[/bold] — date: {for_date}, limit: {limit}")

    # Fetch + score
    leaderboard = fetch_trending_repos(for_date=for_date, limit=limit, token=resolved_token)

    # Filter by min_score
    repos = [r for r in leaderboard.repos if r.composite_score >= min_score]
    leaderboard.repos = repos

    if not repos:
        if not quiet:
            console.print("[yellow]No repos found matching criteria.[/yellow]")
        if json_output:
            print(json.dumps({"date": str(for_date), "repos": []}))
        return

    # JSON output
    if json_output:
        out = {
            "date": str(for_date),
            "generated_at": leaderboard.generated_at.isoformat(),
            "repos": [
                {
                    "rank": r.rank,
                    "full_name": r.full_name,
                    "description": r.description,
                    "stars": r.stars,
                    "language": r.language,
                    "url": r.url,
                    "composite_score": r.composite_score,
                    "top_finding": r.top_finding,
                }
                for r in repos
            ],
        }
        print(json.dumps(out, indent=2))
        return

    # Rich table (unless quiet)
    if not quiet:
        from rich.table import Table
        table = Table(
            title=f"Agent-Ready Repos — {for_date}",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Rank", style="dim", width=5)
        table.add_column("Repo", style="bold", min_width=30)
        table.add_column("Stars", justify="right", width=8)
        table.add_column("Score", justify="right", width=7)
        table.add_column("Top Finding", max_width=40)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        for r in repos:
            score_str = f"{int(round(r.composite_score))}"
            rank_str = medals.get(r.rank, f"#{r.rank}")
            table.add_row(rank_str, r.full_name, f"{r.stars:,}", score_str, r.top_finding)

        console.print(table)

    # --output: save HTML
    html: Optional[str] = None
    if output or share or pages:
        html = render_leaderboard_html(leaderboard)

    if output:
        output.write_text(html, encoding="utf-8")
        if not quiet:
            console.print(f"\n[dim]Report saved to {output.resolve()}[/dim]")

    # --pages: publish HTML to GitHub Pages
    if pages:
        if html is None:
            html = render_leaderboard_html(leaderboard)

        # Resolve repo path
        if pages_repo and pages_repo.startswith("github:"):
            # Format: github:owner/repo — use current working directory
            repo_path = _detect_repo_path_from_remote() or "."
        else:
            repo_path = _detect_repo_path_from_remote() or "."

        result = publish_to_pages(
            html=html,
            leaderboard=leaderboard,
            repo_path=repo_path,
            pages_path=pages_path,
        )

        if result["committed"]:
            if quiet:
                print(result["pages_url"])
            else:
                console.print(f"\n[bold green]Daily leaderboard (permanent):[/bold green] {result['pages_url']}")
        else:
            err = result.get("error", "unknown error")
            if not quiet:
                console.print(f"[yellow]Warning: GitHub Pages publish failed ({err}). Falling back to --share.[/yellow]")
            # Fall back to here.now share
            from agentkit_cli.publish import PublishError
            try:
                url = publish_report(html)
                if quiet:
                    print(url)
                else:
                    console.print(f"\n[bold green]Daily leaderboard (24h):[/bold green] {url}")
                    console.print("[dim]Note: GitHub Pages publish failed; link expires in 24h.[/dim]")
            except PublishError as exc:
                if not quiet:
                    console.print(f"[yellow]Warning: fallback publish also failed ({exc}).[/yellow]")
        return

    # --share: publish to here.now
    if share:
        if html is None:
            html = render_leaderboard_html(leaderboard)

        from agentkit_cli.publish import PublishError

        try:
            url = publish_report(html)
            if quiet:
                # Cron-friendly: URL only
                print(url)
            else:
                console.print(f"\n[bold green]Daily leaderboard:[/bold green] {url}")
                anon = not bool(os.environ.get("HERENOW_API_KEY"))
                if anon:
                    console.print(
                        "[dim]Anonymous publish — link expires in 24h. "
                        "Set HERENOW_API_KEY for persistent links.[/dim]"
                    )
        except PublishError as exc:
            if not quiet:
                console.print(f"[yellow]Warning: publish failed ({exc}). Saving locally.[/yellow]")
            fallback = Path("./daily-leaderboard.html")
            fallback.write_text(html, encoding="utf-8")
            if not quiet:
                console.print(f"[dim]Saved to {fallback.resolve()}[/dim]")
