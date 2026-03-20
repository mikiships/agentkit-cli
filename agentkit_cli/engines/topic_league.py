"""agentkit topic-league engine — multi-topic standings comparison for N GitHub topics."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from agentkit_cli.topic_rank import TopicRankEngine, TopicRankEntry, TopicRankResult
from agentkit_cli.user_scorecard import score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ScoreDistribution:
    """Min/mean/max score distribution for a topic."""

    min_score: float
    mean_score: float
    max_score: float

    def to_dict(self) -> dict:
        return {
            "min": self.min_score,
            "mean": self.mean_score,
            "max": self.max_score,
        }


@dataclass
class LeagueResult:
    """Standings entry for a single topic in the league."""

    rank: int
    topic: str
    score: float  # aggregate (mean) score
    repo_count: int
    top_repo: str  # full_name of highest-scoring repo
    score_distribution: ScoreDistribution
    grade: str = ""

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "topic": self.topic,
            "score": self.score,
            "repo_count": self.repo_count,
            "top_repo": self.top_repo,
            "grade": self.grade,
            "score_distribution": self.score_distribution.to_dict(),
        }


@dataclass
class TopicLeagueResult:
    """Full result of a topic-league comparison."""

    topics: List[str]
    standings: List[LeagueResult]
    topic_results: Dict[str, TopicRankResult] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "topics": self.topics,
            "standings": [s.to_dict() for s in self.standings],
            "topic_results": {k: v.to_dict() for k, v in self.topic_results.items()},
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_distribution(entries: List[TopicRankEntry]) -> ScoreDistribution:
    if not entries:
        return ScoreDistribution(0.0, 0.0, 0.0)
    scores = [e.score for e in entries]
    return ScoreDistribution(
        min_score=round(min(scores), 2),
        mean_score=round(sum(scores) / len(scores), 2),
        max_score=round(max(scores), 2),
    )


def _build_standings(
    topic_results: Dict[str, TopicRankResult],
) -> List[LeagueResult]:
    """Rank topics by their mean score, descending."""
    raw: List[LeagueResult] = []
    for topic, result in topic_results.items():
        dist = _compute_distribution(result.entries)
        top_repo = result.entries[0].repo_full_name if result.entries else ""
        grade = score_to_grade(dist.mean_score)
        raw.append(
            LeagueResult(
                rank=0,  # filled below
                topic=topic,
                score=dist.mean_score,
                repo_count=len(result.entries),
                top_repo=top_repo,
                score_distribution=dist,
                grade=grade,
            )
        )

    raw.sort(key=lambda x: x.score, reverse=True)
    for i, lr in enumerate(raw, 1):
        lr.rank = i
    return raw


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class TopicLeagueEngine:
    """Compare N GitHub topics' agent-readiness by scoring their top repos."""

    MIN_TOPICS = 2
    MAX_TOPICS = 10
    MAX_REPOS_PER_TOPIC = 10

    def __init__(
        self,
        topics: List[str],
        repos_per_topic: int = 5,
        parallel: bool = False,
        token: Optional[str] = None,
        timeout: int = 60,
        _engine_factory: Optional[Callable[[str, int], TopicRankEngine]] = None,
    ) -> None:
        if len(topics) < self.MIN_TOPICS:
            raise ValueError(
                f"topic-league requires at least {self.MIN_TOPICS} topics, got {len(topics)}."
            )
        if len(topics) > self.MAX_TOPICS:
            raise ValueError(
                f"topic-league accepts at most {self.MAX_TOPICS} topics, got {len(topics)}."
            )
        self.topics = [t.strip() for t in topics]
        self.repos_per_topic = max(1, min(repos_per_topic, self.MAX_REPOS_PER_TOPIC))
        self.parallel = parallel
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
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

    def _run_topic(
        self,
        topic: str,
        progress_cb: Optional[Callable[[str, int, int, str], None]],
    ) -> tuple[str, TopicRankResult]:
        engine = self._make_engine(topic)

        def _inner_cb(idx: int, total: int, repo_name: str) -> None:
            if progress_cb:
                progress_cb(topic, idx, total, repo_name)

        result = engine.run(progress_cb=_inner_cb)
        return topic, result

    def run(
        self,
        progress_cb: Optional[Callable[[str, int, int, str], None]] = None,
    ) -> TopicLeagueResult:
        """Fetch and score repos for all topics, then rank into standings."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        topic_results: Dict[str, TopicRankResult] = {}

        if self.parallel:
            max_workers = min(len(self.topics), 4)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._run_topic, topic, progress_cb): topic
                    for topic in self.topics
                }
                for future in as_completed(futures):
                    topic, result = future.result()
                    topic_results[topic] = result
        else:
            for topic in self.topics:
                _, result = self._run_topic(topic, progress_cb)
                topic_results[topic] = result

        standings = _build_standings(topic_results)

        return TopicLeagueResult(
            topics=self.topics,
            standings=standings,
            topic_results=topic_results,
            timestamp=timestamp,
        )
