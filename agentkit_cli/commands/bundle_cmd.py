from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.bundle import BundleEngine

engine = BundleEngine()


def _normalize_format(json_output: bool, format: str) -> str:
    if json_output:
        return "json"
    value = format.strip().lower()
    if value == "text":
        return "markdown"
    if value not in {"markdown", "json"}:
        raise ValueError("format must be markdown, text, or json")
    return value


def bundle_command(
    path: str,
    json_output: bool = False,
    output: Optional[Path] = None,
    format: str = "markdown",
) -> None:
    target = Path(path).resolve()
    if not target.exists() or not target.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {target}")

    fmt = _normalize_format(json_output=json_output, format=format)
    bundle = engine.build(target)
    rendered = bundle.to_json() if fmt == "json" else engine.render_markdown(bundle)

    if output is not None:
        output.write_text(rendered, encoding="utf-8")

    typer.echo(rendered)
