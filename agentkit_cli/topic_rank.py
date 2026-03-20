"""agentkit topic-rank engine — discover top GitHub repos for a topic and rank by agent-readiness."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from agentkit_cli.github_api import GITHUB_API_BASE, _fetch_page
from agentkit_cli.user_scorecard import score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TopicRankEntry:
    """A single ranked repo entry."""
    rank: int
    repo_full_name: str
    score: float
    grade: str
    stars: int = 0
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "repo_full_name": self.repo_full_name,
            "score": self.score,
            "grade": self.grade,
            "stars": self.stars,
            "description": self.description,
        }


@dataclass
class TopicRankResult:
    """Full result of a topic-rank analysis for a GitHub topic."""
    topic: str
    entries: List[TopicRankEntry]
    generated_at: str = ""
    total_analyzed: int = 0

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "entries": [e.to_dict() for e in self.entries],
            "generated_at": self.generated_at,
            "total_analyzed": self.total_analyzed,
        }


# ---------------------------------------------------------------------------
# GitHub topic repo search
# ---------------------------------------------------------------------------


def search_topic_repos(
    topic: str,
    limit: int = 25,
    language: Optional[str] = None,
    token: Optional[str] = None,
) -> List[dict]:
    """Search GitHub for repos matching the given topic.

    Returns list of raw repo dicts (up to limit), sorted by stars descending.
    """
    query = f"topic:{topic}"
    if language:
        query += f" language:{language}"

    per_page = min(limit, 25)
    search_url = (
        f"{GITHUB_API_BASE}/search/repositories"
        f"?q={query}&sort=stars&order=desc&per_page={per_page}"
    )

    try:
        data, _, _ = _fetch_page(search_url, token)
    except Exception:
        return []

    # _fetch_page returns list for non-search, dict for search endpoint
    if isinstance(data, dict):
        repos = data.get("items", [])
    elif isinstance(data, list):
        repos = data
    else:
        repos = []

    return repos[:limit]


# ---------------------------------------------------------------------------
# Score a single repo
# ---------------------------------------------------------------------------


def _score_repo(repo: dict, token: Optional[str], timeout: int) -> float:
    """Score a single repo using agentkit analyze pipeline.

    Falls back to heuristic score if full analysis fails.
    """
    full_name = repo.get("full_name", "")
    if not full_name:
        return 0.0

    try:
        from agentkit_cli.analyze import analyze_target
        result = analyze_target(
            target=f"github:{full_name}",
            keep=False,
            publish=False,
            timeout=timeout,
            no_generate=True,
        )
        if result.composite_score is not None:
            return float(result.composite_score)
    except Exception:
        pass

    # Heuristic fallback — score based on available metadata
    return _heuristic_score(repo)


def _heuristic_score(repo: dict) -> float:
    """Simple heuristic score from repo metadata when full analysis unavailable."""
    score = 30.0

    # Has description
    if repo.get("description"):
        score += 5.0

    # Stars signal
    stars = repo.get("stargazers_count", 0) or 0
    if stars >= 1000:
        score += 15.0
    elif stars >= 100:
        score += 10.0
    elif stars >= 10:
        score += 5.0

    # Recent activity
    if repo.get("pushed_at"):
        score += 5.0

    # License present
    if repo.get("license"):
        score += 5.0

    # Has wiki / homepage
    if repo.get("has_wiki"):
        score += 3.0
    if repo.get("homepage"):
        score += 5.0

    # Not archived
    if not repo.get("archived", False):
        score += 5.0

    # Topics
    topics = repo.get("topics", []) or []
    if topics:
        score += min(len(topics) * 1.0, 5.0)

    return min(score, 100.0)


# ---------------------------------------------------------------------------
# TopicRankEngine
# ---------------------------------------------------------------------------


class TopicRankEngine:
    """Discover top GitHub repos for a topic and rank by agent-readiness."""

    def __init__(
        self,
        topic: str,
        limit: int = 10,
        language: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 60,
        _repos_override: Optional[List[dict]] = None,
        _score_fn: Optional[Callable[[dict, Optional[str], int], float]] = None,
    ) -> None:
        self.topic = topic
        self.limit = min(limit, 25)
        self.language = language
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._repos_override = _repos_override
        self._score_fn = _score_fn  # callable(repo_dict, token, timeout) -> float

    def fetch_repos(self) -> List[dict]:
        """Fetch repos for the topic."""
        if self._repos_override is not None:
            return self._repos_override[: self.limit]
        return search_topic_repos(
            self.topic,
            limit=self.limit,
            language=self.language,
            token=self.token,
        )

    def score_repo(self, repo: dict) -> float:
        """Score a single repo."""
        if self._score_fn is not None:
            return self._score_fn(repo, self.token, self.timeout)
        return _score_repo(repo, self.token, self.timeout)

    def rank_repos(self, repo_scores: List[tuple[dict, float]]) -> List[TopicRankEntry]:
        """Sort by score descending and produce ranked entries."""
        sorted_items = sorted(repo_scores, key=lambda x: x[1], reverse=True)
        entries: List[TopicRankEntry] = []
        for rank, (repo, score) in enumerate(sorted_items, 1):
            grade = score_to_grade(score)
            desc = repo.get("description") or ""
            entries.append(
                TopicRankEntry(
                    rank=rank,
                    repo_full_name=repo.get("full_name", ""),
                    score=round(score, 2),
                    grade=grade,
                    stars=repo.get("stargazers_count", 0) or 0,
                    description=desc,
                )
            )
        return entries

    def build_result(self, entries: List[TopicRankEntry], total_analyzed: int) -> TopicRankResult:
        """Wrap entries in a TopicRankResult."""
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return TopicRankResult(
            topic=self.topic,
            entries=entries,
            generated_at=generated_at,
            total_analyzed=total_analyzed,
        )

    def run(self, progress_cb: Optional[Callable[[int, int, str], None]] = None) -> TopicRankResult:
        """Full pipeline: fetch repos → score each → rank → aggregate."""
        repos = self.fetch_repos()

        if not repos:
            return self.build_result([], 0)

        repo_scores: List[tuple[dict, float]] = []
        for i, repo in enumerate(repos):
            full_name = repo.get("full_name", f"repo_{i}")
            if progress_cb:
                progress_cb(i, len(repos), full_name)
            score = self.score_repo(repo)
            repo_scores.append((repo, score))

        entries = self.rank_repos(repo_scores)
        return self.build_result(entries, total_analyzed=len(repos))
