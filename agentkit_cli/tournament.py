"""Tournament engine for `agentkit tournament` — round-robin bracket."""
from __future__ import annotations

import concurrent.futures
import itertools
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from agentkit_cli.duel import DuelResult, run_duel

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class StandingEntry:
    repo: str
    wins: int
    losses: int
    avg_score: float
    rank: int = 0


@dataclass
class TournamentResult:
    repos: list[str]
    rounds: list[list[DuelResult]]
    standings: list[StandingEntry]
    winner: str
    total_duels: int
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "repos": self.repos,
            "rounds": [
                [d.to_dict() for d in round_duels]
                for round_duels in self.rounds
            ],
            "standings": [
                {
                    "repo": s.repo,
                    "wins": s.wins,
                    "losses": s.losses,
                    "avg_score": s.avg_score,
                    "rank": s.rank,
                }
                for s in self.standings
            ],
            "winner": self.winner,
            "total_duels": self.total_duels,
            "timestamp": self.timestamp,
        }


def _score_for_repo(repo: str, duels: list[DuelResult]) -> float:
    """Compute average composite score for a repo across all duels it participated in."""
    scores: list[float] = []
    for d in duels:
        if d.left_target == repo and d.left_score is not None:
            scores.append(d.left_score)
        elif d.right_target == repo and d.right_score is not None:
            scores.append(d.right_score)
    return sum(scores) / len(scores) if scores else 0.0


def _build_standings(repos: list[str], all_duels: list[DuelResult]) -> list[StandingEntry]:
    """Build ranked standings from all duel results."""
    wins: dict[str, int] = {r: 0 for r in repos}
    losses: dict[str, int] = {r: 0 for r in repos}

    for d in all_duels:
        if d.winner == "left":
            wins[d.left_target] = wins.get(d.left_target, 0) + 1
            losses[d.right_target] = losses.get(d.right_target, 0) + 1
        elif d.winner == "right":
            wins[d.right_target] = wins.get(d.right_target, 0) + 1
            losses[d.left_target] = losses.get(d.left_target, 0) + 1
        elif d.winner == "tie":
            # Ties count as half win, half loss (but stored as int we skip both)
            pass
        # error = no points for either

    entries = [
        StandingEntry(
            repo=repo,
            wins=wins.get(repo, 0),
            losses=losses.get(repo, 0),
            avg_score=_score_for_repo(repo, all_duels),
        )
        for repo in repos
    ]

    # Sort: wins desc, then avg_score desc as tiebreak
    entries.sort(key=lambda e: (e.wins, e.avg_score), reverse=True)
    for i, entry in enumerate(entries, start=1):
        entry.rank = i

    return entries


def run_tournament(
    repos: list[str],
    parallel: bool = True,
    keep: bool = False,
    timeout: int = 120,
    quiet: bool = False,
) -> TournamentResult:
    """Run all round-robin pairings. Reuse duel engine. Return full results."""
    if len(repos) < 4:
        raise ValueError(f"Tournament requires at least 4 repos, got {len(repos)}")
    if len(repos) > 16:
        raise ValueError(f"Tournament supports at most 16 repos, got {len(repos)}")

    pairings = list(itertools.combinations(repos, 2))
    total = len(pairings)
    all_duels: list[DuelResult] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def _run_pairing(pair: tuple[str, str]) -> DuelResult:
        r1, r2 = pair
        label = f"{r1.split('/')[-1]} vs {r2.split('/')[-1]}"
        try:
            return run_duel(r1, r2, keep=keep, timeout=timeout)
        except Exception as exc:
            logger.warning("Pairing %s failed: %s", label, exc)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            return DuelResult(
                left_target=r1,
                right_target=r2,
                left_score=None,
                right_score=None,
                left_breakdown={},
                right_breakdown={},
                winner="error",
                delta=None,
                timestamp=ts,
                left_error=str(exc),
                right_error=None,
                left_repo_name=r1.split("/")[-1],
                right_repo_name=r2.split("/")[-1],
            )

    if parallel:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            disable=quiet,
        ) as progress:
            task = progress.add_task(f"Running {total} duels...", total=total)
            completed = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, total)) as executor:
                future_to_pair = {executor.submit(_run_pairing, p): p for p in pairings}
                for future in concurrent.futures.as_completed(future_to_pair):
                    pair = future_to_pair[future]
                    try:
                        result = future.result()
                    except Exception as exc:
                        logger.warning("Future failed for pair %s: %s", pair, exc)
                        r1, r2 = pair
                        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                        result = DuelResult(
                            left_target=r1,
                            right_target=r2,
                            left_score=None,
                            right_score=None,
                            left_breakdown={},
                            right_breakdown={},
                            winner="error",
                            delta=None,
                            timestamp=ts,
                            left_error=str(exc),
                            right_error=None,
                            left_repo_name=r1.split("/")[-1],
                            right_repo_name=r2.split("/")[-1],
                        )
                    all_duels.append(result)
                    completed += 1
                    r1, r2 = pair
                    progress.update(
                        task,
                        advance=1,
                        description=f"[{completed}/{total}] {r1.split('/')[-1]} vs {r2.split('/')[-1]}",
                    )
    else:
        # Sequential
        for i, pair in enumerate(pairings, start=1):
            r1, r2 = pair
            if not quiet:
                console.print(f"  [{i}/{total}] {r1.split('/')[-1]} vs {r2.split('/')[-1]}...")
            result = _run_pairing(pair)
            all_duels.append(result)

    standings = _build_standings(repos, all_duels)
    winner = standings[0].repo if standings else repos[0]

    # Group into a single "round" for the rounds field
    return TournamentResult(
        repos=repos,
        rounds=[all_duels],
        standings=standings,
        winner=winner,
        total_duels=total,
        timestamp=timestamp,
    )
