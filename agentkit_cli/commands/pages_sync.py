"""agentkit pages-sync command — sync local history DB to docs/data.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


def pages_sync_command(
    push: bool = True,
    dry_run: bool = False,
    json_output: bool = False,
    limit: Optional[int] = None,
    docs_dir: Optional[Path] = None,
    _engine: Optional[object] = None,
) -> dict:
    """Sync history DB results into docs/data.json, optionally commit+push."""
    from agentkit_cli.pages_sync_engine import SyncEngine
    from agentkit_cli.history import HistoryDB

    if _engine is None:
        engine = SyncEngine(docs_dir=docs_dir)
    else:
        engine = _engine

    if not json_output:
        mode = "[dim](dry-run)[/dim]" if dry_run else ""
        console.print(f"[bold]agentkit pages-sync[/bold] {mode}")

    summary = engine.sync(push=push, dry_run=dry_run, limit=limit)

    if json_output:
        print(json.dumps({
            "added": summary["added"],
            "updated": summary["updated"],
            "total": summary["total"],
            "pushed": summary["pushed"],
        }))
        return summary

    # Rich table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Repos added", str(summary["added"]))
    table.add_row("Repos updated", str(summary["updated"]))
    table.add_row("Total in leaderboard", str(summary["total"]))
    if push and not dry_run:
        pushed_str = "[green]yes[/green]" if summary["pushed"] else "[red]no[/red]"
        table.add_row("Pushed to GitHub", pushed_str)
    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run — no files written.[/yellow]")
    else:
        console.print(
            f"[green]✓[/green] Leaderboard updated: "
            f"{summary['added']} added, {summary['updated']} updated, "
            f"{summary['total']} total."
        )

    return summary
