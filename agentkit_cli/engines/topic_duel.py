"""agentkit topic-duel engine — head-to-head comparison of two GitHub topics by agent-readiness."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from agentkit_cli.topic_rank import (
    TopicRankEngine,
    TopicRankEntry,
    TopicRankResult,
    search_topic_repos,
)
from agentkit_cli.user_scorecard import score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TopicDuelDimension:
    """Winner comparison for a single metric dimension."""

    name: str  # e.g. "avg_score", "top_score", "grade_A_count"
    topic1_value: float
    topic2_value: float
    winner: str  # "topic1", "topic2", "tie"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "topic1_value": self.topic1_value,
            "topic2_value": self.topic2_value,
            "winner": self.winner,
        }


@dataclass
class TopicDuelResult:
    """Full result of a topic-duel comparison."""

    topic1: str
    topic2: str
    topic1_result: TopicRankResult
    topic2_result: TopicRankResult
    dimensions: List[TopicDuelDimension] = field(default_factory=list)
    overall_winner: str = "tie"  # "topic1", "topic2", "tie"
    topic1_avg_score: float = 0.0
    topic2_avg_score: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "topic1": self.topic1,
            "topic2": self.topic2,
            "topic1_result": self.topic1_result.to_dict(),
            "topic2_result": self.topic2_result.to_dict(),
            "dimensions": [d.to_dict() for d in self.dimensions],
            "overall_winner": self.overall_winner,
            "topic1_avg_score": self.topic1_avg_score,
            "topic2_avg_score": self.topic2_avg_score,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _avg_score(entries: List[TopicRankEntry]) -> float:
    if not entries:
        return 0.0
    return round(sum(e.score for e in entries) / len(entries), 2)


def _top_score(entries: List[TopicRankEntry]) -> float:
    if not entries:
        return 0.0
    return max(e.score for e in entries)


def _grade_a_count(entries: List[TopicRankEntry]) -> int:
    return sum(1 for e in entries if e.grade == "A")


def _compute_dimensions(
    topic1: str,
    topic2: str,
    entries1: List[TopicRankEntry],
    entries2: List[TopicRankEntry],
) -> List[TopicDuelDimension]:
    """Compute per-dimension winners between the two topic results."""
    dims: List[TopicDuelDimension] = []

    def _dim(name: str, v1: float, v2: float) -> TopicDuelDimension:
        if v1 > v2 + 0.5:
            winner = "topic1"
        elif v2 > v1 + 0.5:
            winner = "topic2"
        else:
            winner = "tie"
        return TopicDuelDimension(name=name, topic1_value=v1, topic2_value=v2, winner=winner)

    dims.append(_dim("avg_score", _avg_score(entries1), _avg_score(entries2)))
    dims.append(_dim("top_score", _top_score(entries1), _top_score(entries2)))
    dims.append(_dim("grade_a_count", float(_grade_a_count(entries1)), float(_grade_a_count(entries2))))
    dims.append(_dim("repo_count", float(len(entries1)), float(len(entries2))))
    return dims


def _overall_winner(
    topic1_avg: float,
    topic2_avg: float,
    dims: List[TopicDuelDimension],
) -> str:
    """Determine overall winner from avg_score (tie-break: most dimension wins)."""
    delta = topic1_avg - topic2_avg
    if abs(delta) >= 1.0:
        return "topic1" if delta > 0 else "topic2"

    # tie-break: count dimension wins
    w1 = sum(1 for d in dims if d.winner == "topic1")
    w2 = sum(1 for d in dims if d.winner == "topic2")
    if w1 > w2:
        return "topic1"
    if w2 > w1:
        return "topic2"
    return "tie"


class TopicDuelEngine:
    """Compare two GitHub topics' agent-readiness by scoring their top repos."""

    def __init__(
        self,
        topic1: str,
        topic2: str,
        repos_per_topic: int = 5,
        token: Optional[str] = None,
        timeout: int = 60,
        _engine_factory: Optional[Callable[[str, int], TopicRankEngine]] = None,
    ) -> None:
        self.topic1 = topic1.strip()
        self.topic2 = topic2.strip()
        self.repos_per_topic = max(1, min(repos_per_topic, 10))
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        # Optional override for testing: callable(topic, limit) -> TopicRankEngine
        self._engine_factory = _engine_factory

    def _make_engine(self, topic: str) -> TopicRankEngine:
        if self._engine_factory is not None:
            return self._engine_factory(topic, self.repos_per_topic)
        return TopicRankEngine(
            topic=topic,
            limit=self.repos_per_topic,
            token=self.token,
            timeout=self.timeout,
        )

    def run(
        self,
        progress_cb: Optional[Callable[[str, int, int, str], None]] = None,
    ) -> TopicDuelResult:
        """Fetch and score repos for both topics, then compare."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        engine1 = self._make_engine(self.topic1)
        engine2 = self._make_engine(self.topic2)

        def _cb1(idx: int, total: int, repo_name: str) -> None:
            if progress_cb:
                progress_cb(self.topic1, idx, total, repo_name)

        def _cb2(idx: int, total: int, repo_name: str) -> None:
            if progress_cb:
                progress_cb(self.topic2, idx, total, repo_name)

        result1 = engine1.run(progress_cb=_cb1)
        result2 = engine2.run(progress_cb=_cb2)

        avg1 = _avg_score(result1.entries)
        avg2 = _avg_score(result2.entries)

        dims = _compute_dimensions(
            self.topic1, self.topic2, result1.entries, result2.entries
        )
        winner = _overall_winner(avg1, avg2, dims)

        return TopicDuelResult(
            topic1=self.topic1,
            topic2=self.topic2,
            topic1_result=result1,
            topic2_result=result2,
            dimensions=dims,
            overall_winner=winner,
            topic1_avg_score=avg1,
            topic2_avg_score=avg2,
            timestamp=timestamp,
        )
