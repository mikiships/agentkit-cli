"""Fetch trending / popular GitHub repositories via the GitHub Search API."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib import error as urllib_error, request as urllib_request
from urllib.request import Request

GITHUB_API_BASE = "https://api.github.com/search/repositories"

PERIOD_DAYS: dict[str, int] = {
    "day": 1,
    "week": 7,
    "month": 30,
}

CATEGORY_QUERIES: dict[str, str] = {
    "ai": "topic:ai-agent OR topic:llm OR topic:agent",
    "python": "language:python",
    "all": "stars:>100",
}


def _date_cutoff(days: int) -> str:
    """Return an ISO date string *days* ago (YYYY-MM-DD)."""
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.strftime("%Y-%m-%d")


def _build_headers(token: Optional[str] = None) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    resolved = token or os.environ.get("GITHUB_TOKEN")
    if resolved:
        headers["Authorization"] = f"Bearer {resolved}"
    return headers


def _make_url(q: str, per_page: int) -> str:
    from urllib.parse import urlencode, quote

    params = {"q": q, "sort": "stars", "order": "desc", "per_page": str(per_page)}
    encoded = "&".join(f"{k}={urllib_request.quote(v, safe='')}" for k, v in params.items())
    return f"{GITHUB_API_BASE}?{encoded}"


def _fetch(url: str, headers: dict[str, str]) -> list[dict]:
    """Make a GET request and return the items list, or [] on rate-limit / error."""
    req = Request(url, headers=headers, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("items", [])
    except urllib_error.HTTPError as e:
        if e.code == 403:
            print("Warning: GitHub API rate limit exceeded. Returning empty results.")
        else:
            print(f"Warning: GitHub API error {e.code}. Returning empty results.")
        return []
    except urllib_error.URLError as e:
        print(f"Warning: Network error fetching GitHub data: {e.reason}. Returning empty results.")
        return []


def _normalize(items: list[dict]) -> list[dict]:
    """Convert raw GitHub Search items to our standard schema."""
    out = []
    for item in items:
        out.append({
            "full_name": item.get("full_name", ""),
            "description": item.get("description") or "",
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language") or "",
            "url": item.get("html_url", ""),
        })
    return out


def fetch_trending(
    period: str = "week",
    topic: Optional[str] = None,
    limit: int = 10,
    token: Optional[str] = None,
) -> list[dict]:
    """Fetch trending GitHub repos created within *period* (day/week/month).

    Parameters
    ----------
    period:
        Time window — "day", "week", or "month".
    topic:
        Optional GitHub topic filter (e.g. "ai-agent").
    limit:
        Maximum number of repos to return (capped at 25 by the caller).
    token:
        GitHub personal access token for higher rate limits.

    Returns
    -------
    list[dict] with keys: full_name, description, stars, language, url
    """
    if period not in PERIOD_DAYS:
        raise ValueError(f"period must be one of {list(PERIOD_DAYS)}; got {period!r}")

    days = PERIOD_DAYS[period]
    cutoff = _date_cutoff(days)
    q = f"created:>{cutoff}"
    if topic:
        q += f" topic:{topic}"

    per_page = min(limit, 25)
    url = _make_url(q, per_page)
    items = _fetch(url, _build_headers(token))
    return _normalize(items)[:limit]


def fetch_popular(
    category: str = "ai",
    limit: int = 10,
    token: Optional[str] = None,
) -> list[dict]:
    """Fetch popular GitHub repos matching a preset *category*.

    Parameters
    ----------
    category:
        One of "ai", "python", "all".
    limit:
        Maximum number of repos to return.
    token:
        GitHub personal access token.

    Returns
    -------
    list[dict] with keys: full_name, description, stars, language, url
    """
    if category not in CATEGORY_QUERIES:
        raise ValueError(f"category must be one of {list(CATEGORY_QUERIES)}; got {category!r}")

    q = CATEGORY_QUERIES[category]
    per_page = min(limit, 25)
    url = _make_url(q, per_page)
    items = _fetch(url, _build_headers(token))
    return _normalize(items)[:limit]
