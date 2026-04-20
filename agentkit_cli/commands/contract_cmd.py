"""agentkit contract command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.contracts import ContractEngine

console = Console()
engine = ContractEngine()


def contract_command(
    objective: str = typer.Argument(..., help="Project objective to turn into a build contract"),
    path: Optional[str] = typer.Option(None, "--path", help="Project directory (default: .)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write contract to this file"),
    title: Optional[str] = typer.Option(None, "--title", help="Override contract title"),
    deliverable: Optional[list[str]] = typer.Option(None, "--deliverable", help="Repeatable deliverable checklist item"),
    test_requirement: Optional[list[str]] = typer.Option(None, "--test-requirement", help="Repeatable test requirement"),
    map_input: Optional[str] = typer.Option(None, "--map", help="Repo map JSON artifact or target to map before drafting the contract"),
    json_output: bool = typer.Option(False, "--json", help="Emit deterministic JSON metadata"),
) -> None:
    project_dir = Path(path).resolve() if path else Path.cwd()
    if not project_dir.exists():
        console.print(f"[red]Path not found: {project_dir}[/red]")
        raise typer.Exit(1)

    try:
        spec = engine.build_spec(
            project_dir=project_dir,
            objective=objective,
            title=title,
            deliverables=list(deliverable or []),
            test_requirements=list(test_requirement or []),
            output_path=output,
            map_input=map_input,
        )
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    try:
        written = engine.write_contract(spec)
    except FileExistsError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    payload = {
        "objective": spec.objective,
        "title": spec.title,
        "project_path": spec.project_path,
        "output_path": str(written),
        "source_context_path": spec.source_context.path,
        "source_context_format": spec.source_context.format,
        "deliverables": spec.deliverables,
        "test_requirements": spec.test_requirements,
        "command_hints": spec.repo_hints.command_hints,
        "context_boundaries": spec.repo_hints.boundaries,
        "report_sections": spec.report_sections,
        "map_context": spec.map_context.to_dict() if spec.map_context else None,
    }

    if json_output:
        print(json.dumps(payload, indent=2))
        return

    console.print(f"[green]Wrote[/green] {written}")
