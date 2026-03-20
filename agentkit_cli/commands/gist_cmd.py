"""agentkit gist — publish analysis output as a GitHub Gist for permanent shareable links."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.gist_publisher import GistPublisher

console = Console()


def gist_command(
    from_file: Optional[Path] = typer.Option(
        None,
        "--from",
        help="Path to a file to publish as a gist (markdown or HTML).",
    ),
    public: bool = typer.Option(
        False,
        "--public",
        help="Create a public gist (default: private/secret).",
    ),
    description: str = typer.Option(
        "agentkit analysis report",
        "--description",
        help="Gist description.",
    ),
    fmt: str = typer.Option(
        "markdown",
        "--format",
        help="Output format: markdown or html.",
    ),
) -> None:
    """Publish a report or analysis output as a permanent GitHub Gist."""
    if from_file is not None:
        p = Path(from_file)
        if not p.exists():
            console.print(f"[red]Error:[/red] File not found: {p}")
            raise typer.Exit(code=1)
        content = p.read_text(encoding="utf-8")
        filename = p.name
    else:
        # Run quickstart analysis on cwd and publish that
        import json as _json

        try:
            from agentkit_cli.analyze import analyze_target
        except ImportError:
            console.print("[red]Error:[/red] Could not import analyze module.")
            raise typer.Exit(code=1)

        console.print("[bold]agentkit gist[/bold] — running analysis on current directory…")
        try:
            result = analyze_target(target=".")
        except Exception as e:
            console.print(f"[red]Analysis failed:[/red] {e}")
            raise typer.Exit(code=1)

        if fmt == "html":
            from agentkit_cli.share import generate_scorecard_html

            content = generate_scorecard_html(
                score_result=result.__dict__ if hasattr(result, "__dict__") else {},
                project_name=".",
            )
            filename = "agentkit-report.html"
        else:
            # Markdown summary
            lines = ["# agentkit Analysis Report\n"]
            if hasattr(result, "score") and result.score is not None:
                lines.append(f"**Score:** {result.score}\n")
            if hasattr(result, "grade") and result.grade:
                lines.append(f"**Grade:** {result.grade}\n")
            content = "\n".join(lines)
            filename = "agentkit-report.md"

    # Determine filename based on format if not from file
    if from_file is None:
        if fmt == "html" and not filename.endswith(".html"):
            filename = "agentkit-report.html"
        elif fmt == "markdown" and not filename.endswith(".md"):
            filename = "agentkit-report.md"

    publisher = GistPublisher()
    result_obj = publisher.publish(
        content=content,
        filename=filename,
        description=description,
        public=public,
    )

    if result_obj is None:
        raise typer.Exit(code=1)

    console.print(f"[green]Published:[/green] {result_obj.url}")
    if not public:
        console.print("[dim]Note: secret gist — only accessible via the URL.[/dim]")
