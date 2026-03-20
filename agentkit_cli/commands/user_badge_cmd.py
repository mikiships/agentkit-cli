"""agentkit user-badge command — generate and inject agent-readiness badge."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.user_badge import (
    UserBadgeEngine,
    inject_badge_into_readme,
    score_to_badge_grade,
    PYPI_LINK,
)

console = Console()


def user_badge_command(
    target: str,
    score: Optional[float] = None,
    grade: Optional[str] = None,
    output: Optional[str] = None,
    share: bool = False,
    json_output: bool = False,
    inject: bool = False,
    dry_run: bool = False,
    limit: int = 20,
    token: Optional[str] = None,
) -> None:
    """Generate an agent-readiness badge for a GitHub user."""
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

    engine = UserBadgeEngine()

    # Fast mode: --score provided, skip GitHub scan
    if score is not None:
        resolved_score = float(score)
        if grade is None:
            resolved_grade, _ = score_to_badge_grade(resolved_score)
        else:
            resolved_grade = grade.upper()
    else:
        # Run full user scorecard scan
        resolved_token = token or os.environ.get("GITHUB_TOKEN")
        try:
            from agentkit_cli.user_scorecard import UserScorecardEngine
            sc_engine = UserScorecardEngine(
                username=username,
                limit=limit,
                token=resolved_token,
            )
            if not json_output:
                console.print(f"\n[bold]agentkit user-badge[/bold] — scanning [bold]{username}[/bold]…")
            sc_result = sc_engine.run()
            resolved_score = sc_result.avg_score
            resolved_grade = sc_result.grade if grade is None else grade.upper()
        except Exception as exc:
            if json_output:
                console.print(json.dumps({"error": str(exc)}))
            else:
                console.print(f"[red]Error running scorecard:[/red] {exc}")
            raise typer.Exit(code=1)

    result = engine.run(user=username, score=resolved_score, grade=resolved_grade)

    # --share: publish scorecard HTML
    share_url: Optional[str] = None
    if share:
        try:
            from agentkit_cli.user_scorecard import UserScorecardEngine
            from agentkit_cli.user_scorecard_report import UserScorecardReportRenderer
            from agentkit_cli.share import upload_scorecard

            resolved_token = token or os.environ.get("GITHUB_TOKEN")
            sc_engine = UserScorecardEngine(username=username, limit=limit, token=resolved_token)
            sc_result = sc_engine.run()
            renderer = UserScorecardReportRenderer()
            html = renderer.render(sc_result)
            share_url = upload_scorecard(html)
            if share_url and not json_output:
                console.print(f"\n[bold green]Profile published:[/bold green] {share_url}")
        except Exception as exc:
            if not json_output:
                console.print(f"[yellow]Share failed:[/yellow] {exc}")

    # JSON output
    if json_output:
        out = result.to_dict()
        if share_url:
            out["share_url"] = share_url
        print(json.dumps(out, indent=2))
        return

    # Terminal output
    console.print(f"\n[bold]Agent-Readiness Badge for @{username}:[/bold]\n")
    console.print(f"  Badge URL: {result.badge_url}\n")
    console.print(f"  README markdown:\n  {result.badge_markdown}\n")
    console.print(
        f"  Add to your GitHub profile README with:\n"
        f"    agentkit user-badge github:{username} --inject\n"
    )

    # --output: write markdown to file
    if output:
        out_path = Path(output)
        out_path.write_text(result.badge_markdown + "\n", encoding="utf-8")
        console.print(f"[green]Badge markdown written to:[/green] {out_path}")

    # --inject: auto-inject into local README.md
    if inject:
        readme_path = Path("README.md")
        if not readme_path.exists():
            console.print(
                f"[yellow]README.md not found in current directory.[/yellow]\n"
                f"Copy this markdown into your README.md:\n\n{result.badge_markdown}\n"
            )
        else:
            content = readme_path.read_text(encoding="utf-8")
            new_content = inject_badge_into_readme(content, result.badge_markdown)
            if dry_run:
                console.print("\n[bold]Dry run — badge section to inject:[/bold]")
                console.print(result.badge_markdown)
            else:
                readme_path.write_text(new_content, encoding="utf-8")
                console.print(f"[green]Badge injected into README.md[/green]")
