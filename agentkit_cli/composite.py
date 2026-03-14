"""CompositeScoreEngine — synthesizes all four toolkit tool outputs into a single 0-100 score."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

WEIGHTS: dict[str, float] = {
    "coderace": 0.30,
    "agentlint": 0.25,
    "agentmd": 0.25,
    "agentreflect": 0.20,
}

GRADE_THRESHOLDS = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
]


def _compute_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


@dataclass
class CompositeResult:
    score: float
    grade: str
    components: dict[str, dict]  # tool -> {raw_score, weight, contribution}
    missing_tools: list[str] = field(default_factory=list)


class CompositeScoreEngine:
    """Compute a weighted composite score from individual tool scores."""

    def __init__(self, weights: Optional[dict[str, float]] = None) -> None:
        self.weights = weights if weights is not None else dict(WEIGHTS)

    def compute(self, tool_scores: dict[str, Optional[float]]) -> CompositeResult:
        """Compute composite score.

        Args:
            tool_scores: dict mapping tool name to score (0-100) or None if not available.

        Returns:
            CompositeResult with score, grade, components, and missing_tools.

        Raises:
            ValueError: if no tools have scores.
        """
        present = {k: v for k, v in tool_scores.items() if v is not None}
        missing = [k for k, v in tool_scores.items() if v is None]
        # Also include tools in WEIGHTS not in tool_scores as missing
        for tool in self.weights:
            if tool not in tool_scores:
                missing.append(tool)

        if not present:
            raise ValueError("No tool scores available — at least one tool score is required.")

        # Renormalize weights among present tools
        total_weight = sum(self.weights.get(tool, 0.0) for tool in present)
        if total_weight == 0.0:
            # Fallback: equal weights for all present tools
            normalized = {tool: 1.0 / len(present) for tool in present}
        else:
            normalized = {
                tool: self.weights.get(tool, 0.0) / total_weight
                for tool in present
            }

        components: dict[str, dict] = {}
        composite = 0.0
        for tool, raw_score in present.items():
            raw = max(0.0, min(100.0, float(raw_score)))
            weight = normalized[tool]
            contribution = raw * weight
            composite += contribution
            components[tool] = {
                "raw_score": round(raw, 1),
                "weight": round(weight, 4),
                "contribution": round(contribution, 2),
            }

        composite = round(composite, 1)
        grade = _compute_grade(composite)

        return CompositeResult(
            score=composite,
            grade=grade,
            components=components,
            missing_tools=sorted(set(missing)),
        )
