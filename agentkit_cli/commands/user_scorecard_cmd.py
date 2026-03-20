"""agentkit user-scorecard command."""
from __future__ import annotations

import json
import os
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentkit_cli.user_scorecard import UserScorecardEngine
from agentkit_cli.user_scorecard_report import UserScorecardReportRenderer
from agentkit_cli.share import upload_scorecard

console = Console()

# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def user_scorecard_command(
    target: str,
    limit: int = 20,
    min_stars: int = 0,
    skip_forks: bool = True,
    json_output: bool = False,
    share: bool = False,
    pages: Optional[str] = None,
    quiet: bool = False,
    timeout: int = 60,
    token: Optional[str] = None,
    badge: bool = False,
) -> None:
    """Fetch all public repos for a GitHub user and generate an agent-readiness profile card."""
    # Parse github:<user> or bare <user>
    if target.startswith("github:"):
        username = target[len("github:"):]
    else:
        username = target

    username = username.strip("/").strip()
    if not username:
        if json_output:
            console.print(json.dumps({"error": "Username is required. Use github:<user> or bare <user>."}))
        else:
            console.print("[red]Error:[/red] Username is required. Use github:<user> or bare <user>.")
        raise typer.Exit(code=1)

    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit user-scorecard[/bold] — profiling [bold]{username}[/bold]")

    engine = UserScorecardEngine(
        username=username,
        limit=limit,
        min_stars=min_stars,
        skip_forks=skip_forks,
        timeout=timeout,
        token=resolved_token,
    )

    # Run with progress bar
    scored = {"count": 0}

    def _progress_cb(full_name: str, score_str: str) -> None:
        scored["count"] += 1
        if not quiet and not json_output:
            console.print(f"  [dim][{full_name}] score {score_str}/100[/dim]")

    try:
        if not quiet and not json_output:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(f"Analyzing repos for [bold]{username}[/bold]…", total=None)
                result = engine.run(progress_callback=_progress_cb)
        else:
            result = engine.run(progress_callback=_progress_cb)
    except ValueError as exc:
        if json_output:
            console.print(json.dumps({"error": str(exc)}))
        else:
            console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1)

    # Generate HTML report
    renderer = UserScorecardReportRenderer()
    html = renderer.render(result)

    # --share
    share_url: Optional[str] = None
    if share:
        share_url = upload_scorecard(html)
        if share_url and not json_output and not quiet:
            console.print(f"\n[bold green]Profile card published:[/bold green] {share_url}")

    # --pages
    pages_url: Optional[str] = None
    if pages:
        pages_url = _push_to_pages(html, pages, username, resolved_token, quiet=quiet, json_output=json_output)

    # Badge generation
    badge_url: Optional[str] = None
    badge_markdown: Optional[str] = None
    if badge or json_output:
        from agentkit_cli.user_badge import UserBadgeEngine as _BadgeEngine
        _be = _BadgeEngine()
        _br = _be.run(user=username, score=result.avg_score, grade=result.grade)
        badge_url = _br.badge_url
        badge_markdown = _br.badge_markdown

    # JSON output
    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        if pages_url:
            out["pages_url"] = pages_url
        if badge_url:
            out["badge_url"] = badge_url
        print(json.dumps(out, indent=2))
        return

    # Quiet: only URL
    if quiet:
        if share_url:
            print(share_url)
        elif pages_url:
            print(pages_url)
        return

    # Rich terminal output
    _print_rich_summary(result, share_url=share_url, pages_url=pages_url)

    # --badge: print badge markdown
    if badge and badge_markdown:
        console.print(f"\n[bold]Agent-Readiness Badge:[/bold]\n{badge_markdown}\n")


def _push_to_pages(
    html: str,
    pages_target: str,
    username: str,
    token: Optional[str],
    quiet: bool = False,
    json_output: bool = False,
) -> Optional[str]:
    """Push HTML to GitHub Pages repo. Returns pages URL."""
    import tempfile
    from pathlib import Path
    from agentkit_cli.engines.org_pages import (
        _clone_or_pull_pages_repo,
        _commit_and_push,
        _parse_pages_url,
    )

    # Parse github:<owner>/<repo>
    if pages_target.startswith("github:"):
        pages_repo = pages_target[len("github:"):]
    else:
        pages_repo = pages_target

    pages_repo = pages_repo.strip("/")

    with tempfile.TemporaryDirectory(prefix="agentkit-user-pages-") as tmp:
        clone_dir = Path(tmp)
        ok, remote_url = _clone_or_pull_pages_repo(
            pages_repo=pages_repo,
            clone_dir=clone_dir,
            pages_branch="main",
            token=token,
        )
        if not ok:
            if not json_output and not quiet:
                console.print("[yellow]Warning: could not clone pages repo[/yellow]")
            return None

        pages_url = _parse_pages_url(remote_url, "docs/")
        out_dir = clone_dir / "docs"
        out_dir.mkdir(parents=True, exist_ok=True)
        html_file = out_dir / "user-scorecard.html"
        html_file.write_text(html, encoding="utf-8")

        pushed, err = _commit_and_push(
            repo_root=clone_dir,
            files=[html_file],
            commit_msg=f"chore: update user-scorecard for {username} [skip ci]",
            pages_branch="main",
        )

        if pushed:
            if not json_output and not quiet:
                console.print(f"\n[bold green]User scorecard page (permanent):[/bold green] {pages_url}docs/user-scorecard.html")
            return pages_url
        else:
            if not json_output and not quiet:
                console.print(f"[yellow]Warning: pages push failed ({err})[/yellow]")
            return None


def _print_rich_summary(result, share_url=None, pages_url=None) -> None:
    """Print rich terminal summary of scorecard result."""
    from agentkit_cli.user_scorecard_report import _grade_color

    grade = result.grade
    username = result.username

    # Grade badge with color
    grade_colors = {"A": "green", "B": "blue", "C": "yellow", "D": "red"}
    grade_rich_color = grade_colors.get(grade, "white")

    console.print(
        f"\n[bold]🧑‍💻 Agent Quality Profile:[/bold] "
        f"[bold cyan]@{username}[/bold cyan]  "
        f"[bold {grade_rich_color}]Grade {grade}[/bold {grade_rich_color}]"
    )
    console.print(
        f"  [dim]{result.analyzed_repos} repos analyzed · "
        f"avg score {result.avg_score:.1f} · "
        f"context coverage {result.context_coverage_pct:.0f}%[/dim]\n"
    )

    # Top repos table
    if result.top_repos:
        top_table = Table(
            title="Top Repositories",
            show_header=True,
            header_style="bold",
        )
        top_table.add_column("Rank", width=4, justify="center")
        top_table.add_column("Repository")
        top_table.add_column("Score", justify="right", width=7)
        top_table.add_column("Grade", justify="center", width=6)
        top_table.add_column("Context", justify="center", width=8)

        for rank, repo in enumerate(result.top_repos, 1):
            score_str = f"{repo.score:.0f}" if repo.score is not None else "—"
            context_str = "[green]✓[/green]" if repo.has_context else "[dim]✗[/dim]"
            repo_grade = repo.grade
            rg_color = grade_colors.get(repo_grade, "white")
            top_table.add_row(
                str(rank),
                repo.full_name,
                score_str,
                f"[{rg_color}]{repo_grade}[/{rg_color}]",
                context_str,
            )
        console.print(top_table)

    # Needs work section
    if result.bottom_repos:
        console.print("\n[bold yellow]Needs Improvement:[/bold yellow]")
        for repo in result.bottom_repos:
            score_str = f"{repo.score:.0f}" if repo.score is not None else "—"
            console.print(
                f"  [red]·[/red] [cyan]{repo.full_name}[/cyan] [dim](score {score_str})[/dim]"
                f"\n    [dim]run: agentkit analyze github:{repo.full_name}[/dim]"
            )

    if share_url:
        console.print(f"\n[bold green]Share URL:[/bold green] {share_url}")
    if pages_url:
        console.print(f"[bold green]Pages URL:[/bold green] {pages_url}")

    console.print("\n[dim]Powered by agentkit-cli[/dim]")
