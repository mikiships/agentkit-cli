"""agentkit topic-duel command — head-to-head comparison of two GitHub topics."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli.engines.topic_duel import TopicDuelEngine, TopicDuelResult

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}
_MAX_REPOS = 10


def topic_duel_command(
    topic1: str,
    topic2: str,
    repos_per_topic: int = 5,
    json_output: bool = False,
    quiet: bool = False,
    output: Optional[str] = None,
    share: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    _engine_factory=None,
) -> None:
    """Head-to-head agent-readiness comparison of two GitHub topics."""
    topic1 = topic1.strip()
    topic2 = topic2.strip()

    if not topic1 or not topic2:
        if json_output:
            console.print(json.dumps({"error": "Two topics are required."}))
        else:
            console.print("[red]Error:[/red] Two topics are required.")
        raise typer.Exit(code=1)

    repos_per_topic = max(1, min(repos_per_topic, _MAX_REPOS))
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not resolved_token and not quiet and not json_output:
        console.print("[yellow]Warning:[/yellow] GITHUB_TOKEN not set. Rate limits may apply.")

    if not quiet and not json_output:
        console.print(
            f"\n[bold]agentkit topic-duel[/bold] — "
            f"[bold cyan]{topic1}[/bold cyan] vs [bold cyan]{topic2}[/bold cyan]"
        )

    engine_kwargs = dict(
        topic1=topic1,
        topic2=topic2,
        repos_per_topic=repos_per_topic,
        token=resolved_token,
        timeout=timeout,
    )
    if _engine_factory is not None:
        engine_kwargs["_engine_factory"] = _engine_factory

    engine = TopicDuelEngine(**engine_kwargs)

    def _progress_cb(topic: str, idx: int, total: int, repo_name: str) -> None:
        if not quiet and not json_output:
            console.print(f"  [dim][{topic}] [{idx + 1}/{total}] scoring {repo_name}[/dim]")

    try:
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
        from agentkit_cli.topic_duel_html import render_topic_duel_html
        html = render_topic_duel_html(result)

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
            from agentkit_cli.topic_duel_html import render_topic_duel_html
            html = render_topic_duel_html(result)
        try:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url and not json_output and not quiet:
                console.print(
                    f"\n[bold green]Topic-duel report published:[/bold green] {share_url}"
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

    # Quiet: only winner / share URL
    if quiet:
        if result.overall_winner == "topic1":
            print(f"winner: {topic1}")
        elif result.overall_winner == "topic2":
            print(f"winner: {topic2}")
        else:
            print(f"tie: {topic1} and {topic2}")
        if share_url:
            print(share_url)
        return

    _print_rich_summary(result, share_url=share_url)


def _print_rich_summary(result: TopicDuelResult, share_url: Optional[str] = None) -> None:
    """Print the rich terminal summary."""
    t1 = result.topic1
    t2 = result.topic2
    s1 = result.topic1_avg_score
    s2 = result.topic2_avg_score

    console.print()

    # Side-by-side summary panels
    e1 = result.topic1_result.entries
    e2 = result.topic2_result.entries

    def _topic_panel(topic, avg_score, entries) -> str:
        lines = [f"  Avg score: [bold]{avg_score:.1f}[/bold]", f"  Repos: {len(entries)}"]
        if entries:
            top = entries[0]
            gc = _GRADE_RICH.get(top.grade, "white")
            lines.append(f"  Top: [cyan]{top.repo_full_name}[/cyan] [{gc}]{top.score:.1f}[/{gc}]")
        return "\n".join(lines)

    panel1 = Panel(_topic_panel(t1, s1, e1), title=f"[bold cyan]{t1}[/bold cyan]", expand=True)
    panel2 = Panel(_topic_panel(t2, s2, e2), title=f"[bold cyan]{t2}[/bold cyan]", expand=True)

    from rich.columns import Columns
    console.print(Columns([panel1, panel2]))

    # Dimensions table
    if result.dimensions:
        dim_table = Table(title="Per-Dimension Comparison", show_header=True, header_style="bold")
        dim_table.add_column("Dimension", style="dim")
        dim_table.add_column(t1, justify="right")
        dim_table.add_column(t2, justify="right")
        dim_table.add_column("Winner", justify="center")

        for dim in result.dimensions:
            if dim.winner == "topic1":
                v1_str = f"[bold green]{dim.topic1_value:.1f}[/bold green]"
                v2_str = f"[dim]{dim.topic2_value:.1f}[/dim]"
                w_str = f"[green]{t1}[/green]"
            elif dim.winner == "topic2":
                v1_str = f"[dim]{dim.topic1_value:.1f}[/dim]"
                v2_str = f"[bold green]{dim.topic2_value:.1f}[/bold green]"
                w_str = f"[green]{t2}[/green]"
            else:
                v1_str = f"[yellow]{dim.topic1_value:.1f}[/yellow]"
                v2_str = f"[yellow]{dim.topic2_value:.1f}[/yellow]"
                w_str = "[yellow]tie[/yellow]"
            dim_table.add_row(dim.name.replace("_", " ").title(), v1_str, v2_str, w_str)

        console.print(dim_table)

    # Winner declaration
    if result.overall_winner == "topic1":
        console.print(
            f"\n[bold green]🏆 {t1} wins![/bold green]  "
            f"avg {s1:.1f} vs {s2:.1f}"
        )
    elif result.overall_winner == "topic2":
        console.print(
            f"\n[bold green]🏆 {t2} wins![/bold green]  "
            f"avg {s2:.1f} vs {s1:.1f}"
        )
    else:
        console.print(
            f"\n[bold yellow]🤝 Tie![/bold yellow]  "
            f"{t1} {s1:.1f} vs {t2} {s2:.1f} — evenly matched"
        )

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
