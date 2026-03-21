"""agentkit leaderboard-page — generate a public HTML leaderboard of top agent-ready GitHub repos by ecosystem."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    import requests as _requests_module
except ImportError:
    _requests_module = None  # type: ignore

from agentkit_cli.existing_scorer import ExistingStateScorer
from agentkit_cli.github_api import GITHUB_API_BASE, _fetch_page
from agentkit_cli.user_scorecard import score_to_grade

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ECOSYSTEMS = ["python", "typescript", "rust", "go", "javascript"]

ECOSYSTEM_LANGUAGE_MAP: Dict[str, str] = {
    "python": "Python",
    "typescript": "TypeScript",
    "rust": "Rust",
    "go": "Go",
    "javascript": "JavaScript",
}

_FALLBACK_REPOS: Dict[str, List[dict]] = {
    "python": [
        {"full_name": "langchain-ai/langchain", "description": "LLM app framework", "stars": 90000, "language": "Python"},
        {"full_name": "fastapi/fastapi", "description": "Fast web framework", "stars": 75000, "language": "Python"},
        {"full_name": "django/django", "description": "Web framework", "stars": 78000, "language": "Python"},
        {"full_name": "psf/requests", "description": "HTTP for Humans", "stars": 51000, "language": "Python"},
        {"full_name": "pallets/flask", "description": "WSGI framework", "stars": 67000, "language": "Python"},
        {"full_name": "openai/openai-python", "description": "OpenAI Python SDK", "stars": 20000, "language": "Python"},
        {"full_name": "huggingface/transformers", "description": "ML models", "stars": 130000, "language": "Python"},
        {"full_name": "pydantic/pydantic", "description": "Data validation", "stars": 20000, "language": "Python"},
        {"full_name": "tiangolo/sqlmodel", "description": "SQL databases with Python", "stars": 13000, "language": "Python"},
        {"full_name": "encode/httpx", "description": "Async HTTP client", "stars": 13000, "language": "Python"},
    ],
    "typescript": [
        {"full_name": "vercel/next.js", "description": "React framework", "stars": 120000, "language": "TypeScript"},
        {"full_name": "microsoft/vscode", "description": "Code editor", "stars": 160000, "language": "TypeScript"},
        {"full_name": "nestjs/nest", "description": "Node.js framework", "stars": 65000, "language": "TypeScript"},
        {"full_name": "supabase/supabase", "description": "Firebase alternative", "stars": 70000, "language": "TypeScript"},
        {"full_name": "trpc/trpc", "description": "End-to-end typesafe APIs", "stars": 34000, "language": "TypeScript"},
        {"full_name": "prisma/prisma", "description": "Next-gen ORM", "stars": 38000, "language": "TypeScript"},
        {"full_name": "colinhacks/zod", "description": "TypeScript schema validation", "stars": 32000, "language": "TypeScript"},
        {"full_name": "vitejs/vite", "description": "Build tool", "stars": 67000, "language": "TypeScript"},
        {"full_name": "tailwindlabs/tailwindcss", "description": "Utility-first CSS", "stars": 80000, "language": "TypeScript"},
        {"full_name": "tanstack/query", "description": "Data fetching", "stars": 39000, "language": "TypeScript"},
    ],
    "rust": [
        {"full_name": "rust-lang/rust", "description": "Rust language", "stars": 95000, "language": "Rust"},
        {"full_name": "tokio-rs/tokio", "description": "Async runtime", "stars": 26000, "language": "Rust"},
        {"full_name": "actix/actix-web", "description": "Web framework", "stars": 21000, "language": "Rust"},
        {"full_name": "serde-rs/serde", "description": "Serialization framework", "stars": 9000, "language": "Rust"},
        {"full_name": "hyperium/hyper", "description": "HTTP library", "stars": 14000, "language": "Rust"},
        {"full_name": "clap-rs/clap", "description": "CLI arg parser", "stars": 13000, "language": "Rust"},
        {"full_name": "rayon-rs/rayon", "description": "Data parallelism", "stars": 10000, "language": "Rust"},
        {"full_name": "diesel-rs/diesel", "description": "ORM and query builder", "stars": 12000, "language": "Rust"},
        {"full_name": "BurntSushi/ripgrep", "description": "Fast grep tool", "stars": 46000, "language": "Rust"},
        {"full_name": "ogham/exa", "description": "ls replacement", "stars": 22000, "language": "Rust"},
    ],
    "go": [
        {"full_name": "golang/go", "description": "Go language", "stars": 120000, "language": "Go"},
        {"full_name": "gin-gonic/gin", "description": "HTTP web framework", "stars": 77000, "language": "Go"},
        {"full_name": "gofiber/fiber", "description": "Web framework", "stars": 33000, "language": "Go"},
        {"full_name": "spf13/cobra", "description": "CLI library", "stars": 36000, "language": "Go"},
        {"full_name": "kubernetes/kubernetes", "description": "Container orchestration", "stars": 108000, "language": "Go"},
        {"full_name": "docker/compose", "description": "Docker Compose", "stars": 33000, "language": "Go"},
        {"full_name": "hashicorp/terraform", "description": "Infrastructure as code", "stars": 42000, "language": "Go"},
        {"full_name": "grafana/grafana", "description": "Observability platform", "stars": 62000, "language": "Go"},
        {"full_name": "cli/cli", "description": "GitHub CLI", "stars": 36000, "language": "Go"},
        {"full_name": "prometheus/prometheus", "description": "Monitoring system", "stars": 55000, "language": "Go"},
    ],
    "javascript": [
        {"full_name": "facebook/react", "description": "UI library", "stars": 220000, "language": "JavaScript"},
        {"full_name": "vuejs/vue", "description": "Progressive JS framework", "stars": 207000, "language": "JavaScript"},
        {"full_name": "expressjs/express", "description": "Web framework", "stars": 64000, "language": "JavaScript"},
        {"full_name": "axios/axios", "description": "HTTP client", "stars": 104000, "language": "JavaScript"},
        {"full_name": "lodash/lodash", "description": "Utility library", "stars": 58000, "language": "JavaScript"},
        {"full_name": "webpack/webpack", "description": "Module bundler", "stars": 64000, "language": "JavaScript"},
        {"full_name": "chartjs/Chart.js", "description": "Charts", "stars": 63000, "language": "JavaScript"},
        {"full_name": "moment/moment", "description": "Date library", "stars": 47000, "language": "JavaScript"},
        {"full_name": "jquery/jquery", "description": "DOM manipulation", "stars": 59000, "language": "JavaScript"},
        {"full_name": "nodejs/node", "description": "Node.js runtime", "stars": 107000, "language": "JavaScript"},
    ],
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class LeaderboardEntry:
    rank: int
    repo_full_name: str
    score: float
    grade: str
    stars: int = 0
    description: str = ""
    ecosystem: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EcosystemLeaderboard:
    ecosystem: str
    entries: List[LeaderboardEntry]
    total_analyzed: int = 0

    def to_dict(self) -> dict:
        return {
            "ecosystem": self.ecosystem,
            "entries": [e.to_dict() for e in self.entries],
            "total_analyzed": self.total_analyzed,
        }


@dataclass
class LeaderboardPageResult:
    ecosystems: List[EcosystemLeaderboard]
    generated_at: str = ""
    embed_markdown: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ecosystems": [e.to_dict() for e in self.ecosystems],
            "generated_at": self.generated_at,
            "embed_markdown": self.embed_markdown,
        }


# ---------------------------------------------------------------------------
# GitHub search
# ---------------------------------------------------------------------------

def search_ecosystem_repos(
    ecosystem: str,
    limit: int = 10,
    token: Optional[str] = None,
) -> List[dict]:
    """Search GitHub for top agent-ready repos in an ecosystem."""
    language = ECOSYSTEM_LANGUAGE_MAP.get(ecosystem, ecosystem)
    query = f"language:{language} stars:>100 topic:agent-ready"
    per_page = min(limit, 25)
    url = (
        f"{GITHUB_API_BASE}/search/repositories"
        f"?q={query}&sort=stars&order=desc&per_page={per_page}"
    )
    try:
        data, _, _ = _fetch_page(url, token)
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = []
        if items:
            return items[:limit]
    except Exception:
        pass

    # Fallback to language-only search
    query2 = f"language:{language} stars:>1000"
    url2 = (
        f"{GITHUB_API_BASE}/search/repositories"
        f"?q={query2}&sort=stars&order=desc&per_page={per_page}"
    )
    try:
        data, _, _ = _fetch_page(url2, token)
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = []
        return items[:limit]
    except Exception:
        pass

    return _FALLBACK_REPOS.get(ecosystem, [])[:limit]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_repo_heuristic(repo: dict) -> float:
    """Heuristic score for a repo without cloning."""
    score = 0.0
    stars = repo.get("stargazers_count") or repo.get("stars") or 0
    if stars > 50000:
        score += 25.0
    elif stars > 10000:
        score += 20.0
    elif stars > 1000:
        score += 15.0
    elif stars > 100:
        score += 10.0

    topics = repo.get("topics") or []
    agent_topics = {"agent-ready", "llm", "ai", "claude", "openai", "langchain", "agents"}
    for t in topics:
        if t in agent_topics:
            score += 5.0
    score = min(score, 20.0)  # cap topic bonus

    desc = repo.get("description") or ""
    if len(desc) > 30:
        score += 10.0

    if repo.get("has_wiki"):
        score += 5.0
    if repo.get("has_issues"):
        score += 5.0

    # Base score for being a known repo
    score += 30.0
    return min(100.0, round(score, 2))


def score_repo_for_leaderboard(
    repo: dict,
    token: Optional[str] = None,
    timeout: int = 30,
) -> float:
    """Score a repo for the leaderboard. Uses clone+ExistingStateScorer when possible."""
    try:
        requests = _requests_module
        if requests is None:
            raise ImportError("requests not available")
        full_name = repo.get("full_name", "")
        if not full_name:
            return _score_repo_heuristic(repo)
        tmpdir = tempfile.mkdtemp(prefix="agentkit_lb_")
        try:
            import subprocess
            clone_url = f"https://github.com/{full_name}.git"
            result = subprocess.run(
                ["git", "clone", "--depth=1", "--quiet", clone_url, tmpdir],
                capture_output=True, timeout=timeout,
            )
            if result.returncode != 0:
                return _score_repo_heuristic(repo)
            scorer = ExistingStateScorer(Path(tmpdir))
            scores = scorer.score_all()
            return scores["composite"]
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        return _score_repo_heuristic(repo)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class LeaderboardPageEngine:
    """Generate an ecosystem leaderboard page."""

    def __init__(
        self,
        ecosystems: Optional[List[str]] = None,
        limit: int = 10,
        token: Optional[str] = None,
        timeout: int = 30,
        _repos_override: Optional[Dict[str, List[dict]]] = None,
        _score_fn: Optional[Callable[[dict, Optional[str], int], float]] = None,
    ) -> None:
        self.ecosystems = [e.lower() for e in (ecosystems or ECOSYSTEMS)]
        self.limit = min(max(1, limit), 25)
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._repos_override = _repos_override or {}
        self._score_fn = _score_fn

    def _get_repos(self, ecosystem: str) -> List[dict]:
        if ecosystem in self._repos_override:
            return self._repos_override[ecosystem][: self.limit]
        return search_ecosystem_repos(ecosystem, limit=self.limit, token=self.token)

    def _score(self, repo: dict) -> float:
        if self._score_fn is not None:
            return self._score_fn(repo, self.token, self.timeout)
        return score_repo_for_leaderboard(repo, self.token, self.timeout)

    def run(self) -> LeaderboardPageResult:
        eco_results: List[EcosystemLeaderboard] = []
        for ecosystem in self.ecosystems:
            repos = self._get_repos(ecosystem)
            scored: List[tuple[dict, float]] = []
            for repo in repos:
                score = self._score(repo)
                scored.append((repo, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            entries: List[LeaderboardEntry] = []
            for rank, (repo, score) in enumerate(scored[: self.limit], 1):
                entries.append(LeaderboardEntry(
                    rank=rank,
                    repo_full_name=repo.get("full_name", ""),
                    score=round(score, 2),
                    grade=score_to_grade(score),
                    stars=repo.get("stargazers_count") or repo.get("stars") or 0,
                    description=repo.get("description") or "",
                    ecosystem=ecosystem,
                ))
            eco_results.append(EcosystemLeaderboard(
                ecosystem=ecosystem,
                entries=entries,
                total_analyzed=len(repos),
            ))
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return LeaderboardPageResult(ecosystems=eco_results, generated_at=now)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def render_leaderboard_html(result: LeaderboardPageResult) -> str:
    """Render the leaderboard as a dark-theme HTML page with SEO and JSON-LD."""
    ecosystems = result.ecosystems
    first_eco = ecosystems[0].ecosystem if ecosystems else "python"
    generated_at = result.generated_at

    # Build JSON-LD ItemList for first ecosystem (SEO)
    jsonld_items = []
    if ecosystems:
        for eco in ecosystems:
            for entry in eco.entries:
                jsonld_items.append({
                    "@type": "ListItem",
                    "position": entry.rank,
                    "name": entry.repo_full_name,
                    "url": f"https://github.com/{entry.repo_full_name}",
                    "description": entry.description,
                })
    jsonld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Top Agent-Ready GitHub Repositories",
        "description": "Ranked leaderboard of top agent-ready GitHub repos by ecosystem, powered by agentkit-cli.",
        "url": "https://agentkit.dev/leaderboard",
        "itemListElement": jsonld_items,
    }

    # Tab buttons
    tab_buttons = "\n".join(
        f'<button class="tab-btn" onclick="showTab(\'{eco.ecosystem}\')" id="btn-{eco.ecosystem}">'
        f'{eco.ecosystem.capitalize()}</button>'
        for eco in ecosystems
    )

    # Tab panels
    tab_panels = ""
    for eco in ecosystems:
        rows = ""
        for e in eco.entries:
            grade_class = {"A": "grade-a", "B": "grade-b", "C": "grade-c", "D": "grade-d", "F": "grade-f"}.get(e.grade, "")
            stars_str = f"{e.stars:,}" if e.stars else "—"
            desc = e.description[:80] + "…" if len(e.description) > 80 else e.description
            rows += (
                f"<tr>"
                f"<td>{e.rank}</td>"
                f'<td><a href="https://github.com/{e.repo_full_name}" target="_blank">{e.repo_full_name}</a></td>'
                f"<td>{desc}</td>"
                f'<td><span class="score">{e.score:.0f}</span></td>'
                f'<td><span class="grade {grade_class}">{e.grade}</span></td>'
                f"<td>⭐ {stars_str}</td>"
                f"</tr>\n"
            )
        tab_panels += f"""
<div class="tab-panel" id="panel-{eco.ecosystem}">
  <h2>{eco.ecosystem.capitalize()} — Top Agent-Ready Repos</h2>
  <table>
    <thead><tr><th>#</th><th>Repository</th><th>Description</th><th>Score</th><th>Grade</th><th>Stars</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Top Agent-Ready {first_eco.capitalize()} GitHub Repos | agentkit Leaderboard</title>
  <meta name="description" content="Ranked leaderboard of the most agent-ready GitHub repositories for {first_eco}, python, typescript, rust, go, and javascript ecosystems. Powered by agentkit-cli.">
  <meta property="og:title" content="Top Agent-Ready GitHub Repos | agentkit Leaderboard">
  <meta property="og:description" content="Discover and rank the most agent-ready open source repositories by ecosystem. Powered by agentkit-cli.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://agentkit.dev/leaderboard">
  <meta property="og:image" content="https://agentkit.dev/og-leaderboard.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Top Agent-Ready GitHub Repos | agentkit Leaderboard">
  <meta name="twitter:description" content="Discover and rank the most agent-ready open source repositories by ecosystem.">
  <script type="application/ld+json">
{json.dumps(jsonld, indent=2)}
  </script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    header {{ padding: 2rem; border-bottom: 1px solid #21262d; }}
    header h1 {{ font-size: 1.8rem; color: #58a6ff; }}
    header p {{ color: #8b949e; margin-top: 0.5rem; }}
    .tabs {{ display: flex; gap: 0.5rem; padding: 1rem 2rem; border-bottom: 1px solid #21262d; flex-wrap: wrap; }}
    .tab-btn {{
      background: #161b22; border: 1px solid #30363d; color: #c9d1d9;
      padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.9rem;
    }}
    .tab-btn:hover, .tab-btn.active {{ background: #1f6feb; border-color: #1f6feb; color: #fff; }}
    .tab-panel {{ display: none; padding: 2rem; }}
    .tab-panel.active {{ display: block; }}
    .tab-panel h2 {{ margin-bottom: 1rem; color: #f0f6fc; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.6rem 1rem; text-align: left; border-bottom: 1px solid #21262d; }}
    th {{ color: #8b949e; font-size: 0.85rem; text-transform: uppercase; }}
    tr:hover {{ background: #161b22; }}
    a {{ color: #58a6ff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .score {{ font-weight: bold; color: #f0f6fc; }}
    .grade {{ display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px; font-weight: bold; font-size: 0.9rem; }}
    .grade-a {{ background: #1a7f37; color: #fff; }}
    .grade-b {{ background: #1158c7; color: #fff; }}
    .grade-c {{ background: #9a6700; color: #fff; }}
    .grade-d {{ background: #b62324; color: #fff; }}
    .grade-f {{ background: #6e0a0a; color: #fff; }}
    footer {{ padding: 1.5rem 2rem; border-top: 1px solid #21262d; color: #8b949e; font-size: 0.85rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; }}
    .badge {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 0.3rem 0.8rem; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <header>
    <h1>🤖 agentkit Leaderboard</h1>
    <p>Top agent-ready GitHub repositories by ecosystem, ranked by documentation quality.</p>
  </header>
  <div class="tabs">
    {tab_buttons}
  </div>
  {tab_panels}
  <footer>
    <span>Last updated: {generated_at}</span>
    <span class="badge">Powered by <a href="https://github.com/agentkit-dev/agentkit-cli">agentkit-cli</a></span>
  </footer>
  <script>
    function showTab(eco) {{
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      var panel = document.getElementById('panel-' + eco);
      var btn = document.getElementById('btn-' + eco);
      if (panel) panel.classList.add('active');
      if (btn) btn.classList.add('active');
    }}
    // Init first tab
    showTab('{first_eco}');
  </script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Embed badge
# ---------------------------------------------------------------------------

def render_embed_badge(
    repo_full_name: str,
    rank: Optional[int] = None,
    score: Optional[float] = None,
    ecosystem: Optional[str] = None,
) -> str:
    """Render a markdown badge snippet for a repo."""
    label = "agentkit"
    message = "agent-ready"
    if rank is not None and score is not None:
        message = f"#{rank} | {score:.0f}pts"
    elif score is not None:
        message = f"{score:.0f}pts"
    elif rank is not None:
        message = f"rank #{rank}"

    eco_str = ecosystem or "python"
    encoded_label = label.replace("-", "--").replace("_", "__")
    encoded_message = message.replace("-", "--").replace("_", "__").replace(" ", "_")
    badge_url = f"https://img.shields.io/badge/{encoded_label}-{encoded_message}-blue?style=flat-square&logo=github"
    leaderboard_url = f"https://agentkit.dev/leaderboard#{eco_str}"
    return (
        f"[![agentkit leaderboard]({badge_url})]({leaderboard_url})\n"
        f"<!-- agentkit leaderboard: {repo_full_name} | rank={rank} | score={score} | ecosystem={eco_str} -->"
    )
