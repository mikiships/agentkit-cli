"""agentkit hot command — score GitHub trending repos for agent-readiness."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli.hot import HotEngine, HotResult, HotRepoResult

console = Console()

_MAX_LIMIT = 25


def _grade_color(grade: Optional[str]) -> str:
    return {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}.get(grade or "", "dim")


def _score_str(score: Optional[float]) -> str:
    if score is None:
        return "[dim]N/A[/dim]"
    color = "green" if score >= 75 else ("yellow" if score >= 50 else "red")
    return f"[{color}]{score:.0f}[/{color}]"


def hot_command(
    language: Optional[str] = None,
    limit: int = 10,
    tweet_only: bool = False,
    share: bool = False,
    json_output: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    _fetch_fn=None,
    _score_fn=None,
) -> None:
    """Fetch GitHub trending repos, score each for agent-readiness, and generate a tweet-ready insight."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    limit = max(1, min(limit, _MAX_LIMIT))

    engine = HotEngine(timeout=timeout, token=resolved_token)

    if not tweet_only and not json_output:
        lang_str = f" ({language})" if language else ""
        console.print(f"\n[bold]🔥 agentkit hot[/bold]{lang_str} — scoring top {limit} trending repos...\n")

    try:
        result = engine.run(
            language=language,
            limit=limit,
            _fetch_fn=_fetch_fn,
            _score_fn=_score_fn,
        )
    except Exception as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    if not result.trending_available and not tweet_only and not json_output:
        console.print("[yellow]Warning: GitHub trending unavailable — using fallback repo list.[/yellow]\n")

    # --share: upload HTML
    if share:
        try:
            from agentkit_cli.hot import render_hot_html
            html = render_hot_html(result)
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            result.share_url = share_url
            if share_url:
                candidate = f"{result.tweet_text} {share_url}"
                if len(candidate) <= 280:
                    result.tweet_text = candidate
                if not tweet_only and not json_output:
                    console.print(f"[bold green]Report published:[/bold green] {share_url}\n")
        except Exception as exc:
            if not tweet_only and not json_output:
                console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    if tweet_only:
        print(result.tweet_text)
        return

    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    # Rich table
    _render_rich_table(result)

    # Tweet box
    console.print(
        Panel(
            f"[bold]{result.tweet_text}[/bold]",
            title="[bold green]Tweet-ready[/bold green]",
            border_style="green",
        )
    )
    console.print()


def _render_rich_table(result: HotResult) -> None:
    """Render the hot results as a Rich table."""
    table = Table(
        title="🔥 GitHub Trending — Agent-Readiness Scores",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Rank", style="dim", width=5)
    table.add_column("Repo", style="cyan", min_width=25)
    table.add_column("Lang", width=12)
    table.add_column("Score", width=8)
    table.add_column("Grade", width=6)
    table.add_column("Stars", width=8)

    for repo in result.repos:
        surprise = "⭐ " if result.most_surprising and repo.full_name == result.most_surprising.full_name else ""
        grade_color = _grade_color(repo.grade)
        grade_str = f"[{grade_color}]{repo.grade or 'N/A'}[/{grade_color}]" if repo.grade else "[dim]N/A[/dim]"
        stars_str = f"{repo.stars:,}" if repo.stars else "—"

        table.add_row(
            f"{surprise}{repo.rank}",
            repo.full_name,
            repo.language or "—",
            _score_str(repo.score),
            grade_str,
            stars_str,
        )

    console.print(table)

    if result.most_surprising:
        ms = result.most_surprising
        score_str = f"{ms.score:.0f}/100" if ms.score is not None else "N/A"
        console.print(
            Panel(
                f"[bold]{ms.full_name}[/bold] (#{ms.rank}) — Score: {score_str}",
                title="[bold yellow]⭐ Most Surprising[/bold yellow]",
                border_style="yellow",
            )
        )
