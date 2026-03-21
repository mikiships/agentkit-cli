"""agentkit daily-duel command — zero-input daily repo duel with tweet output."""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli.daily_duel import DailyDuelEngine, _write_latest_json

console = Console()

_GRADE_RICH = {"A": "green", "B": "blue", "C": "yellow", "D": "red", "F": "red"}


def daily_duel_command(
    seed: Optional[str] = None,
    deep: bool = False,
    share: bool = False,
    json_output: bool = False,
    output: Optional[str] = None,
    pair: Optional[List[str]] = None,
    quiet: bool = False,
    tweet_only: bool = False,
    calendar: bool = False,
    timeout: int = 120,
    token: Optional[str] = None,
    _analyze_factory=None,
    _output_path: Optional[Path] = None,
) -> None:
    """Zero-input daily repo duel. Auto-selects contrasting repos and generates tweet-ready text."""
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    # --calendar: show 7-day schedule, no analysis
    if calendar:
        engine = DailyDuelEngine(token=resolved_token, timeout=timeout, _analyze_factory=_analyze_factory)
        schedule = engine.calendar(days=7)
        if json_output:
            print(json.dumps(schedule, indent=2))
            return
        table = Table(title="📅 Daily Duel — 7-Day Schedule", show_header=True, header_style="bold")
        table.add_column("Date", style="dim")
        table.add_column("Repo 1", style="cyan")
        table.add_column("Repo 2", style="cyan")
        table.add_column("Category", style="yellow")
        for entry in schedule:
            table.add_row(entry["date"], entry["repo1"], entry["repo2"], entry["category"])
        console.print(table)
        return

    # --pair: override auto-pick
    if pair and len(pair) == 2:
        repo1_override, repo2_override = pair[0], pair[1]
        _run_explicit_pair(
            repo1=repo1_override,
            repo2=repo2_override,
            seed=seed,
            deep=deep,
            share=share,
            json_output=json_output,
            output=output,
            quiet=quiet,
            tweet_only=tweet_only,
            token=resolved_token,
            timeout=timeout,
            _analyze_factory=_analyze_factory,
            _output_path=_output_path,
        )
        return

    engine = DailyDuelEngine(
        token=resolved_token,
        timeout=timeout,
        _analyze_factory=_analyze_factory,
    )

    # Preview which pair we'll duel
    effective_seed = seed or date.today().isoformat()
    repo1, repo2, category = engine.pick_pair(seed)

    if not quiet and not json_output and not tweet_only:
        console.print(f"\n[bold]🗓️  Daily Duel[/bold] — [dim]{effective_seed}[/dim]")
        console.print(f"  [bold cyan]{repo1}[/bold cyan] vs [bold cyan]{repo2}[/bold cyan]  [yellow][{category}][/yellow]")
        console.print()

    try:
        result = engine.run_daily_duel(seed=seed, deep=deep)
    except Exception as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Handle --share
    share_url: Optional[str] = None
    if share:
        try:
            from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html
            html = render_repo_duel_html(result)
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            result.share_url = share_url
            if share_url:
                # Append URL to tweet_text if it fits
                candidate = f"{result.tweet_text} {share_url}"
                if len(candidate) <= 280:
                    result.tweet_text = candidate
                # Re-write JSON with share URL
                _write_latest_json(result, _output_path)
                if not quiet and not json_output:
                    console.print(f"[bold green]Report published:[/bold green] {share_url}\n")
        except Exception as exc:
            if not quiet and not json_output:
                console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    # Handle --output
    if output:
        try:
            from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html
            html = render_repo_duel_html(result)
            with open(output, "w", encoding="utf-8") as f:
                f.write(html)
            if not quiet and not json_output:
                console.print(f"[dim]HTML saved to {output}[/dim]")
        except Exception as exc:
            if not quiet and not json_output:
                console.print(f"[yellow]Warning: HTML render failed: {exc}[/yellow]")

    # Save to history DB
    try:
        from agentkit_cli.history import HistoryDB
        db = HistoryDB()
        db.record_run(
            project=f"{result.repo1}__vs__{result.repo2}",
            tool="daily_duel",
            score=result.repo1_score,
            label="daily_duel",
        )
    except Exception:
        pass

    if tweet_only:
        print(result.tweet_text)
        return

    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    if quiet:
        print(result.tweet_text)
        return

    # Rich terminal output
    from agentkit_cli.commands.repo_duel_cmd import _render_rich_table
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


def _run_explicit_pair(
    repo1: str,
    repo2: str,
    seed: Optional[str],
    deep: bool,
    share: bool,
    json_output: bool,
    output: Optional[str],
    quiet: bool,
    tweet_only: bool,
    token: Optional[str],
    timeout: int,
    _analyze_factory,
    _output_path: Optional[Path],
) -> None:
    """Run a duel on explicit --pair repos (bypasses auto-pick)."""
    from agentkit_cli.repo_duel import RepoDuelEngine
    from agentkit_cli.daily_duel import DailyDuelResult, _write_latest_json, _LATEST_JSON, _build_tweet_text

    effective_seed = seed or date.today().isoformat()

    if not quiet and not json_output:
        console.print(f"\n[bold]⚔️  Daily Duel (custom pair)[/bold]  [dim]{effective_seed}[/dim]")
        console.print(f"  [bold cyan]{repo1}[/bold cyan] vs [bold cyan]{repo2}[/bold cyan]")
        console.print()

    engine = RepoDuelEngine(token=token, timeout=timeout, _analyze_factory=_analyze_factory)
    try:
        base = engine.run_duel(repo1=repo1, repo2=repo2, deep=deep)
    except Exception as exc:
        if json_output:
            print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    n_dims = len(base.dimension_results)
    winner_wins = sum(
        1 for d in base.dimension_results
        if d.winner == ("repo1" if base.winner == "repo1" else "repo2")
    )
    tweet_text = _build_tweet_text(
        repo1=repo1,
        repo2=repo2,
        repo1_score=base.repo1_score,
        repo2_score=base.repo2_score,
        repo1_grade=base.repo1_grade,
        repo2_grade=base.repo2_grade,
        winner=base.winner,
        n_dims=n_dims,
        winner_wins=winner_wins,
        pair_category="custom",
        seed=effective_seed,
    )

    result = DailyDuelResult(
        repo1=base.repo1,
        repo2=base.repo2,
        repo1_score=base.repo1_score,
        repo2_score=base.repo2_score,
        repo1_grade=base.repo1_grade,
        repo2_grade=base.repo2_grade,
        dimension_results=base.dimension_results,
        winner=base.winner,
        run_date=base.run_date,
        share_url=base.share_url,
        tweet_text=tweet_text,
        pair_category="custom",
        seed=effective_seed,
    )

    _write_latest_json(result, _output_path)

    share_url: Optional[str] = None
    if share:
        try:
            from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html
            html = render_repo_duel_html(result)
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            result.share_url = share_url
            if share_url:
                candidate = f"{result.tweet_text} {share_url}"
                if len(candidate) <= 280:
                    result.tweet_text = candidate
                _write_latest_json(result, _output_path)
                if not quiet and not json_output:
                    console.print(f"[bold green]Report published:[/bold green] {share_url}\n")
        except Exception as exc:
            if not quiet and not json_output:
                console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    if output:
        try:
            from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html
            html = render_repo_duel_html(result)
            with open(output, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

    try:
        from agentkit_cli.history import HistoryDB
        db = HistoryDB()
        db.record_run(
            project=f"{result.repo1}__vs__{result.repo2}",
            tool="daily_duel",
            score=result.repo1_score,
            label="daily_duel",
        )
    except Exception:
        pass

    if tweet_only:
        print(result.tweet_text)
        return

    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
        return

    if quiet:
        print(result.tweet_text)
        return

    from agentkit_cli.commands.repo_duel_cmd import _render_rich_table
    _render_rich_table(result)
    console.print(
        Panel(
            f"[bold]{result.tweet_text}[/bold]",
            title="[bold green]Tweet-ready[/bold green]",
            border_style="green",
        )
    )
    console.print()
