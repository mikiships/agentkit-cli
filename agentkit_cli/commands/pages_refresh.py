"""agentkit pages-refresh command — refresh GitHub Pages leaderboard with live scores."""
from __future__ import annotations

import json
import os
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from rich.console import Console

from agentkit_cli.site_engine import SiteEngine, build_frontdoor_stats

console = Console()

DEFAULT_ECOSYSTEMS = ["python", "typescript", "rust", "go"]
DEFAULT_LIMIT = 5
DOCS_DIR = Path("docs")


def score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 80:
        return "A"
    elif score >= 65:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    return "F"


def build_data_json(
    result,
    ecosystems_order: Optional[List[str]] = None,
    *,
    frontdoor: Optional[dict[str, Any]] = None,
    generated_at: Optional[str] = None,
) -> dict:
    """Build the data.json structure from a LeaderboardPageResult."""
    repos = []
    seen = set()
    eco_order = ecosystems_order or DEFAULT_ECOSYSTEMS

    for eco in result.ecosystems:
        for entry in eco.entries:
            key = entry.repo_full_name
            if key in seen:
                continue
            seen.add(key)
            repos.append({
                "name": entry.repo_full_name,
                "url": f"https://github.com/{entry.repo_full_name}",
                "score": round(entry.score, 1),
                "grade": entry.grade or score_to_grade(entry.score),
                "ecosystem": entry.ecosystem or eco.ecosystem,
                "source": "ecosystem",
            })

    scores = [r["score"] for r in repos]
    stats = {
        "total": len(repos),
        "median": round(statistics.median(scores), 1) if scores else 0,
        "top_score": round(max(scores), 1) if scores else 0,
    }

    return {
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "frontdoor": build_frontdoor_stats(frontdoor),
        "repos": repos,
        "stats": stats,
    }


def load_existing_data(docs_dir: Path) -> dict:
    data_json_path = docs_dir / "data.json"
    if not data_json_path.exists():
        return {
            "generated_at": "",
            "frontdoor": build_frontdoor_stats(),
            "repos": [],
            "stats": {"total": 0, "median": 0, "top_score": 0},
        }
    return json.loads(data_json_path.read_text(encoding="utf-8"))


def update_index_html(index_path: Path, data: dict) -> bool:
    """Rewrite docs/index.html from the canonical data.json payload. Returns True if changed."""
    engine = SiteEngine()
    html = engine.generate_index(site_data=data).html
    original = index_path.read_text(encoding="utf-8") if index_path.exists() else None
    if html != original:
        index_path.write_text(html, encoding="utf-8")
        return True
    return False


def pages_refresh_command(
    ecosystems: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    docs_dir: Optional[Path] = None,
    token: Optional[str] = None,
    frontdoor_version: Optional[str] = None,
    frontdoor_test_count: Optional[int] = None,
    frontdoor_version_count: Optional[int] = None,
    frontdoor_package_count: Optional[int] = None,
    from_existing_data: bool = False,
    _engine_factory=None,
) -> dict:
    """Run ecosystem scoring and refresh GitHub Pages docs/."""
    from agentkit_cli.leaderboard_page import LeaderboardPageEngine

    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    eco_list = [e.strip().lower() for e in (ecosystems or "python,typescript,rust,go").split(",") if e.strip()]
    docs = docs_dir or DOCS_DIR
    docs.mkdir(parents=True, exist_ok=True)

    existing_data = load_existing_data(docs)
    frontdoor = build_frontdoor_stats(
        existing_data.get("frontdoor"),
        version=frontdoor_version,
        tests=frontdoor_test_count,
        versions=frontdoor_version_count,
        packages=frontdoor_package_count,
    )

    leaderboard_path = docs / "leaderboard.html"
    if from_existing_data:
        console.print("[bold]agentkit pages-refresh[/bold] — refreshing front door from existing docs/data.json…")
        data = {
            **existing_data,
            "frontdoor": frontdoor,
        }
    else:
        console.print("[bold]agentkit pages-refresh[/bold] — scoring ecosystems…")

        if _engine_factory is not None:
            engine = _engine_factory(eco_list, limit, resolved_token)
        else:
            engine = LeaderboardPageEngine(
                ecosystems=eco_list,
                limit=limit,
                token=resolved_token,
            )

        result = engine.run()
        data = build_data_json(result, eco_list, frontdoor=frontdoor)

        from agentkit_cli.leaderboard_page import render_leaderboard_html
        html = render_leaderboard_html(result)
        leaderboard_path.write_text(html, encoding="utf-8")
        console.print(f"[green]✓[/green] Wrote {leaderboard_path}")

    data_json_path = docs / "data.json"
    data_json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] Wrote {data_json_path} ({data['stats']['total']} repos)")

    index_path = docs / "index.html"
    changed = update_index_html(index_path, data)
    if changed:
        console.print(f"[green]✓[/green] Updated {index_path} (repos scored: {data['stats']['total']})")
    else:
        console.print(f"[dim]  {index_path} unchanged[/dim]")

    console.print(f"\n[bold green]Done.[/bold green] {data['stats']['total']} repos scored, top score {data['stats']['top_score']}, median {data['stats']['median']}")
    return data
