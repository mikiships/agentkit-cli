"""agentkit user-card engine — generate a compact agent-readiness card for a GitHub user."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from agentkit_cli.user_scorecard import (
    UserScorecardEngine,
    score_to_grade,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class UserCardResult:
    """Compact agent-readiness card data for a GitHub user."""

    username: str
    avatar_url: str
    grade: str
    avg_score: float
    total_repos: int
    analyzed_repos: int
    context_coverage_pct: float
    top_repo_name: str
    top_repo_score: float
    agent_ready_count: int  # repos with score >= 80
    summary_line: str  # e.g. "3/10 repos agent-ready · Grade B"
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "avatar_url": self.avatar_url,
            "grade": self.grade,
            "avg_score": self.avg_score,
            "total_repos": self.total_repos,
            "analyzed_repos": self.analyzed_repos,
            "context_coverage_pct": self.context_coverage_pct,
            "top_repo_name": self.top_repo_name,
            "top_repo_score": self.top_repo_score,
            "agent_ready_count": self.agent_ready_count,
            "summary_line": self.summary_line,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

AGENT_READY_THRESHOLD = 80.0


class UserCardEngine:
    """Lightweight wrapper over UserScorecardEngine that produces a compact card result."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        limit: int = 10,
        min_stars: int = 0,
        skip_forks: bool = True,
        timeout: int = 60,
    ) -> None:
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.limit = max(1, min(limit, 30))
        self.min_stars = min_stars
        self.skip_forks = skip_forks
        self.timeout = timeout

    def run(self, user: str) -> UserCardResult:
        """Run the scorecard engine and distil into a compact UserCardResult."""
        username = user.strip()
        if username.startswith("github:"):
            username = username[len("github:"):]
        username = username.strip("/").strip()

        if not username:
            return UserCardResult(
                username=username,
                avatar_url="",
                grade="D",
                avg_score=0.0,
                total_repos=0,
                analyzed_repos=0,
                context_coverage_pct=0.0,
                top_repo_name="",
                top_repo_score=0.0,
                agent_ready_count=0,
                summary_line="0/0 repos agent-ready · Grade D",
                error="Username is required",
            )

        try:
            engine = UserScorecardEngine(
                username=username,
                limit=self.limit,
                min_stars=self.min_stars,
                skip_forks=self.skip_forks,
                timeout=self.timeout,
                token=self.github_token,
            )
            scorecard = engine.run()
        except Exception as exc:
            logger.warning("UserScorecardEngine failed for %s: %s", username, exc)
            return UserCardResult(
                username=username,
                avatar_url="",
                grade="D",
                avg_score=0.0,
                total_repos=0,
                analyzed_repos=0,
                context_coverage_pct=0.0,
                top_repo_name="",
                top_repo_score=0.0,
                agent_ready_count=0,
                summary_line="0/0 repos agent-ready · Grade D",
                error=str(exc),
            )

        # Distil scorecard into compact card
        top_repo_name = ""
        top_repo_score = 0.0
        if scorecard.top_repos:
            top = scorecard.top_repos[0]
            top_repo_name = top.name
            top_repo_score = top.score if top.score is not None else 0.0

        agent_ready_count = sum(
            1 for r in scorecard.all_repos
            if r.score is not None and r.score >= AGENT_READY_THRESHOLD
        )

        summary_line = (
            f"{agent_ready_count}/{scorecard.analyzed_repos} repos agent-ready · Grade {scorecard.grade}"
        )

        return UserCardResult(
            username=username,
            avatar_url=f"https://github.com/{username}.png",
            grade=scorecard.grade,
            avg_score=scorecard.avg_score,
            total_repos=scorecard.total_repos,
            analyzed_repos=scorecard.analyzed_repos,
            context_coverage_pct=scorecard.context_coverage_pct,
            top_repo_name=top_repo_name,
            top_repo_score=top_repo_score,
            agent_ready_count=agent_ready_count,
            summary_line=summary_line,
        )
