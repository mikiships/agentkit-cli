"""agentkit site command — multi-page static site generator."""
from __future__ import annotations

import json
import os
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
    live: bool = False,
    share: bool = False,
    deploy: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    json_output: bool = False,
    quiet: bool = False,
    db_path: Optional[Path] = None,
    _engine: Optional[SiteEngine] = None,
    _upload_fn=None,
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

    if deploy:
        if not quiet:
            console.print("[yellow]--deploy copies site to docs/ — push to GitHub Pages manually or via build-loop.[/yellow]")
        docs_dir = Path("docs")
        docs_dir.mkdir(exist_ok=True)
        import shutil
        for item in output_path.iterdir():
            dest = docs_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        if not quiet:
            console.print(f"[green]✓ Copied to docs/[/green]")

    pages_count = len(result.pages)
    sitemap_count = result.sitemap_xml.count("<url>")
    summary = {
        "pages_generated": pages_count,
        "sitemap_count": sitemap_count,
        "output_dir": str(output_path.resolve()),
        "share_url": share_url,
    }

    if json_output:
        print(json.dumps(summary, indent=2))
    elif not quiet:
        console.print(f"\n[bold green]✓ Site generated:[/bold green] {output_path}  ({pages_count} pages, {sitemap_count} in sitemap)")
        if share_url:
            console.print(f"[bold]Share URL:[/bold] {share_url}")

    return summary
