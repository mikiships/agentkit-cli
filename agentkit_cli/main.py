"""agentkit CLI entry point."""
from __future__ import annotations

import typer
from typing import Optional
from pathlib import Path

from agentkit_cli.commands.init_cmd import init_command
from agentkit_cli.commands.run_cmd import run_command
from agentkit_cli.commands.status_cmd import status_command
from agentkit_cli.commands.doctor_cmd import doctor_command

app = typer.Typer(
    name="agentkit",
    help="Unified CLI for the Agent Quality Toolkit (agentmd, coderace, agentlint, agentreflect).",
    add_completion=False,
)


@app.command("init")
def init(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project root"),
) -> None:
    """Initialize agentkit in a project. Creates .agentkit.yaml and checks for quartet tools."""
    init_command(path=path)


@app.command("run")
def run(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    skip: Optional[list[str]] = typer.Option(None, "--skip", help="Steps to skip: generate, lint, benchmark, reflect"),
    benchmark: bool = typer.Option(False, "--benchmark", help="Include benchmark step (off by default)"),
    json_output: bool = typer.Option(False, "--json", help="Emit summary as JSON"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes for agentreflect"),
) -> None:
    """Run the full Agent Quality pipeline sequentially."""
    run_command(path=path, skip=skip, benchmark=benchmark, json_output=json_output, notes=notes)


@app.command("doctor")
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Emit results as JSON"),
) -> None:
    """Diagnose whether all quartet tools are installed and functional."""
    doctor_command(json_output=json_output)


@app.command("status")
def status(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    json_output: bool = typer.Option(False, "--json", help="Emit status as JSON"),
) -> None:
    """Show health status of toolkit and current project."""
    status_command(path=path, json_output=json_output)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
) -> None:
    if version:
        from agentkit_cli import __version__
        typer.echo(f"agentkit-cli v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
