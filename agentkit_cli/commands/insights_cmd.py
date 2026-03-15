"""agentkit insights command — cross-run portfolio analysis."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from agentkit_cli.insights import InsightsEngine

console = Console()

_EMPTY_MSG = (
    "[dim]No history found. Run [bold]agentkit analyze[/bold] or "
    "[bold]agentkit run[/bold] on some repos first.[/dim]"
)


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _direction_icon(direction: str) -> str:
    return "↑" if direction == "up" else "↓"


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_portfolio_summary(engine: InsightsEngine) -> bool:
    """Render portfolio health panel. Returns True if data was shown."""
    summary = engine.get_portfolio_summary()

    if summary["total_runs"] == 0:
        console.print(_EMPTY_MSG)
        return False

    avg = summary["avg_score"]
    color = _score_color(avg)
    lines = [
        f"  [bold]Average Score:[/bold]  [{color}]{avg:.1f}[/{color}]",
        f"  [bold]Total Runs:[/bold]     {summary['total_runs']}",
        f"  [bold]Unique Repos:[/bold]   {summary['unique_repos']}",
        f"  [bold]Best Repo:[/bold]      {summary['best_repo'] or '—'}",
        f"  [bold]Worst Repo:[/bold]     {summary['worst_repo'] or '—'}",
        f"  [bold]Top Issue:[/bold]      {summary['top_issue'] or 'None detected'}",
    ]
    panel = Panel(
        "\n".join(lines),
        title="[bold blue]Portfolio Health[/bold blue]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print()
    console.print(panel)
    return True


def _render_common_findings(engine: InsightsEngine) -> None:
    findings = engine.get_common_findings()
    console.print()
    if not findings:
        console.print("[dim]No common findings across repos.[/dim]")
        return

    table = Table(
        title="Most Common Findings",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Finding", style="yellow")
    table.add_column("Repos Affected", justify="right")
    table.add_column("Total Occurrences", justify="right")

    for f in findings:
        table.add_row(
            f["finding"],
            str(f["repo_count"]),
            str(f["total_occurrences"]),
        )

    console.print(table)


def _render_outliers(engine: InsightsEngine) -> None:
    outliers = engine.get_outliers()
    console.print()
    if not outliers:
        console.print("[dim]No outlier repos detected.[/dim]")
        return

    table = Table(
        title="Outlier Repos (Bottom Quartile)",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Repo")
    table.add_column("Latest Score", justify="right")
    table.add_column("Avg Score", justify="right")
    table.add_column("Runs", justify="right")

    for o in outliers:
        color = _score_color(o["latest_score"])
        table.add_row(
            o["project"],
            f"[{color}]{o['latest_score']:.1f}[/{color}]",
            f"{o['avg_score']:.1f}",
            str(o["run_count"]),
        )

    console.print(table)


def _render_trending(engine: InsightsEngine) -> None:
    trending = engine.get_trending()
    console.print()
    if not trending:
        console.print("[dim]No significant score movement detected.[/dim]")
        return

    table = Table(
        title="Trending Repos (Score Change >10)",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold",
    )
    table.add_column("Repo")
    table.add_column("Prev Score", justify="right")
    table.add_column("Latest Score", justify="right")
    table.add_column("Change", justify="right")

    for t in trending:
        color = "green" if t["direction"] == "up" else "red"
        icon = _direction_icon(t["direction"])
        table.add_row(
            t["project"],
            f"{t['previous_score']:.1f}",
            f"[{color}]{t['latest_score']:.1f}[/{color}]",
            f"[{color}]{icon}{abs(t['delta']):.1f}[/{color}]",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Main command function
# ---------------------------------------------------------------------------

def insights_command(
    db_path: Optional[Path],
    common_findings: bool,
    outliers: bool,
    trending: bool,
    all_sections: bool,
    json_output: bool,
) -> None:
    engine = InsightsEngine(db_path=db_path)

    # --json: structured output with all sections
    if json_output:
        summary = engine.get_portfolio_summary()
        payload = {
            "portfolio_summary": summary,
            "common_findings": engine.get_common_findings(),
            "outliers": engine.get_outliers(),
            "trending": engine.get_trending(),
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    # Determine which sections to show
    show_summary = not (common_findings or outliers or trending)
    show_findings = common_findings or all_sections
    show_outliers = outliers or all_sections
    show_trending = trending or all_sections

    if show_summary or all_sections:
        has_data = _render_portfolio_summary(engine)
        if not has_data and not all_sections:
            return

    if show_findings:
        _render_common_findings(engine)
    if show_outliers:
        _render_outliers(engine)
    if show_trending:
        _render_trending(engine)

    console.print()
