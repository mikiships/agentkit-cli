"""agentkit changelog command."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.changelog_engine import ChangelogEngine


def changelog_command(
    since: Optional[str] = None,
    version: Optional[str] = None,
    fmt: str = "markdown",
    output: Optional[Path] = None,
    score_delta: bool = True,
    no_chore: bool = False,
    project: Optional[str] = None,
    github_release: bool = False,
    create_release: bool = False,
    db_path: Optional[str] = None,
) -> str:
    """Generate a changelog from git commits + quality score deltas."""
    if github_release:
        fmt = "release"

    # Gather data
    commits = ChangelogEngine.from_git(since=since, path=".")

    delta = None
    if score_delta:
        delta = ChangelogEngine.from_history(project=project, since_days=7, db_path=db_path)

    # Filter commits if --no-chore
    _EXCLUDE = {"chore", "test", "ci", "build", "style"}
    if no_chore:
        from agentkit_cli.changelog_engine import _detect_prefix
        commits = [c for c in commits if _detect_prefix(c.message) not in _EXCLUDE]

    # Render
    if fmt == "json":
        payload = {
            "version": version,
            "commits": [
                {
                    "hash": c.hash,
                    "message": c.message,
                    "files_changed": c.files_changed,
                    "author": c.author,
                    "ts": c.ts,
                }
                for c in commits
            ],
            "score_delta": {
                "before": delta.before,
                "after": delta.after,
                "delta": delta.delta,
                "project": delta.project,
            } if delta else None,
        }
        content = json.dumps(payload, indent=2)
    elif fmt == "release":
        content = ChangelogEngine.render_release(commits, delta, version=version, no_chore=no_chore)
        # GITHUB_STEP_SUMMARY support
        ChangelogEngine.write_github_step_summary(content)
    else:
        content = ChangelogEngine.render_markdown(commits, delta, version=version)

    # Output
    if output:
        Path(output).write_text(content, encoding="utf-8")
        typer.echo(f"Changelog written to: {output}")
    else:
        typer.echo(content)

    # Create GitHub release if requested
    if create_release and fmt == "release" and version:
        success = ChangelogEngine.create_github_release(version=version, body=content)
        if success:
            typer.echo(f"GitHub release {version} created.")
        else:
            typer.echo("Failed to create GitHub release. Is `gh` CLI installed and authenticated?", err=True)

    return content
