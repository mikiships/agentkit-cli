"""agentkit user-scorecard engine — fetch all public repos for a GitHub user, analyze each, and aggregate."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from urllib import error as urllib_error, request as urllib_request

from agentkit_cli.github_api import (
    GITHUB_API_BASE,
    _build_headers,
    _fetch_page,
)

# ---------------------------------------------------------------------------
# Grade constants — contract spec: A≥80, B≥65, C≥50, D<50
# ---------------------------------------------------------------------------

GRADE_THRESHOLDS = [
    (80.0, "A"),
    (65.0, "B"),
    (50.0, "C"),
    (0.0, "D"),
]


def score_to_grade(score: Optional[float]) -> str:
    """Convert numeric score to letter grade (A/B/C/D) per contract thresholds."""
    if score is None:
        return "D"
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "D"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RepoResult:
    name: str
    full_name: str
    score: Optional[float]
    grade: str
    has_context: bool
    error: Optional[str] = None
    stars: int = 0

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "full_name": self.full_name,
            "score": self.score,
            "grade": self.grade,
            "has_context": self.has_context,
            "stars": self.stars,
        }
        if self.error is not None:
            d["error"] = self.error
        return d


@dataclass
class UserScorecardResult:
    username: str
    total_repos: int
    analyzed_repos: int
    skipped_repos: int
    avg_score: float
    grade: str
    context_coverage_pct: float
    top_repos: list[RepoResult] = field(default_factory=list)
    bottom_repos: list[RepoResult] = field(default_factory=list)
    all_repos: list[RepoResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "total_repos": self.total_repos,
            "analyzed_repos": self.analyzed_repos,
            "skipped_repos": self.skipped_repos,
            "avg_score": self.avg_score,
            "grade": self.grade,
            "context_coverage_pct": self.context_coverage_pct,
            "top_repos": [r.to_dict() for r in self.top_repos],
            "bottom_repos": [r.to_dict() for r in self.bottom_repos],
            "all_repos": [r.to_dict() for r in self.all_repos],
        }


# ---------------------------------------------------------------------------
# GitHub Contents API helper
# ---------------------------------------------------------------------------

_CONTEXT_FILENAMES = ("CLAUDE.md", "AGENTS.md", "AGENTS")


def _check_context_file(
    full_name: str,
    token: Optional[str] = None,
) -> bool:
    """Return True if the repo contains CLAUDE.md, AGENTS.md, or an AGENTS/ directory."""
    headers = _build_headers(token)
    for filename in _CONTEXT_FILENAMES:
        url = f"{GITHUB_API_BASE}/repos/{full_name}/contents/{filename}"
        req = urllib_request.Request(url, headers=headers, method="GET")
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                if resp.status in (200, 301):
                    return True
        except urllib_error.HTTPError as e:
            if e.code == 404:
                continue
            # Any other error: treat as unknown / no context
        except Exception:
            pass
    return False


# ---------------------------------------------------------------------------
# List public repos (user-specific endpoint)
# ---------------------------------------------------------------------------

def list_public_repos(
    username: str,
    token: Optional[str] = None,
    skip_forks: bool = True,
    min_stars: int = 0,
    limit: int = 20,
) -> list[dict]:
    """List public repos for a GitHub user (not org).

    Returns normalized repo dicts sorted by stars desc.
    """
    url: Optional[str] = f"{GITHUB_API_BASE}/users/{username}/repos?type=public&per_page=100&sort=updated"
    raw: list[dict] = []

    # Check if user exists first
    check_url = f"{GITHUB_API_BASE}/users/{username}"
    headers = _build_headers(token)
    req = urllib_request.Request(check_url, headers=headers, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=10) as resp:
            pass  # user exists
    except urllib_error.HTTPError as e:
        if e.code == 404:
            raise ValueError(f"GitHub user '{username}' not found")
        raise

    while url:
        items, _, next_url = _fetch_page(url, token)
        raw.extend(items)
        url = next_url  # type: ignore[assignment]

    result: list[dict] = []
    for repo in raw:
        if skip_forks and repo.get("fork", False):
            continue
        if repo.get("archived", False):
            continue
        if repo.get("size", 0) == 0:
            continue
        stars = repo.get("stargazers_count", 0)
        if stars < min_stars:
            continue
        result.append({
            "full_name": repo.get("full_name", ""),
            "name": repo.get("name", ""),
            "stars": stars,
            "fork": repo.get("fork", False),
        })

    # Sort by stars descending, take limit
    result.sort(key=lambda r: r["stars"], reverse=True)
    return result[:limit]


# ---------------------------------------------------------------------------
# Analysis helper (runs analyze_target per repo)
# ---------------------------------------------------------------------------

def _analyze_repo(
    full_name: str,
    timeout: int = 60,
) -> tuple[Optional[float], Optional[str]]:
    """Run agentkit analyze on a GitHub repo. Returns (score, error)."""
    try:
        from agentkit_cli.analyze import analyze_target
        result = analyze_target(
            target=f"github:{full_name}",
            timeout=timeout,
            quiet=True,
        )
        return result.composite_score, None
    except Exception as exc:
        return None, str(exc)


# ---------------------------------------------------------------------------
# UserScorecardEngine
# ---------------------------------------------------------------------------

class UserScorecardEngine:
    """Fetch all public repos for a GitHub user and aggregate agent-readiness scores."""

    def __init__(
        self,
        username: str,
        limit: int = 20,
        min_stars: int = 0,
        skip_forks: bool = True,
        timeout: int = 60,
        token: Optional[str] = None,
        _repos_override: Optional[list[dict]] = None,
        _analyze_override: Optional[object] = None,
        _context_override: Optional[object] = None,
    ) -> None:
        self.username = username
        self.limit = limit
        self.min_stars = min_stars
        self.skip_forks = skip_forks
        self.timeout = timeout
        self.token = token or os.environ.get("GITHUB_TOKEN")
        # Test overrides
        self._repos_override = _repos_override
        self._analyze_override = _analyze_override  # callable(full_name, timeout) -> (score, error)
        self._context_override = _context_override  # callable(full_name, token) -> bool

    def list_public_repos(self) -> list[dict]:
        if self._repos_override is not None:
            return self._repos_override
        return list_public_repos(
            username=self.username,
            token=self.token,
            skip_forks=self.skip_forks,
            min_stars=self.min_stars,
            limit=self.limit,
        )

    def run_analysis(
        self,
        repos: list[dict],
        progress_callback=None,
    ) -> list[RepoResult]:
        """Run analysis on each repo and return list of RepoResult."""
        results: list[RepoResult] = []

        for repo in repos:
            full_name = repo["full_name"]
            name = repo["name"]
            stars = repo.get("stars", 0)

            # Check context files
            if self._context_override is not None:
                has_context = self._context_override(full_name, self.token)
            else:
                has_context = _check_context_file(full_name, self.token)

            # Run analysis
            if self._analyze_override is not None:
                score, error = self._analyze_override(full_name, self.timeout)
            else:
                score, error = _analyze_repo(full_name, self.timeout)

            grade = score_to_grade(score)

            repo_result = RepoResult(
                name=name,
                full_name=full_name,
                score=score,
                grade=grade,
                has_context=has_context,
                error=error,
                stars=stars,
            )
            results.append(repo_result)

            if progress_callback is not None:
                score_str = f"{score:.0f}" if score is not None else "err"
                progress_callback(full_name, score_str)

        return results

    def aggregate(self, repo_results: list[RepoResult]) -> UserScorecardResult:
        """Aggregate per-repo results into a UserScorecardResult."""
        total_repos = len(repo_results)
        analyzed = [r for r in repo_results if r.score is not None]
        skipped = [r for r in repo_results if r.score is None]

        avg_score = (
            sum(r.score for r in analyzed) / len(analyzed)  # type: ignore[arg-type]
            if analyzed
            else 0.0
        )
        grade = score_to_grade(avg_score if analyzed else None)

        # Context coverage: % of ALL repos with context file
        context_count = sum(1 for r in repo_results if r.has_context)
        context_coverage_pct = (
            (context_count / total_repos * 100.0) if total_repos > 0 else 0.0
        )

        # Sort by score descending (None scores go last)
        sorted_all = sorted(
            repo_results,
            key=lambda r: (r.score is not None, r.score or 0.0),
            reverse=True,
        )

        top_repos = sorted_all[:3]
        # Only include bottom_repos if ≥5 analyzed
        scored_sorted = [r for r in sorted_all if r.score is not None]
        bottom_repos: list[RepoResult] = []
        if len(scored_sorted) >= 5:
            bottom_repos = scored_sorted[-3:][::-1]  # lowest first

        return UserScorecardResult(
            username=self.username,
            total_repos=total_repos,
            analyzed_repos=len(analyzed),
            skipped_repos=len(skipped),
            avg_score=round(avg_score, 2),
            grade=grade,
            context_coverage_pct=round(context_coverage_pct, 1),
            top_repos=top_repos,
            bottom_repos=bottom_repos,
            all_repos=sorted_all,
        )

    def run(self, progress_callback=None) -> UserScorecardResult:
        """Full pipeline: list repos → analyze → aggregate."""
        repos = self.list_public_repos()
        repo_results = self.run_analysis(repos, progress_callback=progress_callback)
        return self.aggregate(repo_results)
