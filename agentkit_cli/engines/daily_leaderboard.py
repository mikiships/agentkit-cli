"""agentkit daily leaderboard engine — fetch and score today's trending GitHub repos."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from urllib import error as urllib_error, request as urllib_request
from urllib.request import Request

GITHUB_API_BASE = "https://api.github.com/search/repositories"

# Sample repos used as offline/test fallback
_FALLBACK_REPOS = [
    {
        "full_name": "openai/openai-python",
        "description": "OpenAI Python SDK",
        "stars": 25000,
        "language": "Python",
        "url": "https://github.com/openai/openai-python",
        "composite_score": 88.0,
        "top_finding": "Well-structured SDK with clear API surface",
    },
    {
        "full_name": "anthropics/anthropic-sdk-python",
        "description": "Anthropic Python SDK",
        "stars": 12000,
        "language": "Python",
        "url": "https://github.com/anthropics/anthropic-sdk-python",
        "composite_score": 85.0,
        "top_finding": "Comprehensive documentation and type hints",
    },
    {
        "full_name": "microsoft/autogen",
        "description": "Enable Next-Gen LLM Applications",
        "stars": 30000,
        "language": "Python",
        "url": "https://github.com/microsoft/autogen",
        "composite_score": 91.0,
        "top_finding": "Multi-agent framework with strong tool support",
    },
]


@dataclass
class RankedRepo:
    rank: int
    full_name: str
    description: str
    stars: int
    language: str
    url: str
    composite_score: float
    top_finding: str


@dataclass
class DailyLeaderboard:
    date: date
    repos: list[RankedRepo]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_fetched: int = 0


def _build_query(for_date: date) -> str:
    """Build the GitHub Search API query for repos active since *for_date*."""
    date_str = for_date.strftime("%Y-%m-%d")
    return f"stars:>100 pushed:>{date_str}"


def _build_headers(token: Optional[str] = None) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    resolved = token or os.environ.get("GITHUB_TOKEN")
    if resolved:
        headers["Authorization"] = f"Bearer {resolved}"
    return headers


def _build_url(q: str, per_page: int) -> str:
    from urllib.parse import quote
    q_enc = quote(q, safe="")
    return f"{GITHUB_API_BASE}?q={q_enc}&sort=stars&order=desc&per_page={per_page}"


def _http_get_items(url: str, headers: dict[str, str]) -> list[dict]:
    req = Request(url, headers=headers, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("items", [])
    except urllib_error.HTTPError as e:
        if e.code == 403:
            print("Warning: GitHub API rate limit exceeded. Using fallback data.")
        else:
            print(f"Warning: GitHub API error {e.code}. Using fallback data.")
        return []
    except Exception as e:
        print(f"Warning: network error ({e}). Using fallback data.")
        return []


def _normalize_item(item: dict) -> dict:
    return {
        "full_name": item.get("full_name", ""),
        "description": item.get("description") or "",
        "stars": item.get("stargazers_count", 0),
        "language": item.get("language") or "",
        "url": item.get("html_url") or f"https://github.com/{item.get('full_name', '')}",
    }


def _score_repo(repo: dict) -> tuple[float, str]:
    """Score a repo for agent-readiness. Returns (composite_score, top_finding)."""
    score = 50.0
    finding = "Basic repo structure"

    # Stars signal popularity
    stars = repo.get("stars", 0)
    if stars >= 10000:
        score += 20.0
        finding = "Highly popular repository"
    elif stars >= 1000:
        score += 10.0
        finding = "Strong community traction"

    # Language bonus for Python (most agent SDKs)
    lang = (repo.get("language") or "").lower()
    if lang == "python":
        score += 10.0
        finding = "Python — strong agent ecosystem fit"
    elif lang in ("typescript", "javascript"):
        score += 5.0

    # Description signal
    desc = (repo.get("description") or "").lower()
    agent_keywords = ["agent", "llm", "gpt", "ai", "openai", "anthropic", "langchain"]
    if any(kw in desc for kw in agent_keywords):
        score += 15.0
        finding = "Agent/LLM keyword in description"

    # Cap at 100
    score = min(score, 100.0)
    return score, finding


def fetch_trending_repos(
    for_date: Optional[date] = None,
    limit: int = 20,
    token: Optional[str] = None,
    _fallback: Optional[list[dict]] = None,
) -> DailyLeaderboard:
    """Fetch today's trending repos and score each for agent-readiness.

    Parameters
    ----------
    for_date:
        The date to fetch trending repos for (default: today).
    limit:
        Maximum number of repos to return.
    token:
        GitHub API token (falls back to GITHUB_TOKEN env var).
    _fallback:
        Override the fallback repo list (for testing).

    Returns
    -------
    DailyLeaderboard with scored, ranked repos.
    """
    if for_date is None:
        for_date = date.today()

    # Try GitHub Search API
    q = _build_query(for_date)
    url = _build_url(q, per_page=min(limit, 50))
    headers = _build_headers(token)
    raw_items = _http_get_items(url, headers)

    # Fall back to sample data if API returned nothing
    if not raw_items:
        fallback = _fallback if _fallback is not None else _FALLBACK_REPOS
        repos_raw = fallback[:limit]
        # Fallback items may already be normalized
        normalized = []
        for item in repos_raw:
            if "stars" in item:
                normalized.append(item)
            else:
                normalized.append(_normalize_item(item))
    else:
        normalized = [_normalize_item(item) for item in raw_items][:limit]

    # Score each repo
    scored = []
    for repo in normalized:
        if "composite_score" in repo and "top_finding" in repo:
            # Pre-scored (fallback path)
            composite_score = float(repo["composite_score"])
            top_finding = repo["top_finding"]
        else:
            composite_score, top_finding = _score_repo(repo)
        scored.append({**repo, "composite_score": composite_score, "top_finding": top_finding})

    # Sort by composite_score desc
    scored.sort(key=lambda r: -r["composite_score"])

    ranked = [
        RankedRepo(
            rank=i + 1,
            full_name=r["full_name"],
            description=r["description"],
            stars=r["stars"],
            language=r["language"],
            url=r["url"],
            composite_score=r["composite_score"],
            top_finding=r["top_finding"],
        )
        for i, r in enumerate(scored)
    ]

    return DailyLeaderboard(
        date=for_date,
        repos=ranked,
        generated_at=datetime.now(timezone.utc),
        total_fetched=len(raw_items),
    )
