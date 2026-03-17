"""agentkit track command — show PR status for campaign-submitted PRs."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.history import HistoryDB
from agentkit_cli.pr_tracker import PRTracker, TrackedPRStatus

console = Console()

_STATUS_COLORS = {
    "merged": "green",
    "open": "yellow",
    "closed": "red",
    "unknown": "dim",
}


def _color_status(status: str) -> str:
    color = _STATUS_COLORS.get(status, "dim")
    return f"[{color}]{status}[/{color}]"


def _render_table(statuses: list[TrackedPRStatus]) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Repo", style="cyan")
    table.add_column("PR #")
    table.add_column("Status")
    table.add_column("Days Open")
    table.add_column("Reviews")
    table.add_column("Submitted")

    for s in statuses:
        pr_num_str = str(s.pr_number) if s.pr_number is not None else "-"
        submitted_short = s.submitted_at[:10] if s.submitted_at else "-"
        table.add_row(
            s.repo,
            pr_num_str,
            _color_status(s.status),
            str(s.days_open),
            str(s.review_comments),
            submitted_short,
        )

    console.print(table)

    merged = sum(1 for s in statuses if s.status == "merged")
    open_ = sum(1 for s in statuses if s.status == "open")
    closed = sum(1 for s in statuses if s.status == "closed")
    console.print(
        f"[green]{merged} merged[/green], [yellow]{open_} open[/yellow], [red]{closed} closed[/red]"
    )


def track_command(
    campaign_id: Optional[str] = None,
    limit: int = 20,
    all_prs: bool = False,
    json_output: bool = False,
    share: bool = False,
    db_path: Optional[Path] = None,
    token: Optional[str] = None,
) -> None:
    """Show PR status for campaign-submitted PRs."""
    tok = token or os.environ.get("GITHUB_TOKEN")
    tracker = PRTracker(token=tok)

    effective_limit = 10000 if all_prs else limit
    prs = tracker.get_tracked_prs(
        db_path=db_path,
        campaign_id=campaign_id,
        limit=effective_limit,
    )

    if not prs:
        console.print("[yellow]No tracked PRs found.[/yellow]")
        if campaign_id:
            console.print(f"[dim]Campaign ID: {campaign_id}[/dim]")
        return

    statuses = tracker.refresh_statuses(prs, db_path=db_path)

    if json_output:
        payload = [s.to_dict() for s in statuses]
        typer.echo(json.dumps(payload, indent=2))
        return

    _render_table(statuses)

    if share:
        _do_share(statuses)


def _do_share(statuses: list[TrackedPRStatus]) -> None:
    """Generate and upload HTML report via here.now."""
    try:
        from agentkit_cli.track_report import generate_html_report
        from agentkit_cli import __version__
        import urllib.request
        import tempfile
        import os

        html = generate_html_report(statuses, version=__version__)

        # Upload to here.now
        api_url = "https://here.now/api/v1/publish"
        headers = {"Content-Type": "application/json"}
        payload = json.dumps({
            "files": {"index.html": html},
            "ttl": 86400,
        }).encode()

        req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                url = result.get("url", "")
                console.print(f"[bold green]Report uploaded:[/bold green] {url}")
        except Exception as e:
            console.print(f"[yellow]Share failed:[/yellow] {e}")
    except ImportError as e:
        console.print(f"[yellow]Share unavailable:[/yellow] {e}")
