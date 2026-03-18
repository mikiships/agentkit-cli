"""agentkit checks CLI commands.

Subcommands:
  agentkit checks verify  — test that Checks API is configured
  agentkit checks post    — manually post a check run
  agentkit checks status  — show last check run posted
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.checks_client import GitHubChecksClient, ChecksEnv, detect_github_env
from agentkit_cli.checks_formatter import format_check_output
from agentkit_cli.composite import _compute_grade

console = Console()

checks_app = typer.Typer(
    name="checks",
    help="GitHub Checks API: verify config, post check runs, view status.",
    add_completion=False,
)

_STATUS_FILE = ".agentkit-checks.json"


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

@checks_app.command("verify")
def verify_cmd() -> None:
    """Test that the Checks API is configured (token present, env vars set)."""
    import os

    issues: list[str] = []

    actions = os.environ.get("GITHUB_ACTIONS")
    if actions != "true":
        issues.append("GITHUB_ACTIONS is not 'true' — not running in GitHub Actions")

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo:
        issues.append("GITHUB_REPOSITORY is missing or malformed")

    sha = os.environ.get("GITHUB_SHA", "")
    if not sha:
        issues.append("GITHUB_SHA is not set")

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        issues.append("GITHUB_TOKEN is not set")

    if issues:
        for issue in issues:
            console.print(f"[red]✗[/red] {issue}")
        console.print(f"\n[red]{len(issues)} issue(s) found.[/red] Checks API will not work.")
        raise typer.Exit(code=1)

    console.print("[green]✓[/green] GITHUB_ACTIONS=true")
    console.print(f"[green]✓[/green] GITHUB_REPOSITORY={repo}")
    console.print(f"[green]✓[/green] GITHUB_SHA={sha[:12]}...")
    console.print("[green]✓[/green] GITHUB_TOKEN is set")
    console.print("\n[green]Checks API is ready.[/green]")


# ---------------------------------------------------------------------------
# post
# ---------------------------------------------------------------------------

@checks_app.command("post")
def post_cmd(
    score: float = typer.Option(100.0, "--score", help="Composite score (0-100)"),
    grade: Optional[str] = typer.Option(None, "--grade", help="Grade (A/B/C/D/F, auto-computed if omitted)"),
    conclusion: str = typer.Option("success", "--conclusion", help="Check conclusion: success|failure|neutral"),
    name: str = typer.Option("agentkit", "--name", help="Check run name"),
) -> None:
    """Manually post a check run with the given score and conclusion."""
    env = detect_github_env()
    if env is None:
        console.print("[red]Error:[/red] Not in GitHub Actions environment. Set GITHUB_ACTIONS, GITHUB_REPOSITORY, GITHUB_SHA, GITHUB_TOKEN.")
        raise typer.Exit(code=1)

    resolved_grade = grade or _compute_grade(score)
    output = format_check_output({"score": score, "grade": resolved_grade, "components": {}})

    client = GitHubChecksClient(env=env)
    check_id = client.create_check_run(name=name, status="completed")
    if check_id is None:
        console.print("[red]Error:[/red] Failed to create check run.")
        raise typer.Exit(code=1)

    success = client.update_check_run(
        check_id, status="completed", conclusion=conclusion, output=output,
    )
    if not success:
        console.print("[red]Error:[/red] Failed to update check run.")
        raise typer.Exit(code=1)

    # Save to local status file
    status_data = {
        "check_run_id": check_id,
        "score": score,
        "grade": resolved_grade,
        "conclusion": conclusion,
        "repo": env.full_repo,
        "sha": env.sha,
    }
    try:
        Path(_STATUS_FILE).write_text(json.dumps(status_data, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass

    console.print(f"[green]✓[/green] Check run #{check_id} posted: {score:.0f}/100 ({resolved_grade}) — {conclusion}")


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@checks_app.command("status")
def status_cmd() -> None:
    """Show the last check run posted in this repo."""
    status_path = Path(_STATUS_FILE)
    if not status_path.exists():
        console.print("[yellow]No check runs recorded.[/yellow] Run `agentkit checks post` or use `agentkit run --checks` first.")
        raise typer.Exit(code=0)

    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[red]Error reading {_STATUS_FILE}:[/red] {exc}")
        raise typer.Exit(code=1)

    console.print("[bold]Last check run:[/bold]")
    console.print(f"  Check ID:   {data.get('check_run_id', 'unknown')}")
    console.print(f"  Score:      {data.get('score', 'unknown')}")
    console.print(f"  Grade:      {data.get('grade', 'unknown')}")
    console.print(f"  Conclusion: {data.get('conclusion', 'unknown')}")
    console.print(f"  Repo:       {data.get('repo', 'unknown')}")
    console.print(f"  SHA:        {data.get('sha', 'unknown')}")
