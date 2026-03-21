"""agentkit spotlight-queue command — managed rotation queue for spotlight cron."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Manage the spotlight rotation queue.")

_QUEUE_PATH = Path.home() / ".local" / "share" / "agentkit" / "spotlight-queue.json"

DEFAULT_REPOS = [
    "pallets/flask",
    "encode/httpx",
    "tiangolo/fastapi",
    "pydantic/pydantic",
    "pytest-dev/pytest",
    "django/django",
    "celery/celery",
    "sqlalchemy/sqlalchemy",
    "requests/requests",
    "astral-sh/ruff",
]


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _load(path: Path = _QUEUE_PATH) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"repos": [], "lastSpotlighted": {}}


def _save(data: dict, path: Path = _QUEUE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _ensure_seeded(path: Path = _QUEUE_PATH) -> dict:
    """Auto-seed if the queue file does not exist."""
    if not path.exists():
        data = _do_seed(path)
        return data
    return _load(path)


def _do_seed(path: Path = _QUEUE_PATH) -> dict:
    data = _load(path)
    existing = set(data["repos"])
    for repo in DEFAULT_REPOS:
        if repo not in existing:
            data["repos"].append(repo)
    _save(data, path)
    return data


def _parse_repo(repo_arg: str) -> str:
    """Strip 'github:' prefix and return 'owner/repo'."""
    if repo_arg.startswith("github:"):
        return repo_arg[len("github:"):]
    return repo_arg


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

@app.command("add")
def add_repo(
    repo: str = typer.Argument(..., help="Repo to add, e.g. github:owner/repo or owner/repo"),
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Add a repo to the spotlight queue."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = _ensure_seeded(path)
    slug = _parse_repo(repo)
    if slug in data["repos"]:
        typer.echo(f"Already in queue: {slug}")
        return
    data["repos"].append(slug)
    _save(data, path)
    typer.echo(f"Added {slug} to spotlight queue ({len(data['repos'])} repos total).")


@app.command("remove")
def remove_repo(
    repo: str = typer.Argument(..., help="Repo to remove"),
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Remove a repo from the spotlight queue."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = _ensure_seeded(path)
    slug = _parse_repo(repo)
    if slug not in data["repos"]:
        typer.echo(f"Not in queue: {slug}", err=True)
        raise typer.Exit(code=1)
    data["repos"].remove(slug)
    data.get("lastSpotlighted", {}).pop(slug, None)
    _save(data, path)
    typer.echo(f"Removed {slug} from spotlight queue.")


@app.command("list")
def list_queue(
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Show all repos in the queue with last-spotlighted dates."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = _ensure_seeded(path)
    repos = data.get("repos", [])
    last = data.get("lastSpotlighted", {})

    if not repos:
        typer.echo("Spotlight queue is empty. Run `agentkit spotlight-queue seed` to populate.")
        return

    console = Console()
    table = Table(title="Spotlight Queue", show_header=True)
    table.add_column("Repo", style="bold")
    table.add_column("Last Spotlighted")

    for repo in repos:
        table.add_row(repo, last.get(repo, "never"))

    console.print(table)
    console.print(f"Total: {len(repos)} repos")


@app.command("next")
def next_repo(
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Print the next repo to spotlight (plain text, for scripting)."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = _ensure_seeded(path)
    repos = data.get("repos", [])
    last = data.get("lastSpotlighted", {})

    if not repos:
        typer.echo("Spotlight queue is empty.", err=True)
        raise typer.Exit(code=1)

    # Never spotlighted first (in order added)
    for repo in repos:
        if repo not in last:
            # plain stdout, no Rich
            print(repo)
            return

    # All spotlighted — return oldest
    oldest = min(repos, key=lambda r: last.get(r, "0000-00-00"))
    print(oldest)


@app.command("mark-done")
def mark_done(
    repo: str = typer.Argument(..., help="Repo to mark as spotlighted today"),
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Update lastSpotlighted for a repo to today."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = _ensure_seeded(path)
    slug = _parse_repo(repo)
    if slug not in data["repos"]:
        typer.echo(f"Repo not in queue: {slug}", err=True)
        raise typer.Exit(code=1)
    today = str(date.today())
    data.setdefault("lastSpotlighted", {})[slug] = today
    _save(data, path)
    typer.echo(f"Marked {slug} as spotlighted on {today}.")


@app.command("clear")
def clear_queue(
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Empty the spotlight queue."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = {"repos": [], "lastSpotlighted": {}}
    _save(data, path)
    typer.echo("Spotlight queue cleared.")


@app.command("seed")
def seed_queue(
    queue_path: Optional[str] = typer.Option(None, "--queue-path", hidden=True),
) -> None:
    """Seed the queue with 10 default repos."""
    path = Path(queue_path) if queue_path else _QUEUE_PATH
    data = _do_seed(path)
    typer.echo(f"Seeded spotlight queue with default repos ({len(data['repos'])} total).")
