"""agentkit summary command — generate maintainer-facing markdown summaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import typer

from agentkit_cli.commands.report_cmd import TOOLS, _tool_status, run_all


def _normalize_tool_statuses(data: dict[str, Any]) -> list[dict[str, Any]]:
    statuses = data.get("tools")
    if isinstance(statuses, list):
        return statuses
    raw_results = {tool: data.get(tool) for tool in TOOLS}
    return _tool_status(raw_results)


def _load_summary_input(path: Optional[Path], json_input: Optional[Path]) -> dict[str, Any]:
    if path and json_input:
        raise typer.BadParameter("Use either --path or --json-input, not both.")

    if json_input:
        try:
            loaded = json.loads(json_input.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise typer.BadParameter(f"JSON input file not found: {json_input}") from exc
        except json.JSONDecodeError as exc:
            raise typer.BadParameter(f"Invalid JSON in {json_input}: {exc.msg}") from exc
        if not isinstance(loaded, dict):
            raise typer.BadParameter("Summary input JSON must be an object.")
        return loaded

    root = path.resolve() if path else Path.cwd()
    raw_results = run_all(str(root))
    return {
        "project": root.name,
        "path": str(root),
        "tools": _tool_status(raw_results),
        **raw_results,
    }


def _extract_score(result: Any) -> Optional[float]:
    if result is None:
        return None
    if isinstance(result, dict):
        for key in ("score", "freshness_score", "total_score", "composite_score"):
            value = result.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        tool_results = result.get("results")
        if isinstance(tool_results, list):
            scores = [
                float(entry["score"])
                for entry in tool_results
                if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float))
            ]
            if scores:
                return round(sum(scores) / len(scores), 1)
    if isinstance(result, list):
        scores = [
            float(entry["score"])
            for entry in result
            if isinstance(entry, dict) and isinstance(entry.get("score"), (int, float))
        ]
        if scores:
            return round(sum(scores) / len(scores), 1)
    return None


def _tool_note(tool: str, result: Any) -> str:
    if tool == "agentlint" and isinstance(result, dict):
        issues = result.get("issues") or result.get("findings") or result.get("errors") or []
        if not issues:
            return "No issues found"
        return f"{len(issues)} issue(s)"
    if tool == "agentmd" and isinstance(result, dict):
        files = result.get("files")
        if isinstance(files, list):
            return f"{len(files)} file(s) analyzed"
    if tool == "coderace" and isinstance(result, dict):
        if result.get("status") == "no_results":
            return result.get("message", "No benchmark results")
        results = result.get("results")
        if isinstance(results, list):
            return f"{len(results)} benchmark result(s)"
    if tool == "agentreflect" and isinstance(result, dict):
        count = result.get("count")
        if isinstance(count, int):
            return f"{count} suggestion(s)"
    return "No details"


def _coverage_from_statuses(statuses: list[dict[str, Any]]) -> int:
    total = len(statuses)
    if total == 0:
        return 0
    successful = sum(1 for status in statuses if status.get("status") == "success")
    return round(successful / total * 100)


def _overall_score(results: dict[str, Any], statuses: list[dict[str, Any]]) -> int:
    scores = [
        score
        for score in (_extract_score(results.get(tool)) for tool in TOOLS)
        if score is not None
    ]
    if scores:
        return round(sum(scores) / len(scores))
    return _coverage_from_statuses(statuses)


def build_summary_markdown(data: dict[str, Any]) -> str:
    statuses = _normalize_tool_statuses(data)
    results = {tool: data.get(tool) for tool in TOOLS}
    overall = _overall_score(results, statuses)

    lines = [
        "# agentkit summary",
        "",
        f"## Overall",
        "",
        f"- Overall score: {overall}/100",
        "",
        "## Tool status",
        "",
        "| Tool | Status | Score | Notes |",
        "| --- | --- | --- | --- |",
    ]

    status_map = {
        "success": "success",
        "failed": "failed",
        "not_installed": "not installed",
        "skipped": "skipped",
    }
    for status in statuses:
        tool = str(status.get("tool", "unknown"))
        result = results.get(tool)
        score = _extract_score(result)
        score_text = "N/A" if score is None else str(int(round(score)))
        status_text = status_map.get(str(status.get("status")), str(status.get("status", "unknown")))
        lines.append(
            f"| {tool} | {status_text} | {score_text} | {_tool_note(tool, result)} |"
        )

    return "\n".join(lines) + "\n"


def summary_command(
    path: Optional[Path] = None,
    json_input: Optional[Path] = None,
) -> None:
    """Generate a markdown summary from agentkit analysis results."""
    data = _load_summary_input(path=path, json_input=json_input)
    typer.echo(build_summary_markdown(data))
