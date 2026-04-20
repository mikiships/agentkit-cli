from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.materialize import MaterializeEngine, MaterializeError

engine = MaterializeEngine()


def _normalize_format(json_output: bool, format: str) -> str:
    if json_output:
        return "json"
    value = format.strip().lower()
    if value == "text":
        return "markdown"
    if value not in {"markdown", "json"}:
        raise ValueError("format must be markdown, text, or json")
    return value


def materialize_command(
    path: str,
    target: Optional[str] = None,
    json_output: bool = False,
    output: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    worktree_root: Optional[Path] = None,
    dry_run: bool = False,
    format: str = "markdown",
) -> None:
    project = Path(path).resolve()
    if not project.exists() or not project.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {project}")

    try:
        fmt = _normalize_format(json_output=json_output, format=format)
        if dry_run:
            plan = engine.build(project, target=target, worktree_root=worktree_root, dry_run=True)
        else:
            plan = engine.materialize(project, target=target, worktree_root=worktree_root, dry_run=False)
    except (FileNotFoundError, MaterializeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    rendered = plan.to_json() if fmt == "json" else engine.render_markdown(plan)
    if output is not None:
        output.write_text(rendered, encoding="utf-8")
    if output_dir is not None:
        written = engine.write_directory(plan, output_dir)
        typer.echo(f"Wrote materialize directory: {written}")
    typer.echo(rendered)
