"""agentkit doctor command — diagnose quartet tools installation."""
from __future__ import annotations

import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli import __version__
from agentkit_cli.tools import QUARTET_TOOLS, INSTALL_HINTS, is_installed, get_version

console = Console()


def check_tool(name: str) -> dict:
    """Check a single tool and return status dict."""
    installed = is_installed(name)
    version = get_version(name) if installed else None
    return {
        "name": name,
        "installed": installed,
        "version": version or "NOT FOUND",
        "install_hint": INSTALL_HINTS.get(name, f"pip install {name}"),
    }


def doctor_command(json_output: bool = False) -> None:
    """Run doctor checks on all quartet tools."""
    results = {tool: check_tool(tool) for tool in QUARTET_TOOLS}
    all_found = all(r["installed"] for r in results.values())

    if json_output:
        out = {name: (r["version"] if r["installed"] else "NOT FOUND") for name, r in results.items()}
        out["agentkit-cli"] = __version__
        print(json.dumps(out, indent=2))
        if not all_found:
            raise typer.Exit(code=1)
        return

    # Rich table output
    console.print(f"\n[bold]agentkit doctor[/bold] — agentkit-cli v{__version__}\n")

    table = Table(show_header=True)
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("Install Command")

    for name, r in results.items():
        if r["installed"]:
            status = "[green]✓ installed[/green]"
            version = r["version"]
            hint = ""
        else:
            status = "[red]✗ missing[/red]"
            version = "NOT FOUND"
            hint = r["install_hint"]
        table.add_row(name, status, version, hint)

    # Also show self
    table.add_row("agentkit-cli", "[green]✓ installed[/green]", __version__, "")

    console.print(table)

    if all_found:
        console.print("\n[green]All tools installed.[/green]\n")
    else:
        missing = [n for n, r in results.items() if not r["installed"]]
        console.print(f"\n[red]Missing tools: {', '.join(missing)}[/red]\n")
        raise typer.Exit(code=1)
