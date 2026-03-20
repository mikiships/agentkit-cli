"""agentkit ecosystem command — macro State of AI Agent Readiness across language ecosystems."""
from __future__ import annotations

import json
import os
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.engines.ecosystem import EcosystemEngine, EcosystemResult, LANG_EMOJI, PRESETS

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}
_VALID_PRESETS = list(PRESETS.keys()) + ["custom"]


def ecosystem_command(
    preset: str = "default",
    topics: Optional[List[str]] = None,
    repos_per_topic: int = 3,
    parallel: bool = True,
    json_output: bool = False,
    quiet: bool = False,
    output: Optional[str] = None,
    share: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    _league_factory=None,
) -> None:
    """Macro State of AI Agent Readiness scan across language/tech ecosystems."""
    # Validate preset
    if preset not in _VALID_PRESETS:
        choices = ", ".join(_VALID_PRESETS)
        msg = f"Invalid preset '{preset}'. Choices: {choices}"
        if json_output:
            console.print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)

    # Validate custom preset has topics
    if preset == "custom" and (not topics or len([t for t in topics if t.strip()]) < 2):
        msg = "Custom preset requires at least 2 topics via --topics."
        if json_output:
            console.print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not resolved_token and not quiet and not json_output:
        console.print("[yellow]Warning:[/yellow] GITHUB_TOKEN not set. Rate limits may apply.")

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit ecosystem[/bold] — preset=[cyan]{preset}[/cyan]")

    engine_kwargs: dict = dict(
        preset=preset,
        repos_per_topic=repos_per_topic,
        parallel=parallel,
        token=resolved_token,
        timeout=timeout,
    )
    if topics:
        engine_kwargs["topics"] = [t.strip() for t in topics if t.strip()]
    if _league_factory is not None:
        engine_kwargs["_league_factory"] = _league_factory

    try:
        engine = EcosystemEngine(**engine_kwargs)
    except ValueError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

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
                n = len(engine.topics)
                progress.add_task(
                    f"Scanning {n} ecosystems ([dim]{'parallel' if parallel else 'sequential'}[/dim])…",
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
        from agentkit_cli.renderers.ecosystem_html import EcosystemHTMLRenderer
        renderer = EcosystemHTMLRenderer()
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
            from agentkit_cli.renderers.ecosystem_html import EcosystemHTMLRenderer
            html = EcosystemHTMLRenderer().render(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url and not json_output and not quiet:
                console.print(f"\n[bold green]Ecosystem report published:[/bold green] {share_url}")
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
        if result.winner:
            print(f"winner: {result.winner.topic}")
        if share_url:
            print(share_url)
        return

    _print_rich_summary(result, share_url=share_url)


def _print_rich_summary(result: EcosystemResult, share_url: Optional[str] = None) -> None:
    """Print rich terminal standings table."""
    console.print()

    table = Table(
        title="🌐 State of AI Agent Readiness",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Rank", width=6, justify="center")
    table.add_column("Ecosystem", style="cyan")
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
        emoji = LANG_EMOJI.get(s.topic, "🔷")
        table.add_row(
            rank_str,
            f"{emoji} {s.topic}",
            f"[{gc}]{s.score:.1f}[/{gc}]",
            f"[{gc}]{s.grade}[/{gc}]",
            str(s.repo_count),
            s.top_repo,
        )

    console.print(table)

    # Winner callout
    if result.winner:
        champ = result.winner
        gc = _GRADE_RICH.get(champ.grade, "white")
        emoji = LANG_EMOJI.get(champ.topic, "🔷")
        console.print(
            f"\n[bold yellow]🏆 Winner:[/bold yellow] "
            f"[bold cyan]{emoji} {champ.topic}[/bold cyan] "
            f"[{gc}]{champ.score:.1f} / 100  {champ.grade}[/{gc}]"
        )

    n_eco = len(result.standings)
    n_repos = result.total_repos
    winner_str = result.winner.topic if result.winner else "n/a"
    winner_score = f"{result.winner.score:.1f}" if result.winner else "n/a"
    console.print(
        f"\n[dim]Scanned {n_eco} ecosystems, {n_repos} repos total. "
        f"Winner: {winner_str} (score: {winner_score})[/dim]"
    )

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
