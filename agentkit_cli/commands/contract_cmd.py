"""agentkit contract command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.contracts import ContractEngine
from agentkit_cli.spec_engine import SpecEngine

console = Console()
engine = ContractEngine()
spec_engine = SpecEngine()


def contract_command(
    objective: Optional[str] = typer.Argument(None, help="Project objective to turn into a build contract"),
    path: Optional[str] = typer.Option(None, "--path", help="Project directory (default: .)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write contract to this file"),
    title: Optional[str] = typer.Option(None, "--title", help="Override contract title"),
    deliverable: Optional[list[str]] = typer.Option(None, "--deliverable", help="Repeatable deliverable checklist item"),
    test_requirement: Optional[list[str]] = typer.Option(None, "--test-requirement", help="Repeatable test requirement"),
    map_input: Optional[str] = typer.Option(None, "--map", help="Repo map JSON artifact or target to map before drafting the contract"),
    spec_input: Optional[str] = typer.Option(None, "--spec", help="Saved spec.json artifact to seed the contract directly"),
    json_output: bool = typer.Option(False, "--json", help="Emit deterministic JSON metadata"),
) -> None:
    try:
        seeded_spec = spec_engine.load_artifact(spec_input) if spec_input else None
        seed = seeded_spec.contract_seed if seeded_spec else None
        project_dir = Path(path).resolve() if path else Path(seeded_spec.project_path).resolve() if seeded_spec else Path.cwd()
        if not project_dir.exists():
            console.print(f"[red]Path not found: {project_dir}[/red]")
            raise typer.Exit(1)
        if objective is None and seed is None:
            console.print("[red]Provide an objective or --spec[/red]")
            raise typer.Exit(1)

        spec = engine.build_spec(
            project_dir=project_dir,
            objective=objective or seed.objective,
            title=title or (seed.title if seed else None),
            deliverables=list(deliverable or (seed.deliverables if seed else [])),
            test_requirements=list(test_requirement or (seed.test_requirements if seed else [])),
            output_path=output,
            map_input=map_input or (seed.map_input if seed else None),
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
