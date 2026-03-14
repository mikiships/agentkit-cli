"""agentkit sweep command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.sweep import resolve_targets, run_sweep, sort_results

console = Console()


def sweep_command(
    targets: Sequence[str],
    targets_file: Optional[Path] = None,
    keep: bool = False,
    publish: bool = False,
    timeout: int = 120,
    no_generate: bool = False,
    sort_by: str = "score",
    limit: Optional[int] = None,
    json_output: bool = False,
) -> None:
    """Run `agentkit analyze` across multiple targets."""
    try:
        resolved_targets = resolve_targets(targets, targets_file=targets_file)
    except OSError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    if not resolved_targets:
        if json_output:
            console.print(json.dumps({"error": "Provide at least one target or --targets-file."}))
        else:
            console.print("[red]Error:[/red] Provide at least one target or --targets-file.")
        raise typer.Exit(code=1)

    sweep_result = run_sweep(
        resolved_targets,
        keep=keep,
        publish=publish,
        timeout=timeout,
        no_generate=no_generate,
    )

    # Sort results
    sorted_results = sort_results(sweep_result.results, sort_by=sort_by)

    if json_output:
        # Stable JSON output (D3)
        ranked_results = []
        for rank, result in enumerate(sorted_results, 1):
            entry: dict = {
                "rank": rank,
                "target": result.target,
                "score": result.composite_score,
                "grade": result.grade,
                "status": result.status,
            }
            if result.error is not None:
                entry["error"] = result.error
            ranked_results.append(entry)

        output = {
            "targets": list(sweep_result.targets),
            "results": ranked_results,
            "summary_counts": sweep_result.summary_counts(),
        }
        console.print(json.dumps(output, indent=2))
        return

    # Apply limit for display only
    display_results = sorted_results[:limit] if limit else sorted_results

    console.print(
        f"\n[bold]agentkit sweep[/bold] — analyzed {len(sweep_result.results)} target(s)\n"
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("target")
    table.add_column("score", justify="right")
    table.add_column("grade", justify="center")
    table.add_column("status")
    table.add_column("error")

    for result in display_results:
        score_str = f"{result.composite_score:.0f}" if result.composite_score is not None else "—"
        grade_str = result.grade or "—"
        if result.status == "succeeded":
            status_str = "[green]✓ succeeded[/green]"
        else:
            status_str = "[red]✗ failed[/red]"
        error_str = result.error or ""

        table.add_row(result.target, score_str, grade_str, status_str, error_str)

    console.print(table)

    counts = sweep_result.summary_counts()
    if limit and limit < len(sorted_results):
        console.print(f"\nShowing top {limit} of {len(sorted_results)} results.")
    console.print(
        f"\n[dim]Total: {counts['total']} | "
        f"Succeeded: {counts['succeeded']} | "
        f"Failed: {counts['failed']}[/dim]"
    )
