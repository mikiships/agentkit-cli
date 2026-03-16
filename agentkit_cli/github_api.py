"""GitHub REST API client for agentkit org command."""
from __future__ import annotations

import json
import os
import time
from typing import Optional
from urllib import error as urllib_error, request as urllib_request
from urllib.request import Request

GITHUB_API_BASE = "https://api.github.com"


def _build_headers(token: Optional[str] = None) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    resolved = token or os.environ.get("GITHUB_TOKEN")
    if resolved:
        headers["Authorization"] = f"Bearer {resolved}"
    return headers


def _check_rate_limit(headers: dict) -> None:
    """Sleep if remaining rate-limit calls are near zero."""
    remaining = headers.get("X-RateLimit-Remaining")
    reset = headers.get("X-RateLimit-Reset")
    if remaining is not None:
        try:
            if int(remaining) < 5 and reset is not None:
                wait = int(reset) - int(time.time()) + 1
                if wait > 0:
                    time.sleep(min(wait, 60))
        except (ValueError, TypeError):
            pass


def _fetch_page(url: str, token: Optional[str] = None) -> tuple[list[dict], dict, Optional[str]]:
    """Fetch one page of results. Returns (items, response_headers, next_url)."""
    headers = _build_headers(token)
    req = Request(url, headers=headers, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=15) as resp:
            resp_headers = dict(resp.headers)
            _check_rate_limit(resp_headers)
            data = json.loads(resp.read().decode("utf-8"))
            # Parse Link header for next page
            next_url: Optional[str] = None
            link_header = resp_headers.get("Link", "")
            if link_header:
                for part in link_header.split(","):
                    part = part.strip()
                    if 'rel="next"' in part:
                        url_part = part.split(";")[0].strip()
                        next_url = url_part.strip("<>")
                        break
            return data if isinstance(data, list) else [], resp_headers, next_url
    except urllib_error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Owner not found: {url}")
        if e.code in (403, 429):
            retry_after = e.headers.get("Retry-After", "60")
            try:
                time.sleep(int(retry_after))
            except (ValueError, TypeError):
                time.sleep(60)
            return [], {}, None
        raise
    except urllib_error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}") from e


def list_repos(
    owner: str,
    include_forks: bool = False,
    include_archived: bool = False,
    token: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """List all public repos for a GitHub org or user.

    Tries org endpoint first, falls back to user endpoint on 404.
    Returns list of repo dicts with keys: full_name, name, description,
    stars, language, url, fork, archived, size.
    """
    # Try org first, fall back to user
    base_url: Optional[str] = None
    for endpoint in [
        f"{GITHUB_API_BASE}/orgs/{owner}/repos",
        f"{GITHUB_API_BASE}/users/{owner}/repos",
    ]:
        try:
            url = f"{endpoint}?type=public&per_page=100&sort=updated"
            items, _, _ = _fetch_page(url, token)
            base_url = endpoint
            break
        except ValueError:
            continue

    if base_url is None:
        raise ValueError(f"Owner '{owner}' not found as org or user on GitHub")

    # Paginate all results
    all_repos: list[dict] = []
    url = f"{base_url}?type=public&per_page=100&sort=updated"
    while url:
        items, _, next_url = _fetch_page(url, token)
        all_repos.extend(items)
        url = next_url  # type: ignore[assignment]
        if limit and len(all_repos) >= limit:
            break

    # Normalize and filter
    result: list[dict] = []
    for repo in all_repos:
        if not include_forks and repo.get("fork", False):
            continue
        if not include_archived and repo.get("archived", False):
            continue
        if repo.get("size", 0) == 0:
            continue  # empty repo
        result.append({
            "full_name": repo.get("full_name", ""),
            "name": repo.get("name", ""),
            "description": repo.get("description") or "",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language") or "",
            "url": repo.get("html_url", ""),
            "fork": repo.get("fork", False),
            "archived": repo.get("archived", False),
            "size": repo.get("size", 0),
        })
        if limit and len(result) >= limit:
            break

    return result
