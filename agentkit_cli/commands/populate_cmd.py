"""agentkit populate command — fetch + score top GitHub repos for configured topics."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.populate_engine import PopulateEngine

console = Console()

DEFAULT_TOPICS = "python,typescript,rust,go"


def populate_command(
    topics: str = DEFAULT_TOPICS,
    limit: int = 10,
    force: bool = False,
    dry_run: bool = False,
    json_output: bool = typer.Option(False, "--json"),
    quiet: bool = False,
    db_path: Optional[Path] = None,
    _engine: Optional[PopulateEngine] = None,
) -> Optional[dict]:
    """Fetch top GitHub repos for topics and score each with agentkit analyze."""
    topic_list = [t.strip().lower() for t in topics.split(",") if t.strip()]

    engine = _engine or PopulateEngine(db_path=db_path)

    if not quiet:
        if dry_run:
            console.print("[yellow]Dry run — showing what would be scored (no changes made).[/yellow]")
        console.print(f"Populating data for {len(topic_list)} topic(s): {', '.join(topic_list)}")

    progress_messages: List[str] = []

    def _progress(repo: str, current: int, total: int) -> None:
        msg = f"Scoring {repo} ({current}/{total})"
        progress_messages.append(msg)

    if not quiet and not dry_run:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Populating repos…", total=None)

            # Run with inline progress updates
            class _CB:
                def __call__(self, repo: str, current: int, total: int) -> None:
                    progress.update(task, description=f"Scoring {repo} ({current}/{total})")

            result = engine.populate(
                topics=topic_list,
                limit=limit,
                force_refresh=force,
                dry_run=dry_run,
                quiet=quiet,
                progress_callback=_CB(),
            )
    else:
        result = engine.populate(
            topics=topic_list,
            limit=limit,
            force_refresh=force,
            dry_run=dry_run,
            quiet=quiet,
        )

    summary = result.to_dict()

    if json_output:
        print(json.dumps(summary, indent=2))
    elif not quiet:
        table = Table(title="Populate Summary", show_header=True)
        table.add_column("Topic")
        table.add_column("Repos Scored", justify="right")
        table.add_column("Avg Score", justify="right")
        table.add_column("Skipped", justify="right")
        table.add_column("Time (s)", justify="right")
        for tr in result.topic_results:
            table.add_row(
                tr.topic,
                str(tr.repo_count),
                f"{tr.avg_score:.1f}" if tr.repo_count else "—",
                str(tr.skipped_count),
                f"{tr.elapsed:.1f}",
            )
        console.print(table)
        total_s = f"{result.total_elapsed:.1f}s"
        console.print(
            f"\n[bold green]✓ Done:[/bold green] {result.total_scored} scored, "
            f"{result.total_skipped} skipped  [{total_s}]"
        )

    return summary
