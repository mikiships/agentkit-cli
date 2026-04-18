"""agentkit optimize command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.optimize import OptimizeEngine
from agentkit_cli.renderers.optimize_renderer import OptimizeRenderer

console = Console()


def optimize_command(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory (default: cwd)"),
    file: Optional[Path] = typer.Option(None, "--file", help="Explicit CLAUDE.md or AGENTS.md target"),
    apply: bool = typer.Option(False, "--apply", help="Overwrite the targeted context file with the optimized result"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write optimized content or rendered review to file"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON"),
    fmt: str = typer.Option("text", "--format", help="Review format: text or markdown"),
) -> None:
    root = (path or Path(".")).resolve()
    engine = OptimizeEngine(root)
    renderer = OptimizeRenderer()

    try:
        result = engine.optimize(file=file)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    applied = False
    if apply and not result.no_op:
        current_text = Path(result.source_file).read_text(encoding="utf-8")
        if current_text != result.optimized_text:
            Path(result.source_file).write_text(result.optimized_text, encoding="utf-8")
            applied = True

    if json_output:
        payload = result.to_dict()
        payload["applied"] = applied
        print(json.dumps(payload, indent=2))
    else:
        review = renderer.render(result, fmt=fmt)
        if apply:
            if applied:
                console.print(f"[green]Applied optimized context to[/green] {result.source_file}\n")
            else:
                console.print(f"[cyan]No rewrite needed for[/cyan] {result.source_file}\n")
        console.print(review, end="")

    if output:
        content = result.to_dict() if json_output else (result.optimized_text if applied else renderer.render(result, fmt=fmt))
        if isinstance(content, dict):
            output.write_text(json.dumps(content, indent=2), encoding="utf-8")
        else:
            output.write_text(content, encoding="utf-8")
