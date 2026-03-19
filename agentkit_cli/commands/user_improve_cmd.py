"""agentkit user-improve command."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.user_improve import UserImproveEngine
from agentkit_cli.renderers.user_improve_html import UserImproveHTMLRenderer, upload_user_improve_report
from agentkit_cli.history import record_run

console = Console()


def user_improve_command(
    target: str,
    limit: int = 5,
    below: int = 80,
    share: bool = False,
    json_output: bool = False,
    dry_run: bool = False,
    token: Optional[str] = None,
) -> None:
    """Find a GitHub user's lowest-scoring repos and auto-improve them."""
    # Parse github:<user> or bare <user>
    if target.startswith("github:"):
        username = target[len("github:"):]
    else:
        username = target

    username = username.strip("/").strip()
    if not username:
        msg = "Username is required. Use github:<user> or bare <user>."
        if json_output:
            console.print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(code=1)

    if limit < 1:
        limit = 1
    if limit > 20:
        limit = 20

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not json_output:
        console.print(f"\n[bold]agentkit user-improve[/bold] — improving repos for [bold cyan]@{username}[/bold cyan]")
        if dry_run:
            console.print("[bold yellow]Dry run[/bold yellow] — no changes will be applied.\n")

    engine = UserImproveEngine(github_token=resolved_token)

    # Dry run: show what would be improved
    if dry_run:
        try:
            repos = engine.fetch_user_repos(username)
            scored = engine.score_repos(repos)
            targets = engine.select_targets(scored, limit=limit, below=below)
        except ValueError as exc:
            if json_output:
                console.print(json.dumps({"error": str(exc)}))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1)
        except Exception as exc:
            if json_output:
                console.print(json.dumps({"error": str(exc)}))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1)

        if json_output:
            console.print(json.dumps({
                "dry_run": True,
                "user": username,
                "would_improve": [t.to_dict() for t in targets],
            }, indent=2))
        else:
            if not targets:
                console.print(f"[green]No repos scoring below {below} found.[/green]")
            else:
                table = Table(title=f"Would improve (limit={limit}, below={below})", show_header=True)
                table.add_column("Repo")
                table.add_column("Score", justify="right")
                table.add_column("Grade", justify="center")
                for t in targets:
                    table.add_row(t.full_name, f"{t.score:.0f}", t.grade)
                console.print(table)
        return

    # Full run
    def _progress_cb(full_name: str, status: str) -> None:
        if not json_output:
            console.print(f"  [dim][{full_name}] {status}[/dim]")

    try:
        if not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(f"Improving repos for [bold]{username}[/bold]…", total=None)
                report = engine.run(username, limit=limit, below=below, progress_callback=_progress_cb)
        else:
            report = engine.run(username, limit=limit, below=below, progress_callback=_progress_cb)
    except ValueError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)
    except Exception as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Record to history DB
    try:
        record_run(
            project=f"github:{username}",
            tool="user-improve",
            score=report.summary_stats.get("avg_lift", 0.0),
            details=report.summary_stats,
            label="user-improve",
        )
    except Exception:
        pass

    # Generate HTML report
    renderer = UserImproveHTMLRenderer()
    html = renderer.render(report)

    # --share
    share_url: Optional[str] = None
    if share:
        share_url = upload_user_improve_report(html)
        if share_url and not json_output:
            console.print(f"\n[bold green]Improvement report published:[/bold green] {share_url}")

    # JSON output
    if json_output:
        out = report.to_dict()
        if share_url:
            out["share_url"] = share_url
        console.print(json.dumps(out, indent=2))
        return

    # Rich terminal output
    _print_rich_summary(report, share_url=share_url)


def _print_rich_summary(report, share_url=None) -> None:
    from agentkit_cli.user_improve import UserImproveResult

    stats = report.summary_stats
    avg_lift = stats.get("avg_lift", 0.0)
    lift_color = "green" if avg_lift > 0 else ("yellow" if avg_lift == 0 else "red")
    lift_sign = "+" if avg_lift >= 0 else ""

    console.print(
        f"\n[bold]🔧 Agent Improvement Report:[/bold] "
        f"[bold cyan]@{report.user}[/bold cyan]  "
        f"[bold {lift_color}]avg lift {lift_sign}{avg_lift:.1f} pts[/bold {lift_color}]"
    )
    console.print(
        f"  [dim]{report.improved} repos improved · "
        f"{report.skipped} skipped · "
        f"from {report.total_repos} total[/dim]\n"
    )

    if report.results:
        table = Table(
            title="Improvement Results",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Repository")
        table.add_column("Before", justify="right", width=7)
        table.add_column("After", justify="right", width=7)
        table.add_column("Lift", justify="right", width=8)
        table.add_column("Status", justify="center", width=8)

        for result in report.results:
            lift_str = f"+{result.lift:.1f}" if result.lift >= 0 else f"{result.lift:.1f}"
            l_color = "green" if result.lift > 0 else ("yellow" if result.lift == 0 else "red")
            status = "[dim]skipped[/dim]" if result.skipped else "[green]✓[/green]"
            table.add_row(
                result.full_name,
                f"{result.before_score:.0f}",
                f"{result.after_score:.0f}",
                f"[{l_color}]{lift_str}[/{l_color}]",
                status,
            )
        console.print(table)

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
