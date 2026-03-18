"""agentkit timeline command — visual quality timeline from history DB."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.timeline import TimelineEngine
from agentkit_cli.timeline_report import render_html_timeline

console = Console()


def _upload_to_herenow(html_content: str, filename: str = "agentkit-timeline.html") -> Optional[str]:
    """Upload HTML to here.now if HERENOW_API_KEY is set. Returns URL or None."""
    api_key = os.environ.get("HERENOW_API_KEY", "")
    if not api_key:
        return None
    try:
        import urllib.request
        import urllib.error

        body = json.dumps({"files": [{"name": filename, "content_type": "text/html"}]}).encode()
        req = urllib.request.Request(
            "https://here.now/api/v1/publish",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            publish_data = json.loads(resp.read())

        upload_url = publish_data["files"][0]["upload_url"]
        final_url = publish_data.get("url") or publish_data.get("site_url", "")

        content_bytes = html_content.encode()
        put_req = urllib.request.Request(
            upload_url,
            data=content_bytes,
            headers={"Content-Type": "text/html"},
            method="PUT",
        )
        with urllib.request.urlopen(put_req, timeout=30):
            pass

        site_id = publish_data.get("site_id") or publish_data.get("id", "")
        if site_id:
            finalize_body = json.dumps({"site_id": site_id}).encode()
            fin_req = urllib.request.Request(
                "https://here.now/api/v1/finalize",
                data=finalize_body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            with urllib.request.urlopen(fin_req, timeout=30) as resp:
                fin_data = json.loads(resp.read())
                final_url = fin_data.get("url") or final_url

        return final_url or None
    except Exception as e:
        console.print(f"[yellow]Warning: upload failed: {e}[/yellow]")
        return None


def timeline_command(
    project: Optional[str] = None,
    limit: int = 50,
    since: Optional[str] = None,
    output: Path = Path("timeline.html"),
    share: bool = False,
    json_output: bool = False,
    db_path: Optional[Path] = None,
) -> None:
    """Generate a visual quality timeline from the history DB."""
    engine = TimelineEngine(db_path=db_path)
    payload = engine.build_full_payload(project=project, limit=limit, since=since)
    chart = payload["chart"]
    stats = payload["stats"]
    by_project = chart.get("by_project", {})

    # Handle empty DB
    if not by_project:
        console.print("[yellow]No history found. Run [bold]agentkit run[/bold] first.[/yellow]")
        raise typer.Exit(0)

    # JSON output mode
    if json_output:
        out = {
            "project": project,
            "stats": stats,
            "chart": {
                "dates": chart.get("dates", []),
                "scores": chart.get("scores", []),
                "per_tool": chart.get("per_tool", {}),
                "projects": chart.get("projects", []),
            },
        }
        print(json.dumps(out, indent=2))
        return

    # Rich summary table
    table = Table(title="Quality Timeline Summary", show_lines=False)
    table.add_column("Project", style="bold cyan")
    table.add_column("Runs", justify="right")
    table.add_column("Latest Score", justify="right")
    table.add_column("Trend", justify="center")

    for proj, pdata in by_project.items():
        scores = [s for s in pdata.get("scores", []) if s is not None]
        run_count = len(scores)
        latest = f"{scores[-1]:.1f}" if scores else "—"
        if len(scores) >= 2:
            delta = scores[-1] - scores[0]
            trend_ch = "↑" if delta > 2 else "↓" if delta < -2 else "→"
        else:
            trend_ch = "→"
        table.add_row(proj, str(run_count), latest, trend_ch)

    console.print(table)

    # Stats row
    avg = stats.get("avg")
    mn = stats.get("min")
    mx = stats.get("max")
    trend = stats.get("trend", "stable")
    streak = stats.get("streak", 0)

    console.print(
        f"\n[bold]Overall:[/bold] "
        f"avg=[cyan]{avg if avg is not None else '—'}[/cyan]  "
        f"min=[cyan]{mn if mn is not None else '—'}[/cyan]  "
        f"max=[cyan]{mx if mx is not None else '—'}[/cyan]  "
        f"trend=[cyan]{trend}[/cyan]"
    )
    if streak >= 3:
        console.print(f"[green]Streak: {streak} consecutive runs above 80[/green]")

    # Render HTML
    html_content = render_html_timeline(payload, project_name=project)
    output.write_text(html_content, encoding="utf-8")
    console.print(f"\n[green]Timeline written to[/green] [bold]{output}[/bold]")

    # Share
    if share:
        url = _upload_to_herenow(html_content)
        if url:
            console.print(f"[bold green]Shared:[/bold green] {url}")
        else:
            console.print("[yellow]Set HERENOW_API_KEY to enable sharing.[/yellow]")
