"""agentkit leaderboard command — ranked comparison of run labels."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.history import HistoryDB

console = Console()

_VALID_TOOLS = {"overall", "agentmd", "agentlint", "coderace", "agentreflect"}


def _parse_since(since_str: str) -> str:
    """Parse '7d' or 'YYYY-MM-DD' into an ISO timestamp string."""
    if since_str.endswith("d"):
        days = int(since_str[:-1])
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return cutoff.isoformat()
    # Assume YYYY-MM-DD
    dt = datetime.strptime(since_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _trend_display(delta: float) -> str:
    """Format trend delta as ↑+N.N / ↓-N.N / →."""
    if delta > 0.05:
        return f"↑+{delta:.1f}"
    if delta < -0.05:
        return f"↓{delta:.1f}"
    return "→"


def leaderboard_command(
    by: str = typer.Option("overall", "--by", help="Score dimension: overall, agentmd, agentlint, coderace, agentreflect"),
    project: Optional[str] = typer.Option(None, "--project", help="Filter by project name (default: cwd basename)"),
    last: Optional[int] = typer.Option(None, "--last", help="Only use the most recent N runs per label"),
    since: Optional[str] = typer.Option(None, "--since", help="Filter by date: '7d' or 'YYYY-MM-DD'"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Show a ranked leaderboard of agent runs grouped by label."""
    if by not in _VALID_TOOLS:
        console.print(f"[red]Unknown --by dimension '{by}'. Valid: {', '.join(sorted(_VALID_TOOLS))}[/red]")
        raise typer.Exit(code=1)

    db = HistoryDB(db_path) if db_path else HistoryDB()

    project_name = project or Path.cwd().name
    since_ts = _parse_since(since) if since else None

    rows = db.get_leaderboard_data(
        tool=by,
        project=project_name,
        since=since_ts,
        last_n=last,
    )

    if json_output:
        output = {
            "tool": by,
            "project": project_name,
            "leaderboard": rows,
        }
        print(json.dumps(output, indent=2))
        return

    if not rows:
        console.print(f"[dim]No leaderboard data for project '{project_name}' (tool: {by}).[/dim]")
        console.print("[dim]Tip: run 'agentkit run --label <name>' to tag runs for comparison.[/dim]")
        return

    table = Table(
        title=f"Agent Quality Leaderboard — {project_name} (scored by {by})",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Rank", justify="right", style="bold")
    table.add_column("Label")
    table.add_column("Runs", justify="right")
    table.add_column("Avg Score", justify="right")
    table.add_column("Trend")
    table.add_column("Best", justify="right")
    table.add_column("Worst", justify="right")

    for i, row in enumerate(rows, 1):
        avg = row["avg_score"]
        color = "green" if avg >= 80 else "yellow" if avg >= 50 else "red"
        trend = _trend_display(row["trend"])
        trend_color = "green" if row["trend"] > 0.05 else "red" if row["trend"] < -0.05 else "white"
        table.add_row(
            str(i),
            row["label"],
            str(row["runs"]),
            f"[{color}]{avg:.1f}[/{color}]",
            f"[{trend_color}]{trend}[/{trend_color}]",
            f"{row['best']:.1f}",
            f"{row['worst']:.1f}",
        )

    console.print()
    console.print(table)
