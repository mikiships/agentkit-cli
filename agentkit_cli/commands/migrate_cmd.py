"""agentkit migrate command, convert between context projections."""
from __future__ import annotations

import difflib
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.context_projections import ContextProjectionEngine, FORMAT_ALL, FORMAT_FILENAMES, KNOWN_FORMATS, normalize_format

console = Console()
engine = ContextProjectionEngine()


def _resolve_format(value: str) -> str:
    try:
        return normalize_format(value)
    except ValueError:
        console.print(f"[red]Unknown format: {value}[/red]")
        raise typer.Exit(1)


def migrate_command(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    from_format: Optional[str] = typer.Option(None, "--from", help="Source format override"),
    to_format: Optional[str] = typer.Option(None, "--to", help="Target format or all"),
    all_formats: bool = typer.Option(False, "--all", help="Equivalent to --to all"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print what would be written without writing"),
    diff: bool = typer.Option(False, "--diff", help="Show before/after diff of each file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write to specific file instead of default"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without prompting"),
) -> None:
    project_dir = Path(path).resolve() if path else Path.cwd()
    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    resolved_to = _resolve_format("all" if all_formats else (to_format or "all"))
    resolved_from = _resolve_format(from_format or "auto")

    detected = engine.detect_source(project_dir, override=None if resolved_from == "auto" else resolved_from)
    if detected is None:
        console.print(f"[red]No AGENTS.md, CLAUDE.md, AGENT.md, GEMINI.md, COPILOT.md, or llms.txt found in {project_dir}[/red]")
        raise typer.Exit(1)
    source_fmt, source_path = detected
    source_content = source_path.read_text(encoding="utf-8", errors="replace")

    target_formats = [fmt for fmt in KNOWN_FORMATS if fmt != source_fmt] if resolved_to == FORMAT_ALL else [resolved_to]
    results = []
    for target_fmt in target_formats:
        out_path = Path(output) if output and len(target_formats) == 1 else project_dir / FORMAT_FILENAMES[target_fmt]
        result = engine.convert(source_content, source_fmt, target_fmt, str(source_path), str(out_path))
        if out_path.exists() and not force and not dry_run:
            confirm = typer.confirm(f"Overwrite {out_path.name}?", default=True)
            if not confirm:
                result.skipped = True
                result.skip_reason = "user skipped"
                results.append(result)
                continue
        if diff:
            existing = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else ""
            diff_lines = difflib.unified_diff(existing.splitlines(keepends=True), result.content.splitlines(keepends=True), fromfile=f"{out_path.name} (before)", tofile=f"{out_path.name} (after)", n=3)
            rendered = "".join(diff_lines)
            console.print(rendered if rendered else f"[dim]No changes for {out_path.name}[/dim]")
        if not dry_run and not result.skipped:
            out_path.write_text(result.content, encoding="utf-8")
        results.append(result)

    table = Table(title="agentkit migrate", show_header=True)
    table.add_column("Source")
    table.add_column("Target")
    table.add_column("Output file")
    table.add_column("Lines")
    table.add_column("Status")
    for result in results:
        status = "[yellow]skipped[/yellow]" if result.skipped else ("[dim]dry-run[/dim]" if dry_run else "[green]written[/green]")
        table.add_row(result.source_format, result.target_format, Path(result.output_path).name, str(result.line_count), status)
    console.print(table)
