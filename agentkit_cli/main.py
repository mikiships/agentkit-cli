"""agentkit CLI entry point."""
from __future__ import annotations

import typer
from typing import List, Optional
from pathlib import Path

from agentkit_cli.commands.init_cmd import init_command
from agentkit_cli.commands.run_cmd import run_command
from agentkit_cli.commands.status_cmd import status_command
from agentkit_cli.commands.doctor_cmd import doctor_command
from agentkit_cli.commands.ci import ci_command
from agentkit_cli.commands.watch import watch_command
from agentkit_cli.commands.demo_cmd import demo_command

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
    skip: Optional[List[str]] = typer.Option(None, "--skip", help="Steps to skip: generate, lint, benchmark, reflect"),
    benchmark: bool = typer.Option(False, "--benchmark", help="Include benchmark step (off by default)"),
    json_output: bool = typer.Option(False, "--json", help="Emit summary as JSON"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes for agentreflect"),
    ci: bool = typer.Option(False, "--ci", help="CI mode: plain output, exit 1 on failure"),
) -> None:
    """Run the full Agent Quality pipeline sequentially."""
    run_command(path=path, skip=skip, benchmark=benchmark, json_output=json_output, notes=notes, ci=ci)


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


@app.command("ci")
def ci(
    python_version: str = typer.Option("3.12", "--python-version", help="Python version for the workflow"),
    benchmark: bool = typer.Option(False, "--benchmark", help="Include coderace benchmark step"),
    min_score: Optional[int] = typer.Option(None, "--min-score", help="Gate on maintainer rubric score"),
    output_dir: Path = typer.Option(Path(".github/workflows"), "--output-dir", help="Where to write the workflow file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print to stdout instead of writing file"),
) -> None:
    """Generate a GitHub Actions workflow that runs the agentkit pipeline on every PR."""
    ci_command(
        python_version=python_version,
        benchmark=benchmark,
        min_score=min_score,
        output_dir=output_dir,
        dry_run=dry_run,
    )


@app.command("demo")
def demo(
    task: Optional[str] = typer.Option(None, "--task", help="Coderace task to benchmark (default: auto-pick)"),
    agents: Optional[str] = typer.Option(None, "--agents", help="Comma-separated agents, e.g. claude,codex"),
    skip_benchmark: bool = typer.Option(False, "--skip-benchmark", help="Skip coderace benchmark step"),
    json_output: bool = typer.Option(False, "--json", help="Emit results as JSON"),
) -> None:
    """Zero-config demo: shows the toolkit in action without any setup."""
    demo_command(task=task, agents=agents, skip_benchmark=skip_benchmark, json_output=json_output)


@app.command("watch")
def watch(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to watch"),
    extensions: Optional[List[str]] = typer.Option(None, "--extensions", help="File extensions to watch (e.g. .py,.md)"),
    debounce: float = typer.Option(2.0, "--debounce", help="Debounce delay in seconds"),
    ci: bool = typer.Option(False, "--ci", help="Run pipeline in CI mode on changes"),
) -> None:
    """Watch the project for changes and re-run the pipeline automatically."""
    watch_command(path=path, extensions=extensions, debounce=debounce, ci=ci)


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
