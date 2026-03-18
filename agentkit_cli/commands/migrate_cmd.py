"""agentkit migrate command — convert between AGENTS.md/CLAUDE.md/llms.txt."""
from __future__ import annotations

import difflib
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.migrate import (
    MigrateEngine,
    FORMAT_AGENTS_MD,
    FORMAT_CLAUDE_MD,
    FORMAT_LLMSTXT,
    FORMAT_ALL,
    FORMAT_FILENAMES,
    KNOWN_FORMATS,
)

console = Console()
engine = MigrateEngine()


def _resolve_format(value: str) -> str:
    mapping = {
        "agents": FORMAT_AGENTS_MD,
        "agents-md": FORMAT_AGENTS_MD,
        "claude": FORMAT_CLAUDE_MD,
        "claude-md": FORMAT_CLAUDE_MD,
        "llmstxt": FORMAT_LLMSTXT,
        "llms": FORMAT_LLMSTXT,
        "llms.txt": FORMAT_LLMSTXT,
        "all": FORMAT_ALL,
        "auto": "auto",
    }
    key = value.lower().strip()
    if key in mapping:
        return mapping[key]
    console.print(f"[red]Unknown format: {value}[/red]")
    raise typer.Exit(1)


def migrate_command(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    from_format: Optional[str] = typer.Option(None, "--from", help="Source format: agents-md, claude-md, llmstxt, auto"),
    to_format: Optional[str] = typer.Option(None, "--to", help="Target format: agents-md, claude-md, llmstxt, all"),
    all_formats: bool = typer.Option(False, "--all", help="Equivalent to --to all"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print what would be written without writing"),
    diff: bool = typer.Option(False, "--diff", help="Show before/after diff of each file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write to specific file instead of default"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without prompting"),
) -> None:
    """Convert between AGENTS.md, CLAUDE.md, and llms.txt formats."""
    project_dir = Path(path).resolve() if path else Path.cwd()

    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    # Resolve --to / --all
    resolved_to = FORMAT_ALL if all_formats else (to_format or FORMAT_ALL)
    resolved_to = _resolve_format(resolved_to)

    # Resolve --from
    src_fmt_input = from_format or "auto"
    resolved_from = _resolve_format(src_fmt_input)

    # Auto-detect source if needed
    if resolved_from == "auto":
        detected = engine.detect_source(project_dir)
        if detected is None:
            console.print(
                f"[red]No AGENTS.md, CLAUDE.md, or llms.txt found in {project_dir}[/red]"
            )
            raise typer.Exit(1)
        resolved_from, source_path = detected
        source_content = source_path.read_text(encoding="utf-8", errors="replace")
        console.print(f"[dim]Auto-detected source: {source_path.name} ({resolved_from})[/dim]")
    else:
        # Look for the file with the expected filename
        expected_name = FORMAT_FILENAMES.get(resolved_from)
        if expected_name:
            source_path = project_dir / expected_name
        else:
            console.print(f"[red]Unknown source format: {resolved_from}[/red]")
            raise typer.Exit(1)
        if not source_path.exists():
            console.print(f"[red]Source file not found: {source_path}[/red]")
            raise typer.Exit(1)
        source_content = source_path.read_text(encoding="utf-8", errors="replace")

    # Build list of target formats
    if resolved_to == FORMAT_ALL:
        target_formats = [f for f in KNOWN_FORMATS if f != resolved_from]
    else:
        target_formats = [resolved_to]

    # Run conversions
    results = []
    for target_fmt in target_formats:
        out_path = Path(output) if output and len(target_formats) == 1 else project_dir / FORMAT_FILENAMES[target_fmt]
        r = engine.convert(
            source_content=source_content,
            source_format=resolved_from,
            target_format=target_fmt,
            source_path=str(source_path),
            output_path=str(out_path),
        )
        r.output_path = str(out_path)

        # Check existing file
        if out_path.exists() and not force and not dry_run:
            confirm = typer.confirm(f"Overwrite {out_path.name}?", default=True)
            if not confirm:
                r.skipped = True
                r.skip_reason = "user skipped"
                results.append(r)
                continue

        # Show diff if requested
        if diff:
            existing = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else ""
            diff_lines = list(difflib.unified_diff(
                existing.splitlines(keepends=True),
                r.content.splitlines(keepends=True),
                fromfile=f"{out_path.name} (before)",
                tofile=f"{out_path.name} (after)",
                n=3,
            ))
            if diff_lines:
                console.print("".join(diff_lines))
            else:
                console.print(f"[dim]No changes for {out_path.name}[/dim]")

        # Write or dry-run
        if not dry_run:
            out_path.write_text(r.content, encoding="utf-8")

        results.append(r)

    # Summary table
    table = Table(title="agentkit migrate", show_header=True)
    table.add_column("Source")
    table.add_column("Target")
    table.add_column("Output file")
    table.add_column("Lines")
    table.add_column("Status")

    for r in results:
        if r.skipped:
            status = "[yellow]skipped[/yellow]"
        elif dry_run:
            status = "[dim]dry-run[/dim]"
        else:
            status = "[green]written[/green]"
        table.add_row(
            r.source_format,
            r.target_format,
            Path(r.output_path).name,
            str(r.line_count),
            status,
        )

    console.print(table)
