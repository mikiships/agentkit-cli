"""agentkit status command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.tools import tool_status
from agentkit_cli.config import find_project_root, config_exists, load_last_run

console = Console()


def status_command(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to check"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show health status of the Agent Quality Toolkit."""
    root = path or find_project_root()
    console.print(f"\n[bold]agentkit status[/bold] — project: {root}\n")

    # Tool table
    tool_table = Table(title="Quartet Tools", show_header=True)
    tool_table.add_column("Tool", style="bold")
    tool_table.add_column("Status")
    tool_table.add_column("Version")
    tool_table.add_column("Path")

    ts = tool_status()
    for tool, info in ts.items():
        if info["installed"]:
            status_str = "[green]✓ installed[/green]"
            version_str = info.get("version") or "—"
            path_str = info.get("path") or "—"
        else:
            status_str = "[red]✗ missing[/red]"
            version_str = "—"
            path_str = "—"
        tool_table.add_row(tool, status_str, version_str, path_str)

    console.print(tool_table)

    # Project files table
    files_table = Table(title="Project Files", show_header=True)
    files_table.add_column("File", style="bold")
    files_table.add_column("Status")

    config_ok = config_exists(root)
    claude_ok = (root / "CLAUDE.md").exists()
    last_run_ok = (root / ".agentkit-last-run.json").exists()

    files_table.add_row(
        ".agentkit.yaml",
        "[green]✓ exists[/green]" if config_ok else "[yellow]✗ missing — run agentkit init[/yellow]",
    )
    files_table.add_row(
        "CLAUDE.md",
        "[green]✓ exists[/green]" if claude_ok else "[yellow]✗ missing[/yellow]",
    )
    files_table.add_row(
        ".agentkit-last-run.json",
        "[green]✓ exists[/green]" if last_run_ok else "[dim]not found[/dim]",
    )

    console.print(files_table)

    # Last run summary
    last_run = load_last_run(root)
    if last_run:
        lr_table = Table(title="Last Run Summary", show_header=True)
        lr_table.add_column("Key", style="bold")
        lr_table.add_column("Value")
        lr_table.add_row("Timestamp", last_run.get("timestamp", "—"))
        lr_table.add_row("Passed", str(last_run.get("passed", "—")))
        lr_table.add_row("Failed", str(last_run.get("failed", "—")))
        lr_table.add_row("Skipped", str(last_run.get("skipped", "—")))
        console.print(lr_table)

    if json_output:
        output = {
            "project": str(root),
            "tools": ts,
            "files": {
                ".agentkit.yaml": config_ok,
                "CLAUDE.md": claude_ok,
                ".agentkit-last-run.json": last_run_ok,
            },
            "last_run": last_run,
        }
        console.print("\n[bold]JSON Output:[/bold]")
        print(json.dumps(output, indent=2))

    console.print()
