"""agentkit topic command — rank top GitHub repos for a topic by agent-readiness."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.topic_rank import TopicRankEngine
from agentkit_cli.topic_rank_html import TopicRankHTMLRenderer

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}
_MAX_LIMIT = 25


def topic_rank_command(
    topic: str,
    limit: int = 10,
    language: Optional[str] = None,
    json_output: bool = False,
    output: Optional[str] = None,
    share: bool = False,
    quiet: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
) -> None:
    """Rank top GitHub repos for a topic by agent-readiness score."""
    topic = topic.strip()

    if not topic:
        if json_output:
            console.print(json.dumps({"error": "Topic is required."}))
        else:
            console.print("[red]Error:[/red] Topic is required.")
        raise typer.Exit(code=1)

    limit = max(1, min(limit, _MAX_LIMIT))
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not resolved_token and not quiet and not json_output:
        console.print("[yellow]Warning:[/yellow] GITHUB_TOKEN not set. Rate limits may apply.")

    if not quiet and not json_output:
        console.print(
            f"\n[bold]agentkit topic[/bold] — ranking repos for topic [bold]{topic}[/bold]"
        )

    engine = TopicRankEngine(
        topic=topic,
        limit=limit,
        language=language,
        token=resolved_token,
        timeout=timeout,
    )

    def _progress_cb(idx: int, total: int, repo_name: str) -> None:
        if not quiet and not json_output:
            console.print(f"  [dim][{idx + 1}/{total}] scoring {repo_name}[/dim]")

    try:
        if not quiet and not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(
                    f"Analyzing repos for topic [bold]{topic}[/bold]…", total=None
                )
                result = engine.run(progress_cb=_progress_cb)
        else:
            result = engine.run(progress_cb=_progress_cb)
    except Exception as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Render HTML
    html: Optional[str] = None
    if share or output:
        renderer = TopicRankHTMLRenderer()
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
            renderer = TopicRankHTMLRenderer()
            html = renderer.render(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url and not json_output and not quiet:
                console.print(
                    f"\n[bold green]Topic-rank report published:[/bold green] {share_url}"
                )
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
    """Print rich terminal summary of topic-rank result."""
    topic = result.topic

    console.print(
        f"\n[bold]🏆 Agent-Ready Repos:[/bold] "
        f"[bold cyan]{topic}[/bold cyan]  "
        f"[dim]{result.total_analyzed} analyzed[/dim]"
    )

    if not result.entries:
        console.print("[yellow]No repos found for this topic.[/yellow]")
        console.print(
            f"\n[dim]Drill down: [bold]agentkit topic {topic}[/bold] for topic-specific repos[/dim]"
        )
        return

    table = Table(
        title=f"Top Repos — {topic}",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Rank", width=5, justify="center")
    table.add_column("Repo", style="cyan")
    table.add_column("Score", justify="right", width=8)
    table.add_column("Grade", justify="center", width=6)
    table.add_column("Stars", justify="right", width=7)
    table.add_column("Description", style="dim", max_width=40)

    for entry in result.entries:
        gc = _GRADE_RICH.get(entry.grade, "white")
        desc = entry.description[:40] if entry.description else "—"
        table.add_row(
            str(entry.rank),
            entry.repo_full_name,
            f"{entry.score:.1f}",
            f"[{gc}]{entry.grade}[/{gc}]",
            f"⭐ {entry.stars:,}",
            desc,
        )

    console.print(table)

    # Top scorer spotlight
    if result.entries:
        top = result.entries[0]
        tc = _GRADE_RICH.get(top.grade, "white")
        console.print(
            f"\n[bold yellow]🏆 Top Repo:[/bold yellow] "
            f"[bold cyan]{top.repo_full_name}[/bold cyan] "
            f"[{tc}]{top.score:.1f} / 100  {top.grade}[/{tc}]"
        )

    console.print(
        f"\n[dim]Drill down: [bold]agentkit topic {topic}[/bold] for topic-specific repos[/dim]"
    )

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
