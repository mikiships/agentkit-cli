"""Core gate engine for `agentkit gate`."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from agentkit_cli.composite import CompositeResult, CompositeScoreEngine, _compute_grade
from agentkit_cli.commands.report_cmd import TOOLS, _tool_status, run_all
from agentkit_cli.config import find_project_root


class GateError(RuntimeError):
    """Raised when the gate command cannot complete evaluation."""


def _mean_score(entries: list[dict[str, Any]]) -> Optional[float]:
    scores = [
        float(entry["score"])
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float))
    ]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


def extract_tool_score(tool: str, result: Any) -> Optional[float]:
    """Extract a 0-100 score from a report payload entry."""
    if result is None:
        return None

    if isinstance(result, dict):
        for key in ("score", "freshness_score", "total_score", "composite_score"):
            value = result.get(key)
            if isinstance(value, (int, float)):
                return float(value)

        if tool == "coderace":
            entries = result.get("results") or result.get("agents")
            if isinstance(entries, list):
                return _mean_score(entries)

    if isinstance(result, list):
        return _mean_score(result)

    return None


def build_tool_scores(payload: dict[str, Any]) -> dict[str, Optional[float]]:
    """Build the tool-score map expected by CompositeScoreEngine."""
    return {tool: extract_tool_score(tool, payload.get(tool)) for tool in TOOLS}


def compute_payload_score(payload: dict[str, Any]) -> CompositeResult:
    """Compute a composite score from a report-like payload."""
    if isinstance(payload.get("score"), (int, float)):
        score = round(float(payload["score"]), 1)
        return CompositeResult(
            score=score,
            grade=_compute_grade(score),
            components=dict(payload.get("components") or {}),
            missing_tools=list(payload.get("missing_tools") or []),
        )

    tool_scores = build_tool_scores(payload)
    if any(score is not None for score in tool_scores.values()):
        return CompositeScoreEngine().compute(tool_scores)

    return CompositeResult(
        score=0.0,
        grade=_compute_grade(0.0),
        components={},
        missing_tools=list(TOOLS),
    )


def load_report_payload(path: Path) -> dict[str, Any]:
    """Load and validate a report JSON payload."""
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise GateError(f"Baseline report file not found: {path}") from exc
    except OSError as exc:
        raise GateError(f"Could not read baseline report {path}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GateError(f"Invalid JSON in baseline report {path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise GateError(f"Baseline report {path} must contain a JSON object.")

    return payload


@dataclass
class GateResult:
    verdict: str
    passed: bool
    score: float
    grade: str
    thresholds: dict[str, Any]
    failure_reasons: list[str]
    components: dict[str, dict[str, float]]
    missing_tools: list[str]
    tool_status: list[dict[str, Any]]
    baseline_delta: Optional[float] = None

    def to_json_payload(self) -> dict[str, Any]:
        """Return a stable dict suitable for JSON serialization and machine consumption."""
        return {
            "verdict": self.verdict,
            "passed": self.passed,
            "score": self.score,
            "grade": self.grade,
            "thresholds": {
                "min_score": self.thresholds.get("min_score"),
                "max_drop": self.thresholds.get("max_drop"),
                "baseline_score": self.thresholds.get("baseline_score"),
                "baseline_delta": self.baseline_delta,
            },
            "failure_reasons": self.failure_reasons,
        }

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "verdict": self.verdict,
            "passed": self.passed,
            "score": self.score,
            "grade": self.grade,
            "thresholds": self.thresholds,
            "failure_reasons": self.failure_reasons,
            "components": self.components,
            "missing_tools": self.missing_tools,
            "tool_status": self.tool_status,
        }
        if self.baseline_delta is not None:
            payload["baseline_delta"] = self.baseline_delta
        return payload


def evaluate_gate_rules(
    score: float,
    *,
    min_score: Optional[float] = None,
    baseline_score: Optional[float] = None,
    max_drop: Optional[float] = None,
) -> tuple[bool, list[str], Optional[float]]:
    """Evaluate gate thresholds and return pass/fail with failure reasons."""
    failure_reasons: list[str] = []
    baseline_delta: Optional[float] = None

    if min_score is not None and score < min_score:
        failure_reasons.append(
            f"score {score:.1f} is below min-score {min_score:.1f}"
        )

    if baseline_score is not None:
        baseline_delta = round(score - baseline_score, 1)
        if max_drop is not None and baseline_delta < (-1 * max_drop):
            failure_reasons.append(
                f"score dropped {abs(baseline_delta):.1f} points from baseline "
                f"{baseline_score:.1f} (max allowed drop: {max_drop:.1f})"
            )

    return (not failure_reasons, failure_reasons, baseline_delta)


def run_gate(
    *,
    path: Optional[Path] = None,
    min_score: Optional[float] = None,
    baseline_report: Optional[Path] = None,
    max_drop: Optional[float] = None,
) -> GateResult:
    """Run the gate evaluation against the current project."""
    if min_score is None and max_drop is None:
        raise GateError("Provide at least one gate rule via --min-score and/or --max-drop.")
    if max_drop is not None and baseline_report is None:
        raise GateError("--max-drop requires --baseline-report.")

    root = (path or find_project_root()).resolve()
    results = run_all(str(root))
    current_payload = {
        "project": root.name,
        "tools": _tool_status(results),
        **results,
    }
    current_score = compute_payload_score(current_payload)

    thresholds: dict[str, Any] = {}
    if min_score is not None:
        thresholds["min_score"] = float(min_score)

    baseline_score: Optional[float] = None
    if baseline_report is not None:
        baseline_payload = load_report_payload(baseline_report)
        baseline_result = compute_payload_score(baseline_payload)
        baseline_score = baseline_result.score
        thresholds["baseline_report"] = str(baseline_report)
        thresholds["baseline_score"] = baseline_score
    if max_drop is not None:
        thresholds["max_drop"] = float(max_drop)

    passed, failure_reasons, baseline_delta = evaluate_gate_rules(
        current_score.score,
        min_score=min_score,
        baseline_score=baseline_score,
        max_drop=max_drop,
    )

    return GateResult(
        verdict="PASS" if passed else "FAIL",
        passed=passed,
        score=current_score.score,
        grade=current_score.grade,
        thresholds=thresholds,
        failure_reasons=failure_reasons,
        components=current_score.components,
        missing_tools=current_score.missing_tools,
        tool_status=current_payload["tools"],
        baseline_delta=baseline_delta,
    )
