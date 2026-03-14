"""agentkit sweep command."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import typer
from rich.console import Console

from agentkit_cli.sweep import resolve_targets, run_sweep

console = Console()


def sweep_command(
    targets: Sequence[str],
    targets_file: Optional[Path] = None,
    keep: bool = False,
    publish: bool = False,
    timeout: int = 120,
    no_generate: bool = False,
) -> None:
    """Run `agentkit analyze` across multiple targets."""
    try:
        resolved_targets = resolve_targets(targets, targets_file=targets_file)
    except OSError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    if not resolved_targets:
        console.print("[red]Error:[/red] Provide at least one target or --targets-file.")
        raise typer.Exit(code=1)

    sweep_result = run_sweep(
        resolved_targets,
        keep=keep,
        publish=publish,
        timeout=timeout,
        no_generate=no_generate,
    )

    console.print(f"[bold]agentkit sweep[/bold] — analyzed {len(sweep_result.targets)} target(s)")
    for result in sweep_result.results:
        if result.status == "succeeded":
            console.print(
                f"[green]✓[/green] {result.target} -> "
                f"{result.composite_score:.0f}/100 ({result.grade})"
            )
        else:
            console.print(f"[red]✗[/red] {result.target} -> {result.error}")
