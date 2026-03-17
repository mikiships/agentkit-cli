"""agentkit campaign command — batch PR submission to multiple repos."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.campaign import CampaignEngine, CampaignResult, RepoSpec

console = Console()


def _stars_fmt(stars: int) -> str:
    if stars >= 1000:
        return f"★ {stars // 1000}k"
    return f"★ {stars}"


def _render_table(result: CampaignResult, dry_run: bool = False) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Repo", style="cyan")
    table.add_column("Stars")
    table.add_column("Status")
    table.add_column("PR URL / Note")

    submitted_repos = {r.repo.full_name for r in result.submitted}
    skipped_repos = {r.full_name for r in result.skipped}
    failed_repos = {r.full_name for (r, _) in result.failed}

    for pr in result.submitted:
        status = "[DRY RUN]" if dry_run else "✅ PR"
        table.add_row(
            pr.repo.repo,
            _stars_fmt(pr.repo.stars),
            status,
            pr.pr_url or "",
        )

    for repo in result.skipped:
        table.add_row(
            repo.repo,
            _stars_fmt(repo.stars),
            "⏭ skip",
            f"Already has context file",
        )

    for repo, err in result.failed:
        table.add_row(
            repo.repo,
            _stars_fmt(repo.stars),
            "❌ err",
            err[:60],
        )

    console.print(table)
    pr_word = "PRs" if len(result.submitted) != 1 else "PR"
    console.print(
        f"Campaign complete. {len(result.submitted)} {pr_word} opened, "
        f"{len(result.skipped)} skipped, {len(result.failed)} failed."
    )


def campaign_command(
    target: str,
    limit: int = 5,
    language: Optional[str] = None,
    min_stars: int = 100,
    file: str = "CLAUDE.md",
    force: bool = False,
    dry_run: bool = False,
    json_output: bool = False,
    no_filter: bool = False,
    skip_pr: bool = False,
    share: bool = False,
    db_path: Optional[Path] = None,
) -> CampaignResult:
    """Run a campaign: discover repos and submit PRs."""

    console.print(f"[bold]Campaign ID[/bold]: generating...")
    engine = CampaignEngine()

    # Discover repos
    try:
        repos = engine.find_repos(
            target_spec=target,
            limit=limit,
            language=language,
            min_stars=min_stars if min_stars > 0 else None,
        )
    except Exception as e:
        console.print(f"[red]Discovery failed:[/red] {e}")
        raise typer.Exit(code=1)

    if not repos:
        console.print("[yellow]No repos found matching criteria.[/yellow]")
        raise typer.Exit(code=0)

    # Filter repos missing context file
    if not no_filter:
        filtered = []
        for repo in repos:
            try:
                if engine.has_context_file(repo.owner, repo.repo):
                    pass  # will be skipped in run_campaign
            except Exception:
                pass
            filtered.append(repo)
        repos = filtered

    console.print(f"\n[bold]Campaign[/bold] target=[cyan]{target}[/cyan]  limit={limit}  file={file}\n")

    if skip_pr:
        # Only discovery
        table = Table(show_header=True, header_style="bold")
        table.add_column("Repo", style="cyan")
        table.add_column("Stars")
        table.add_column("Language")
        for r in repos:
            table.add_row(r.repo, _stars_fmt(r.stars), r.language or "—")
        console.print(table)
        result = CampaignResult(target_spec=target, file=file)
        result.skipped = repos
        if json_output:
            typer.echo(json.dumps(result.to_dict(), indent=2))
        return result

    # Run PRs
    result = engine.run_campaign(
        repos=repos,
        dry_run=dry_run,
        file=file,
        force=force,
        target_spec=target,
    )

    # Record in history DB
    try:
        from agentkit_cli.history import HistoryDB
        db = HistoryDB(db_path) if db_path else HistoryDB()
        db.record_campaign(result)
    except Exception:
        pass

    if json_output:
        typer.echo(json.dumps(result.to_dict(), indent=2))
        return result

    # Rich table output
    console.print(f"[bold]Campaign ID:[/bold] {result.campaign_id}")
    console.print(f"[bold]Target:[/bold] {target}  [bold]Limit:[/bold] {limit}  [bold]File:[/bold] {file}\n")

    _render_table(result, dry_run=dry_run)

    # --share
    if share:
        _do_share(result)

    return result


def _do_share(result: CampaignResult) -> None:
    try:
        from agentkit_cli.campaign_report import upload_campaign_report
        url = upload_campaign_report(result)
        if url:
            console.print(f"\n[bold green]📋 Campaign report:[/bold green] {url}")
        else:
            console.print("[yellow]Share: no HERENOW_API_KEY set, skipped.[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Share failed:[/yellow] {e}")
