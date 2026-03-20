"""agentkit user-team engine — fetch top contributors from a GitHub org and aggregate agent-readiness scores."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional
from urllib import error as urllib_error, request as urllib_request

from agentkit_cli.github_api import GITHUB_API_BASE, _build_headers, _fetch_page
from agentkit_cli.user_scorecard import UserScorecardEngine, UserScorecardResult, score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TeamScorecardResult:
    """Full result of a team scorecard analysis for a GitHub org."""
    org: str
    contributor_results: List[UserScorecardResult]
    aggregate_score: float
    aggregate_grade: str
    top_scorer: str
    contributor_count: int
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "org": self.org,
            "contributor_results": [r.to_dict() for r in self.contributor_results],
            "aggregate_score": self.aggregate_score,
            "aggregate_grade": self.aggregate_grade,
            "top_scorer": self.top_scorer,
            "contributor_count": self.contributor_count,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# GitHub org member / contributor fetchers
# ---------------------------------------------------------------------------

def fetch_org_members(
    org: str,
    token: Optional[str] = None,
    limit: int = 10,
) -> List[str]:
    """Fetch public members of a GitHub org. Returns list of logins."""
    url: Optional[str] = f"{GITHUB_API_BASE}/orgs/{org}/members?per_page=100"
    logins: List[str] = []

    while url and len(logins) < limit * 2:
        items, _, next_url = _fetch_page(url, token)
        for item in items:
            login = item.get("login", "")
            if login:
                logins.append(login)
        url = next_url  # type: ignore[assignment]

    return logins[:limit]


def fetch_org_contributors(
    org: str,
    token: Optional[str] = None,
    limit: int = 10,
) -> List[str]:
    """Fetch top contributors from org's repos. Returns deduplicated list of logins."""
    # Get org's most recently updated repos
    repos_url: Optional[str] = f"{GITHUB_API_BASE}/orgs/{org}/repos?per_page=30&sort=updated"
    repos: List[dict] = []

    try:
        items, _, _ = _fetch_page(repos_url, token)
        repos = items[:10]
    except Exception:
        return []

    contributor_counts: dict[str, int] = {}

    for repo in repos:
        repo_name = repo.get("name", "")
        if not repo_name:
            continue
        contrib_url = f"{GITHUB_API_BASE}/repos/{org}/{repo_name}/contributors?per_page=30"
        try:
            contribs, _, _ = _fetch_page(contrib_url, token)
            for c in contribs:
                login = c.get("login", "")
                if login and not login.endswith("[bot]"):
                    count = c.get("contributions", 1)
                    contributor_counts[login] = contributor_counts.get(login, 0) + count
        except Exception:
            continue

    # Sort by total contributions
    sorted_contribs = sorted(contributor_counts.items(), key=lambda x: x[1], reverse=True)
    return [login for login, _ in sorted_contribs[:limit]]


# ---------------------------------------------------------------------------
# TeamScorecardEngine
# ---------------------------------------------------------------------------

class TeamScorecardEngine:
    """Analyze top contributors of a GitHub org for agent-readiness."""

    def __init__(
        self,
        org: str,
        limit: int = 10,
        token: Optional[str] = None,
        timeout: int = 60,
        _members_override: Optional[List[str]] = None,
        _scorecard_factory: Optional[Callable] = None,
    ) -> None:
        self.org = org
        self.limit = limit
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._members_override = _members_override
        self._scorecard_factory = _scorecard_factory  # callable(username, token, timeout) -> UserScorecardResult

    def fetch_contributors(self) -> List[str]:
        """Fetch top contributors for the org."""
        if self._members_override is not None:
            return self._members_override[:self.limit]

        # Try contributors first (more meaningful), fall back to members
        try:
            contribs = fetch_org_contributors(self.org, token=self.token, limit=self.limit)
            if contribs:
                return contribs
        except Exception:
            pass

        # Fall back to members list
        try:
            members = fetch_org_members(self.org, token=self.token, limit=self.limit)
            return members
        except urllib_error.HTTPError as e:
            if e.code in (404, 403):
                raise ValueError(f"GitHub org '{self.org}' not found or not accessible")
            raise

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

    def aggregate(self, results: List[UserScorecardResult]) -> TeamScorecardResult:
        """Aggregate per-user results into a TeamScorecardResult."""
        contributor_count = len(results)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if not results:
            return TeamScorecardResult(
                org=self.org,
                contributor_results=[],
                aggregate_score=0.0,
                aggregate_grade="D",
                top_scorer="",
                contributor_count=0,
                timestamp=timestamp,
            )

        scores = [r.avg_score for r in results]
        aggregate_score = round(sum(scores) / len(scores), 2)
        aggregate_grade = score_to_grade(aggregate_score)

        # top_scorer: contributor with highest avg_score
        top_result = max(results, key=lambda r: r.avg_score)
        top_scorer = top_result.username

        return TeamScorecardResult(
            org=self.org,
            contributor_results=results,
            aggregate_score=aggregate_score,
            aggregate_grade=aggregate_grade,
            top_scorer=top_scorer,
            contributor_count=contributor_count,
            timestamp=timestamp,
        )

    def run(self, progress_callback=None) -> TeamScorecardResult:
        """Full pipeline: fetch contributors → score each → aggregate."""
        contributors = self.fetch_contributors()

        if not contributors:
            return self.aggregate([])

        results: List[UserScorecardResult] = []
        for i, username in enumerate(contributors):
            if progress_callback:
                progress_callback(i, len(contributors), username)
            result = self.score_contributor(username)
            results.append(result)

        return self.aggregate(results)
