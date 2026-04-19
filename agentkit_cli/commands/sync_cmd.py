"""agentkit sync command, keep context format files in sync."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.context_projections import (
    ContextProjectionEngine,
    FORMAT_AGENTKIT_SOURCE,
    FORMAT_FILENAMES,
    FORMAT_AGENTS_MD,
    FORMAT_CLAUDE_MD,
    FORMAT_LLMSTXT,
    KNOWN_FORMATS,
    source_path_for_format,
)

console = Console()
engine = ContextProjectionEngine()

_STATUS_ICONS = {
    "source": "[cyan]source[/cyan]",
    "ok": "[green]ok[/green]",
    "stale": "[yellow]stale[/yellow]",
    "missing": "[dim]missing[/dim]",
    "unmanaged": "[dim]unmanaged[/dim]",
}

_DISPLAY_FILES = {
    FORMAT_AGENTKIT_SOURCE: ".agentkit/source.md",
    **FORMAT_FILENAMES,
}


def sync_command(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    check: bool = typer.Option(False, "--check", help="Report sync status; exit 1 if stale"),
    fix: bool = typer.Option(False, "--fix", help="Refresh stale or missing projected files"),
) -> None:
    project_dir = Path(path).resolve() if path else Path.cwd()
    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    status = engine.get_sync_status(project_dir)
    if not status:
        console.print("[yellow]No managed context files found[/yellow]")
        raise typer.Exit(1)

    table = Table(title="agentkit sync, context projection status", show_header=True)
    table.add_column("Format")
    table.add_column("File")
    table.add_column("Status")

    stale_or_missing: list[str] = []
    source_fmt = next((fmt for fmt, state in status.items() if state == "source"), None)
    required_for_check = {FORMAT_AGENTS_MD, FORMAT_CLAUDE_MD, FORMAT_LLMSTXT}
    display_formats = [FORMAT_AGENTKIT_SOURCE] + list(KNOWN_FORMATS) if status.get(FORMAT_AGENTKIT_SOURCE) == "source" else list(KNOWN_FORMATS)
    for fmt in display_formats:
        state = status.get(fmt, "missing")
        table.add_row(fmt, _DISPLAY_FILES[fmt], _STATUS_ICONS.get(state, state))
        if fmt in KNOWN_FORMATS and (state == "stale" or (state == "missing" and fmt in required_for_check)):
            stale_or_missing.append(fmt)
    console.print(table)

    if fix:
        if source_fmt is None:
            console.print("[red]Cannot fix: no canonical source detected.[/red]")
            raise typer.Exit(1)
        source_path = source_path_for_format(project_dir, source_fmt)
        source_content = source_path.read_text(encoding="utf-8", errors="replace")
        fixed = 0
        for fmt in KNOWN_FORMATS:
            if fmt == source_fmt:
                continue
            state = status.get(fmt, "missing")
            if state not in {"missing", "stale"}:
                continue
            out_path = project_dir / FORMAT_FILENAMES[fmt]
            result = engine.convert(source_content, source_fmt, fmt, str(source_path), str(out_path))
            out_path.write_text(result.content, encoding="utf-8")
            console.print(f"[green]Fixed:[/green] {out_path.name}")
            fixed += 1
        if fixed == 0:
            console.print("[green]All files already in sync.[/green]")
    elif check and stale_or_missing:
        console.print("[yellow]Projected files drifted or missing: " + ", ".join(FORMAT_FILENAMES[f] for f in stale_or_missing) + "[/yellow]")
        raise typer.Exit(1)
    elif check:
        console.print("[green]All managed files in sync.[/green]")
    elif stale_or_missing:
        console.print(f"[yellow]Run 'agentkit sync --fix' to update {len(stale_or_missing)} file(s).[/yellow]")
