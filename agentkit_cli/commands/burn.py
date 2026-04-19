from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.burn import BurnAnalysisEngine
from agentkit_cli.renderers.burn_report import render_burn_html

console = Console()


def burn_command(
    path: Optional[Path] = None,
    format: str = "table",
    since: Optional[str] = None,
    limit: Optional[int] = None,
    project: Optional[str] = None,
    output: Optional[Path] = None,
) -> None:
    engine = BurnAnalysisEngine()
    search_path = (path or Path("tests/fixtures/burn")).resolve()
    sessions = engine.load(search_path)
    if not sessions:
        console.print(f"[yellow]No transcripts found under {search_path}[/yellow]")
        raise typer.Exit(0)
    report = engine.analyze(sessions, since=since, limit=limit, project=project)
    if format == "json":
        typer.echo(json.dumps(report.to_dict(), indent=2))
    else:
        _render_console(report)
    if output:
        output.write_text(render_burn_html(report), encoding="utf-8")
        if format != "json":
            console.print(f"[green]Burn report written to[/green] [bold]{output}[/bold]")


def _render_console(report) -> None:
    console.print("[bold cyan]agentkit burn[/bold cyan]")
    console.print(f"Total cost: [bold]${report.total_cost_usd:.6f}[/bold] across {report.session_count} sessions and {report.turn_count} turns")
    table = Table(title="Top spend buckets")
    table.add_column("Project", style="cyan")
    table.add_column("Cost USD", justify="right")
    table.add_column("Turns", justify="right")
    for row in report.totals.get("by_project", [])[:5]:
        table.add_row(str(row["key"]), f"{row['cost_usd']:.6f}", str(row["turns"]))
    console.print(table)
    findings = Table(title="Waste findings")
    findings.add_column("Severity")
    findings.add_column("Finding")
    for finding in report.findings[:5]:
        findings.add_row(finding.severity, finding.title)
    console.print(findings)
    sessions = Table(title="Most expensive sessions")
    sessions.add_column("Session")
    sessions.add_column("Project")
    sessions.add_column("Cost USD", justify="right")
    for row in report.top_sessions[:5]:
        sessions.add_row(row["session_id"], str(row["project_root"] or "unknown"), f"{row['cost_usd']:.6f}")
    console.print(sessions)
