from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.taskpack import TaskpackEngine

engine = TaskpackEngine()


def _normalize_format(json_output: bool, format: str) -> str:
    if json_output:
        return "json"
    value = format.strip().lower()
    if value == "text":
        return "markdown"
    if value not in {"markdown", "json"}:
        raise ValueError("format must be markdown, text, or json")
    return value


def taskpack_command(
    path: str,
    target: str = "generic",
    json_output: bool = False,
    output: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    format: str = "markdown",
) -> None:
    project = Path(path).resolve()
    if not project.exists() or not project.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {project}")

    try:
        fmt = _normalize_format(json_output=json_output, format=format)
        pack = engine.build(project, target=target)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    rendered = pack.to_json() if fmt == "json" else engine.render_markdown(pack)
    if output is not None:
        output.write_text(rendered, encoding="utf-8")
    if output_dir is not None:
        written = engine.write_directory(pack, output_dir)
        typer.echo(f"Wrote taskpack directory: {written}")
    typer.echo(rendered)
