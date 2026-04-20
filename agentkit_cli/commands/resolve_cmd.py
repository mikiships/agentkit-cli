from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.resolve import ResolveEngine

engine = ResolveEngine()


def _normalize_format(json_output: bool, format: str) -> str:
    if json_output:
        return "json"
    value = format.strip().lower()
    if value == "text":
        return "markdown"
    if value not in {"markdown", "json"}:
        raise ValueError("format must be markdown, text, or json")
    return value


def resolve_command(
    path: str,
    answers: Path,
    target: str = "generic",
    json_output: bool = False,
    output: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    format: str = "markdown",
) -> None:
    project = Path(path).resolve()
    if not project.exists() or not project.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {project}")
    answers_path = answers.resolve()
    if not answers_path.exists() or not answers_path.is_file():
        raise typer.BadParameter(f"Answers file not found: {answers_path}")

    try:
        fmt = _normalize_format(json_output=json_output, format=format)
        result = engine.build(project, answers_path=answers_path, target=target)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    rendered = result.to_json() if fmt == "json" else engine.render_markdown(result)
    if output is not None:
        output.write_text(rendered, encoding="utf-8")
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "resolve.md").write_text(engine.render_markdown(result), encoding="utf-8")
        (output_dir / "resolve.json").write_text(result.to_json(), encoding="utf-8")
        typer.echo(f"Wrote resolve directory: {output_dir.resolve()}")
    typer.echo(rendered)
