"""agentkit init command."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from agentkit_cli.tools import QUARTET_TOOLS, is_installed, INSTALL_HINTS
from agentkit_cli.config import find_project_root, config_path, config_exists, write_default_config

console = Console()


def init_command(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project root (default: git root or cwd)"),
) -> None:
    """Initialize agentkit in a project directory."""
    root = path or find_project_root()
    console.print(f"\n[bold]Initializing agentkit in:[/bold] {root}\n")

    # Check quartet tools
    table = Table(title="Agent Quality Toolkit — Tool Status", show_header=True)
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

    # Write config
    cfg_path = config_path(root)
    if config_exists(root):
        console.print(f"\n[yellow]Config already exists:[/yellow] {cfg_path}")
    else:
        written = write_default_config(root)
        console.print(f"\n[green]Created config:[/green] {written}")

    # Print install instructions for missing tools
    if missing:
        console.print("\n[yellow]Install missing tools:[/yellow]")
        for tool in missing:
            console.print(f"  pip install {tool}")

    # Next steps
    next_steps = "\n".join([
        "1. Install any missing tools (see above)",
        "2. Run [bold]agentkit run[/bold] to execute the full quality pipeline",
        "3. Run [bold]agentkit status[/bold] to check your setup at any time",
    ])
    console.print(Panel(next_steps, title="Next Steps", border_style="blue"))
    console.print()
