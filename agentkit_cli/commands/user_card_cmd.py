"""agentkit user-card command — compact embeddable agent-readiness card."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from agentkit_cli.user_card import UserCardEngine
from agentkit_cli.renderers.user_card_html import UserCardHTMLRenderer, upload_user_card
from agentkit_cli.history import record_run

console = Console()

_GRADE_COLORS = {
    "A": "green",
    "B": "blue",
    "C": "yellow",
    "D": "red",
}


def user_card_command(
    target: str,
    limit: int = 10,
    min_stars: int = 0,
    skip_forks: bool = True,
    share: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    badge: bool = False,
) -> None:
    """Generate a compact embeddable agent-readiness card for a GitHub user."""
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

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit user-card[/bold] — card for [bold]{username}[/bold]")

    engine = UserCardEngine(
        github_token=resolved_token,
        limit=limit,
        min_stars=min_stars,
        skip_forks=skip_forks,
        timeout=timeout,
    )

    try:
        if not quiet and not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(f"Building card for [bold]{username}[/bold]…", total=None)
                result = engine.run(username)
        else:
            result = engine.run(username)
    except Exception as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    if result.error and not json_output and not quiet:
        console.print(f"[yellow]Warning:[/yellow] {result.error}")

    # Record to history DB
    try:
        record_run(
            project=f"github:{username}",
            tool="user-card",
            score=result.avg_score,
            details={"grade": result.grade, "agent_ready_count": result.agent_ready_count},
            label="user-card",
        )
    except Exception:
        pass

    # Render HTML
    renderer = UserCardHTMLRenderer()
    html = renderer.render(result)

    # --share
    share_url: Optional[str] = None
    if share:
        share_url = upload_user_card(html)
        if share_url:
            # Re-render with embed comment
            html = renderer.render(result, share_url=share_url)
            if not json_output and not quiet:
                console.print(f"\n[bold green]Card published:[/bold green] {share_url}")

    # Badge generation
    badge_url: Optional[str] = None
    badge_markdown: Optional[str] = None
    if badge or json_output:
        from agentkit_cli.user_badge import UserBadgeEngine as _BadgeEngine
        _be = _BadgeEngine()
        _br = _be.run(user=result.username, score=result.avg_score, grade=result.grade)
        badge_url = _br.badge_url
        badge_markdown = _br.badge_markdown

    # JSON output
    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        if badge_url:
            out["badge_url"] = badge_url
        print(json.dumps(out, indent=2))
        return

    # Quiet: only URL
    if quiet:
        if share_url:
            print(share_url)
        return

    # Rich terminal output
    _print_rich_card(result, share_url=share_url)

    # --badge: print badge markdown
    if badge and badge_markdown:
        console.print(f"\n[bold]Agent-Readiness Badge:[/bold]\n{badge_markdown}\n")


def _print_rich_card(result, share_url: Optional[str] = None) -> None:
    """Print compact rich terminal card."""
    grade_color = _GRADE_COLORS.get(result.grade, "white")
    avg_str = f"{result.avg_score:.1f}"

    console.print(
        f"\n[bold]🃏 Agent-Readiness Card:[/bold] "
        f"[bold cyan]@{result.username}[/bold cyan]  "
        f"[bold {grade_color}]Grade {result.grade}[/bold {grade_color}]"
    )
    console.print(
        f"  [dim]Score {avg_str}/100 · "
        f"Context {result.context_coverage_pct:.0f}% · "
        f"{result.agent_ready_count}/{result.analyzed_repos} agent-ready repos[/dim]"
    )
    if result.top_repo_name:
        top_score_str = f"{result.top_repo_score:.0f}/100"
        console.print(
            f"  [dim]Top repo: [cyan]{result.top_repo_name}[/cyan] ({top_score_str})[/dim]"
        )

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")
        console.print(
            f"  [dim]Embed: [/dim]![Agent-Readiness Card]({share_url})"
        )

    console.print(f"\n[dim]{result.summary_line}[/dim]")
    console.print("[dim]Powered by agentkit-cli[/dim]\n")
