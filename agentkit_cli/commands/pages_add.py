"""agentkit pages-add — analyze a single repo and add it to the leaderboard."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console

from agentkit_cli.analyze import analyze_target, parse_target
from agentkit_cli.pages_sync_engine import SyncEngine

console = Console()


def pages_add_command(
    target: str,
    push: bool = True,
    share: bool = False,
    docs_dir: Optional[Path] = None,
) -> dict:
    """Analyze target and immediately add it to docs/data.json + push."""

    # Validate target
    try:
        _url, repo_name = parse_target(target)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        return {"error": str(e)}

    console.print(f"[bold]agentkit pages-add[/bold] — analyzing {target} …")

    # Run analysis
    try:
        result = analyze_target(target=target)
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        return {"error": str(e)}

    console.print(
        f"[green]✓[/green] Analyzed [bold]{repo_name}[/bold]: "
        f"score={result.composite_score:.1f} grade={result.grade}"
    )

    # --share: upload scorecard
    share_url: Optional[str] = None
    if share:
        try:
            from agentkit_cli.share import generate_scorecard_html, upload_scorecard
            score_result = {"composite": result.composite_score}
            for key, tr in result.tools.items():
                if tr.get("score") is not None:
                    score_result[key] = tr["score"]
            html = generate_scorecard_html(
                score_result,
                project_name=result.repo_name,
                ref=target,
                repo_url=target,
                repo_name=result.repo_name,
            )
            share_url = upload_scorecard(html)
            if share_url:
                console.print(f"[green]✓[/green] Score card: {share_url}")
        except Exception as e:
            console.print(f"[yellow]Warning: share failed — {e}[/yellow]")

    # Sync to data.json + push
    engine = SyncEngine(docs_dir=docs_dir)
    sync_summary = engine.sync(push=push)

    if share_url:
        # Annotate the entry in data.json with share_url
        try:
            data = engine.load_existing()
            for entry in data.get("repos", []):
                if entry["name"] == repo_name:
                    entry["share_url"] = share_url
                    break
            engine.write_data_json(data)
        except Exception:
            pass

    console.print(
        f"[green]✓[/green] Leaderboard updated: "
        f"{sync_summary['added']} added, {sync_summary['updated']} updated, "
        f"{sync_summary['total']} total repos."
    )
    if push and sync_summary.get("pushed"):
        console.print("[green]✓[/green] Pushed to GitHub.")
    console.print("Leaderboard: https://mikiships.github.io/agentkit-cli/")

    return {
        "repo": repo_name,
        "score": result.composite_score,
        "grade": result.grade,
        "share_url": share_url,
        **sync_summary,
    }
