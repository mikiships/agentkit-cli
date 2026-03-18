"""agentkit search — discover GitHub repos missing AI context files."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional


GITHUB_API_BASE = "https://api.github.com"
_SLEEP_BETWEEN_CHECKS = 0.4  # seconds between Contents API calls (rate limit)


@dataclass
class SearchResult:
    """A single repository result from GitHub search."""

    owner: str
    repo: str
    url: str
    stars: int
    language: Optional[str]
    description: Optional[str]
    has_claude_md: bool = False
    has_agents_md: bool = False
    score: float = 0.0

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def missing_context(self) -> bool:
        """True when neither CLAUDE.md nor AGENTS.md exists."""
        return not self.has_claude_md and not self.has_agents_md

    def to_dict(self) -> dict:
        return {
            "repo": self.full_name,
            "url": self.url,
            "stars": self.stars,
            "language": self.language,
            "description": self.description,
            "has_claude_md": self.has_claude_md,
            "has_agents_md": self.has_agents_md,
            "missing_context": self.missing_context,
            "score": round(self.score, 3),
        }


class SearchEngine:
    """Discover GitHub repos and check for AI context files."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        *,
        language: Optional[str] = None,
        topic: Optional[str] = None,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        limit: int = 20,
        check_contents: bool = True,
        missing_only: bool = False,
    ) -> List[SearchResult]:
        """Search GitHub repos and optionally check for context files.

        Args:
            query: Free-text search query.
            language: Filter by programming language (e.g. "python").
            topic: Filter by GitHub topic (e.g. "ai-agents").
            min_stars: Minimum star count.
            max_stars: Maximum star count.
            limit: Maximum results to return.
            check_contents: If True, check each repo for CLAUDE.md/AGENTS.md.
            missing_only: If True, return only repos without any context file.

        Returns:
            List of SearchResult objects sorted by stars descending.
        """
        q = self._build_query(query, language=language, topic=topic,
                               min_stars=min_stars, max_stars=max_stars)
        raw = self._search_repos(q, limit=limit)
        results = [self._parse_item(item) for item in raw]

        if check_contents:
            for result in results:
                self._check_context_files(result)
                time.sleep(_SLEEP_BETWEEN_CHECKS)

        if missing_only:
            results = [r for r in results if r.missing_context]

        # Score: prioritise repos that are missing context + have more stars
        for r in results:
            r.score = self._compute_score(r)

        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def check_repo(self, owner: str, repo: str) -> SearchResult:
        """Fetch a single repo and check its context files."""
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        data = self._github_request(url)
        result = self._parse_item(data)
        self._check_context_files(result)
        result.score = self._compute_score(result)
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _build_query(
        query: str,
        *,
        language: Optional[str],
        topic: Optional[str],
        min_stars: Optional[int],
        max_stars: Optional[int],
    ) -> str:
        parts = [query] if query else []
        if language:
            parts.append(f"language:{language}")
        if topic:
            parts.append(f"topic:{topic}")
        if min_stars is not None and max_stars is not None:
            parts.append(f"stars:{min_stars}..{max_stars}")
        elif min_stars is not None:
            parts.append(f"stars:>={min_stars}")
        elif max_stars is not None:
            parts.append(f"stars:<={max_stars}")
        return " ".join(parts) if parts else "stars:>=10"

    def _search_repos(self, q: str, limit: int) -> list:
        per_page = min(limit, 100)
        url = (
            f"{GITHUB_API_BASE}/search/repositories"
            f"?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page={per_page}"
        )
        data = self._github_request(url)
        items = data.get("items", [])
        return items[:limit]

    @staticmethod
    def _parse_item(item: dict) -> SearchResult:
        owner_info = item.get("owner") or {}
        owner = owner_info.get("login") or item.get("full_name", "/").split("/")[0]
        repo = item.get("name") or item.get("full_name", "").split("/")[-1]
        return SearchResult(
            owner=owner,
            repo=repo,
            url=item.get("html_url", f"https://github.com/{owner}/{repo}"),
            stars=item.get("stargazers_count", 0),
            language=item.get("language"),
            description=item.get("description"),
        )

    def _check_context_files(self, result: SearchResult) -> None:
        """Populate has_claude_md / has_agents_md in place."""
        result.has_claude_md = self._file_exists(result.owner, result.repo, "CLAUDE.md")
        result.has_agents_md = self._file_exists(result.owner, result.repo, "AGENTS.md")

    def _file_exists(self, owner: str, repo: str, filename: str) -> bool:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{filename}"
        try:
            self._github_request(url)
            return True
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            raise
        except Exception:
            return False

    def _github_request(self, url: str) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "agentkit-cli",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    @staticmethod
    def _compute_score(result: SearchResult) -> float:
        """Score 0-1. Missing context + more stars = higher priority."""
        star_score = min(result.stars / 10_000, 1.0)
        context_bonus = 0.5 if result.missing_context else 0.0
        return round(star_score * 0.5 + context_bonus, 3)


# ---------------------------------------------------------------------------
# Lazy import fix for urllib.parse used in _search_repos
# ---------------------------------------------------------------------------
import urllib.parse  # noqa: E402  (stdlib, safe)
