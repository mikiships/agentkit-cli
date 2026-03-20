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
        winner_name = (
            repo1 if base_result.winner == "repo1"
            else repo2 if base_result.winner == "repo2"
            else "draw"
        )
        n_dims = len(base_result.dimension_results)
        winner_wins = sum(
            1 for d in base_result.dimension_results
            if d.winner == ("repo1" if base_result.winner == "repo1" else "repo2")
        )

        tweet_text = (
            f"{repo1} vs {repo2} agent-readiness: "
            f"{repo1} {base_result.repo1_score:.0f}/100 ({base_result.repo1_grade}), "
            f"{repo2} {base_result.repo2_score:.0f}/100 ({base_result.repo2_grade}). "
            f"Winner: {winner_name} on {winner_wins}/{n_dims} dimensions."
        )
        # Truncate if needed (share URL added later if --share)
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:277] + "..."

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
