"""agentkit certify command — generate a dated cert report for a repo."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.certify import CertEngine, CertResult
from agentkit_cli.certify_report import render_html_cert

console = Console()
certify_app = typer.Typer(name="certify", help="Generate a dated certification report for a repo.")


def _verdict_style(verdict: str) -> str:
    return {"PASS": "bold green", "WARN": "bold yellow", "FAIL": "bold red"}.get(verdict, "white")


def _upload_to_herenow(html_content: str, filename: str = "agentkit-cert.html") -> Optional[str]:
    """Upload HTML to here.now if HERENOW_API_KEY is set. Returns URL or None."""
    api_key = os.environ.get("HERENOW_API_KEY", "")
    if not api_key:
        return None
    try:
        import urllib.request
        import urllib.error

        # Step 1: get upload URL
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

        # Step 2: PUT file
        content_bytes = html_content.encode()
        put_req = urllib.request.Request(
            upload_url,
            data=content_bytes,
            headers={"Content-Type": "text/html"},
            method="PUT",
        )
        with urllib.request.urlopen(put_req, timeout=30):
            pass

        # Step 3: finalize
        site_id = publish_data.get("site_id") or publish_data.get("id", "")
        if site_id:
            fin_body = json.dumps({"site_id": site_id}).encode()
            fin_req = urllib.request.Request(
                "https://here.now/api/v1/finalize",
                data=fin_body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(fin_req, timeout=30) as resp:
                    fin_data = json.loads(resp.read())
                    final_url = fin_data.get("url") or final_url
            except Exception:
                pass

        return final_url or None
    except Exception as exc:
        console.print(f"[yellow]Share upload failed: {exc}[/yellow]")
        return None


def _print_cert(result: CertResult) -> None:
    """Print rich cert summary to console."""
    style = _verdict_style(result.verdict)
    console.print()
    console.print(f"[bold]agentkit certify[/bold] — cert_id: [cyan]{result.cert_id}[/cyan]")
    console.print(f"Timestamp: [dim]{result.timestamp}[/dim]")
    console.print(f"Verdict:   [{style}]{result.verdict}[/{style}]")
    console.print()

    table = Table(show_header=True, header_style="bold dim")
    table.add_column("Check", style="bold")
    table.add_column("Score", justify="right")
    table.add_row("Composite Score", str(result.score))
    table.add_row("Redteam Resistance", str(result.redteam_score))
    table.add_row("Context Freshness", str(result.freshness_score))
    table.add_row("Tests Found", str(result.tests_found))
    console.print(table)
    console.print()
    console.print(f"SHA256: [dim]{result.sha256}[/dim]")
    console.print()


@certify_app.callback(invoke_without_command=True)
def certify_command(
    ctx: typer.Context,
    path: Optional[Path] = typer.Argument(None, help="Path to repo (default: current directory)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write HTML cert report to file"),
    json_output: bool = typer.Option(False, "--json", help="Print JSON cert to stdout"),
    min_score: int = typer.Option(0, "--min-score", help="Fail (exit 1) if composite score < N"),
    share: bool = typer.Option(False, "--share", help="Upload HTML report to here.now"),
    badge: bool = typer.Option(False, "--badge", help="Inject/update cert badge in README.md"),
    dry_run: bool = typer.Option(False, "--dry-run", help="With --badge: print what would change"),
) -> None:
    """Generate a dated, shareable certification report for a repo."""
    if ctx.invoked_subcommand is not None:
        return

    target = (path or Path.cwd()).resolve()
    engine = CertEngine()

    if not json_output:
        console.print(f"\n[dim]Running agentkit certify on {target} ...[/dim]")

    result = engine.certify(str(target))

    if json_output:
        print(result.to_json())
    else:
        _print_cert(result)

    # --output: write HTML
    html_content = render_html_cert(result, project_name=target.name)
    if output:
        output.write_text(html_content, encoding="utf-8")
        if not json_output:
            console.print(f"[green]HTML report written to {output}[/green]")

    # --share
    if share:
        if not json_output:
            console.print("[dim]Uploading HTML report to here.now...[/dim]")
        url = _upload_to_herenow(html_content)
        if url:
            if json_output:
                pass  # don't pollute JSON
            else:
                console.print(f"[green]Shared: {url}[/green]")
        else:
            if not json_output:
                console.print("[yellow]Share upload skipped (no HERENOW_API_KEY or upload failed)[/yellow]")

    # --badge
    if badge:
        from agentkit_cli.commands.certify_cmd import _inject_badge
        _inject_badge(result, target, dry_run=dry_run)

    # --min-score gate
    if min_score > 0 and result.score < min_score:
        if not json_output:
            console.print(f"[red]FAILED: composite score {result.score} < required {min_score}[/red]")
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Badge inject (also used by --badge flag)
# ---------------------------------------------------------------------------

BADGE_PATTERN = r"!\[agentkit certified\]\(https://img\.shields\.io/badge/agentkit-[^)]*\)"
BADGE_LINE_PATTERN = r"^.*!\[agentkit certified\].*$"


def _verdict_badge_url(verdict: str) -> str:
    color = {"PASS": "brightgreen", "WARN": "yellow", "FAIL": "red"}.get(verdict, "lightgrey")
    return f"https://img.shields.io/badge/agentkit-{verdict}-{color}"


def _build_badge_md(verdict: str) -> str:
    return f"![agentkit certified]({_verdict_badge_url(verdict)})"


def _inject_badge(result: CertResult, repo_path: Path, dry_run: bool = False) -> None:
    """Inject or update the agentkit certified badge in README.md."""
    import re
    readme = repo_path / "README.md"
    badge_md = _build_badge_md(result.verdict)

    if not readme.exists():
        console.print("[yellow]README.md not found — skipping badge inject[/yellow]")
        return

    content = readme.read_text(encoding="utf-8")
    new_line = badge_md

    if re.search(BADGE_LINE_PATTERN, content, re.MULTILINE):
        new_content = re.sub(BADGE_LINE_PATTERN, new_line, content, flags=re.MULTILINE)
        action = "Updated"
    else:
        new_content = new_line + "\n\n" + content
        action = "Inserted"

    if dry_run:
        console.print(f"[dim]--dry-run: {action} badge line:[/dim]")
        console.print(f"  {new_line}")
        return

    readme.write_text(new_content, encoding="utf-8")
    console.print(f"[green]{action} badge in README.md: {new_line}[/green]")
