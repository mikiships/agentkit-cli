"""agentkit user-improve engine — find a GitHub user's lowest-scoring repos and improve them."""
from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from agentkit_cli.user_scorecard import (
    UserScorecardEngine,
    RepoResult,
    list_public_repos,
    score_to_grade,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class UserRepoScore:
    """Score for a single repo, used as input to improve_repo."""
    name: str
    full_name: str
    score: float
    grade: str
    stars: int = 0
    repo_url: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "full_name": self.full_name,
            "score": self.score,
            "grade": self.grade,
            "stars": self.stars,
            "repo_url": self.repo_url,
        }


@dataclass
class UserImproveResult:
    """Result from improving a single repo."""
    repo_url: str
    full_name: str
    before_score: float
    after_score: float
    lift: float
    files_generated: list[str] = field(default_factory=list)
    files_hardened: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: bool = False

    def to_dict(self) -> dict:
        return {
            "repo_url": self.repo_url,
            "full_name": self.full_name,
            "before_score": self.before_score,
            "after_score": self.after_score,
            "lift": self.lift,
            "files_generated": self.files_generated,
            "files_hardened": self.files_hardened,
            "errors": self.errors,
            "skipped": self.skipped,
        }


@dataclass
class UserImproveReport:
    """Aggregated result for a user-improve run."""
    user: str
    avatar_url: str
    total_repos: int
    improved: int
    skipped: int
    results: list[UserImproveResult] = field(default_factory=list)
    summary_stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "user": self.user,
            "avatar_url": self.avatar_url,
            "total_repos": self.total_repos,
            "improved": self.improved,
            "skipped": self.skipped,
            "results": [r.to_dict() for r in self.results],
            "summary_stats": self.summary_stats,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_avatar_url(user: str, token: Optional[str] = None) -> str:
    """Fetch GitHub avatar URL for a user."""
    try:
        from agentkit_cli.github_api import GITHUB_API_BASE, _build_headers
        from urllib import request as urllib_request, error as urllib_error
        import json as _json
        headers = _build_headers(token)
        url = f"{GITHUB_API_BASE}/users/{user}"
        req = urllib_request.Request(url, headers=headers, method="GET")
        with urllib_request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read().decode())
            return data.get("avatar_url", "")
    except Exception:
        return ""


def _score_from_repo_result(r: RepoResult) -> Optional[float]:
    return r.score


def _clone_repo(full_name: str, dest: str, token: Optional[str] = None) -> bool:
    """Clone a GitHub repo to dest. Returns True on success."""
    import subprocess
    if token:
        clone_url = f"https://{token}@github.com/{full_name}.git"
    else:
        clone_url = f"https://github.com/{full_name}.git"
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", clone_url, dest],
            capture_output=True,
            timeout=120,
            check=True,
        )
        return True
    except Exception as exc:
        logger.warning("Clone failed for %s: %s", full_name, exc)
        return False


def _run_improve_engine(path: str) -> tuple[float, float, list[str], list[str]]:
    """Run the improve engine on a local path. Returns (before, after, files_generated, files_hardened)."""
    from agentkit_cli.improve_engine import ImproveEngine
    from pathlib import Path as _Path
    engine = ImproveEngine()
    plan = engine.run(path, no_generate=False, no_harden=False, dry_run=False)
    files_generated = [a for a in plan.actions_taken if "generate" in a.lower() or "claude.md" in a.lower()]
    files_hardened = [a for a in plan.actions_taken if "harden" in a.lower() or "redteam" in a.lower()]
    return plan.baseline_score, plan.final_score, files_generated, files_hardened


# ---------------------------------------------------------------------------
# UserImproveEngine
# ---------------------------------------------------------------------------

class UserImproveEngine:
    """Find a GitHub user's lowest-scoring repos and auto-improve them."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        tempdir: Optional[str] = None,
        _repos_override: Optional[list[dict]] = None,
        _analyze_override=None,
        _improve_override=None,
        _avatar_override: Optional[str] = None,
    ) -> None:
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self._tempdir = tempdir
        self._repos_override = _repos_override
        self._analyze_override = _analyze_override
        self._improve_override = _improve_override
        self._avatar_override = _avatar_override

    def fetch_user_repos(self, user: str) -> list[dict]:
        """Fetch top public repos for a GitHub user."""
        if self._repos_override is not None:
            return self._repos_override
        return list_public_repos(
            username=user,
            token=self.github_token,
            skip_forks=True,
            limit=50,
        )

    def score_repos(self, repos: list[dict]) -> list[UserRepoScore]:
        """Run agentkit analyze on each repo and return scores."""
        results: list[UserRepoScore] = []
        for repo in repos:
            full_name = repo["full_name"]
            name = repo["name"]
            stars = repo.get("stars", 0)
            repo_url = f"https://github.com/{full_name}"

            if self._analyze_override is not None:
                score, error = self._analyze_override(full_name, 60)
            else:
                try:
                    from agentkit_cli.user_scorecard import _analyze_repo
                    score, error = _analyze_repo(full_name, timeout=60)
                except Exception as exc:
                    score, error = None, str(exc)

            if score is None:
                logger.warning("Skipping %s — analyze failed: %s", full_name, error)
                continue

            grade = score_to_grade(score)
            results.append(UserRepoScore(
                name=name,
                full_name=full_name,
                score=score,
                grade=grade,
                stars=stars,
                repo_url=repo_url,
            ))
        return results

    def select_targets(
        self,
        scores: list[UserRepoScore],
        limit: int,
        below: int,
    ) -> list[UserRepoScore]:
        """Select repos scoring below threshold, sorted by score ascending, up to limit."""
        candidates = [s for s in scores if s.score < below]
        candidates.sort(key=lambda r: r.score)
        return candidates[:limit]

    def improve_repo(self, repo: UserRepoScore, tempdir: str) -> UserImproveResult:
        """Clone and improve a single repo. Always cleans up in finally."""
        import os as _os
        clone_dir = _os.path.join(tempdir, repo.name)
        try:
            if self._improve_override is not None:
                before, after, files_gen, files_hard = self._improve_override(repo, clone_dir)
            else:
                cloned = _clone_repo(repo.full_name, clone_dir, token=self.github_token)
                if not cloned:
                    return UserImproveResult(
                        repo_url=repo.repo_url,
                        full_name=repo.full_name,
                        before_score=repo.score,
                        after_score=repo.score,
                        lift=0.0,
                        errors=["Clone failed"],
                        skipped=True,
                    )
                before, after, files_gen, files_hard = _run_improve_engine(clone_dir)

            lift = round(after - before, 2)
            return UserImproveResult(
                repo_url=repo.repo_url,
                full_name=repo.full_name,
                before_score=before,
                after_score=after,
                lift=lift,
                files_generated=files_gen,
                files_hardened=files_hard,
            )
        except Exception as exc:
            logger.warning("improve_repo failed for %s: %s", repo.full_name, exc)
            return UserImproveResult(
                repo_url=repo.repo_url,
                full_name=repo.full_name,
                before_score=repo.score,
                after_score=repo.score,
                lift=0.0,
                errors=[str(exc)],
                skipped=True,
            )
        finally:
            import shutil
            if _os.path.exists(clone_dir):
                try:
                    shutil.rmtree(clone_dir)
                except Exception:
                    pass

    def run(
        self,
        user: str,
        limit: int = 5,
        below: int = 80,
        progress_callback=None,
    ) -> UserImproveReport:
        """Full pipeline: fetch → score → select → improve → report."""
        if limit > 20:
            limit = 20

        # Fetch avatar
        if self._avatar_override is not None:
            avatar_url = self._avatar_override
        else:
            avatar_url = _fetch_avatar_url(user, token=self.github_token)

        # Fetch repos
        repos = self.fetch_user_repos(user)

        # Score repos
        scored = self.score_repos(repos)

        # Select targets
        targets = self.select_targets(scored, limit=limit, below=below)

        # Improve each target
        results: list[UserImproveResult] = []
        use_tempdir = self._tempdir

        def _do_improve(td: str) -> None:
            for repo in targets:
                if progress_callback:
                    progress_callback(repo.full_name, "improving")
                result = self.improve_repo(repo, td)
                results.append(result)
                if progress_callback:
                    lift_str = f"+{result.lift:.1f}" if result.lift >= 0 else f"{result.lift:.1f}"
                    progress_callback(repo.full_name, lift_str)

        if use_tempdir:
            _do_improve(use_tempdir)
        else:
            with tempfile.TemporaryDirectory(prefix="agentkit-user-improve-") as td:
                _do_improve(td)

        # Aggregate stats
        improved_results = [r for r in results if not r.skipped]
        skipped_results = [r for r in results if r.skipped]

        avg_before = (
            sum(r.before_score for r in improved_results) / len(improved_results)
            if improved_results else 0.0
        )
        avg_after = (
            sum(r.after_score for r in improved_results) / len(improved_results)
            if improved_results else 0.0
        )
        avg_lift = round(avg_after - avg_before, 2)

        summary_stats = {
            "avg_before": round(avg_before, 2),
            "avg_after": round(avg_after, 2),
            "avg_lift": avg_lift,
            "total_files_generated": sum(len(r.files_generated) for r in results),
            "total_files_hardened": sum(len(r.files_hardened) for r in results),
        }

        return UserImproveReport(
            user=user,
            avatar_url=avatar_url,
            total_repos=len(repos),
            improved=len(improved_results),
            skipped=len(skipped_results),
            results=results,
            summary_stats=summary_stats,
        )
