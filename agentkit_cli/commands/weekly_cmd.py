"""agentkit weekly — generate a 7-day quality digest across tracked projects."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.weekly_engine import WeeklyReportEngine

console = Console()


def weekly_command(
    days: int = 7,
    projects: Optional[list[str]] = None,
    json_output: bool = False,
    output: Optional[Path] = None,
    quiet: bool = False,
    tweet_only: bool = False,
    share: bool = False,
    db_path: Optional[Path] = None,
) -> None:
    """Generate a 7-day agent quality digest across all tracked projects."""
    engine = WeeklyReportEngine(db_path=db_path)
    report = engine.generate(days=days, projects=projects)

    # --tweet-only: print tweet and exit
    if tweet_only:
        print(report.tweet_text)
        return

    # --json: print JSON and exit
    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    # Rich table output
    if not quiet:
        _print_rich(report)

    # --output: save HTML
    if output:
        from agentkit_cli.weekly_html import render_weekly_html
        html = render_weekly_html(report)
        output.write_text(html, encoding="utf-8")
        if not quiet:
            console.print(f"\n[dim]Report saved to {output.resolve()}[/dim]")

    # --share: publish HTML
    if share:
        from agentkit_cli.weekly_html import render_weekly_html
        from agentkit_cli.publish import PublishError
        html = render_weekly_html(report)
        try:
            from agentkit_cli.trending_report import publish_report
            url = publish_report(html)
            if quiet:
                print(url)
            else:
                console.print(f"\n[bold green]Weekly report:[/bold green] {url}")
        except (PublishError, Exception) as exc:
            if not quiet:
                console.print(f"[yellow]Warning: publish failed ({exc}).[/yellow]")
            fallback = Path("./weekly-report.html")
            fallback.write_text(html, encoding="utf-8")
            if not quiet:
                console.print(f"[dim]Saved to {fallback.resolve()}[/dim]")


def _print_rich(report) -> None:
    """Print a rich-formatted weekly report."""
    trend_emoji = {"improving": "📈", "regressing": "📉", "stable": "➡️"}.get(
        report.overall_trend, "➡️"
    )
    week_str = report.period_start.strftime("%Y-%m-%d")

    console.print(
        f"\n[bold]agentkit weekly[/bold] — {week_str} → "
        f"{report.period_end.strftime('%Y-%m-%d')} {trend_emoji}"
    )
    console.print(
        f"  [dim]Projects tracked:[/dim] {report.projects_tracked}  "
        f"[dim]Runs in period:[/dim] {report.runs_in_period}  "
        f"[dim]Avg score:[/dim] {report.avg_score if report.avg_score is not None else 'N/A'}"
    )

    if not report.per_project:
        console.print("[yellow]No project data found. Run `agentkit run` to populate history.[/yellow]")
        return

    table = Table(
        title="Project Score Changes",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Project", style="bold", min_width=20)
    table.add_column("Start", justify="right", width=8)
    table.add_column("End", justify="right", width=8)
    table.add_column("Delta", justify="right", width=8)
    table.add_column("Status", width=12)
    table.add_column("Runs", justify="right", width=5)

    _STATUS_STYLE = {
        "improving": "[green]📈 improving[/green]",
        "regressing": "[red]📉 regressing[/red]",
        "stable": "[dim]➡️ stable[/dim]",
        "no_data": "[dim]— no data[/dim]",
    }

    for p in sorted(report.per_project, key=lambda x: -(x.delta or 0)):
        start_str = f"{p.score_start:.1f}" if p.score_start is not None else "—"
        end_str = f"{p.score_end:.1f}" if p.score_end is not None else "—"
        delta_str = (
            f"[green]+{p.delta:.1f}[/green]"
            if (p.delta or 0) > 0
            else f"[red]{p.delta:.1f}[/red]"
            if (p.delta or 0) < 0
            else "0.0"
        ) if p.delta is not None else "—"
        status_str = _STATUS_STYLE.get(p.status, p.status)
        table.add_row(p.name, start_str, end_str, delta_str, status_str, str(p.runs))

    console.print(table)

    if report.top_actions:
        console.print("\n[bold]Top Recommended Actions:[/bold]")
        for i, action in enumerate(report.top_actions[:5], 1):
            console.print(f"  {i}. {action}")

    if report.common_findings:
        console.print("\n[bold]Common Findings:[/bold]")
        for finding in report.common_findings[:5]:
            console.print(f"  • {finding}")

    console.print(f"\n[dim]Tweet:[/dim] {report.tweet_text[:80]}...")
