"""agentkit leaderboard-page command — generate a public HTML leaderboard of top agent-ready repos."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.leaderboard_page import (
    ECOSYSTEMS,
    LeaderboardPageEngine,
    LeaderboardPageResult,
    render_embed_badge,
    render_leaderboard_html,
)

console = Console()

_MAX_LIMIT = 25


def leaderboard_page_command(
    output: str = "leaderboard.html",
    ecosystems: Optional[str] = None,
    limit: int = 10,
    share: bool = False,
    json_output: bool = False,
    pages: bool = False,
    embed: Optional[str] = None,
    embed_only: bool = False,
    token: Optional[str] = None,
    _repos_override=None,
    _score_fn=None,
) -> None:
    """Generate a public HTML leaderboard page of top agent-ready GitHub repos by ecosystem."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    limit = max(1, min(limit, _MAX_LIMIT))

    # Parse ecosystems
    eco_list: Optional[List[str]] = None
    if ecosystems:
        eco_list = [e.strip().lower() for e in ecosystems.split(",") if e.strip()]

    # Resolve output path
    output_path = Path(output)
    if pages:
        output_path = Path("docs/leaderboard.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Handle embed-only
    if embed and embed_only:
        repo_full_name = embed.replace("github:", "", 1)
        md = render_embed_badge(repo_full_name, ecosystem=(eco_list[0] if eco_list else "python"))
        print(md)
        return

    engine = LeaderboardPageEngine(
        ecosystems=eco_list,
        limit=limit,
        token=resolved_token,
        _repos_override=_repos_override or {},
        _score_fn=_score_fn,
    )

    if not json_output and not embed_only:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Scoring ecosystems…", total=None)
            result = engine.run()
    else:
        result = engine.run()

    # Handle embed (non-only)
    if embed:
        repo_full_name = embed.replace("github:", "", 1)
        # Find rank/score for this repo across ecosystems
        rank = None
        score = None
        eco_name = None
        for eco in result.ecosystems:
            for entry in eco.entries:
                if entry.repo_full_name == repo_full_name:
                    rank = entry.rank
                    score = entry.score
                    eco_name = eco.ecosystem
                    break
            if rank:
                break
        result.embed_markdown = render_embed_badge(repo_full_name, rank=rank, score=score, ecosystem=eco_name)

    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    # Render HTML
    html = render_leaderboard_html(result)
    output_path.write_text(html, encoding="utf-8")

    if not embed_only:
        console.print(f"\n[bold green]✓ Leaderboard written to:[/bold green] {output_path}")
        _print_summary_table(result)

    if share:
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url:
                console.print(f"[bold green]📡 Published:[/bold green] {share_url}")
        except Exception as exc:
            console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    if result.embed_markdown:
        console.print("\n[bold]Badge markdown:[/bold]")
        console.print(result.embed_markdown)


def _print_summary_table(result: LeaderboardPageResult) -> None:
    for eco in result.ecosystems:
        table = Table(title=f"🤖 {eco.ecosystem.capitalize()} — Top Repos", show_header=True, header_style="bold")
        table.add_column("Rank", style="dim", width=5)
        table.add_column("Repository", style="cyan", min_width=30)
        table.add_column("Score", width=8)
        table.add_column("Grade", width=6)
        table.add_column("Stars", width=10)
        for entry in eco.entries:
            grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}
            gc = grade_colors.get(entry.grade, "dim")
            stars_str = f"{entry.stars:,}" if entry.stars else "—"
            table.add_row(
                str(entry.rank),
                entry.repo_full_name,
                f"{entry.score:.0f}",
                f"[{gc}]{entry.grade}[/{gc}]",
                stars_str,
            )
        console.print(table)
        console.print()
