from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.map_engine import RepoMapEngine

console = Console()
engine = RepoMapEngine()


def _normalize_format(json_output: bool, format: str) -> str:
    if json_output:
        return 'json'
    value = format.strip().lower()
    if value == 'table':
        return 'text'
    if value not in {'markdown', 'json', 'text'}:
        raise ValueError('format must be markdown, json, or text')
    return value


def map_command(
    target: str,
    json_output: bool = False,
    output: Optional[Path] = None,
    format: str = 'text',
) -> None:
    fmt = _normalize_format(json_output=json_output, format=format)
    try:
        repo_map = engine.map_target(target)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f'[red]Error:[/red] {exc}')
        raise typer.Exit(1)

    if fmt == 'json':
        rendered = engine.to_json(repo_map)
    elif fmt == 'markdown':
        rendered = engine.render_markdown(repo_map)
    else:
        rendered = engine.render_text(repo_map)

    if output is not None:
        output.write_text(rendered, encoding='utf-8')

    if fmt == 'text' and output is None:
        _render_rich(repo_map)
        return

    typer.echo(rendered)


def _render_rich(repo_map) -> None:
    console.print(f"\n[bold]repo map[/bold] {repo_map.summary.name}")
    console.print(
        f"[dim]{repo_map.summary.total_files} files, {repo_map.summary.total_dirs} dirs, primary language: {repo_map.summary.primary_language or 'Unknown'}[/dim]"
    )

    table = Table(show_header=True, header_style='bold')
    table.add_column('Section')
    table.add_column('Highlights')
    table.add_row('Entrypoints', '\n'.join(item.path for item in repo_map.entrypoints[:4]) or 'None')
    table.add_row('Scripts', '\n'.join(item.name for item in repo_map.scripts[:6]) or 'None')
    table.add_row('Tests', '\n'.join(item.path for item in repo_map.tests[:4]) or 'None')
    table.add_row('Subsystems', '\n'.join(item.name for item in repo_map.subsystems[:6]) or 'None')
    table.add_row('Risks', '\n'.join(item.title for item in repo_map.risks[:4]) or 'None')
    console.print(table)

    if repo_map.hints:
        console.print('\n[bold]Likely work surfaces[/bold]')
        for hint in repo_map.hints[:6]:
            console.print(f'- {hint.title}: {hint.detail}')

    console.print('\n[bold]Contract handoff[/bold]')
    for line in repo_map.contract_handoff.summary_lines:
        console.print(f'- {line}')
