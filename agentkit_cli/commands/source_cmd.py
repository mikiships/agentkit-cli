"""agentkit source command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.context_projections import (
    ContextProjectionEngine,
    DETECTION_PRIORITY,
    FORMAT_AGENTKIT_SOURCE,
    dedicated_source_path,
    normalize_format,
    source_path_for_format,
)

console = Console()
engine = ContextProjectionEngine()


def _relative_display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _render_template(project_dir: Path, title: Optional[str]) -> str:
    project_name = title or project_dir.name or "Project"
    return (
        f"# {project_name}\n\n"
        "## Overview\n"
        "Describe the repo, its purpose, and the outcomes agents should optimize for.\n\n"
        "## Commands\n"
        "List the build, test, lint, and run commands agents should prefer.\n\n"
        "## Patterns & Conventions\n"
        "Capture architecture constraints, coding conventions, and review expectations.\n\n"
        "## Context & Workspace\n"
        "Note important files, safety boundaries, and workflow rules for the repo.\n"
    )


def _detect_promote_source(project_dir: Path, from_format: Optional[str]) -> Optional[tuple[str, Path]]:
    if from_format:
        resolved = normalize_format(from_format)
        if resolved == FORMAT_AGENTKIT_SOURCE:
            return None
        return engine.detect_source(project_dir, override=resolved)

    for fmt in DETECTION_PRIORITY:
        if fmt == FORMAT_AGENTKIT_SOURCE:
            continue
        candidate = source_path_for_format(project_dir, fmt)
        if candidate.exists():
            return fmt, candidate
    for candidate in sorted(project_dir.iterdir() if project_dir.exists() else []):
        if candidate.is_file():
            fmt = engine.detect_format(candidate)
            if fmt and fmt != FORMAT_AGENTKIT_SOURCE:
                return fmt, candidate
    return None


def source_command(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    init: bool = typer.Option(False, "--init", help="Create a fresh dedicated canonical source template"),
    promote: bool = typer.Option(False, "--promote", help="Copy the best detected legacy context file into the dedicated source path"),
    from_format: Optional[str] = typer.Option(None, "--from", help="Legacy source format to promote explicitly"),
    title: Optional[str] = typer.Option(None, "--title", help="Template title to use with --init"),
    force: bool = typer.Option(False, "--force", help="Overwrite the dedicated source file if it already exists"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON summary"),
) -> None:
    project_dir = Path(path).resolve() if path else Path.cwd()
    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    if init == promote:
        console.print("[red]Choose exactly one of --init or --promote[/red]")
        raise typer.Exit(1)

    destination = dedicated_source_path(project_dir)
    if destination.exists() and not force:
        console.print(f"[red]Dedicated source already exists: {_relative_display(destination, project_dir)}[/red]")
        raise typer.Exit(1)

    action = "init"
    copied_from: Optional[str] = None
    promoted_format: Optional[str] = None
    if init:
        content = _render_template(project_dir, title)
    else:
        detected = _detect_promote_source(project_dir, from_format)
        if detected is None:
            console.print("[red]No legacy source found to promote into .agentkit/source.md[/red]")
            raise typer.Exit(1)
        promoted_format, source_path = detected
        copied_from = str(source_path)
        content = source_path.read_text(encoding="utf-8", errors="replace")
        action = "promote"

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")

    payload = {
        "action": action,
        "destination": str(destination),
        "destination_display": _relative_display(destination, project_dir),
        "source_format": FORMAT_AGENTKIT_SOURCE,
        "promoted_from": copied_from,
        "promoted_from_format": promoted_format,
    }

    if json_output:
        print(json.dumps(payload, indent=2))
        return

    if action == "init":
        console.print(f"[green]Initialized[/green] {_relative_display(destination, project_dir)}")
    else:
        console.print(
            f"[green]Promoted[/green] {_relative_display(Path(copied_from or ''), project_dir)} -> {_relative_display(destination, project_dir)}"
        )
