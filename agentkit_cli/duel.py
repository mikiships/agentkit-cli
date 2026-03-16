"""Core duel engine for `agentkit duel` — head-to-head agent-readiness comparison."""
from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agentkit_cli.analyze import AnalyzeResult, analyze_target


@dataclass
class DuelResult:
    left_target: str
    right_target: str
    left_score: Optional[float]
    right_score: Optional[float]
    left_breakdown: dict
    right_breakdown: dict
    winner: str  # "left", "right", "tie", "error"
    delta: Optional[float]
    timestamp: str
    left_error: Optional[str] = None
    right_error: Optional[str] = None
    left_repo_name: str = ""
    right_repo_name: str = ""
    left_grade: str = ""
    right_grade: str = ""

    def to_dict(self) -> dict:
        return {
            "left_target": self.left_target,
            "right_target": self.right_target,
            "left_score": self.left_score,
            "right_score": self.right_score,
            "left_breakdown": self.left_breakdown,
            "right_breakdown": self.right_breakdown,
            "winner": self.winner,
            "delta": self.delta,
            "timestamp": self.timestamp,
            "left_error": self.left_error,
            "right_error": self.right_error,
            "left_repo_name": self.left_repo_name,
            "right_repo_name": self.right_repo_name,
            "left_grade": self.left_grade,
            "right_grade": self.right_grade,
        }


def _determine_winner(
    left_score: Optional[float],
    right_score: Optional[float],
) -> tuple[str, Optional[float]]:
    """Return (winner, delta). Tie if scores within 5 points."""
    if left_score is None and right_score is None:
        return "error", None
    if left_score is None:
        return "right", None
    if right_score is None:
        return "left", None
    delta = abs(left_score - right_score)
    if delta <= 5:
        return "tie", delta
    if left_score > right_score:
        return "left", delta
    return "right", delta


def run_duel(
    target1: str,
    target2: str,
    keep: bool = False,
    timeout: int = 120,
) -> DuelResult:
    """Analyze two targets in parallel and return a DuelResult.

    Uses ThreadPoolExecutor(max_workers=2) for concurrent analysis.
    Handles failures gracefully — partial duel result if one side fails.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    left_result: Optional[AnalyzeResult] = None
    right_result: Optional[AnalyzeResult] = None
    left_error: Optional[str] = None
    right_error: Optional[str] = None

    def _analyze_left() -> AnalyzeResult:
        return analyze_target(target1, keep=keep, timeout=timeout)

    def _analyze_right() -> AnalyzeResult:
        return analyze_target(target2, keep=keep, timeout=timeout)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_left = executor.submit(_analyze_left)
        future_right = executor.submit(_analyze_right)

        try:
            left_result = future_left.result()
        except Exception as exc:
            left_error = str(exc)

        try:
            right_result = future_right.result()
        except Exception as exc:
            right_error = str(exc)

    left_score = left_result.composite_score if left_result else None
    right_score = right_result.composite_score if right_result else None
    left_breakdown = left_result.tools if left_result else {}
    right_breakdown = right_result.tools if right_result else {}
    left_repo_name = left_result.repo_name if left_result else target1.split("/")[-1]
    right_repo_name = right_result.repo_name if right_result else target2.split("/")[-1]
    left_grade = left_result.grade if left_result else ""
    right_grade = right_result.grade if right_result else ""

    winner, delta = _determine_winner(left_score, right_score)

    return DuelResult(
        left_target=target1,
        right_target=target2,
        left_score=left_score,
        right_score=right_score,
        left_breakdown=left_breakdown,
        right_breakdown=right_breakdown,
        winner=winner,
        delta=delta,
        timestamp=timestamp,
        left_error=left_error,
        right_error=right_error,
        left_repo_name=left_repo_name,
        right_repo_name=right_repo_name,
        left_grade=left_grade,
        right_grade=right_grade,
    )
