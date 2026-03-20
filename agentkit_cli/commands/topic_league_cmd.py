"""agentkit topic-league command — multi-topic standings comparison for N GitHub topics."""
from __future__ import annotations

import json
import os
from typing import Callable, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.engines.topic_league import TopicLeagueEngine, TopicLeagueResult

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}
_MAX_REPOS = 10
_MIN_TOPICS = 2
_MAX_TOPICS = 10


def topic_league_command(
    topics: List[str],
    repos_per_topic: int = 5,
    parallel: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    output: Optional[str] = None,
    share: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    _engine_factory=None,
) -> None:
    """Multi-topic standings comparison — rank N GitHub topics by agent-readiness."""
    topics = [t.strip() for t in topics if t.strip()]

    if len(topics) < _MIN_TOPICS:
        msg = f"topic-league requires at least {_MIN_TOPICS} topics, got {len(topics)}."
        if json_output:
            console.print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)

    if len(topics) > _MAX_TOPICS:
        msg = f"topic-league accepts at most {_MAX_TOPICS} topics, got {len(topics)}."
        if json_output:
            console.print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)

    repos_per_topic = max(1, min(repos_per_topic, _MAX_REPOS))
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not resolved_token and not quiet and not json_output:
        console.print("[yellow]Warning:[/yellow] GITHUB_TOKEN not set. Rate limits may apply.")

    if not quiet and not json_output:
        topic_str = " · ".join(f"[bold cyan]{t}[/bold cyan]" for t in topics)
        console.print(f"\n[bold]agentkit topic-league[/bold] — {topic_str}")

    engine_kwargs = dict(
        topics=topics,
        repos_per_topic=repos_per_topic,
        parallel=parallel,
        token=resolved_token,
        timeout=timeout,
    )
    if _engine_factory is not None:
        engine_kwargs["_engine_factory"] = _engine_factory

    engine = TopicLeagueEngine(**engine_kwargs)

    def _progress_cb(topic: str, idx: int, total: int, repo_name: str) -> None:
        if not quiet and not json_output:
            console.print(f"  [dim][{topic}] [{idx + 1}/{total}] scoring {repo_name}[/dim]")

    try:
        if not quiet and not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                n = len(topics)
                progress.add_task(
                    f"Analyzing {n} topics ([dim]{'parallel' if parallel else 'sequential'}[/dim])…",
                    total=None,
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

    # Render HTML if needed
    html: Optional[str] = None
    if share or output:
        from agentkit_cli.renderers.topic_league_html import TopicLeagueHTMLRenderer
        renderer = TopicLeagueHTMLRenderer()
        html = renderer.render(result)

    # --output: save HTML
    if output and html:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)
        if not quiet and not json_output:
            console.print(f"[dim]HTML saved to {output}[/dim]")

    # --share: publish to here.now
    share_url: Optional[str] = None
    if share:
        if html is None:
            from agentkit_cli.renderers.topic_league_html import TopicLeagueHTMLRenderer
            html = TopicLeagueHTMLRenderer().render(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url and not json_output and not quiet:
                console.print(
                    f"\n[bold green]Topic-league report published:[/bold green] {share_url}"
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

    # Quiet: only winner and share URL
    if quiet:
        if result.standings:
            print(f"winner: {result.standings[0].topic}")
        if share_url:
            print(share_url)
        return

    _print_rich_summary(result, share_url=share_url)


def _print_rich_summary(result: TopicLeagueResult, share_url: Optional[str] = None) -> None:
    """Print rich terminal standings table."""
    console.print()

    table = Table(
        title="🏆 Topic League Standings",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Rank", width=6, justify="center")
    table.add_column("Topic", style="cyan")
    table.add_column("Avg Score", justify="right", width=10)
    table.add_column("Grade", justify="center", width=7)
    table.add_column("Repos", justify="right", width=6)
    table.add_column("Top Repo", style="dim", max_width=40)

    for s in result.standings:
        rank_str = (
            "🥇" if s.rank == 1
            else "🥈" if s.rank == 2
            else "🥉" if s.rank == 3
            else str(s.rank)
        )
        gc = _GRADE_RICH.get(s.grade, "white")
        table.add_row(
            rank_str,
            s.topic,
            f"[{gc}]{s.score:.1f}[/{gc}]",
            f"[{gc}]{s.grade}[/{gc}]",
            str(s.repo_count),
            s.top_repo,
        )

    console.print(table)

    # Champion callout
    if result.standings:
        champ = result.standings[0]
        gc = _GRADE_RICH.get(champ.grade, "white")
        console.print(
            f"\n[bold yellow]🏆 Champion:[/bold yellow] "
            f"[bold cyan]{champ.topic}[/bold cyan] "
            f"[{gc}]{champ.score:.1f} / 100  {champ.grade}[/{gc}]"
        )

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
