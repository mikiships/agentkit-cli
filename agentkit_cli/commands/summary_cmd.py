"""agentkit summary command — generate maintainer-facing summaries."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import typer

from agentkit_cli.commands.report_cmd import TOOLS, _tool_status, run_all
from agentkit_cli.suggest_engine import (
    CATEGORY_SEVERITY,
    parse_agentlint_check_context,
    prioritize,
    prioritize_findings,
)


SUMMARY_TOP_FIX_LIMIT = 5


def _normalize_tool_statuses(data: dict[str, Any]) -> list[dict[str, Any]]:
    statuses = data.get("tool_status")
    if isinstance(statuses, list):
        return [status for status in statuses if isinstance(status, dict)]

    statuses = data.get("tools")
    if isinstance(statuses, list) and all(isinstance(status, dict) for status in statuses):
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


def _normalize_issue_severity(issue: dict[str, Any]) -> str:
    severity = str(issue.get("severity") or "").strip().lower()
    if severity in {"critical", "high", "medium", "low"}:
        return severity
    if severity in {"warn", "warning"}:
        return "warning"
    if severity in {"error", "fail", "failed"}:
        return "critical"

    category = str(issue.get("type") or issue.get("category") or "").strip().lower()
    return CATEGORY_SEVERITY.get(category, "warning")


def _agentlint_issues(result: Any) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return []
    issues = result.get("issues") or result.get("findings") or result.get("errors") or []
    return [issue for issue in issues if isinstance(issue, dict)]


def _tool_note(tool: str, result: Any) -> str:
    if tool == "agentlint":
        issues = _agentlint_issues(result)
        if not issues:
            return "No issues found"
        counts: dict[str, int] = {}
        for issue in issues:
            severity = _normalize_issue_severity(issue)
            counts[severity] = counts.get(severity, 0) + 1

        labels = {
            "critical": "critical",
            "high": "high-priority",
            "warning": "warning(s)",
            "medium": "medium-priority",
            "low": "low-priority",
        }
        ordered = ["critical", "high", "warning", "medium", "low"]
        parts = [
            f"{counts[severity]} {labels[severity]}"
            for severity in ordered
            if counts.get(severity)
        ]
        return ", ".join(parts)

    if tool == "agentmd" and isinstance(result, dict):
        files = result.get("files")
        if isinstance(files, list):
            return f"{len(files)} file(s) analyzed"
    if tool == "coderace" and isinstance(result, dict):
        if result.get("status") == "no_results":
            return str(result.get("message", "No benchmark results"))
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


def _overall_score(
    results: dict[str, Any],
    statuses: list[dict[str, Any]],
    score_override: Optional[float],
) -> int:
    if isinstance(score_override, (int, float)):
        return int(round(float(score_override)))

    scores = [
        score
        for score in (_extract_score(results.get(tool)) for tool in TOOLS)
        if score is not None
    ]
    if scores:
        return round(sum(scores) / len(scores))
    return _coverage_from_statuses(statuses)


def _normalize_fix_entry(entry: Any) -> Optional[dict[str, Any]]:
    if isinstance(entry, str):
        summary = entry.strip()
        if not summary:
            return None
        return {
            "tool": "summary",
            "severity": "medium",
            "category": "suggestion",
            "summary": summary,
            "fix_hint": summary,
            "auto_fixable": False,
            "file": None,
        }

    if not isinstance(entry, dict):
        return None

    summary = (
        entry.get("summary")
        or entry.get("description")
        or entry.get("message")
        or entry.get("title")
        or entry.get("fix_hint")
    )
    if not isinstance(summary, str) or not summary.strip():
        return None

    severity = str(entry.get("severity") or "medium").strip().lower()
    if severity in {"warn", "warning"}:
        severity = "warning"

    category = str(entry.get("category") or entry.get("type") or "suggestion")
    fix_hint = entry.get("fix_hint") or entry.get("hint") or summary
    return {
        "tool": str(entry.get("tool") or "summary"),
        "severity": severity,
        "category": category,
        "summary": summary.strip(),
        "fix_hint": str(fix_hint),
        "auto_fixable": bool(entry.get("auto_fixable", False)),
        "file": entry.get("file") or entry.get("path"),
    }


def _reflect_suggestions(result: Any) -> list[dict[str, Any]]:
    if not isinstance(result, dict):
        return []

    suggestions = result.get("suggestions")
    if isinstance(suggestions, list):
        normalized = [
            _normalize_fix_entry(
                {
                    "tool": "agentreflect",
                    "severity": "medium",
                    "category": "reflection",
                    "summary": suggestion,
                    "fix_hint": suggestion,
                }
            )
            for suggestion in suggestions
        ]
        return [entry for entry in normalized if entry is not None]

    markdown = result.get("suggestions_md")
    if not isinstance(markdown, str):
        return []

    extracted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("### "):
            summary = line[4:].strip()
        elif line.startswith(("- ", "* ")):
            summary = line[2:].strip()
        else:
            continue
        if not summary or summary in seen:
            continue
        seen.add(summary)
        extracted.append(
            {
                "tool": "agentreflect",
                "severity": "medium",
                "category": "reflection",
                "summary": summary,
                "fix_hint": summary,
                "auto_fixable": False,
                "file": None,
            }
        )
    return extracted


def _derive_top_fixes(data: dict[str, Any]) -> list[dict[str, Any]]:
    explicit_top_fixes = data.get("top_fixes")
    if isinstance(explicit_top_fixes, list):
        normalized = [_normalize_fix_entry(entry) for entry in explicit_top_fixes]
        return [entry for entry in normalized if entry is not None][:SUMMARY_TOP_FIX_LIMIT]

    prioritized = prioritize_findings(data.get("findings"))
    if not prioritized:
        prioritized = prioritize(parse_agentlint_check_context(data.get("agentlint")))

    fixes = [
        {
            "tool": finding.tool,
            "severity": finding.severity,
            "category": finding.category,
            "summary": finding.description,
            "fix_hint": finding.fix_hint,
            "auto_fixable": finding.auto_fixable,
            "file": finding.file,
        }
        for finding in prioritized[:SUMMARY_TOP_FIX_LIMIT]
    ]

    if len(fixes) >= SUMMARY_TOP_FIX_LIMIT:
        return fixes

    suggestion_sources: list[Any] = []
    suggestions = data.get("suggestions")
    if isinstance(suggestions, list):
        suggestion_sources.extend(suggestions)

    suggestion_sources.extend(_reflect_suggestions(data.get("agentreflect")))

    seen = {
        (fix["summary"], fix.get("file"))
        for fix in fixes
    }
    for raw in suggestion_sources:
        normalized = _normalize_fix_entry(raw)
        if normalized is None:
            continue
        dedup_key = (normalized["summary"], normalized.get("file"))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        fixes.append(normalized)
        if len(fixes) >= SUMMARY_TOP_FIX_LIMIT:
            break

    return fixes


def _normalize_compare_data(data: dict[str, Any]) -> Optional[dict[str, Any]]:
    raw_compare = (
        data.get("compare")
        or data.get("compare_metadata")
        or data.get("compare_result")
    )
    if not isinstance(raw_compare, dict):
        return None

    tools = raw_compare.get("tools")
    normalized_tools: list[dict[str, Any]] = []
    if isinstance(tools, list):
        for entry in tools:
            if not isinstance(entry, dict):
                continue
            normalized_tools.append(
                {
                    "tool": str(entry.get("tool") or "unknown"),
                    "score_ref1": entry.get("score_ref1"),
                    "score_ref2": entry.get("score_ref2"),
                    "delta": entry.get("delta"),
                }
            )

    net_delta = raw_compare.get("net_delta")
    if isinstance(net_delta, (int, float)):
        net_delta = round(float(net_delta), 2)
    else:
        net_delta = None

    return {
        "ref1": str(raw_compare.get("ref1") or raw_compare.get("base") or "unknown"),
        "ref2": str(raw_compare.get("ref2") or raw_compare.get("head") or "unknown"),
        "verdict": str(raw_compare.get("verdict") or "NEUTRAL"),
        "net_delta": net_delta,
        "tools": normalized_tools,
    }


def _summary_verdict(
    tool_status: list[dict[str, Any]],
    top_fixes: list[dict[str, Any]],
    compare: Optional[dict[str, Any]],
) -> str:
    if compare and compare.get("verdict") == "DEGRADED":
        return "REGRESSION_DETECTED"

    if any(
        status.get("status") in {"failed", "not_installed"}
        for status in tool_status
    ):
        return "ACTION_REQUIRED"

    if any(fix.get("severity") in {"critical", "high"} for fix in top_fixes):
        return "ACTION_REQUIRED"

    if top_fixes:
        return "WARNINGS_PRESENT"

    return "PASSING"


def _display_verdict(verdict: str) -> str:
    return verdict.replace("_", " ").title()


def _project_name(data: dict[str, Any]) -> str:
    project = data.get("project")
    if isinstance(project, str) and project.strip():
        return project

    raw_path = data.get("path")
    if isinstance(raw_path, str) and raw_path.strip():
        return Path(raw_path).name

    return "current-project"


def build_summary_payload(data: dict[str, Any]) -> dict[str, Any]:
    statuses = _normalize_tool_statuses(data)
    results = {tool: data.get(tool) for tool in TOOLS}

    tool_status: list[dict[str, Any]] = []
    for status in statuses:
        tool = str(status.get("tool", "unknown"))
        result = results.get(tool)
        existing_score = status.get("score")
        score = existing_score if isinstance(existing_score, (int, float)) else _extract_score(result)
        tool_status.append(
            {
                "tool": tool,
                "installed": bool(status.get("installed", True)),
                "status": str(status.get("status", "unknown")),
                "score": None if score is None else int(round(float(score))),
                "notes": str(status.get("notes") or _tool_note(tool, result)),
            }
        )

    compare = _normalize_compare_data(data)
    top_fixes = _derive_top_fixes(data)
    overall = _overall_score(results, tool_status, data.get("overall_score"))
    verdict = str(data.get("verdict") or _summary_verdict(tool_status, top_fixes, compare))

    return {
        "project": _project_name(data),
        "path": data.get("path"),
        "overall_score": overall,
        "verdict": verdict,
        "tool_status": tool_status,
        "top_fixes": top_fixes,
        "compare": compare,
    }


def _compare_table(compare: dict[str, Any]) -> list[str]:
    lines = [
        "## Compare",
        "",
        f"- Base ref: {compare['ref1']}",
        f"- Head ref: {compare['ref2']}",
        f"- Verdict: {compare['verdict']}",
    ]
    if compare.get("net_delta") is not None:
        lines.append(f"- Net delta: {compare['net_delta']:+.2f}")

    if compare.get("tools"):
        lines.extend(
            [
                "",
                "| Tool | Base | Head | Delta |",
                "| --- | --- | --- | --- |",
            ]
        )
        for entry in compare["tools"]:
            score_ref1 = entry.get("score_ref1")
            score_ref2 = entry.get("score_ref2")
            delta = entry.get("delta")
            base = "N/A" if score_ref1 is None else str(int(round(float(score_ref1))))
            head = "N/A" if score_ref2 is None else str(int(round(float(score_ref2))))
            delta_text = "N/A" if delta is None else f"{float(delta):+.1f}"
            lines.append(
                f"| {entry['tool']} | {base} | {head} | {delta_text} |"
            )

    return lines


def build_summary_markdown(data: dict[str, Any]) -> str:
    summary = build_summary_payload(data)
    tool_status = summary["tool_status"]

    lines = [
        "# agentkit summary",
        "",
        "## Overview",
        "",
        f"- Project: {summary['project']}",
        f"- Verdict: {_display_verdict(summary['verdict'])}",
        f"- Overall score: {summary['overall_score']}/100",
        f"- Tools passing: {sum(1 for status in tool_status if status['status'] == 'success')}/{len(tool_status)}",
    ]

    compare = summary.get("compare")
    if compare and compare.get("net_delta") is not None:
        lines.append(
            f"- Compare status: {compare['verdict']} ({compare['net_delta']:+.2f})"
        )

    lines.extend(
        [
            "",
            "## Tool status",
            "",
            "| Tool | Status | Score | Notes |",
            "| --- | --- | --- | --- |",
        ]
    )

    status_map = {
        "success": "success",
        "failed": "failed",
        "not_installed": "not installed",
        "skipped": "skipped",
    }
    for status in tool_status:
        score = status.get("score")
        score_text = "N/A" if score is None else str(score)
        status_text = status_map.get(status["status"], status["status"])
        lines.append(
            f"| {status['tool']} | {status_text} | {score_text} | {status['notes']} |"
        )

    lines.extend(
        [
            "",
            "## Top fixes",
            "",
        ]
    )
    if summary["top_fixes"]:
        for index, fix in enumerate(summary["top_fixes"], start=1):
            severity = str(fix["severity"]).replace("_", " ")
            category = str(fix["category"])
            file_text = f" ({fix['file']})" if fix.get("file") else ""
            lines.append(
                f"{index}. [{severity}] {fix['summary']}{file_text} — {category}"
            )
    else:
        lines.append("- No actionable fixes found.")

    if compare:
        lines.extend(["", *_compare_table(compare)])

    return "\n".join(lines) + "\n"


def _write_markdown_output(markdown: str, output: Optional[Path], job_summary: bool) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")

    if not job_summary:
        return

    summary_target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_target:
        raise typer.BadParameter(
            "--job-summary requires the GITHUB_STEP_SUMMARY environment variable."
        )

    summary_path = Path(summary_target)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write(markdown)


def summary_command(
    path: Optional[Path] = None,
    json_input: Optional[Path] = None,
    output: Optional[Path] = None,
    job_summary: bool = False,
    json_output: bool = False,
) -> None:
    """Generate a maintainer-facing summary from agentkit analysis results."""
    if json_output and output:
        raise typer.BadParameter("--json cannot be combined with --output.")
    if json_output and job_summary:
        raise typer.BadParameter("--json cannot be combined with --job-summary.")

    data = _load_summary_input(path=path, json_input=json_input)
    markdown = build_summary_markdown(data)

    if json_output:
        payload = build_summary_payload(data)
        payload["markdown"] = markdown
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    _write_markdown_output(markdown, output=output, job_summary=job_summary)
    typer.echo(markdown, nl=False)
