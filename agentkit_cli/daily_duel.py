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
    "cli-tools": [
        "the best CLI tools write docs agents can consume directly",
        "top CLI libraries know agents parse their help output too",
        "leading CLI frameworks make argument parsing transparent for agents",
    ],
    "legacy-vs-modern": [
        "modern libs invest in agent-readiness; legacy ones lag behind",
        "documentation debt is real — newer projects know it",
        "the doc gap between old and new is widening fast",
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


# ---------------------------------------------------------------------------
# Diff-tier helpers and tweet templates
# ---------------------------------------------------------------------------

def _diff_tier(score_diff: float) -> str:
    """Classify score difference into 'large', 'medium', or 'small'."""
    if score_diff > 30:
        return "large"
    elif score_diff >= 15:
        return "medium"
    else:
        return "small"


_LARGE_DIFF_TEMPLATES = [
    (
        "{winner} ({ws}/100) crushes {loser} ({ls}/100) in agent-readiness: "
        "wins {ww}/{nd} dimensions. The doc gap between modern and legacy is real."
    ),
    (
        "{winner} dominates {loser} {ws} vs {ls}/100 — a {diff}-point gap across {nd} "
        "agent-readiness dimensions. This is what documentation debt looks like."
    ),
    (
        "Agent-readiness gap: {winner} scores {ws}/100, {loser} scores {ls}/100. "
        "{winner} wins {ww}/{nd} dimensions by {diff} points. Legacy libs fall behind."
    ),
    (
        "{winner} ({ws}/100) vs {loser} ({ls}/100): {diff}-point gap, {ww}/{nd} "
        "dimensions won. If you're handing a repo to an AI agent, pick the one "
        "that documents itself."
    ),
]

_MEDIUM_DIFF_TEMPLATES = [
    (
        "{winner} ({ws}/100) beats {loser} ({ls}/100) across {ww}/{nd} "
        "agent-readiness dimensions. Which one would you hand to an AI agent?"
    ),
    (
        "Agent-readiness: {winner} {ws}/100 vs {loser} {ls}/100 — a {diff}-point "
        "gap. {winner} wins {ww}/{nd} dimensions. The difference is in the docs."
    ),
    (
        "{winner} edges out {loser} by {diff} points ({ws} vs {ls}/100) across "
        "{nd} agent-readiness dimensions. Clear winner, clear reason: documentation."
    ),
    (
        "{winner} ({ws}/100) outpaces {loser} ({ls}/100) on {ww}/{nd} dimensions. "
        "A {diff}-point gap that shows up the moment an agent tries to use these repos."
    ),
]


def _pick_template(templates: list[str], seed: str) -> str:
    """Deterministically pick a template from a list using a seed."""
    digest = hashlib.sha256(seed.encode()).hexdigest()
    return templates[int(digest, 16) % len(templates)]


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
        diff = int(score_diff)
        tweet_text = (
            f"{winner_repo} ({winner_score:.0f}/100) vs {loser_repo} ({loser_score:.0f}/100): "
            f"extremely close. {winner_repo.split('/')[-1].capitalize()} edges "
            f"{loser_repo.split('/')[-1].capitalize()} by {diff} point{'s' if diff != 1 else ''} "
            f"across {n_dims} agent-readiness dimensions."
        )
    else:
        # Clear winner: use tier-appropriate template
        winner_repo = repo1 if winner == "repo1" else repo2
        loser_repo = repo2 if winner == "repo1" else repo1
        winner_score = repo1_score if winner == "repo1" else repo2_score
        loser_score = repo2_score if winner == "repo1" else repo1_score
        diff = int(score_diff)
        tier = _diff_tier(score_diff)

        if tier == "large":
            tmpl = _pick_template(_LARGE_DIFF_TEMPLATES, seed)
        else:
            tmpl = _pick_template(_MEDIUM_DIFF_TEMPLATES, seed)

        # Short repo names for tweet brevity
        winner_short = winner_repo.split("/")[-1]
        loser_short = loser_repo.split("/")[-1]

        tweet_text = tmpl.format(
            winner=winner_short,
            loser=loser_short,
            ws=int(winner_score),
            ls=int(loser_score),
            ww=winner_wins,
            nd=n_dims,
            diff=diff,
        )

    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."

    return tweet_text


# ---------------------------------------------------------------------------
# Preset repo pairs
# Each tuple: (repo1, repo2, category, narrative_type)
# narrative_type: "asymmetric" | "balanced"
# ---------------------------------------------------------------------------

# Asymmetric pairs: one repo clearly has stronger agent-readiness docs
ASYMMETRIC_PAIRS: list[Tuple[str, str, str, str]] = [
    # Web frameworks: modern vs legacy
    ("tiangolo/fastapi", "bottlepy/bottle", "web-frameworks", "asymmetric"),
    ("tiangolo/fastapi", "cherrypy/cherrypy", "web-frameworks", "asymmetric"),
    ("django/django", "webpy/webpy", "web-frameworks", "asymmetric"),
    ("encode/starlette", "pallets/werkzeug", "web-frameworks", "asymmetric"),
    # HTTP clients: modern vs stdlib
    ("encode/httpx", "python/cpython", "http-clients", "asymmetric"),  # httpx vs urllib
    ("psf/requests", "urllib3/urllib3", "http-clients", "asymmetric"),
    # CLI tools: modern vs legacy
    ("pallets/click", "python/cpython", "cli-tools", "asymmetric"),  # click vs argparse
    ("tiangolo/typer", "pallets/click", "cli-tools", "asymmetric"),
    # Linting/formatting: modern vs legacy
    ("astral-sh/ruff", "PyCQA/pylint", "devtools", "asymmetric"),
    ("astral-sh/ruff", "PyCQA/pycodestyle", "devtools", "asymmetric"),
    ("psf/black", "PyCQA/autopep8", "devtools", "asymmetric"),
    # Async/networking: modern vs legacy
    ("encode/uvicorn", "tornadoweb/tornado", "async-networking", "asymmetric"),
    ("encode/uvicorn", "cherrypy/cherrypy", "async-networking", "asymmetric"),
    # Databases: modern async vs legacy
    ("MagicStack/asyncpg", "psycopg/psycopg2", "databases", "asymmetric"),
    ("aio-libs/aiopg", "psycopg/psycopg2", "databases", "asymmetric"),
    ("sqlalchemy/sqlalchemy", "coleifer/peewee", "databases", "asymmetric"),
    # Testing: modern vs legacy
    ("pytest-dev/pytest", "nose-devs/nose", "testing", "asymmetric"),
    ("HypothesisWorks/hypothesis", "nose-devs/nose", "testing", "asymmetric"),
    # JS frameworks: modern vs legacy
    ("facebook/react", "jashkenas/backbone", "js-frameworks", "asymmetric"),
    ("vuejs/vue", "jashkenas/backbone", "js-frameworks", "asymmetric"),
    ("vercel/next.js", "emberjs/ember.js", "js-frameworks", "asymmetric"),
    # ML/AI: new SDKs vs legacy
    ("openai/openai-python", "openai/openai-python", "ml-ai", "asymmetric"),  # placeholder — overridden below
    ("anthropics/anthropic-sdk-python", "huggingface/transformers", "ml-ai", "asymmetric"),
    # Package managers/build tools
    ("astral-sh/uv", "pypa/setuptools", "devtools", "asymmetric"),
    ("astral-sh/uv", "pypa/pip", "devtools", "asymmetric"),
]

# Remove the placeholder duplicate
ASYMMETRIC_PAIRS = [p for p in ASYMMETRIC_PAIRS if not (p[0] == "openai/openai-python" and p[1] == "openai/openai-python")]

# Re-add a real asymmetric ML pair
ASYMMETRIC_PAIRS.append(("openai/openai-python", "openai/tiktoken", "ml-ai", "asymmetric"))

# Balanced pairs: both repos have strong agent-readiness docs
BALANCED_PAIRS: list[Tuple[str, str, str, str]] = [
    # Web frameworks
    ("tiangolo/fastapi", "pallets/flask", "web-frameworks", "balanced"),
    ("django/django", "tiangolo/fastapi", "web-frameworks", "balanced"),
    ("tiangolo/fastapi", "encode/starlette", "web-frameworks", "balanced"),
    ("expressjs/express", "fastify/fastify", "web-frameworks", "balanced"),
    # HTTP clients
    ("encode/httpx", "psf/requests", "http-clients", "balanced"),
    ("urllib3/urllib3", "encode/httpx", "http-clients", "balanced"),
    # ML/AI
    ("huggingface/transformers", "openai/openai-python", "ml-ai", "balanced"),
    ("langchain-ai/langchain", "microsoft/semantic-kernel", "ml-ai", "balanced"),
    ("pytorch/pytorch", "google/jax", "ml-ai", "balanced"),
    ("openai/openai-python", "anthropics/anthropic-sdk-python", "ml-ai", "balanced"),
    # Testing
    ("pytest-dev/pytest", "robotframework/robotframework", "testing", "balanced"),
    ("pytest-dev/pytest", "HypothesisWorks/hypothesis", "testing", "balanced"),
    # Async/networking
    ("python-trio/trio", "encode/uvicorn", "async-networking", "balanced"),
    ("aio-libs/aiohttp", "encode/uvicorn", "async-networking", "balanced"),
    # Databases
    ("sqlalchemy/sqlalchemy", "mongodb/motor", "databases", "balanced"),
    ("tortoise/tortoise-orm", "sqlalchemy/sqlalchemy", "databases", "balanced"),
    # JS/TS frameworks
    ("vercel/next.js", "remix-run/remix", "js-frameworks", "balanced"),
    ("facebook/react", "vuejs/vue", "js-frameworks", "balanced"),
    # DevTools
    ("astral-sh/ruff", "PyCQA/flake8", "devtools", "balanced"),
    ("astral-sh/ruff", "psf/black", "devtools", "balanced"),
    ("pre-commit/pre-commit", "astral-sh/ruff", "devtools", "balanced"),
    ("astral-sh/uv", "conda/conda", "devtools", "balanced"),
]

# Combined list (maintains backward-compatible 3-tuple interface via property below)
PRESET_PAIRS: list[Tuple[str, str, str, str]] = ASYMMETRIC_PAIRS + BALANCED_PAIRS


# ---------------------------------------------------------------------------
# DailyDuelResult
# ---------------------------------------------------------------------------

@dataclass
class DailyDuelResult(RepoDuelResult):
    """Extends RepoDuelResult with daily-duel-specific fields."""
    tweet_text: str = ""
    pair_category: str = ""
    seed: str = ""
    narrative_type: str = ""

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["tweet_text"] = self.tweet_text
        d["pair_category"] = self.pair_category
        d["seed"] = self.seed
        d["narrative_type"] = self.narrative_type
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
        existing: bool = True,
    ) -> None:
        self.token = token
        self.timeout = timeout
        self._analyze_factory = _analyze_factory
        # existing=True by default: skip agentmd generation, score what's already there
        self.existing = existing

    def pick_pair(self, seed: Optional[str] = None) -> Tuple[str, str, str]:
        """Deterministically pick a (repo1, repo2, category) triple from presets.

        Default seed = today's date YYYY-MM-DD so same pair runs all day.
        Custom seed = any string for ad-hoc picks.

        Returns a 3-tuple for backward compatibility; use pick_pair_full for 4-tuple.
        """
        effective_seed = seed or date.today().isoformat()
        digest = hashlib.sha256(effective_seed.encode()).hexdigest()
        index = int(digest, 16) % len(PRESET_PAIRS)
        r1, r2, cat, _nt = PRESET_PAIRS[index]
        return (r1, r2, cat)

    def pick_pair_full(self, seed: Optional[str] = None) -> Tuple[str, str, str, str]:
        """Return the full 4-tuple (repo1, repo2, category, narrative_type)."""
        effective_seed = seed or date.today().isoformat()
        digest = hashlib.sha256(effective_seed.encode()).hexdigest()
        index = int(digest, 16) % len(PRESET_PAIRS)
        return PRESET_PAIRS[index]

    def run_daily_duel(self, seed: Optional[str] = None, deep: bool = False) -> DailyDuelResult:
        """Pick a pair and run a duel, returning a DailyDuelResult."""
        effective_seed = seed or date.today().isoformat()
        repo1, repo2, category, narrative_type = self.pick_pair_full(seed)

        engine = RepoDuelEngine(
            token=self.token,
            timeout=self.timeout,
            _analyze_factory=self._analyze_factory,
            existing=self.existing,
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
            narrative_type=narrative_type,
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
            repo1, repo2, category, narrative_type = self.pick_pair_full(seed)
            schedule.append({
                "date": seed,
                "repo1": repo1,
                "repo2": repo2,
                "category": category,
                "narrative_type": narrative_type,
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
