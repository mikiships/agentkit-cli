"""agentkit analyze command — analyze any repo's agent quality."""
from __future__ import annotations

import json
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.analyze import analyze_target, parse_target, AnalyzeResult
from agentkit_cli.share import generate_scorecard_html, upload_scorecard

console = Console()


def _grade_color(grade: str) -> str:
    return {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}.get(grade, "white")


def _score_color(score: Optional[float]) -> str:
    if score is None:
        return "dim"
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def analyze_command(
    target: str,
    json_output: bool = False,
    keep: bool = False,
    publish: bool = False,
    timeout: int = 120,
    no_generate: bool = False,
    profile: Optional[str] = None,
    share: bool = False,
    record_findings: bool = False,
) -> None:
    """Analyze a GitHub repo or local path for agent quality."""
    # Validate target early
    try:
        _url, _repo = parse_target(target)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    is_local = target.startswith((".", "/", "~"))
    if not json_output:
        if is_local:
            console.print(f"\n[bold]agentkit analyze[/bold] — target: {target}")
        else:
            console.print(f"\n[bold]agentkit analyze[/bold] — cloning {_url} …")

    try:
        result = analyze_target(
            target=target,
            keep=keep,
            publish=publish,
            timeout=timeout,
            no_generate=no_generate,
        )
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # --share: generate and upload scorecard
    share_url: Optional[str] = None
    if share:
        score_result = {"composite": result.composite_score}
        for key, tr in result.tools.items():
            if tr.get("score") is not None:
                score_result[key] = tr["score"]
        html = generate_scorecard_html(
            score_result,
            project_name=result.repo_name,
            ref=target,
            repo_url=target if not target.startswith((".", "/", "~")) else None,
            repo_name=result.repo_name,
        )
        share_url = upload_scorecard(html)
        if share_url and not json_output:
            console.print(f"\n[bold green]Score card published:[/bold green] {share_url}")

    if json_output:
        d = result.to_dict()
        if share_url:
            d["share_url"] = share_url
        print(json.dumps(d, indent=2))
        return

    # Rich table output
    table = Table(title=f"Analysis: {result.repo_name}", show_header=True, header_style="bold")
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Score")
    table.add_column("Key Finding", max_width=60)

    STATUS_ICONS = {
        "pass": ("✓ pass", "green"),
        "fail": ("✗ fail", "red"),
        "skipped": ("⊘ skipped", "yellow"),
        "error": ("✗ error", "red"),
    }

    for key, tr in result.tools.items():
        status = tr["status"]
        icon, color = STATUS_ICONS.get(status, (status, "white"))
        score = tr["score"]
        score_str = f"{score:.0f}" if score is not None else "—"
        sc = _score_color(score)
        finding = tr.get("finding", "") or ""
        table.add_row(
            tr["tool"] + (f" ({key})" if key != tr["tool"] else ""),
            f"[{color}]{icon}[/{color}]",
            f"[{sc}]{score_str}[/{sc}]",
            finding,
        )

    console.print()
    console.print(table)

    grade_color = _grade_color(result.grade)
    sep = "─" * 60
    console.print(f"\n[dim]{sep}[/dim]")
    console.print(
        f"[bold]Agent Quality Score:[/bold] [{grade_color}]{result.composite_score:.0f}/100 ({result.grade})[/{grade_color}]"
        f"  [dim]repo: {result.repo_name}[/dim]"
    )
    if result.generated_context:
        console.print("[dim]  (context file generated for this analysis)[/dim]")
    if result.temp_dir:
        console.print(f"[dim]  Clone kept at: {result.temp_dir}[/dim]")
    if result.report_url:
        console.print(f"[bold]Report URL:[/bold] {result.report_url}")
    console.print(f"[dim]{sep}[/dim]\n")
