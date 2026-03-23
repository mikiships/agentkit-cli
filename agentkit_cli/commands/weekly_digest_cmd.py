"""agentkit weekly-digest — generate and share the weekly AI Agent Readiness report."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

err_console = Console(stderr=True)

from agentkit_cli.weekly_digest_engine import WeeklyDigestEngine, DigestReport
from agentkit_cli.renderers.weekly_digest_renderer import render_html, render_markdown

app = typer.Typer(help="Generate a weekly 'State of AI Agent Readiness' digest report.")
console = Console()


def _share_html(html: str, quiet: bool = False) -> Optional[str]:
    """Upload HTML to here.now and return URL or None."""
    try:
        from agentkit_cli.share import upload_scorecard
        api_key = os.environ.get("HERENOW_API_KEY") or None
        url = upload_scorecard(html, api_key=api_key)
        return url
    except Exception as e:
        if not quiet:
            err_console.print(f"[red]Share failed:[/red] {e}")
        return None


def _print_rich_table(report: DigestReport) -> None:
    """Print a Rich summary table to stdout."""
    stats = report.week_stats
    total = stats.get("total_analyses", 0)
    avg = stats.get("avg_score", 0.0)
    top_scorer = stats.get("top_scorer", "N/A")

    console.print(f"\n[bold blue]State of AI Agent Readiness[/bold blue]")
    console.print(f"Generated: {report.generated_at}\n")

    # Stats row
    console.print(f"  Analyses this week: [cyan]{total}[/cyan]")
    console.print(f"  Average score:      [cyan]{avg:.1f}[/cyan]")
    console.print(f"  Top scorer:         [cyan]{top_scorer}[/cyan]\n")

    # Top repos table
    table = Table(title="Top Repositories", show_header=True, header_style="bold blue")
    table.add_column("Repository", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Grade")

    for repo_info in report.top_repos:
        repo = repo_info.get("repo", "")
        score = repo_info.get("score", 0.0)
        grade = repo_info.get("grade", "")
        score_color = "green" if float(score) >= 80 else ("yellow" if float(score) >= 60 else "red")
        table.add_row(repo, f"[{score_color}]{score}[/{score_color}]", grade)

    console.print(table)


@app.callback(invoke_without_command=True)
def weekly_digest(
    ctx: typer.Context,
    share: bool = typer.Option(False, "--share", help="Publish HTML to here.now and print URL"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save HTML to file instead of opening"),
    json_output: bool = typer.Option(False, "--json", help="Structured JSON output (DigestReport as dict)"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress Rich progress output"),
    since: int = typer.Option(7, "--since", help="Lookback window in days (default 7)"),
    cron: bool = typer.Option(False, "--cron", help="Cron mode: quiet, no browser, always share, URL to stdout only"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Generate a weekly 'State of AI Agent Readiness' digest report."""
    if ctx.invoked_subcommand is not None:
        return

    # Cron mode: quiet + always share
    if cron:
        quiet = True
        share = True

    engine = WeeklyDigestEngine(db_path=db_path)
    if not quiet and not json_output:
        err_console.print("[dim]Generating weekly digest...[/dim]")

    report = engine.generate(since_days=since)

    # JSON mode
    if json_output:
        print(json.dumps(asdict(report)))
        return

    # Rich table output (not cron, not quiet)
    if not quiet and not cron:
        _print_rich_table(report)

    # HTML output or share
    html = render_html(report)

    if output:
        output.write_text(html, encoding="utf-8")
        if not quiet:
            console.print(f"[green]Saved:[/green] {output}")

    if share:
        if not quiet:
            err_console.print("[dim]Uploading to here.now...[/dim]")
        url = _share_html(html, quiet=quiet)
        if url:
            # cron mode: URL to stdout only
            print(url)
        else:
            if not quiet:
                err_console.print("[red]Share failed[/red]")
            sys.exit(1)
