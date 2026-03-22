"""agentkit hooks command — install/uninstall/status/run pre-commit quality gates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.hooks import HookEngine

console = Console()
hooks_app = typer.Typer(name="hooks", help="Manage pre-commit quality gate hooks.")
_engine = HookEngine()


@hooks_app.command("install")
def hooks_install(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Repo root (default: current directory)"),
    min_score: int = typer.Option(60, "--min-score", help="Minimum score threshold (default: 60)"),
    mode: str = typer.Option("both", "--mode", help="Hook mode: git|precommit|both (default: both)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be installed without writing"),
) -> None:
    """Install agentkit quality gate hooks in a git repository."""
    if mode not in ("git", "precommit", "both"):
        typer.echo(f"Invalid --mode '{mode}'. Must be one of: git, precommit, both", err=True)
        raise typer.Exit(code=2)

    path = path.resolve()

    if dry_run:
        if mode in ("git", "both"):
            console.print(f"[cyan]Would install:[/cyan] git hook at [bold]{path / '.git' / 'hooks' / 'pre-commit'}[/bold] (min-score={min_score})")
        if mode in ("precommit", "both"):
            console.print(f"[cyan]Would install:[/cyan] pre-commit hook in [bold]{path / '.pre-commit-config.yaml'}[/bold] (min-score={min_score})")
        console.print("[dim]Dry run: no files written.[/dim]")
        return

    results = _engine.install(path=path, mode=mode, min_score=min_score)

    git_result = results.get("git")
    precommit_result = results.get("precommit")

    if git_result:
        status = git_result.get("status", "")
        if status == "installed":
            console.print(f"[green]✓[/green] Installed git hook at [bold]{path / '.git' / 'hooks' / 'pre-commit'}[/bold]")
        elif status == "skipped":
            console.print(f"[yellow]Skipped git hook:[/yellow] {git_result.get('reason', '')}")
        else:
            console.print(f"[dim]Git hook: {git_result}[/dim]")

    if precommit_result:
        status = precommit_result.get("status", "")
        if status == "installed":
            console.print(f"[green]✓[/green] Updated [bold]{path / '.pre-commit-config.yaml'}[/bold]")
        else:
            console.print(f"[dim]pre-commit: {precommit_result}[/dim]")


@hooks_app.command("status")
def hooks_status(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Repo root (default: current directory)"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Show hook installation status for a repository."""
    path = path.resolve()
    result = _engine.status(path)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
        return

    git_icon = "[green]✓[/green]" if result["git_installed"] else "[red]✗[/red]"
    pc_icon = "[green]✓[/green]" if result["precommit_installed"] else "[red]✗[/red]"
    console.print(f"  git hook:      {git_icon}")
    console.print(f"  pre-commit:    {pc_icon}")
    if result.get("min_score") is not None:
        console.print(f"  min-score:     {result['min_score']}")
    if not result["git_installed"] and not result["precommit_installed"]:
        console.print("[dim]Tip: run [bold]agentkit hooks install[/bold] to add quality gates.[/dim]")


@hooks_app.command("uninstall")
def hooks_uninstall(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Repo root (default: current directory)"),
    mode: str = typer.Option("both", "--mode", help="Hook mode to remove: git|precommit|both (default: both)"),
) -> None:
    """Remove agentkit quality gate hooks."""
    if mode not in ("git", "precommit", "both"):
        typer.echo(f"Invalid --mode '{mode}'. Must be one of: git, precommit, both", err=True)
        raise typer.Exit(code=2)

    path = path.resolve()
    results = _engine.uninstall(path=path, mode=mode)

    git_result = results.get("git")
    precommit_result = results.get("precommit")

    if git_result:
        status = git_result.get("status", "")
        if status == "removed":
            console.print(f"[green]✓[/green] Removed git hook at [bold]{path / '.git' / 'hooks' / 'pre-commit'}[/bold]")
        elif status == "not_found":
            console.print("[dim]Git hook not installed.[/dim]")
        else:
            console.print(f"[dim]Git hook: {git_result}[/dim]")

    if precommit_result:
        status = precommit_result.get("status", "")
        if status == "removed":
            console.print(f"[green]✓[/green] Removed agentkit entry from [bold]{path / '.pre-commit-config.yaml'}[/bold]")
        elif status == "not_found":
            console.print("[dim]pre-commit hook not installed.[/dim]")
        else:
            console.print(f"[dim]pre-commit: {precommit_result}[/dim]")


@hooks_app.command("run")
def hooks_run(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Repo root (default: current directory)"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Manually run the hook quality check."""
    path = path.resolve()
    result = _engine.check(path)

    if json_output:
        typer.echo(json.dumps(result, indent=2))
    else:
        icon = "[green]✓ PASSED[/green]" if result["passed"] else "[red]✗ FAILED[/red]"
        console.print(f"  hooks run: {icon}  (min-score={result['min_score']})")
        if result.get("stdout"):
            console.print(result["stdout"].strip())
        if result.get("stderr"):
            console.print(f"[dim]{result['stderr'].strip()}[/dim]")

    if not result["passed"]:
        raise typer.Exit(code=1)
