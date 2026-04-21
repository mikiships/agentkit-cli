from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.commands.relaunch_cmd import _normalize_format
from agentkit_cli.land import LandEngine, LandError

engine = LandEngine()


def land_command(
    path: str,
    json_output: bool = False,
    output: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    closeout_path: Optional[Path] = None,
    packet_dir: Optional[Path] = None,
    format: str = "markdown",
) -> None:
    project = Path(path).resolve()
    if not project.exists() or not project.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {project}")

    try:
        fmt = _normalize_format(json_output=json_output, format=format)
        plan = engine.build(project, closeout_path=closeout_path, packet_dir=packet_dir or output_dir)
    except (FileNotFoundError, LandError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    rendered = plan.to_json() if fmt == "json" else engine.render_markdown(plan)
    if output is not None:
        output.write_text(rendered, encoding="utf-8")
    if output_dir is not None:
        written = engine.write_directory(plan, output_dir)
        typer.echo(f"Wrote land directory: {written}")
    typer.echo(rendered)
