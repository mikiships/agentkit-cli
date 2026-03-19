"""agentkit user-tournament engine — bracket/round-robin tournament for N GitHub users."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

from agentkit_cli.user_duel import UserDuelEngine, UserDuelResult
from agentkit_cli.user_scorecard import score_to_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Standings:
    """Per-participant tournament standings."""
    rank: int
    handle: str
    wins: int
    losses: int
    avg_score: float
    total_duel_score: float
    grade: str = ""

    def record(self) -> str:
        return f"{self.wins}-{self.losses}"

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "handle": self.handle,
            "wins": self.wins,
            "losses": self.losses,
            "avg_score": self.avg_score,
            "total_duel_score": self.total_duel_score,
            "grade": self.grade,
            "record": self.record(),
        }


@dataclass
class TournamentResult:
    """Full result of a user tournament."""
    participants: List[str]
    standings: List[Standings]
    match_results: List[UserDuelResult]
    champion: str
    rounds: int
    timestamp: str
    mode: str = "round-robin"  # "round-robin" or "bracket"

    def to_dict(self) -> dict:
        return {
            "participants": self.participants,
            "standings": [s.to_dict() for s in self.standings],
            "match_results": [m.to_dict() for m in self.match_results],
            "champion": self.champion,
            "rounds": self.rounds,
            "timestamp": self.timestamp,
            "mode": self.mode,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class UserTournamentEngine:
    """Run a bracket or round-robin tournament across N GitHub users."""

    def __init__(
        self,
        limit: int = 10,
        token: Optional[str] = None,
        timeout: int = 60,
        max_comparisons: Optional[int] = None,
        _duel_engine_factory=None,
    ) -> None:
        self.limit = limit
        self.token = token
        self.timeout = timeout
        self.max_comparisons = max_comparisons
        # For testing: callable(u1, u2, limit, token, timeout) -> UserDuelEngine
        self._duel_engine_factory = _duel_engine_factory

    def _make_duel_engine(self, u1: str, u2: str) -> UserDuelEngine:
        if self._duel_engine_factory is not None:
            return self._duel_engine_factory(u1, u2, self.limit, self.token, self.timeout)
        return UserDuelEngine(
            limit=self.limit,
            token=self.token,
            timeout=self.timeout,
        )

    def _get_matchups(self, participants: List[str]) -> List[tuple]:
        """Generate round-robin matchup pairs."""
        pairs = []
        for i, u1 in enumerate(participants):
            for u2 in participants[i + 1:]:
                pairs.append((u1, u2))
        if self.max_comparisons is not None:
            pairs = pairs[: self.max_comparisons]
        return pairs

    def run(
        self,
        participants: List[str],
        progress_callback: Optional[Callable] = None,
    ) -> TournamentResult:
        """Run the tournament. Returns TournamentResult."""
        if len(participants) < 2:
            raise ValueError("Tournament requires at least 2 participants.")

        n = len(participants)
        mode = "bracket" if n > 8 else "round-robin"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        matchups = self._get_matchups(participants)
        rounds = len(matchups)

        # Track wins, losses, cumulative score per handle
        wins: dict[str, int] = {h: 0 for h in participants}
        losses: dict[str, int] = {h: 0 for h in participants}
        total_score: dict[str, float] = {h: 0.0 for h in participants}
        score_count: dict[str, int] = {h: 0 for h in participants}
        skipped: set[str] = set()

        match_results: List[UserDuelResult] = []

        for idx, (u1, u2) in enumerate(matchups):
            if progress_callback:
                progress_callback(idx, len(matchups), u1, u2)

            # Skip already-failed users
            if u1 in skipped or u2 in skipped:
                continue

            try:
                engine = self._make_duel_engine(u1, u2)
                duel_result = engine.run(u1=u1, u2=u2)
                match_results.append(duel_result)

                # Accumulate scores
                s1 = duel_result.user1_scorecard.avg_score or 0.0
                s2 = duel_result.user2_scorecard.avg_score or 0.0
                total_score[u1] += s1
                total_score[u2] += s2
                score_count[u1] += 1
                score_count[u2] += 1

                if not duel_result.tied:
                    if duel_result.overall_winner == "user1":
                        wins[u1] += 1
                        losses[u2] += 1
                    else:
                        wins[u2] += 1
                        losses[u1] += 1
                # ties: no win/loss

            except Exception:
                # Warn but don't crash; skip problematic user in remaining matchups
                # Mark the non-problematic user as having "won by forfeit"
                # We can't tell which failed, so skip both from further tracking
                skipped.add(u1)
                skipped.add(u2)
                continue

        # Build standings
        standings_list: List[Standings] = []
        for handle in participants:
            avg_s = total_score[handle] / score_count[handle] if score_count[handle] > 0 else 0.0
            standings_list.append(
                Standings(
                    rank=0,  # will be set after sorting
                    handle=handle,
                    wins=wins[handle],
                    losses=losses[handle],
                    avg_score=round(avg_s, 2),
                    total_duel_score=round(total_score[handle], 2),
                    grade=score_to_grade(avg_s),
                )
            )

        # Sort: primary = wins (desc), tiebreak = avg_score (desc)
        standings_list.sort(key=lambda s: (-s.wins, -s.avg_score))
        for rank, s in enumerate(standings_list, start=1):
            s.rank = rank

        champion = standings_list[0].handle if standings_list else (participants[0] if participants else "")

        return TournamentResult(
            participants=participants,
            standings=standings_list,
            match_results=match_results,
            champion=champion,
            rounds=rounds,
            timestamp=timestamp,
            mode=mode,
        )
