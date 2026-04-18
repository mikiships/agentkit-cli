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
    all_files: bool = typer.Option(False, "--all", help="Discover and optimize all CLAUDE.md and AGENTS.md files under the repo"),
    check: bool = typer.Option(False, "--check", help="Exit non-zero when meaningful rewrites are available"),
    apply: bool = typer.Option(False, "--apply", help="Overwrite the targeted context file with the optimized result"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write optimized content or rendered review to file"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON"),
    fmt: str = typer.Option("text", "--format", help="Review format: text or markdown"),
) -> None:
    root = (path or Path(".")).resolve()
    engine = OptimizeEngine(root)
    renderer = OptimizeRenderer()

    if all_files and file is not None:
        console.print("[red]Error:[/red] --all cannot be combined with --file")
        raise typer.Exit(code=2)

    try:
        result = engine.optimize_sweep() if all_files else engine.optimize(file=file)
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    applied = False
    applied_files = 0
    if all_files:
        if apply:
            for item in result.results:
                if item.no_op:
                    continue
                current_text = Path(item.source_file).read_text(encoding="utf-8")
                if current_text != item.optimized_text:
                    Path(item.source_file).write_text(item.optimized_text, encoding="utf-8")
                    applied_files += 1
            result.summary.applied_files = applied_files
            applied = applied_files > 0
        exit_code = 1 if check and result.summary.rewritable_files > 0 else 0
    else:
        if apply and not result.no_op:
            current_text = Path(result.source_file).read_text(encoding="utf-8")
            if current_text != result.optimized_text:
                Path(result.source_file).write_text(result.optimized_text, encoding="utf-8")
                applied = True
        exit_code = 1 if check and not result.no_op else 0

    if json_output:
        payload = result.to_dict()
        payload["applied"] = applied
        if all_files:
            payload["applied_files"] = applied_files
        print(json.dumps(payload, indent=2))
    else:
        review = renderer.render(result, fmt=fmt)
        if apply:
            if all_files:
                console.print(f"[green]Applied optimized context to[/green] {applied_files} file(s)\n" if applied_files else "[cyan]No rewrites needed across repo sweep[/cyan]\n")
            elif applied:
                console.print(f"[green]Applied optimized context to[/green] {result.source_file}\n")
            else:
                console.print(f"[cyan]No rewrite needed for[/cyan] {result.source_file} ([bold]{result.verdict}[/bold])\n")
        console.print(review, end="")

    if output:
        if json_output:
            payload = result.to_dict()
            payload["applied"] = applied
            if all_files:
                payload["applied_files"] = applied_files
            output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            if all_files or not applied:
                output.write_text(renderer.render(result, fmt=fmt), encoding="utf-8")
            else:
                output.write_text(result.optimized_text, encoding="utf-8")

    raise typer.Exit(code=exit_code)
