"""agentkit benchmark command — cross-agent benchmarking on your codebase."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.benchmark import (
    BenchmarkConfig,
    BenchmarkEngine,
    BenchmarkReport,
    DEFAULT_AGENTS,
    DEFAULT_TASKS,
    DEFAULT_TIMEOUT,
    DEFAULT_ROUNDS,
)

console = Console()


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _render_table(report: BenchmarkReport) -> None:
    """Render final ranked table to console."""
    table = Table(title=f"Benchmark Results: {report.project}", show_header=True)
    table.add_column("Rank", style="bold", justify="center")
    table.add_column("Agent", style="bold")
    table.add_column("Tasks", justify="center")
    table.add_column("Mean Score", justify="center")
    table.add_column("Mean Time (s)", justify="center")
    table.add_column("Win Rate", justify="center")

    ranked = sorted(report.summary.values(), key=lambda s: (-s.mean_score, -s.win_rate))
    for i, stats in enumerate(ranked, 1):
        color = _score_color(stats.mean_score)
        crown = " 👑" if stats.agent == report.winner else ""
        table.add_row(
            str(i),
            f"{stats.agent}{crown}",
            str(len(stats.task_scores)),
            f"[{color}]{stats.mean_score:.1f}[/{color}]",
            f"{stats.mean_duration:.1f}",
            f"{stats.win_rate * 100:.0f}%",
        )

    console.print(table)
    console.print(f"\n[bold green]Winner:[/bold green] {report.winner} 👑")


def benchmark_command(
    path: Path = typer.Argument(Path("."), help="Project path (default: current dir)"),
    agents: Optional[str] = typer.Option(None, "--agents", help="Comma-separated agents (default: auto-detect)"),
    tasks: Optional[str] = typer.Option(None, "--tasks", help="Comma-separated tasks (default: all 5)"),
    rounds: int = typer.Option(DEFAULT_ROUNDS, "--rounds", help="Rounds per task (3+ for confidence)"),
    timeout: int = typer.Option(DEFAULT_TIMEOUT, "--timeout", help="Timeout per task in seconds"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save report to file"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
) -> None:
    """Run a cross-agent benchmark on your codebase."""
    project_path = str(path.resolve())

    agent_list = [a.strip() for a in agents.split(",")] if agents else list(DEFAULT_AGENTS)
    task_list = [t.strip() for t in tasks.split(",")] if tasks else list(DEFAULT_TASKS)

    config = BenchmarkConfig(
        agents=agent_list,
        tasks=task_list,
        rounds=rounds,
        timeout=timeout,
    )

    if not quiet and not json_output:
        console.print(f"[bold]Running benchmark on:[/bold] {project_path}")
        console.print(f"Agents: {', '.join(agent_list)}")
        console.print(f"Tasks:  {', '.join(task_list)}")
        console.print(f"Rounds: {rounds}  Timeout: {timeout}s\n")

    completed = []

    def progress_callback(agent, task, round_num, result):
        completed.append(result)
        if not quiet and not json_output:
            color = _score_color(result.score) if not result.error else "red"
            status = f"[{color}]{result.score:.0f}[/{color}]" if not result.error else f"[red]ERR[/red]"
            console.print(f"  [{round_num}] {agent:<10} {task:<20} {status}")

    engine = BenchmarkEngine()

    if not quiet and not json_output:
        console.print("[bold]Running...[/bold]")


    report = engine.run(project_path, config=config, progress_callback=progress_callback)

    # Output handling
    if json_output:
        console.print(json.dumps(report.to_dict(), indent=2))
        return

    if not quiet:
        console.print()
        _render_table(report)

    if output:
        from agentkit_cli.benchmark_report import BenchmarkReportRenderer
        html = BenchmarkReportRenderer().render(report)
        output.write_text(html, encoding="utf-8")
        if not quiet:
            console.print(f"\n[bold]Report saved:[/bold] {output}")

    if share:
        from agentkit_cli.benchmark_report import publish_benchmark
        url = publish_benchmark(report)
        if url:
            console.print(f"\n[bold green]Benchmark published:[/bold green] {url}")
        else:
            console.print("[yellow]Publish failed — check HERENOW_API_KEY[/yellow]")
