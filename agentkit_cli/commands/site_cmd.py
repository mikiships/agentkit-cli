"""agentkit site command — multi-page static site generator."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from agentkit_cli.site_engine import SiteConfig, SiteEngine

console = Console()

DEFAULT_BASE_URL = "https://mikiships.github.io/agentkit-cli/"
DEFAULT_TOPICS = "python,typescript,rust,go"


def site_command(
    output_dir: str = "site",
    topics: str = DEFAULT_TOPICS,
    limit: int = 20,
    live: bool = typer.Option(False, "--live", help="Fetch and score top repos before generating site"),
    share: bool = False,
    deploy: bool = typer.Option(False, "--deploy", help="Copy generated site into docs/ and commit+push to GitHub Pages"),
    base_url: str = DEFAULT_BASE_URL,
    json_output: bool = False,
    quiet: bool = False,
    db_path: Optional[Path] = None,
    repo_path: Optional[Path] = None,
    deploy_dir: str = "docs",
    commit_message: str = "chore: update agentkit site [skip ci]",
    no_push: bool = False,
    _engine: Optional[SiteEngine] = None,
    _upload_fn=None,
    _populate_fn=None,
) -> Optional[dict]:
    """Generate a multi-page static site from agentkit history data."""
    topic_list = [t.strip().lower() for t in topics.split(",") if t.strip()]
    output_path = Path(output_dir)

    config = SiteConfig(base_url=base_url, topics=topic_list, limit=max(1, limit))

    if _engine is not None:
        engine = _engine
        engine.config = config
    else:
        engine = SiteEngine(config=config, db_path=db_path)

    # --live: populate data first
    if live:
        if not quiet:
            console.print(f"[bold]Populating data for {len(topic_list)} topic(s)…[/bold]")
        try:
            if _populate_fn is not None:
                _populate_fn(topic_list, limit)
            else:
                from agentkit_cli.populate_engine import PopulateEngine
                pop_engine = PopulateEngine(db_path=db_path)
                pop_engine.populate(topics=topic_list, limit=limit, quiet=quiet)
        except Exception as exc:
            if not quiet:
                console.print(f"[yellow]Warning: populate step failed: {exc}[/yellow]")

    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Generating site pages…", total=None)
            result = engine.generate_site(output_path, topics=topic_list, limit=limit)
    else:
        result = engine.generate_site(output_path, topics=topic_list, limit=limit)

    share_url: Optional[str] = None
    if share:
        index_html = (output_path / "index.html").read_text(encoding="utf-8")
        try:
            if _upload_fn is not None:
                share_url = _upload_fn(index_html)
            else:
                from agentkit_cli.share import upload_scorecard
                share_url = upload_scorecard(index_html)
            if not quiet and share_url:
                console.print(f"[bold green]📡 Published:[/bold green] {share_url}")
        except Exception as exc:
            if not quiet:
                console.print(f"[yellow]Warning: share failed: {exc}[/yellow]")

    deploy_result: Optional[dict] = None
    if deploy:
        deploy_result = _run_deploy(
            output_path=output_path,
            repo_path=repo_path or Path("."),
            deploy_dir=deploy_dir,
            commit_message=commit_message,
            no_push=no_push,
            quiet=quiet,
        )

    pages_count = len(result.pages)
    sitemap_count = result.sitemap_xml.count("<url>")
    summary = {
        "pages_generated": pages_count,
        "sitemap_count": sitemap_count,
        "output_dir": str(output_path.resolve()),
        "share_url": share_url,
        "deploy": deploy_result,
    }

    if json_output:
        print(json.dumps(summary, indent=2))
    elif not quiet:
        console.print(f"\n[bold green]✓ Site generated:[/bold green] {output_path}  ({pages_count} pages, {sitemap_count} in sitemap)")
        if share_url:
            console.print(f"[bold]Share URL:[/bold] {share_url}")

    return summary


def _run_deploy(
    output_path: Path,
    repo_path: Path,
    deploy_dir: str,
    commit_message: str,
    no_push: bool,
    quiet: bool,
) -> dict:
    """Copy output_path to deploy_dir within repo_path, commit, and optionally push."""
    docs_dir = repo_path / deploy_dir
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Copy site files
    for item in output_path.iterdir():
        dest = docs_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    if not quiet:
        console.print(f"[green]✓ Copied site to {docs_dir}[/green]")

    # git add + commit
    cwd = str(repo_path.resolve())
    try:
        subprocess.run(
            ["git", "add", deploy_dir],
            cwd=cwd,
            check=True,
            capture_output=True,
        )
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=cwd,
            capture_output=True,
        )
        committed = False
        if diff.returncode != 0:
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=cwd,
                check=True,
                capture_output=True,
            )
            committed = True
            if not quiet:
                console.print(f"[green]✓ Committed: {commit_message}[/green]")
        else:
            if not quiet:
                console.print("[dim]No changes to commit.[/dim]")

        pushed = False
        if not no_push and committed:
            subprocess.run(
                ["git", "push"],
                cwd=cwd,
                check=True,
                capture_output=True,
            )
            pushed = True
            if not quiet:
                console.print("[green]✓ Pushed to remote.[/green]")

        return {"success": True, "committed": committed, "pushed": pushed, "deploy_dir": str(docs_dir)}
    except subprocess.CalledProcessError as exc:
        msg = exc.stderr.decode() if exc.stderr else str(exc)
        if not quiet:
            console.print(f"[red]Deploy error: {msg}[/red]")
        return {"success": False, "error": msg, "deploy_dir": str(docs_dir)}
