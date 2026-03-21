"""agentkit daily-duel engine — auto-selects contrasting GitHub repo pairs for daily comparison."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Tuple

from agentkit_cli.repo_duel import RepoDuelEngine, RepoDuelResult


# ---------------------------------------------------------------------------
# Category insights for draw/near-draw tweet copy
# ---------------------------------------------------------------------------

CATEGORY_INSIGHTS: dict[str, list[str]] = {
    "web-frameworks": [
        "top web frameworks maintain excellent agent docs",
        "leading web frameworks set the bar for agent-readiness",
        "the best web frameworks write for humans and agents alike",
        "quality rises to the top",
        "great web frameworks make life easy for agents and devs",
    ],
    "http-clients": [
        "elite HTTP clients prioritise clear, machine-readable docs",
        "top HTTP clients make integration effortless for agents",
        "leading HTTP client authors know agents read their docs too",
        "great HTTP clients document every edge case — agents love that",
    ],
    "ml-ai": [
        "the best ML/AI SDKs are built with agents in mind",
        "top ML/AI repos raise the standard for agent-readable docs",
        "elite ML/AI libraries know their users include AI agents",
        "leading ML/AI SDKs set the bar for LLM-friendly documentation",
        "in ML/AI, excellent agent-readiness is the expectation",
    ],
    "testing": [
        "great testing frameworks document everything — even for agents",
        "top testing libraries make onboarding effortless for agents",
        "leading test frameworks set the standard for clear, tool-friendly docs",
        "quality testing repos know agents read their docs too",
    ],
    "async-networking": [
        "elite async libraries ship documentation agents can reason over",
        "top async networking repos write for humans and agents equally",
        "leading async frameworks prioritise clarity — agents included",
        "great async libraries make integration easy at every level",
    ],
    "databases": [
        "top ORM and database libraries ship agent-ready documentation",
        "leading database libraries prioritise machine-readable clarity",
        "elite database repos know agents depend on precise docs",
        "great database libraries make schema and API docs crystal clear",
    ],
    "js-frameworks": [
        "top JS frameworks maintain docs that agents can navigate",
        "leading JS frameworks set the standard for agent-readable structure",
        "elite JS repos write for humans and AI agents alike",
        "great JS frameworks make onboarding frictionless for agents",
    ],
    "devtools": [
        "leading devtools set the bar for agent-readiness",
        "top devtools repos know their users include AI agents",
        "elite devtools maintain documentation agents can rely on",
        "great devtools write specs agents and humans both appreciate",
        "top-tier devtools prove quality and agent-readiness go together",
    ],
}

_DEFAULT_INSIGHTS = [
    "the best repos write for humans and agents equally",
    "top OSS projects raise the bar for agent-readiness",
    "elite repos make machine-readable documentation a priority",
    "leading projects know agents read their docs too",
]


def _category_insight(category: str, seed: str) -> str:
    """Return a deterministic category insight phrase."""
    phrases = CATEGORY_INSIGHTS.get(category, _DEFAULT_INSIGHTS)
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return phrases[int(digest, 16) % len(phrases)]


def _build_tweet_text(
    repo1: str,
    repo2: str,
    repo1_score: float,
    repo2_score: float,
    repo1_grade: str,
    repo2_grade: str,
    winner: str,
    n_dims: int,
    winner_wins: int,
    pair_category: str,
    seed: str,
) -> str:
    """Build tweet text with personality for draws, near-draws, and winners."""
    score_diff = abs(repo1_score - repo2_score)

    if winner == "draw" or score_diff == 0:
        # Draw case: both repos are high-quality
        insight = _category_insight(pair_category, seed)
        tweet_text = (
            f"{repo1} vs {repo2}: both score {repo1_score:.0f}/100 — a draw of champions. "
            f"In {pair_category}, {insight}."
        )
    elif score_diff <= 5:
        # Near-draw case: lead with the close margin
        winner_repo = repo1 if winner == "repo1" else repo2
        loser_repo = repo2 if winner == "repo1" else repo1
        winner_score = repo1_score if winner == "repo1" else repo2_score
        loser_score = repo2_score if winner == "repo1" else repo1_score
        winner_grade = repo1_grade if winner == "repo1" else repo2_grade
        loser_grade = repo2_grade if winner == "repo1" else repo1_grade
        diff = int(score_diff)
        tweet_text = (
            f"{winner_repo} ({winner_score:.0f}/100) vs {loser_repo} ({loser_score:.0f}/100): "
            f"extremely close. {winner_repo.split('/')[-1].capitalize()} edges "
            f"{loser_repo.split('/')[-1].capitalize()} by {diff} point{'s' if diff != 1 else ''} "
            f"across {n_dims} agent-readiness dimensions."
        )
    else:
        # Clear winner case: current format
        winner_name = (
            repo1 if winner == "repo1"
            else repo2 if winner == "repo2"
            else "draw"
        )
        tweet_text = (
            f"{repo1} vs {repo2} agent-readiness: "
            f"{repo1} {repo1_score:.0f}/100 ({repo1_grade}), "
            f"{repo2} {repo2_score:.0f}/100 ({repo2_grade}). "
            f"Winner: {winner_name} on {winner_wins}/{n_dims} dimensions."
        )

    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    return tweet_text


# ---------------------------------------------------------------------------
# Preset repo pairs
# ---------------------------------------------------------------------------

PRESET_PAIRS: list[Tuple[str, str, str]] = [
    # (repo1, repo2, category)
    # Web frameworks
    ("tiangolo/fastapi", "pallets/flask", "web-frameworks"),
    ("django/django", "tiangolo/fastapi", "web-frameworks"),
    ("tiangolo/fastapi", "encode/starlette", "web-frameworks"),
    ("expressjs/express", "fastify/fastify", "web-frameworks"),
    # HTTP clients
    ("encode/httpx", "psf/requests", "http-clients"),
    ("urllib3/urllib3", "encode/httpx", "http-clients"),
    # ML/AI
    ("huggingface/transformers", "openai/openai-python", "ml-ai"),
    ("langchain-ai/langchain", "microsoft/semantic-kernel", "ml-ai"),
    ("pytorch/pytorch", "google/jax", "ml-ai"),
    ("openai/openai-python", "anthropics/anthropic-sdk-python", "ml-ai"),
    # Testing
    ("pytest-dev/pytest", "robotframework/robotframework", "testing"),
    ("pytest-dev/pytest", "HypothesisWorks/hypothesis", "testing"),
    # Async/networking
    ("python-trio/trio", "encode/uvicorn", "async-networking"),
    ("aio-libs/aiohttp", "encode/uvicorn", "async-networking"),
    # Databases
    ("sqlalchemy/sqlalchemy", "mongodb/motor", "databases"),
    ("tortoise/tortoise-orm", "sqlalchemy/sqlalchemy", "databases"),
    # JS/TS frameworks
    ("vercel/next.js", "remix-run/remix", "js-frameworks"),
    ("facebook/react", "vuejs/vue", "js-frameworks"),
    # DevTools
    ("astral-sh/uv", "pypa/pip", "devtools"),
    ("astral-sh/ruff", "PyCQA/flake8", "devtools"),
    ("astral-sh/ruff", "psf/black", "devtools"),
    ("pre-commit/pre-commit", "astral-sh/ruff", "devtools"),
]


# ---------------------------------------------------------------------------
# DailyDuelResult
# ---------------------------------------------------------------------------

@dataclass
class DailyDuelResult(RepoDuelResult):
    """Extends RepoDuelResult with daily-duel-specific fields."""
    tweet_text: str = ""
    pair_category: str = ""
    seed: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["tweet_text"] = self.tweet_text
        d["pair_category"] = self.pair_category
        d["seed"] = self.seed
        return d


# ---------------------------------------------------------------------------
# DailyDuelEngine
# ---------------------------------------------------------------------------

class DailyDuelEngine:
    """Auto-selects contrasting GitHub repo pairs and runs daily duels."""

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: int = 120,
        _analyze_factory=None,
    ) -> None:
        self.token = token
        self.timeout = timeout
        self._analyze_factory = _analyze_factory

    def pick_pair(self, seed: Optional[str] = None) -> Tuple[str, str, str]:
        """Deterministically pick a (repo1, repo2, category) triple from presets.

        Default seed = today's date YYYY-MM-DD so same pair runs all day.
        Custom seed = any string for ad-hoc picks.
        """
        effective_seed = seed or date.today().isoformat()
        digest = hashlib.sha256(effective_seed.encode()).hexdigest()
        index = int(digest, 16) % len(PRESET_PAIRS)
        return PRESET_PAIRS[index]

    def run_daily_duel(self, seed: Optional[str] = None, deep: bool = False) -> DailyDuelResult:
        """Pick a pair and run a duel, returning a DailyDuelResult."""
        effective_seed = seed or date.today().isoformat()
        repo1, repo2, category = self.pick_pair(seed)

        engine = RepoDuelEngine(
            token=self.token,
            timeout=self.timeout,
            _analyze_factory=self._analyze_factory,
        )
        base_result = engine.run_duel(repo1=repo1, repo2=repo2, deep=deep)

        # Build tweet text
        n_dims = len(base_result.dimension_results)
        winner_wins = sum(
            1 for d in base_result.dimension_results
            if d.winner == ("repo1" if base_result.winner == "repo1" else "repo2")
        )

        tweet_text = _build_tweet_text(
            repo1=repo1,
            repo2=repo2,
            repo1_score=base_result.repo1_score,
            repo2_score=base_result.repo2_score,
            repo1_grade=base_result.repo1_grade,
            repo2_grade=base_result.repo2_grade,
            winner=base_result.winner,
            n_dims=n_dims,
            winner_wins=winner_wins,
            pair_category=category,
            seed=effective_seed,
        )

        result = DailyDuelResult(
            repo1=base_result.repo1,
            repo2=base_result.repo2,
            repo1_score=base_result.repo1_score,
            repo2_score=base_result.repo2_score,
            repo1_grade=base_result.repo1_grade,
            repo2_grade=base_result.repo2_grade,
            dimension_results=base_result.dimension_results,
            winner=base_result.winner,
            run_date=base_result.run_date,
            share_url=base_result.share_url,
            tweet_text=tweet_text,
            pair_category=category,
            seed=effective_seed,
        )

        # Write latest JSON atomically
        _write_latest_json(result)

        return result

    def calendar(self, days: int = 7, start_date: Optional[date] = None) -> list[dict]:
        """Return a schedule of upcoming daily pairs."""
        start = start_date or date.today()
        schedule = []
        for i in range(days):
            d = start + timedelta(days=i)
            seed = d.isoformat()
            repo1, repo2, category = self.pick_pair(seed)
            schedule.append({
                "date": seed,
                "repo1": repo1,
                "repo2": repo2,
                "category": category,
            })
        return schedule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OUTPUT_DIR = Path.home() / ".local" / "share" / "agentkit"
_LATEST_JSON = _OUTPUT_DIR / "daily-duel-latest.json"


def _write_latest_json(result: DailyDuelResult, path: Optional[Path] = None) -> None:
    """Atomically write the daily-duel result as JSON."""
    target = path or _LATEST_JSON
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(result.to_dict(), indent=2)
    fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        os.replace(tmp, target)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
