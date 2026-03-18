"""agentkit share — generate and upload a shareable score card to here.now."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.share import generate_scorecard_html, upload_scorecard

console = Console()


def _get_project_name(path: Optional[Path], override: Optional[str]) -> str:
    if override:
        return override
    # Try git remote origin
    try:
        cwd = str(path or Path.cwd())
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract repo name from URL
            name = url.rstrip("/").split("/")[-1]
            if name.endswith(".git"):
                name = name[:-4]
            if name:
                return name
    except Exception:
        pass
    return (path or Path.cwd()).resolve().name


def _get_git_ref(path: Optional[Path]) -> str:
    try:
        cwd = str(path or Path.cwd())
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result.returncode == 0:
            ref = result.stdout.strip()
            if ref and ref != "HEAD":
                return ref
        # Detached HEAD: try short sha
        result2 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5,
        )
        if result2.returncode == 0:
            return result2.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _load_report_json(report_path: Path) -> dict:
    with report_path.open() as f:
        return json.load(f)


def _run_score_inline(path: Optional[Path]) -> dict:
    """Run agentkit score --json inline and return parsed result."""
    from agentkit_cli.composite import CompositeScoreEngine
    from agentkit_cli.config import find_project_root
    from agentkit_cli.commands.score_cmd import _run_agentlint_fast, _get_last_tool_score
    from pathlib import Path as _Path

    cwd = str(path or Path.cwd())
    try:
        root = find_project_root(cwd)
    except Exception:
        root = cwd

    root_path = _Path(root).resolve()
    project = root_path.name

    # Gather tool scores (same logic as score_cmd)
    tool_scores: dict = {}
    tool_scores["agentlint"] = _run_agentlint_fast(str(root_path))
    for tool in ("coderace", "agentmd", "agentreflect"):
        tool_scores[tool] = _get_last_tool_score(project, tool)

    engine = CompositeScoreEngine()
    result = engine.compute(tool_scores)
    return {
        "composite": result.score,
        "breakdown": result.components,
    }


def share_command(
    report: Optional[Path],
    project: Optional[str],
    no_scores: bool,
    json_output: bool,
    path: Optional[Path],
    api_key: Optional[str],
) -> None:
    """Generate and upload a shareable score card to here.now."""

    # Resolve project name and ref
    project_name = _get_project_name(path, project)
    ref = _get_git_ref(path)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Get scores
    if report is not None:
        if not report.exists():
            print(f"Error: Report file not found: {report}", file=sys.stderr)
            raise typer.Exit(1)
        try:
            score_result = _load_report_json(report)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in report: {e}", file=sys.stderr)
            raise typer.Exit(1)
    else:
        print("Computing scores…", file=sys.stderr)
        try:
            score_result = _run_score_inline(path)
        except Exception as e:
            print(f"Error: Failed to compute scores: {e}", file=sys.stderr)
            raise typer.Exit(1)

    # Generate HTML
    html = generate_scorecard_html(
        score_result=score_result,
        project_name=project_name,
        ref=ref,
        timestamp=timestamp,
        no_scores=no_scores,
    )

    # Upload
    print("Uploading score card…", file=sys.stderr)
    resolved_key = api_key or os.environ.get("HERENOW_API_KEY") or None
    url = upload_scorecard(html, api_key=resolved_key)

    if url is None:
        print("Warning: Upload failed. Score card not published.", file=sys.stderr)
        raise typer.Exit(1)

    # Extract composite score for JSON output
    composite = score_result.get("composite") or score_result.get("score")

    if json_output:
        out: dict = {"url": url}
        if composite is not None:
            out["score"] = int(round(float(composite)))
        print(json.dumps(out))
    else:
        print(f"Score card: {url}")
        anonymous = not bool(resolved_key)
        if anonymous:
            print("Note: anonymous publish — link expires in 24h. Set HERENOW_API_KEY for persistent links.")
