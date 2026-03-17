"""agentkit history command — view quality score trends."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.history import HistoryDB

console = Console()

_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _sparkline(scores: list[float]) -> str:
    """Render a single-line sparkline from a list of scores."""
    if not scores:
        return ""
    lo = min(scores)
    hi = max(scores)
    span = hi - lo or 1.0
    chars = []
    for s in scores:
        idx = int((s - lo) / span * (len(_SPARK_CHARS) - 1))
        chars.append(_SPARK_CHARS[idx])
    return "".join(chars)


def _bar(score: float, width: int = 10) -> str:
    """Render a block progress bar."""
    filled = int(score / 100.0 * width)
    return "█" * filled + "░" * (width - filled)


def _trend_arrow(delta: Optional[float]) -> str:
    if delta is None:
        return "—"
    if delta > 0.05:
        return f"↑+{delta:.1f}"
    if delta < -0.05:
        return f"↓{delta:.1f}"
    return f"—{delta:+.1f}"


def history_command(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of runs to show"),
    tool: Optional[str] = typer.Option(None, "--tool", "-t", help="Filter to one tool"),
    project: Optional[str] = typer.Option(None, "--project", help="Override project name (default: cwd basename)"),
    graph: bool = typer.Option(False, "--graph", help="Show ASCII sparkline trend"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    clear: bool = typer.Option(False, "--clear", help="Delete history for this project"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt for --clear"),
    all_projects: bool = typer.Option(False, "--all-projects", help="Show history for all projects"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
    campaigns: bool = typer.Option(False, "--campaigns", help="Show campaign-grouped summary"),
    campaign_id: Optional[str] = typer.Option(None, "--campaign-id", help="Show all PRs from a specific campaign"),
) -> None:
    """Show agent quality history and trends."""
    db = HistoryDB(db_path) if db_path else HistoryDB()
    project_name = project or Path.cwd().name

    # --clear
    if clear:
        if not yes:
            confirmed = typer.confirm(f"Delete history for project '{project_name}'?")
            if not confirmed:
                typer.echo("Aborted.")
                raise typer.Exit()
        deleted = db.clear_history(project_name)
        typer.echo(f"Deleted {deleted} record(s) for project '{project_name}'.")
        return

    # --campaigns
    if campaigns:
        _show_campaigns(db, json_output, limit)
        return

    # --campaign-id
    if campaign_id:
        _show_campaign_detail(db, campaign_id, json_output)
        return

    # --all-projects
    if all_projects:
        _show_all_projects(db, json_output)
        return

    # Fetch rows
    rows = db.get_history(project=project_name, tool=tool or None, limit=limit)

    # --graph
    if graph:
        overall_rows = db.get_history(project=project_name, tool="overall", limit=10)
        scores = [r["score"] for r in reversed(overall_rows)]
        spark = _sparkline(scores)
        if json_output:
            result = {"runs": rows, "sparkline": spark}
            typer.echo(json.dumps(result, indent=2))
            return
        typer.echo(f"\nQuality trend for {project_name} (last {len(scores)} overall runs):")
        typer.echo(f"  {spark}  [{min(scores, default=0):.0f}–{max(scores, default=0):.0f}]")
        return

    # --json
    if json_output:
        overall_rows = db.get_history(project=project_name, tool="overall", limit=10)
        scores = [r["score"] for r in reversed(overall_rows)]
        result = {"runs": rows, "sparkline": _sparkline(scores)}
        typer.echo(json.dumps(result, indent=2))
        return

    # Default: Rich table
    _show_table(rows, project_name)


def _show_table(rows: list[dict], project_name: str) -> None:
    if not rows:
        console.print(f"[dim]No history found for project '{project_name}'.[/dim]")
        return

    table = Table(
        title=f"Agent Quality History — {project_name}",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Date", style="dim")
    table.add_column("Tool")
    table.add_column("Score", justify="right")
    table.add_column("Bar")
    table.add_column("Trend")

    prev_score: Optional[float] = None
    for row in rows:
        ts = row["ts"][:10]  # date only
        tool_name = row["tool"]
        score = row["score"]
        bar = _bar(score)
        delta = (score - prev_score) if prev_score is not None else None
        trend = _trend_arrow(delta)
        color = "green" if score >= 80 else "yellow" if score >= 50 else "red"
        table.add_row(
            ts,
            tool_name,
            f"[{color}]{score:.1f}[/{color}]",
            bar,
            trend,
        )
        prev_score = score

    console.print()
    console.print(table)


def _show_all_projects(db: HistoryDB, json_output: bool) -> None:
    summary = db.get_project_summary()

    if json_output:
        typer.echo(json.dumps(summary, indent=2))
        return

    if not summary:
        console.print("[dim]No history found.[/dim]")
        return

    table = Table(title="Agent Quality History — All Projects", show_header=True, header_style="bold")
    table.add_column("Project")
    table.add_column("Runs", justify="right")
    table.add_column("Latest Score", justify="right")
    table.add_column("Avg Score", justify="right")
    table.add_column("Last Run", style="dim")

    for row in summary:
        latest = row.get("latest_score")
        avg = row.get("avg_score")
        latest_str = f"{latest:.1f}" if latest is not None else "N/A"
        avg_str = f"{avg:.1f}" if avg is not None else "N/A"
        table.add_row(
            row["project"],
            str(row["run_count"]),
            latest_str,
            avg_str,
            (row["last_ts"] or "")[:10],
        )

    console.print()
    console.print(table)


def _show_campaigns(db: HistoryDB, json_output: bool, limit: int = 20) -> None:
    rows = db.get_campaigns(limit=limit)
    if json_output:
        typer.echo(json.dumps(rows, indent=2))
        return
    if not rows:
        console.print("[dim]No campaigns found.[/dim]")
        return
    table = Table(title="Campaign History", show_header=True, header_style="bold")
    table.add_column("Campaign ID")
    table.add_column("Target")
    table.add_column("When", style="dim")
    table.add_column("PRs", justify="right")
    table.add_column("Skipped", justify="right")
    table.add_column("Failed", justify="right")
    for row in rows:
        table.add_row(
            row["campaign_id"],
            row["target_spec"],
            (row["started_at"] or "")[:16].replace("T", " "),
            str(row["pr_count"]),
            str(row["skip_count"]),
            str(row["fail_count"]),
        )
    console.print(table)


def _show_campaign_detail(db: HistoryDB, campaign_id: str, json_output: bool) -> None:
    runs = db.get_campaign_runs(campaign_id)
    campaigns = db.get_campaigns(limit=100)
    campaign = next((c for c in campaigns if c["campaign_id"] == campaign_id), None)
    if json_output:
        typer.echo(json.dumps({"campaign": campaign, "runs": runs}, indent=2))
        return
    if campaign:
        console.print(f"[bold]Campaign:[/bold] {campaign_id}")
        console.print(f"  Target: {campaign['target_spec']}  PRs: {campaign['pr_count']}  Skipped: {campaign['skip_count']}  Failed: {campaign['fail_count']}")
    if not runs:
        console.print("[dim]No run records linked to this campaign.[/dim]")
        return
    table = Table(show_header=True, header_style="bold")
    table.add_column("Project")
    table.add_column("Tool")
    table.add_column("Score", justify="right")
    table.add_column("When", style="dim")
    for run in runs:
        table.add_row(
            run["project"],
            run["tool"],
            f"{run['score']:.1f}",
            (run["ts"] or "")[:16].replace("T", " "),
        )
    console.print(table)
