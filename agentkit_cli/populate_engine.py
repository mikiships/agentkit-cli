"""agentkit populate engine — fetch top GitHub repos by topic and score them."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from agentkit_cli.history import HistoryDB
from agentkit_cli.topic_rank import search_topic_repos
from agentkit_cli.user_scorecard import score_to_grade


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class PopulateEntry:
    """Result of populating a single repo."""
    repo: str           # owner/repo
    topic: str
    score: Optional[float]
    grade: str
    skipped: bool = False
    skip_reason: str = ""
    elapsed: float = 0.0

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "topic": self.topic,
            "score": self.score,
            "grade": self.grade,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "elapsed": round(self.elapsed, 2),
        }


@dataclass
class PopulateTopicResult:
    """Aggregated result for a single topic."""
    topic: str
    entries: List[PopulateEntry] = field(default_factory=list)
    elapsed: float = 0.0

    @property
    def repo_count(self) -> int:
        return len([e for e in self.entries if not e.skipped])

    @property
    def avg_score(self) -> float:
        scores = [e.score for e in self.entries if not e.skipped and e.score is not None]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    @property
    def skipped_count(self) -> int:
        return len([e for e in self.entries if e.skipped])

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "repo_count": self.repo_count,
            "avg_score": self.avg_score,
            "skipped_count": self.skipped_count,
            "elapsed": round(self.elapsed, 2),
            "entries": [e.to_dict() for e in self.entries],
        }


@dataclass
class PopulateResult:
    """Full result of a populate run."""
    topics: List[str]
    topic_results: List[PopulateTopicResult] = field(default_factory=list)
    total_elapsed: float = 0.0
    dry_run: bool = False

    @property
    def total_scored(self) -> int:
        return sum(r.repo_count for r in self.topic_results)

    @property
    def total_skipped(self) -> int:
        return sum(r.skipped_count for r in self.topic_results)

    def to_dict(self) -> dict:
        return {
            "topics": self.topics,
            "topic_results": [r.to_dict() for r in self.topic_results],
            "total_scored": self.total_scored,
            "total_skipped": self.total_skipped,
            "total_elapsed": round(self.total_elapsed, 2),
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class PopulateEngine:
    """Fetch top repos by topic, score each via `agentkit analyze`, store in DB."""

    DEFAULT_TOPICS = ["python", "typescript", "rust", "go"]
    DEFAULT_LIMIT = 10
    FRESHNESS_SECONDS = 86400  # 24 hours

    def __init__(
        self,
        db_path: Optional[Path] = None,
        db: Optional[HistoryDB] = None,
        token: Optional[str] = None,
        _analyze_fn: Optional[Callable[[str], Optional[float]]] = None,
        _search_fn: Optional[Callable[[str, int, Optional[str], Optional[str]], List[dict]]] = None,
    ) -> None:
        self.db = db if db is not None else HistoryDB(db_path=db_path)
        self.token = token
        # Injectable for testing
        self._analyze_fn = _analyze_fn
        self._search_fn = _search_fn or search_topic_repos

    def _is_fresh(self, repo: str) -> bool:
        """Return True if repo has a history entry younger than FRESHNESS_SECONDS."""
        history = self.db.get_history(project=repo, limit=1)
        if not history:
            return False
        try:
            last_ts = datetime.fromisoformat(history[0]["ts"].replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - last_ts).total_seconds()
            return age < self.FRESHNESS_SECONDS
        except (KeyError, ValueError, TypeError):
            return False

    def _score_repo(self, repo: str) -> Optional[float]:
        """Run `agentkit analyze github:owner/repo` and return score."""
        if self._analyze_fn is not None:
            return self._analyze_fn(repo)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "agentkit_cli", "analyze", f"github:{repo}", "--json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("score")
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            pass
        return None

    def populate(
        self,
        topics: Optional[List[str]] = None,
        limit: int = DEFAULT_LIMIT,
        force_refresh: bool = False,
        dry_run: bool = False,
        quiet: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> PopulateResult:
        """
        Fetch top repos for each topic, score and store in DB.

        Args:
            topics: List of GitHub topics. Defaults to DEFAULT_TOPICS.
            limit: Max repos per topic.
            force_refresh: Re-score even if history is fresh.
            dry_run: Show what would be scored without scoring.
            quiet: Suppress all output.
            progress_callback: Called as (repo_name, current, total) for each repo.

        Returns:
            PopulateResult with per-topic aggregates.
        """
        resolved_topics = topics if topics is not None else self.DEFAULT_TOPICS
        start = time.monotonic()
        result = PopulateResult(topics=resolved_topics, dry_run=dry_run)

        for topic in resolved_topics:
            topic_start = time.monotonic()
            topic_result = PopulateTopicResult(topic=topic)

            try:
                repos = self._search_fn(topic, limit, None, self.token)
            except Exception:
                repos = []

            total = len(repos)
            for idx, repo_data in enumerate(repos):
                repo_name = repo_data.get("full_name", "")
                if not repo_name:
                    continue

                entry: PopulateEntry
                if not force_refresh and self._is_fresh(repo_name):
                    entry = PopulateEntry(
                        repo=repo_name,
                        topic=topic,
                        score=None,
                        grade="",
                        skipped=True,
                        skip_reason="fresh",
                    )
                elif dry_run:
                    entry = PopulateEntry(
                        repo=repo_name,
                        topic=topic,
                        score=None,
                        grade="",
                        skipped=True,
                        skip_reason="dry_run",
                    )
                else:
                    if progress_callback:
                        progress_callback(repo_name, idx + 1, total)
                    t0 = time.monotonic()
                    score = self._score_repo(repo_name)
                    elapsed = time.monotonic() - t0
                    grade = score_to_grade(score) if score is not None else ""
                    if score is not None:
                        self.db.record_run(
                            project=repo_name,
                            tool="agentkit_populate",
                            score=score,
                            details=json.dumps({"topic": topic, "via": "populate"}),
                        )
                    entry = PopulateEntry(
                        repo=repo_name,
                        topic=topic,
                        score=score,
                        grade=grade,
                        skipped=False,
                        elapsed=elapsed,
                    )

                topic_result.entries.append(entry)

            topic_result.elapsed = time.monotonic() - topic_start
            result.topic_results.append(topic_result)

        result.total_elapsed = time.monotonic() - start
        return result
