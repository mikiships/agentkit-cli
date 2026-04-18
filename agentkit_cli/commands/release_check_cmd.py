"""agentkit release-check command."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.release_check import Registry, ReleaseCheckResult, run_release_check, write_step_summary

console = Console()

_STATUS_STYLES = {
    "pass": ("✓ PASS", "green"),
    "fail": ("✗ FAIL", "red"),
    "skip": ("⊘ SKIP", "dim"),
    "error": ("✗ ERROR", "red"),
}

_VERDICT_STYLES = {
    "SHIPPED": "bold green",
    "RELEASE-READY": "bold yellow",
    "BUILT": "bold cyan",
    "UNKNOWN": "bold red",
}


def _render_table(result: ReleaseCheckResult) -> None:
    console.print()
    console.print(f"[bold]agentkit release-check[/bold]: {result.path}")
    if result.package:
        console.print(f"[bold]Package:[/bold] {result.package}  [bold]Version:[/bold] {result.version}  [bold]Registry:[/bold] {result.registry}")
    console.print()

    table = Table(title="Release Surface Checks", show_header=True)
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail", max_width=60)
    table.add_column("Hint", max_width=50)

    for check in result.checks:
        symbol, color = _STATUS_STYLES.get(check.status, (check.status, "white"))
        table.add_row(
            check.name,
            f"[{color}]{symbol}[/{color}]",
            check.detail,
            f"[dim]{check.hint}[/dim]" if check.hint else "",
        )

    console.print(table)

    verdict_style = _VERDICT_STYLES.get(result.verdict, "bold")
    console.print(f"\n[bold]Verdict:[/bold] [{verdict_style}]{result.verdict}[/{verdict_style}]")

    if result.verdict != "SHIPPED":
        hints = [c.hint for c in result.checks if c.hint and c.status in ("fail", "error")]
        if hints:
            console.print("\n[bold]Next steps:[/bold]")
            for hint in hints:
                console.print(f"  • {hint}")
    console.print()


def release_check_command(
    path: Optional[Path] = None,
    version: Optional[str] = None,
    package: Optional[str] = None,
    registry: Registry = "auto",
    skip_tests: bool = False,
    json_output: bool = False,
    changelog: bool = False,
) -> None:
    if registry not in ("pypi", "npm", "auto"):
        typer.echo(f"Invalid --registry '{registry}'. Must be: pypi, npm, auto", err=True)
        raise typer.Exit(code=2)

    root = path or Path.cwd()
    result = run_release_check(
        path=root,
        package=package,
        version=version,
        registry=registry,
        skip_tests=skip_tests,
    )

    changelog_content: Optional[str] = None
    if changelog:
        from agentkit_cli.changelog_engine import ChangelogEngine
        commits = ChangelogEngine.from_git(since=None, path=str(root))
        delta = ChangelogEngine.from_history(project=None, since_days=7)
        changelog_content = ChangelogEngine.render_markdown(commits, delta, version=result.version)

    write_step_summary(result)

    if json_output:
        data = result.as_dict()
        if changelog_content is not None:
            data["changelog_preview"] = changelog_content
        typer.echo(json.dumps(data, indent=2))
    else:
        _render_table(result)
        console.print("[bold]Markdown summary:[/bold]")
        console.print(result.to_markdown())
        if changelog_content is not None:
            console.print("\n[bold]Changelog Preview:[/bold]")
            console.print(changelog_content)

    raise typer.Exit(code=0 if result.passed else 1)
