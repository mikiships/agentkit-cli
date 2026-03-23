"""agentkit pages-refresh command — refresh GitHub Pages leaderboard with live scores."""
from __future__ import annotations

import json
import os
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from rich.console import Console

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


def build_data_json(result, ecosystems_order: Optional[List[str]] = None) -> dict:
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
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repos": repos,
        "stats": stats,
    }


def update_index_html(index_path: Path, data: dict) -> bool:
    """Update docs/index.html stat counters from data.json. Returns True if changed."""
    if not index_path.exists():
        return False

    html = index_path.read_text(encoding="utf-8")
    original = html

    total = data["stats"]["total"]

    # Update hero badge: "v0.93.0 · 0 repos scored" -> "v0.93.0 · N repos scored"
    html = re.sub(
        r'(v[\d.]+\s*&middot;\s*)\d+(\s*repos scored)',
        rf'\g<1>{total}\2',
        html,
    )

    # Update stat-num for Repos Scored (handle optional id attribute)
    html = re.sub(
        r'(<div class="stat-num"[^>]*>)\d+(</div><div class="stat-label">Repos Scored</div>)',
        rf'\g<1>{total}\2',
        html,
    )

    # Ensure repos-scored-stat id is present on the Repos Scored stat
    html = re.sub(
        r'<div class="stat-num"(?! id="repos-scored-stat")([^>]*>)(\d+)(</div><div class="stat-label">Repos Scored</div>)',
        rf'<div class="stat-num" id="repos-scored-stat"\1\2\3',
        html,
    )

    # Inject/replace Recently Scored Repos section and fetch script
    recently_section = _recently_scored_section()
    fetch_script = _fetch_script()

    # Replace existing recently-scored-section if present, else insert after stats-strip closing tag
    if 'id="recently-scored"' in html:
        html = re.sub(
            r'<section[^>]*id="recently-scored"[^>]*>.*?</section>',
            recently_section,
            html,
            flags=re.DOTALL,
        )
    else:
        # Insert after </section> that closes the pipeline-section (first </section> after stats-strip)
        # Find the stats strip close and insert the recently-scored section after it
        stats_close_pattern = r'(</section>\s*)(<!-- recently-scored placeholder -->)?'
        # More targeted: insert after the first </section> after stats-strip
        html = html.replace(
            '<section class="pipeline-section">',
            recently_section + '\n        <section class="pipeline-section">',
            1,
        )

    # Inject fetch script before </body> if not already present
    if 'renderRecentlyScored' not in html:
        html = html.replace('</body>', fetch_script + '\n</body>', 1)

    if html != original:
        index_path.write_text(html, encoding="utf-8")
        return True
    return False


def _recently_scored_section() -> str:
    return """        <section class="recently-scored-section" id="recently-scored">
          <h2 class="section-title">Recently Scored Repos</h2>
          <div id="recently-scored-list" class="recently-scored-list">
            <p class="loading-msg">Loading…</p>
          </div>
        </section>"""


def _fetch_script() -> str:
    return """<script>
(function() {
  function gradeClass(g) {
    return {'A':'grade-a','B':'grade-b','C':'grade-c','D':'grade-d','F':'grade-f'}[g] || '';
  }
  function renderRecentlyScored(data) {
    var el = document.getElementById('recently-scored-list');
    if (!el) return;
    if (!data || !data.repos || !data.repos.length) {
      el.innerHTML = '<p class="loading-msg">No data available.</p>';
      return;
    }
    var top = data.repos.slice(0, 5);
    var html = '<ul class="repo-list">';
    top.forEach(function(r) {
      var src = r.source || 'ecosystem';
      var srcLabel = src === 'community' ? 'community' : src === 'manual' ? 'manual' : 'ecosystem';
      var srcClass = 'source-' + srcLabel;
      html += '<li class="repo-item">'
        + '<a href="' + r.url + '" target="_blank" rel="noopener" class="repo-name">' + r.name + '</a>'
        + '<span class="eco-badge">' + (r.ecosystem || '') + '</span>'
        + '<span class="source-badge ' + srcClass + '">' + srcLabel + '</span>'
        + '<span class="score-val">' + r.score + '</span>'
        + '<span class="grade ' + gradeClass(r.grade) + '">' + r.grade + '</span>'
        + '</li>';
    });
    html += '</ul>';
    if (data.stats) {
      html += '<p class="data-ts">Updated: ' + (data.generated_at ? data.generated_at.slice(0,10) : '') + '</p>';
    }
    el.innerHTML = html;
    // Update repos-scored stat
    var statEl = document.getElementById('repos-scored-stat') || document.querySelector('.stat-num');
    if (statEl && data.stats && data.stats.total) {
      statEl.textContent = data.stats.total;
    }
    // Update community-scored stat
    var communityCount = (data.repos || []).filter(function(r) { return r.source === 'community'; }).length;
    var commEl = document.getElementById('community-scored-stat');
    if (commEl) { commEl.textContent = communityCount; }
    // Update hero badge
    var badge = document.querySelector('.hero-badge');
    if (badge && data.stats && data.stats.total) {
      badge.textContent = badge.textContent.replace(/\\d+ repos scored/, data.stats.total + ' repos scored');
    }
  }
  fetch('/agentkit-cli/data.json')
    .then(function(r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(renderRecentlyScored)
    .catch(function() {
      var el = document.getElementById('recently-scored-list');
      if (el) el.innerHTML = '<p class="loading-msg">Score data unavailable.</p>';
    });
})();
</script>"""


def pages_refresh_command(
    ecosystems: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    docs_dir: Optional[Path] = None,
    token: Optional[str] = None,
    _engine_factory=None,
) -> dict:
    """Run ecosystem scoring and refresh GitHub Pages docs/."""
    from agentkit_cli.leaderboard_page import LeaderboardPageEngine

    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    eco_list = [e.strip().lower() for e in (ecosystems or "python,typescript,rust,go").split(",") if e.strip()]
    docs = docs_dir or DOCS_DIR
    docs.mkdir(parents=True, exist_ok=True)

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

    # Build data.json
    data = build_data_json(result, eco_list)

    data_json_path = docs / "data.json"
    data_json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]✓[/green] Wrote {data_json_path} ({data['stats']['total']} repos)")

    # Write leaderboard.html
    from agentkit_cli.leaderboard_page import render_leaderboard_html
    html = render_leaderboard_html(result)
    leaderboard_path = docs / "leaderboard.html"
    leaderboard_path.write_text(html, encoding="utf-8")
    console.print(f"[green]✓[/green] Wrote {leaderboard_path}")

    # Update index.html
    index_path = docs / "index.html"
    changed = update_index_html(index_path, data)
    if changed:
        console.print(f"[green]✓[/green] Updated {index_path} (repos scored: {data['stats']['total']})")
    else:
        console.print(f"[dim]  {index_path} unchanged[/dim]")

    console.print(f"\n[bold green]Done.[/bold green] {data['stats']['total']} repos scored, top score {data['stats']['top_score']}, median {data['stats']['median']}")
    return data
