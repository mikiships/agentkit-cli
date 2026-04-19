"""agentkit project command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.context_projections import (
    ContextProjectionEngine,
    FORMAT_ALL,
    FORMAT_FILENAMES,
    KNOWN_FORMATS,
    normalize_format,
)

console = Console()
engine = ContextProjectionEngine()


def _resolve_targets(value: str) -> list[str]:
    if value.lower().strip() == "all":
        return list(KNOWN_FORMATS)
    targets: list[str] = []
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        targets.append(normalize_format(chunk))
    unknown = [t for t in targets if t == FORMAT_ALL]
    if unknown:
        raise ValueError("'all' cannot be mixed with other targets")
    return targets


def project_command(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    from_format: Optional[str] = typer.Option(None, "--from", help="Canonical source format override"),
    targets: str = typer.Option("all", "--targets", help="Comma-separated target list or 'all'"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", help="Write projected files into this directory"),
    check: bool = typer.Option(False, "--check", help="Exit non-zero when projected output would drift"),
    write: bool = typer.Option(False, "--write", help="Write projected files"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON summary"),
) -> None:
    project_dir = Path(path).resolve() if path else Path.cwd()
    destination_dir = Path(output_dir).resolve() if output_dir else project_dir

    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    try:
        requested_targets = _resolve_targets(targets)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    detected = engine.detect_source(project_dir, override=from_format)
    if detected is None:
        console.print(f"[red]No canonical source found in {project_dir}[/red]")
        raise typer.Exit(1)
    source_format, source_path = detected
    source_content = source_path.read_text(encoding="utf-8", errors="replace")

    written_targets: list[str] = []
    drifted_targets: list[str] = []
    skipped_targets: list[str] = []

    table = Table(title="agentkit project", show_header=True)
    table.add_column("Target")
    table.add_column("File")
    table.add_column("Status")

    for target in requested_targets:
        out_path = destination_dir / FORMAT_FILENAMES[target]
        result = engine.convert(
            source_content=source_content,
            source_format=source_format,
            target_format=target,
            source_path=str(source_path),
            output_path=str(out_path),
        )
        status = "would-write"
        if out_path.exists():
            existing = out_path.read_text(encoding="utf-8", errors="replace")
            if existing == result.content:
                status = "ok"
            else:
                status = "drifted"
                drifted_targets.append(target)
        elif check:
            status = "missing"
            drifted_targets.append(target)

        if target == source_format and destination_dir == project_dir:
            status = "source"
            skipped_targets.append(target)
        elif write and status in {"would-write", "drifted", "missing"}:
            destination_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_text(result.content, encoding="utf-8")
            written_targets.append(target)
            status = "written"
        elif status == "ok":
            skipped_targets.append(target)

        table.add_row(target, out_path.name, status)

    payload = {
        "canonical_source": str(source_path),
        "canonical_source_format": source_format,
        "requested_targets": requested_targets,
        "written_targets": written_targets,
        "drifted_targets": drifted_targets,
        "skipped_targets": skipped_targets,
        "output_dir": str(destination_dir),
    }

    if json_output:
        print(json.dumps(payload, indent=2))
    else:
        console.print(table)
        if not write:
            console.print("[dim]Dry-run only. Re-run with --write to materialize projections.[/dim]")

    if check and drifted_targets:
        raise typer.Exit(1)
