"""Format agentkit results as GitHub Check Run output.

Converts composite score results into the ``output`` dict expected by
the GitHub Checks API (title, summary, text body, annotations).
"""
from __future__ import annotations

from typing import Any, Optional

from agentkit_cli.composite import _compute_grade

# Maximum annotations the Checks API accepts per update
_MAX_ANNOTATIONS = 50


def _score_status(score: float) -> str:
    """Return a human-readable status emoji for a tool score."""
    if score >= 80:
        return "pass"
    if score >= 60:
        return "warn"
    return "fail"


def _build_tool_table(components: dict[str, dict[str, Any]]) -> str:
    """Build a markdown table of per-tool scores."""
    lines = [
        "| Tool | Score | Weight | Status |",
        "|------|------:|-------:|--------|",
    ]
    for tool in sorted(components):
        comp = components[tool]
        raw = comp.get("raw_score", 0.0)
        weight = comp.get("weight", 0.0)
        status = _score_status(raw)
        status_icon = {"pass": ":white_check_mark:", "warn": ":warning:", "fail": ":x:"}.get(
            status, ""
        )
        lines.append(f"| {tool} | {raw:.0f} | {weight:.2f} | {status_icon} {status} |")
    return "\n".join(lines)


def _build_annotations(
    components: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build annotations for tools scoring below 80."""
    annotations: list[dict[str, Any]] = []
    for tool in sorted(components):
        comp = components[tool]
        raw = comp.get("raw_score", 0.0)
        if raw >= 80:
            continue
        level = "failure" if raw < 60 else "warning"
        annotations.append({
            "path": "CLAUDE.md",
            "start_line": 1,
            "end_line": 1,
            "annotation_level": level,
            "title": f"{tool}: {raw:.0f}/100",
            "message": f"{tool} scored {raw:.0f}/100 — below the 80-point threshold.",
        })
        if len(annotations) >= _MAX_ANNOTATIONS:
            break
    return annotations


def format_check_output(
    result: dict[str, Any],
    *,
    gate_result: Optional[dict[str, Any]] = None,
    share_url: Optional[str] = None,
) -> dict[str, Any]:
    """Convert a score result dict to a GitHub Check Run output payload.

    Args:
        result: Must contain ``score`` (float), ``grade`` (str), and
            ``components`` (dict of tool dicts with raw_score/weight).
        gate_result: Optional gate evaluation dict with ``passed`` and
            ``failure_reasons`` keys.
        share_url: Optional URL to the published scorecard.

    Returns:
        Dict with keys ``title``, ``summary``, ``text``, ``annotations``.
    """
    score = float(result.get("score", 0))
    grade = result.get("grade") or _compute_grade(score)
    components: dict[str, dict[str, Any]] = result.get("components") or {}

    # Title
    title = f"Agent Quality: {score:.0f}/100 ({grade})"

    # Summary
    summary_parts = [f"Composite score: **{score:.0f}/100 ({grade})**"]
    if gate_result is not None:
        passed = gate_result.get("passed", True)
        verdict = "PASS" if passed else "FAIL"
        summary_parts.append(f"Gate verdict: **{verdict}**")
        failure_reasons = gate_result.get("failure_reasons") or []
        for reason in failure_reasons:
            summary_parts.append(f"- {reason}")
    if share_url:
        summary_parts.append(f"\n[View scorecard]({share_url})")
    summary = "\n".join(summary_parts)

    # Text body — per-tool table
    text = _build_tool_table(components) if components else "No per-tool breakdown available."

    # Annotations
    annotations = _build_annotations(components)

    return {
        "title": title,
        "summary": summary,
        "text": text,
        "annotations": annotations,
    }
