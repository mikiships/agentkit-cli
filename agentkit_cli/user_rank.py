"""agentkit user-rank engine — discover top GitHub contributors for a topic and rank by agent-readiness."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from agentkit_cli.github_api import GITHUB_API_BASE, _fetch_page
from agentkit_cli.user_scorecard import UserScorecardEngine, UserScorecardResult, score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class UserRankEntry:
    """A single ranked contributor entry."""
    rank: int
    username: str
    score: float
    grade: str
    top_repo: str = ""
    avatar_url: str = ""

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "username": self.username,
            "score": self.score,
            "grade": self.grade,
            "top_repo": self.top_repo,
            "avatar_url": self.avatar_url,
        }


@dataclass
class UserRankResult:
    """Full result of a user-rank analysis for a GitHub topic."""
    topic: str
    contributors: List[UserRankEntry]
    top_scorer: str
    mean_score: float
    grade_distribution: Dict[str, int]
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "contributors": [c.to_dict() for c in self.contributors],
            "top_scorer": self.top_scorer,
            "mean_score": self.mean_score,
            "grade_distribution": self.grade_distribution,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# GitHub topic contributor fetchers
# ---------------------------------------------------------------------------

def search_topic_contributors(
    topic: str,
    token: Optional[str] = None,
    limit: int = 20,
) -> List[str]:
    """Search GitHub for repos matching topic, extract unique contributors.

    Returns deduplicated list of contributor logins (up to limit).
    """
    # Search for repos with the topic
    search_url = (
        f"{GITHUB_API_BASE}/search/repositories"
        f"?q=topic:{topic}&sort=stars&per_page=50"
    )

    try:
        repos_data, _, _ = _fetch_page(search_url, token)
    except Exception:
        return []

    # repos_data for search is the list of items
    if isinstance(repos_data, dict):
        repos = repos_data.get("items", [])
    else:
        repos = repos_data or []

    # Extract contributors from top repos
    seen: dict[str, int] = {}
    for repo in repos[:10]:
        owner = repo.get("owner", {}).get("login", "")
        repo_name = repo.get("name", "")
        if not owner or not repo_name:
            continue

        contrib_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/contributors?per_page=30"
        try:
            contribs, _, _ = _fetch_page(contrib_url, token)
            for c in contribs:
                login = c.get("login", "")
                if login and not login.endswith("[bot]"):
                    count = c.get("contributions", 1)
                    seen[login] = seen.get(login, 0) + count
        except Exception:
            continue

        if len(seen) >= limit * 3:
            break

    # Sort by contribution count and return top logins
    sorted_logins = sorted(seen.items(), key=lambda x: x[1], reverse=True)
    return [login for login, _ in sorted_logins[:limit]]


# ---------------------------------------------------------------------------
# UserRankEngine
# ---------------------------------------------------------------------------

class UserRankEngine:
    """Discover top GitHub contributors for a topic and rank by agent-readiness."""

    def __init__(
        self,
        topic: str,
        limit: int = 20,
        token: Optional[str] = None,
        timeout: int = 60,
        _contributors_override: Optional[List[str]] = None,
        _scorecard_factory: Optional[Callable] = None,
    ) -> None:
        self.topic = topic
        self.limit = limit
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._contributors_override = _contributors_override
        self._scorecard_factory = _scorecard_factory  # callable(username, token, timeout) -> UserScorecardResult

    def fetch_contributors(self) -> List[str]:
        """Fetch contributors for the topic."""
        if self._contributors_override is not None:
            return self._contributors_override[:self.limit]

        try:
            return search_topic_contributors(self.topic, token=self.token, limit=self.limit)
        except Exception:
            return []

    def score_contributor(self, username: str) -> UserScorecardResult:
        """Run UserScorecardEngine for a single contributor."""
        if self._scorecard_factory is not None:
            return self._scorecard_factory(username, self.token, self.timeout)

        engine = UserScorecardEngine(
            username=username,
            limit=20,
            token=self.token,
            timeout=self.timeout,
        )
        return engine.run()

    def rank_contributors(self, scorecard_results: List[UserScorecardResult]) -> List[UserRankEntry]:
        """Score and sort contributors into ranked entries."""
        sorted_results = sorted(scorecard_results, key=lambda r: r.avg_score, reverse=True)
        entries: List[UserRankEntry] = []
        for rank, r in enumerate(sorted_results, 1):
            top_repo = ""
            if r.top_repos:
                top_repo = r.top_repos[0].name if r.top_repos else ""
            entry = UserRankEntry(
                rank=rank,
                username=r.username,
                score=round(r.avg_score, 2),
                grade=r.grade,
                top_repo=top_repo,
                avatar_url=f"https://github.com/{r.username}.png?size=40",
            )
            entries.append(entry)
        return entries

    def build_result(self, entries: List[UserRankEntry]) -> UserRankResult:
        """Aggregate ranked entries into a UserRankResult."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if not entries:
            return UserRankResult(
                topic=self.topic,
                contributors=[],
                top_scorer="",
                mean_score=0.0,
                grade_distribution={"A": 0, "B": 0, "C": 0, "D": 0},
                timestamp=timestamp,
            )

        scores = [e.score for e in entries]
        mean_score = round(sum(scores) / len(scores), 2)
        top_scorer = entries[0].username  # already sorted by score desc

        grade_distribution: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        for e in entries:
            g = e.grade if e.grade in grade_distribution else "D"
            grade_distribution[g] += 1

        return UserRankResult(
            topic=self.topic,
            contributors=entries,
            top_scorer=top_scorer,
            mean_score=mean_score,
            grade_distribution=grade_distribution,
            timestamp=timestamp,
        )

    def run(self, progress_callback=None) -> UserRankResult:
        """Full pipeline: fetch contributors → score each → rank → aggregate."""
        contributors = self.fetch_contributors()

        if not contributors:
            return self.build_result([])

        scorecard_results: List[UserScorecardResult] = []
        for i, username in enumerate(contributors):
            if progress_callback:
                progress_callback(i, len(contributors), username)
            result = self.score_contributor(username)
            scorecard_results.append(result)

        entries = self.rank_contributors(scorecard_results)
        return self.build_result(entries)
