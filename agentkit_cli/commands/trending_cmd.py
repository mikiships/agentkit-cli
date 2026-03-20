"""agentkit trending — fetch and rank trending GitHub repos by agent quality."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.trending import fetch_trending, fetch_popular

console = Console()

_MAX_LIMIT = 25


def _grade_color(grade: str) -> str:
    return {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}.get(grade, "dim")


def _score_color(score: Optional[float]) -> str:
    if score is None:
        return "dim"
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _analyze_repo(full_name: str, timeout: int = 120) -> dict:
    """Run `agentkit analyze` on a GitHub repo and return score/grade.

    Returns dict with 'score' (float|None) and 'grade' (str|None).
    """
    from agentkit_cli.analyze import analyze_target

    try:
        result = analyze_target(
            target=f"github:{full_name}",
            keep=False,
            publish=False,
            timeout=timeout,
            no_generate=True,
        )
        return {
            "score": result.composite_score,
            "grade": _score_to_grade(result.composite_score),
        }
    except Exception as exc:
        console.print(f"[dim]  Warning: analysis failed for {full_name}: {exc}[/dim]", stderr=True)
        return {"score": None, "grade": None}


def _score_to_grade(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def trending_command(
    period: str = "week",
    topic: Optional[str] = None,
    limit: int = 10,
    category: str = "ai",
    share: bool = False,
    json_output: bool = False,
    no_analyze: bool = False,
    min_stars: int = 100,
    token: Optional[str] = None,
) -> None:
    """Fetch trending GitHub repos and score each with agentkit analyze."""
    # Clamp limit
    limit = min(limit, _MAX_LIMIT)

    # Resolve token
    resolved_token = token or os.environ.get("GITHUB_TOKEN")

    if not json_output:
        if topic:
            console.print(f"\n[bold]agentkit trending[/bold] — period: {period}, topic: {topic}, limit: {limit}")
        else:
            console.print(f"\n[bold]agentkit trending[/bold] — period: {period}, category: {category}, limit: {limit}")

    # Fetch repos
    if topic:
        repos = fetch_trending(period=period, topic=topic, limit=limit, token=resolved_token)
    else:
        # Merge trending + popular for category, deduplicate by full_name
        trending_repos = fetch_trending(period=period, limit=limit, token=resolved_token)
        popular_repos = fetch_popular(category=category, limit=limit, token=resolved_token)
        seen: set[str] = set()
        repos = []
        for r in trending_repos + popular_repos:
            if r["full_name"] not in seen:
                seen.add(r["full_name"])
                repos.append(r)
        repos = repos[:limit]

    # Filter by min_stars
    repos = [r for r in repos if r.get("stars", 0) >= min_stars]

    if not repos:
        if json_output:
            print(json.dumps({"period": period, "topic": topic, "repos": []}))
        else:
            console.print("[yellow]No repos found matching criteria.[/yellow]")
        return

    # Analyze
    results = []
    for i, repo in enumerate(repos, start=1):
        if not json_output and not no_analyze:
            console.print(f"  [{i}/{len(repos)}] Analyzing [bold]{repo['full_name']}[/bold]…")

        score_info: dict = {"score": None, "grade": None}
        if not no_analyze:
            score_info = _analyze_repo(repo["full_name"])

        results.append({
            "rank": i,
            "full_name": repo["full_name"],
            "description": repo.get("description", ""),
            "stars": repo.get("stars", 0),
            "language": repo.get("language", ""),
            "url": repo.get("url", f"https://github.com/{repo['full_name']}"),
            "score": score_info["score"],
            "grade": score_info["grade"],
        })

    # Sort by score desc (None last)
    results.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    for i, r in enumerate(results, start=1):
        r["rank"] = i

    if json_output:
        out = {
            "period": period,
            "topic": topic,
            "repos": [
                {
                    "rank": r["rank"],
                    "full_name": r["full_name"],
                    "stars": r["stars"],
                    "score": r["score"],
                    "grade": r["grade"],
                    "url": r["url"],
                }
                for r in results
            ],
        }
        print(json.dumps(out, indent=2))
        return

    # Rich table
    table = Table(title="Trending Repos — Agent Quality Rankings", show_header=True, header_style="bold")
    table.add_column("Rank", style="dim", width=5)
    table.add_column("Repo", style="bold", min_width=30)
    table.add_column("Stars", justify="right", width=8)
    table.add_column("Score", justify="right", width=7)
    table.add_column("Grade", justify="center", width=6)
    table.add_column("URL", max_width=45)

    for r in results:
        score_str = str(int(round(r["score"]))) if r["score"] is not None else "N/A"
        grade_str = r["grade"] or "N/A"
        table.add_row(
            f"#{r['rank']}",
            r["full_name"],
            f"{r['stars']:,}",
            f"[{_score_color(r['score'])}]{score_str}[/]",
            f"[{_grade_color(grade_str)}]{grade_str}[/]",
            r["url"],
        )

    console.print(table)

    # Drill-down hint
    if topic:
        console.print(
            f"\n[dim]Drill down: [bold]agentkit topic {topic}[/bold] for topic-specific repos[/dim]"
        )

    # --share
    if share:
        from agentkit_cli.trending_report import generate_html, publish_report
        from agentkit_cli.publish import PublishError

        console.print("\nGenerating report…", style="dim")
        html = generate_html(results)

        try:
            url = publish_report(html)
            console.print(f"\n[bold green]Trending report:[/bold green] {url}")
            anon = not bool(os.environ.get("HERENOW_API_KEY"))
            if anon:
                console.print(
                    "[dim]Note: anonymous publish — link expires in 24h. "
                    "Set HERENOW_API_KEY for persistent links.[/dim]"
                )
        except PublishError as exc:
            console.print(f"[yellow]Warning: publish failed ({exc}). Saving locally.[/yellow]")
            fallback = Path("./trending-report.html")
            fallback.write_text(html, encoding="utf-8")
            console.print(f"[dim]Saved to {fallback.resolve()}[/dim]")
