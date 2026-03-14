"""agentkit doctor command wrapper."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from agentkit_cli.doctor import render_human_report, run_doctor


def doctor_command(json_output: bool = False, path: Path | None = None) -> None:
    """Run doctor checks and print either human or JSON output."""
    report = run_doctor(root=path)

    if json_output:
        typer.echo(json.dumps(report.as_dict(), indent=2))
    else:
        render_human_report(report)

    raise typer.Exit(code=report.exit_code())
