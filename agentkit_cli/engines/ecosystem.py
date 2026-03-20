"""agentkit ecosystem engine — macro "State of AI Agent Readiness" across language ecosystems."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from agentkit_cli.engines.topic_league import TopicLeagueEngine, TopicLeagueResult, LeagueResult


# ---------------------------------------------------------------------------
# Language emoji map
# ---------------------------------------------------------------------------

LANG_EMOJI: Dict[str, str] = {
    "python": "🐍",
    "typescript": "📘",
    "javascript": "🟨",
    "go": "🐹",
    "rust": "🦀",
    "java": "☕",
    "kotlin": "🎯",
    "swift": "🍎",
    "ruby": "💎",
    "php": "🐘",
    "scala": "⚡",
    "dart": "🎯",
    "elixir": "💧",
    "csharp": "🔷",
    "cpp": "⚙️",
    "haskell": "λ",
}


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS: Dict[str, List[str]] = {
    "default": ["python", "typescript", "rust", "go", "java"],
    "extended": [
        "python", "typescript", "rust", "go", "java",
        "kotlin", "swift", "ruby", "php", "scala", "dart", "elixir",
    ],
}


def get_preset_topics(preset: str) -> List[str]:
    """Return topic list for a preset name. Raises ValueError for unknown preset."""
    if preset not in PRESETS:
        choices = ", ".join(sorted(PRESETS.keys()))
        raise ValueError(f"Unknown preset '{preset}'. Choices: {choices}")
    return list(PRESETS[preset])


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class EcosystemResult:
    """Full result of an ecosystem scan."""

    preset: str
    topics: List[str]
    standings: List[LeagueResult]
    league_result: TopicLeagueResult
    timestamp: str = ""

    # convenience
    @property
    def winner(self) -> Optional[LeagueResult]:
        return self.standings[0] if self.standings else None

    @property
    def total_repos(self) -> int:
        return sum(s.repo_count for s in self.standings)

    def to_dict(self) -> dict:
        return {
            "preset": self.preset,
            "topics": self.topics,
            "standings": [s.to_dict() for s in self.standings],
            "winner": self.winner.to_dict() if self.winner else None,
            "total_repos": self.total_repos,
            "timestamp": self.timestamp,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class EcosystemEngine:
    """Macro 'State of AI Agent Readiness' scan across language/tech ecosystems.

    Reuses TopicLeagueEngine internally — no duplicated scoring logic.
    """

    MIN_TOPICS = 2
    MAX_REPOS_PER_TOPIC = 10

    def __init__(
        self,
        preset: str = "default",
        topics: Optional[List[str]] = None,
        repos_per_topic: int = 3,
        parallel: bool = True,
        token: Optional[str] = None,
        timeout: int = 60,
        _league_factory: Optional[Callable[..., TopicLeagueEngine]] = None,
    ) -> None:
        # Resolve topics
        if preset == "custom":
            if not topics or len(topics) < self.MIN_TOPICS:
                raise ValueError(
                    f"Custom preset requires at least {self.MIN_TOPICS} topics via --topics."
                )
            resolved_topics = [t.strip() for t in topics if t.strip()]
        else:
            resolved_topics = get_preset_topics(preset)
            if topics:
                # User-supplied extra topics merged into preset
                resolved_topics = list(dict.fromkeys(resolved_topics + [t.strip() for t in topics if t.strip()]))

        if len(resolved_topics) < self.MIN_TOPICS:
            raise ValueError(
                f"Ecosystem requires at least {self.MIN_TOPICS} topics, got {len(resolved_topics)}."
            )

        self.preset = preset
        self.topics = resolved_topics
        self.repos_per_topic = max(1, min(repos_per_topic, self.MAX_REPOS_PER_TOPIC))
        self.parallel = parallel
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.timeout = timeout
        self._league_factory = _league_factory

    def _make_league_engine(self) -> TopicLeagueEngine:
        if self._league_factory is not None:
            return self._league_factory(
                topics=self.topics,
                repos_per_topic=self.repos_per_topic,
                parallel=self.parallel,
                token=self.token,
                timeout=self.timeout,
            )
        return TopicLeagueEngine(
            topics=self.topics,
            repos_per_topic=self.repos_per_topic,
            parallel=self.parallel,
            token=self.token,
            timeout=self.timeout,
        )

    def run(
        self,
        progress_cb: Optional[Callable[[str, int, int, str], None]] = None,
    ) -> EcosystemResult:
        """Run the ecosystem scan and return an EcosystemResult."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        engine = self._make_league_engine()
        league_result = engine.run(progress_cb=progress_cb)

        return EcosystemResult(
            preset=self.preset,
            topics=self.topics,
            standings=league_result.standings,
            league_result=league_result,
            timestamp=timestamp,
        )
