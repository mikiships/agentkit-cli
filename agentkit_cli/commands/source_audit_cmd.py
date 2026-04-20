from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.source_audit import SourceAuditEngine

console = Console()
engine = SourceAuditEngine()


def source_audit_command(
    path: Optional[str] = None,
    json_output: bool = False,
    output: Optional[Path] = None,
    format: str = "text",
) -> None:
    target = Path(path).resolve() if path else Path.cwd()
    if not target.exists():
        console.print(f"[red]Path not found:[/red] {target}")
        raise typer.Exit(1)
    if not target.is_dir():
        console.print(f"[red]Path is not a directory:[/red] {target}")
        raise typer.Exit(1)

    fmt = _normalize_format(json_output=json_output, format=format)
    result = engine.audit(target)
    if fmt == "json":
        rendered = result.to_json()
    else:
        rendered = engine.render_markdown(result)

    if output is not None:
        output.write_text(rendered, encoding="utf-8")

    if fmt == "text" and output is None:
        _render_rich(result)
        return
    typer.echo(rendered)


def _normalize_format(json_output: bool, format: str) -> str:
    if json_output:
        return "json"
    value = format.strip().lower()
    if value == "table":
        return "text"
    if value not in {"text", "markdown", "json"}:
        raise ValueError("format must be text, markdown, or json")
    return value


def _render_rich(result) -> None:
    console.print("\n[bold]source audit[/bold]")
    console.print(f"[dim]source: {result.source_path or 'missing'}[/dim]")
    console.print(
        f"[dim]ready for contract: {'yes' if result.readiness.ready_for_contract else 'no'} | blockers: {result.readiness.blocker_count} | warnings: {result.readiness.warning_count}[/dim]"
    )

    checks = Table(show_header=True, header_style="bold")
    checks.add_column("Section")
    checks.add_column("Status")
    checks.add_column("Evidence")
    for item in result.section_checks:
        checks.add_row(str(item["name"]), "present" if item["present"] else "missing", str(item["evidence"]))
    if result.section_checks:
        console.print(checks)

    if result.findings:
        console.print("\n[bold]findings[/bold]")
        for finding in result.findings:
            console.print(f"- [{finding.severity}] {finding.title}: {finding.evidence}")
            console.print(f"  fix: {finding.suggestion}")
    else:
        console.print("\n[green]No findings. Source is structurally ready.[/green]")

    console.print(f"\n[bold]contract readiness[/bold] {result.readiness.summary}")
