"""agentkit repo-duel engine — head-to-head agent-readiness comparison for two GitHub repos."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from agentkit_cli.composite import _compute_grade


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DimensionResult:
    """Result for a single comparison dimension."""
    name: str
    repo1_value: float
    repo2_value: float
    winner: str  # "repo1", "repo2", "draw"
    delta: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "repo1_value": self.repo1_value,
            "repo2_value": self.repo2_value,
            "winner": self.winner,
            "delta": self.delta,
        }


@dataclass
class RepoDuelResult:
    """Full result of a repo-duel comparison."""
    repo1: str
    repo2: str
    repo1_score: float
    repo2_score: float
    repo1_grade: str
    repo2_grade: str
    dimension_results: list[DimensionResult] = field(default_factory=list)
    winner: str = "draw"  # "repo1", "repo2", "draw"
    run_date: str = ""
    share_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "repo1": self.repo1,
            "repo2": self.repo2,
            "repo1_score": self.repo1_score,
            "repo2_score": self.repo2_score,
            "repo1_grade": self.repo1_grade,
            "repo2_grade": self.repo2_grade,
            "dimension_results": [dr.to_dict() for dr in self.dimension_results],
            "winner": self.winner,
            "run_date": self.run_date,
        }
        if self.share_url:
            d["share_url"] = self.share_url
        return d


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_dimension(name: str, v1: float, v2: float, higher_wins: bool = True) -> DimensionResult:
    delta = round(v1 - v2, 2)
    if abs(delta) < 0.01:
        winner = "draw"
    elif higher_wins:
        winner = "repo1" if v1 > v2 else "repo2"
    else:
        winner = "repo1" if v1 < v2 else "repo2"
    return DimensionResult(name=name, repo1_value=v1, repo2_value=v2, winner=winner, delta=delta)


def _tool_score(analyze_result, tool_name: str) -> float:
    """Extract a tool score from an AnalyzeResult.tools dict."""
    t = analyze_result.tools.get(tool_name, {})
    if isinstance(t, dict):
        return t.get("score") or 0.0
    return 0.0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RepoDuelEngine:
    """Compare two GitHub repos' agent-readiness scores."""

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: int = 120,
        _analyze_factory=None,
        existing: bool = False,
    ) -> None:
        self.token = token
        self.timeout = timeout
        # Test override: callable(target, timeout) -> AnalyzeResult
        self._analyze_factory = _analyze_factory
        self.existing = existing

    def _analyze(self, target: str):
        if self._analyze_factory is not None:
            return self._analyze_factory(target, self.timeout)
        if self.existing:
            from agentkit_cli.analyze import analyze_existing
            return analyze_existing(target, timeout=self.timeout)
        from agentkit_cli.analyze import analyze_target
        return analyze_target(target, timeout=self.timeout)

    def run_duel(self, repo1: str, repo2: str, deep: bool = False) -> RepoDuelResult:
        """Analyze both repos and produce a duel result."""
        run_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        r1 = self._analyze(repo1)
        r2 = self._analyze(repo2)

        # Core dimensions
        dims: list[DimensionResult] = [
            _make_dimension("composite_score", r1.composite_score, r2.composite_score),
            _make_dimension("context_coverage", _tool_score(r1, "agentmd"), _tool_score(r2, "agentmd")),
            _make_dimension("test_coverage", _tool_score(r1, "coderace"), _tool_score(r2, "coderace")),
            _make_dimension("lint_score", _tool_score(r1, "agentlint"), _tool_score(r2, "agentlint")),
        ]

        if deep:
            dims.append(
                _make_dimension("redteam_resistance", _tool_score(r1, "agentreflect"), _tool_score(r2, "agentreflect"))
            )

        # Overall winner: most dimension wins
        r1_wins = sum(1 for d in dims if d.winner == "repo1")
        r2_wins = sum(1 for d in dims if d.winner == "repo2")
        if r1_wins > r2_wins:
            winner = "repo1"
        elif r2_wins > r1_wins:
            winner = "repo2"
        else:
            winner = "draw"

        return RepoDuelResult(
            repo1=repo1,
            repo2=repo2,
            repo1_score=r1.composite_score,
            repo2_score=r2.composite_score,
            repo1_grade=r1.grade,
            repo2_grade=r2.grade,
            dimension_results=dims,
            winner=winner,
            run_date=run_date,
        )
