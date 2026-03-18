"""agentkit search command — discover GitHub repos missing AI context files."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.search import SearchEngine, SearchResult

console = Console()


def _stars_fmt(stars: int) -> str:
    if stars >= 1_000:
        return f"★ {stars // 1000}k"
    return f"★ {stars}"


def _context_status(result: SearchResult) -> str:
    parts = []
    if result.has_claude_md:
        parts.append("[green]CLAUDE.md[/green]")
    if result.has_agents_md:
        parts.append("[green]AGENTS.md[/green]")
    if not parts:
        return "[red]missing[/red]"
    return " ".join(parts)


def _render_table(results: list[SearchResult]) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Repository", style="cyan")
    table.add_column("Stars")
    table.add_column("Language")
    table.add_column("Context Files")
    table.add_column("Score")

    for r in results:
        table.add_row(
            r.full_name,
            _stars_fmt(r.stars),
            r.language or "—",
            _context_status(r),
            f"{r.score:.2f}",
        )
    console.print(table)


def search_command(
    query: str = "",
    language: Optional[str] = None,
    topic: Optional[str] = None,
    min_stars: Optional[int] = None,
    max_stars: Optional[int] = None,
    missing_only: bool = False,
    limit: int = 20,
    json_output: bool = False,
    share: bool = False,
    output: Optional[Path] = None,
    github_token: Optional[str] = None,
    no_check: bool = False,
) -> list[SearchResult]:
    """Discover GitHub repos missing CLAUDE.md / AGENTS.md."""

    engine = SearchEngine(token=github_token)

    if not json_output:
        console.print(f"[bold]Searching GitHub repos…[/bold]")
        if query:
            console.print(f"  query=[cyan]{query}[/cyan]", end="")
        if language:
            console.print(f"  language=[cyan]{language}[/cyan]", end="")
        if topic:
            console.print(f"  topic=[cyan]{topic}[/cyan]", end="")
        if min_stars:
            console.print(f"  min-stars=[cyan]{min_stars}[/cyan]", end="")
        console.print()

    try:
        results = engine.search(
            query=query,
            language=language,
            topic=topic,
            min_stars=min_stars,
            max_stars=max_stars,
            limit=limit,
            check_contents=not no_check,
            missing_only=missing_only,
        )
    except Exception as exc:
        console.print(f"[red]Search failed:[/red] {exc}")
        raise typer.Exit(code=1)

    if not results:
        console.print("[yellow]No repos found matching criteria.[/yellow]")
        return results

    # JSON output
    if json_output:
        typer.echo(json.dumps([r.to_dict() for r in results], indent=2))
        return results

    # Rich table
    _render_table(results)
    missing_count = sum(1 for r in results if r.missing_context)
    console.print(
        f"\n[bold]{len(results)}[/bold] repos found · "
        f"[red]{missing_count}[/red] missing context files"
    )

    # HTML report
    if output or share:
        from agentkit_cli.search_report import generate_search_report, upload_search_report

        html = generate_search_report(results, query=query)
        if output:
            output.write_text(html, encoding="utf-8")
            console.print(f"[green]Report written:[/green] {output}")

        if share:
            url = upload_search_report(results, query=query)
            if url:
                console.print(f"[bold green]📋 Search report:[/bold green] {url}")
            else:
                console.print("[yellow]Share: set HERENOW_API_KEY to publish.[/yellow]")

    return results
