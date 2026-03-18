"""agentkit sync command — keep context format files in sync."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.migrate import (
    MigrateEngine,
    FORMAT_FILENAMES,
    KNOWN_FORMATS,
)

console = Console()
engine = MigrateEngine()

_STATUS_ICONS = {
    "source": "[cyan]source[/cyan]",
    "ok": "[green]ok[/green]",
    "stale": "[yellow]stale[/yellow]",
    "missing": "[dim]missing[/dim]",
    "unmanaged": "[dim]unmanaged[/dim]",
}


def sync_command(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    check: bool = typer.Option(False, "--check", help="Report sync status; exit 1 if stale"),
    fix: bool = typer.Option(False, "--fix", help="Re-run migrate to bring derived files in sync"),
) -> None:
    """Check or fix sync status between AGENTS.md, CLAUDE.md, and llms.txt."""
    project_dir = Path(path).resolve() if path else Path.cwd()

    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    status = engine.get_sync_status(project_dir)

    if not status:
        console.print("[yellow]No managed context files found (AGENTS.md, CLAUDE.md, llms.txt)[/yellow]")
        raise typer.Exit(1)

    # Print table
    table = Table(title="agentkit sync — context format status", show_header=True)
    table.add_column("Format")
    table.add_column("File")
    table.add_column("Status")

    stale_or_missing: list[str] = []
    for fmt in KNOWN_FORMATS:
        s = status.get(fmt, "missing")
        fname = FORMAT_FILENAMES[fmt]
        table.add_row(fmt, fname, _STATUS_ICONS.get(s, s))
        if s in ("stale", "missing"):
            stale_or_missing.append(fmt)

    console.print(table)

    if fix:
        # Re-run migrate for stale/missing derived files
        source_entry = next(
            ((fmt, p) for fmt, s in status.items() if s == "source"
             for p in [project_dir / FORMAT_FILENAMES[fmt]] if p.exists()),
            None,
        )
        if source_entry is None:
            console.print("[red]Cannot fix: no source file detected.[/red]")
            raise typer.Exit(1)
        source_fmt, source_path = source_entry
        source_content = source_path.read_text(encoding="utf-8", errors="replace")
        fixed = 0
        for fmt in stale_or_missing:
            r = engine.convert(source_content, source_fmt, fmt,
                               source_path=str(source_path),
                               output_path=str(project_dir / FORMAT_FILENAMES[fmt]))
            (project_dir / FORMAT_FILENAMES[fmt]).write_text(r.content, encoding="utf-8")
            console.print(f"[green]Fixed:[/green] {FORMAT_FILENAMES[fmt]}")
            fixed += 1
        if fixed == 0:
            console.print("[green]All files already in sync.[/green]")
    elif check:
        if stale_or_missing:
            console.print(
                f"[yellow]{len(stale_or_missing)} file(s) out of sync: "
                + ", ".join(FORMAT_FILENAMES[f] for f in stale_or_missing)
                + "[/yellow]"
            )
            raise typer.Exit(1)
        else:
            console.print("[green]All managed files in sync.[/green]")
    else:
        if stale_or_missing:
            console.print(
                f"[yellow]Run 'agentkit sync --fix' to update {len(stale_or_missing)} file(s).[/yellow]"
            )
