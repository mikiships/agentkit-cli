"""agentkit init command."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli.tools import QUARTET_TOOLS, is_installed, INSTALL_HINTS
from agentkit_cli.config import find_project_root, config_path, config_exists, write_default_config
from agentkit_cli.commands.project_cmd import project_command

console = Console()


def init_command(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project root (default: git root or cwd)"),
    project_targets: Optional[str] = typer.Option(None, "--project-targets", help="Optional projection fan-out after init, for example 'all' or 'claude,gemini'"),
    write_projections: bool = typer.Option(False, "--write-projections", help="Write requested projections during init"),
) -> None:
    """Initialize agentkit in a project directory."""
    root = path or find_project_root()
    console.print(f"\n[bold]Initializing agentkit in:[/bold] {root}\n")

    table = Table(title="Agent Quality Toolkit, Tool Status", show_header=True)
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Install Command")

    missing = []
    for tool in QUARTET_TOOLS:
        if is_installed(tool):
            table.add_row(tool, "[green]✓ installed[/green]", "")
        else:
            table.add_row(tool, "[red]✗ missing[/red]", INSTALL_HINTS.get(tool, f"pip install {tool}"))
            missing.append(tool)

    console.print(table)

    cfg_path = config_path(root)
    if config_exists(root):
        console.print(f"\n[yellow]Config already exists:[/yellow] {cfg_path}")
    else:
        written = write_default_config(root)
        console.print(f"\n[green]Created config:[/green] {written}")

    if missing:
        console.print("\n[yellow]Install missing tools:[/yellow]")
        for tool in missing:
            console.print(f"  pip install {tool}")

    if project_targets:
        project_command(path=str(root), targets=project_targets, write=write_projections, check=False, json_output=False, from_format=None, output_dir=None)

    next_steps = [
        "1. Install any missing tools (see above)",
        "2. Run [bold]agentkit run[/bold] to execute the full quality pipeline",
        "3. Run [bold]agentkit status[/bold] to check your setup at any time",
    ]
    if project_targets and not write_projections:
        next_steps.append("4. Re-run init with [bold]--write-projections[/bold] or use [bold]agentkit project --write[/bold] to materialize projections")
    console.print(Panel("\n".join(next_steps), title="Next Steps", border_style="blue"))
    console.print()
