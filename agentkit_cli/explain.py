"""explain.py — LLM-powered coaching report for agentkit.

ExplainEngine reads a run report (from agentkit run --json) and produces
a human-readable markdown coaching report explaining WHY scores are what they are.

LLM: Claude via Anthropic API (claude-3-5-haiku-20241022 by default).
Fallback: template_explain() — rule-based prose, no API key needed.
"""
from __future__ import annotations

import json
import logging
import os
import warnings
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Score tier thresholds
TIER_A = 90
TIER_B = 70
TIER_C = 50

# Plain-language explanations for common findings
FINDING_PLAIN: dict[str, str] = {
    "path-rot": (
        "File paths referenced in your context file don't exist, which confuses agents "
        "trying to navigate your codebase."
    ),
    "year-rot": (
        "References to past years make your context file appear stale, "
        "reducing agent trust in its accuracy."
    ),
    "bloat": (
        "Your context file is too long; agents perform better with focused, essential context."
    ),
    "script-rot": (
        "Scripts or commands referenced in your context file may be outdated or broken, "
        "causing agents to run invalid commands."
    ),
    "stale-todo": (
        "Old TODO items clutter your context file, adding noise that reduces agent focus."
    ),
    "multi-file-conflict": (
        "Conflicting instructions across multiple context files cause agents to behave "
        "inconsistently depending on which file they read first."
    ),
    "mcp-security": (
        "MCP tool configurations expose security risks that could allow agents to "
        "perform unintended or dangerous actions."
    ),
    "trailing-whitespace": (
        "Minor formatting issues that can cause diff noise and minor friction."
    ),
    "duplicate-blank-lines": (
        "Excessive blank lines add length without value, diluting important instructions."
    ),
}

DEFAULT_CODERACE_LOW = (
    "Agents scored lower on benchmark tasks, suggesting your codebase structure "
    "makes it harder for them to navigate and complete changes."
)


def _score_tier(score: float) -> str:
    if score >= TIER_A:
        return "A"
    if score >= TIER_B:
        return "B"
    if score >= TIER_C:
        return "C"
    return "F"


def _extract_composite(report: dict) -> float:
    """Extract composite score from various report shapes."""
    # Direct composite key
    for key in ("composite", "composite_score", "score"):
        v = report.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    # Nested summary
    summary = report.get("summary", {})
    if isinstance(summary, dict):
        for key in ("composite", "score"):
            v = summary.get(key)
            if isinstance(v, (int, float)):
                return float(v)
    # Derive from pass/fail/total
    total = report.get("total", 0)
    passed = report.get("passed", 0)
    if total:
        return round(100.0 * passed / total, 1)
    return 0.0


def _extract_findings(report: dict) -> list[dict]:
    """Extract top findings from report in a normalized list."""
    findings: list[dict] = []
    # From findings key (agentlint style)
    raw = report.get("findings", [])
    if isinstance(raw, list):
        for f in raw:
            if isinstance(f, dict):
                findings.append(f)
    # From steps output (run command format)
    for step in report.get("steps", []):
        if not isinstance(step, dict):
            continue
        step_findings = step.get("findings", [])
        if isinstance(step_findings, list):
            findings.extend([f for f in step_findings if isinstance(f, dict)])
    return findings[:10]  # Cap at 10


def _extract_tool_scores(report: dict) -> dict[str, Any]:
    """Extract per-tool scores from report."""
    scores: dict[str, Any] = {}
    breakdown = report.get("breakdown", {})
    if isinstance(breakdown, dict):
        scores.update(breakdown)
    # From summary steps
    for step in report.get("summary", {}).get("steps", []):
        if not isinstance(step, dict):
            continue
        name = step.get("step") or step.get("name", "")
        status = step.get("status", "")
        if name and status:
            scores.setdefault(name, status)
    return scores


def _extract_project(report: dict) -> str:
    """Extract project name from report."""
    proj = report.get("project", "") or report.get("name", "")
    if proj:
        return str(proj)
    return "your project"


def _extract_file_count(report: dict) -> Optional[int]:
    meta = report.get("meta", {})
    if isinstance(meta, dict):
        return meta.get("file_count") or meta.get("files")
    return None


class ExplainEngine:
    """LLM-powered coaching report engine.

    Usage:
        engine = ExplainEngine()
        report = engine.load_report("report.json")
        markdown = engine.explain(report)
    """

    def __init__(self, model: str = "claude-3-5-haiku-20241022", timeout: int = 30) -> None:
        self.model = model
        self.timeout = timeout

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def load_report(self, path: str) -> dict:
        """Load a report JSON file produced by `agentkit run --json`."""
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        return data

    # ------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------

    def build_prompt(self, report: dict) -> str:
        """Build a concise LLM prompt from report data (< 2000 tokens)."""
        composite = _extract_composite(report)
        tier = _score_tier(composite)
        project = _extract_project(report)
        file_count = _extract_file_count(report)
        tool_scores = _extract_tool_scores(report)
        findings = _extract_findings(report)

        lines = [
            "You are an expert in AI coding agent quality. Analyze the following agentkit report",
            "and produce a markdown coaching report for the project owner.",
            "",
            f"**Project:** {project}",
            f"**Composite Score:** {composite}/100 (Tier {tier})",
        ]
        if file_count is not None:
            lines.append(f"**File Count:** {file_count}")

        if tool_scores:
            lines.append("")
            lines.append("**Per-tool scores/status:**")
            for tool, score in list(tool_scores.items())[:8]:
                lines.append(f"  - {tool}: {score}")

        if findings:
            lines.append("")
            lines.append("**Top findings (up to 5):**")
            for f in findings[:5]:
                cat = f.get("type") or f.get("category", "unknown")
                msg = f.get("message") or f.get("description", "")
                sev = f.get("severity", "")
                entry = f"  - [{cat}]"
                if sev:
                    entry += f" ({sev})"
                if msg:
                    entry += f": {msg[:120]}"
                lines.append(entry)

        lines += [
            "",
            "Produce a markdown coaching report with EXACTLY these four sections:",
            "",
            "## What This Score Means",
            "(2-3 sentences explaining what this score means for AI coding agents working on this repo)",
            "",
            "## Key Findings Explained",
            "(Explain the top 2-3 findings in plain language — what does each finding actually hurt?)",
            "",
            "## Top 3 Next Steps",
            "(3 concrete next steps ordered by impact, as a numbered list)",
            "",
            "## If You Do Nothing Else",
            "(One single most important recommendation, 1-2 sentences)",
            "",
            "Be concise and practical. Use plain language. Focus on what AI agents actually need.",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # LLM call
    # ------------------------------------------------------------------

    def call_llm(self, prompt: str) -> str:
        """Call Anthropic API; fall back to template_explain() on any failure."""
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning(
                "ANTHROPIC_API_KEY not set — using template-based explanation. "
                "Install the anthropic package and set ANTHROPIC_API_KEY for LLM coaching."
            )
            return ""  # Caller will use template fallback

        try:
            import anthropic  # type: ignore
        except ImportError:
            warnings.warn(
                "anthropic package not installed. "
                "Run: pip install anthropic\n"
                "Falling back to template-based explanation.",
                stacklevel=3,
            )
            return ""

        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=1024,
                timeout=self.timeout,
                messages=[{"role": "user", "content": prompt}],
            )
            # Extract text content
            content = message.content
            if isinstance(content, list) and content:
                block = content[0]
                if hasattr(block, "text"):
                    return block.text
                if isinstance(block, dict):
                    return block.get("text", "")
            if isinstance(content, str):
                return content
            return str(content)
        except Exception as exc:
            logger.warning("Anthropic API call failed (%s) — falling back to template.", exc)
            return ""

    # ------------------------------------------------------------------
    # Template fallback
    # ------------------------------------------------------------------

    def template_explain(self, report: dict) -> str:
        """Rule-based markdown coaching report. No API key needed."""
        composite = _extract_composite(report)
        tier = _score_tier(composite)
        project = _extract_project(report)
        findings = _extract_findings(report)
        tool_scores = _extract_tool_scores(report)

        # ------ What This Score Means ------
        score_int = int(round(composite))
        if composite >= TIER_A:
            score_meaning = (
                f"Your repo is well-configured for AI agents. "
                f"With a score of {score_int}/100, agents can navigate `{project}` effectively, "
                f"find relevant context, and complete tasks with minimal friction. "
                f"Here's what's already working and what to preserve."
            )
        elif composite >= TIER_B:
            score_meaning = (
                f"Good foundation with room to improve. "
                f"A score of {score_int}/100 means agents can work on `{project}`, "
                f"but they'll occasionally hit friction points that slow them down or cause "
                f"incorrect assumptions. The biggest opportunities are in the findings below."
            )
        elif composite >= TIER_C:
            score_meaning = (
                f"Mixed results. "
                f"AI agents can work on `{project}` but will hit friction in several areas "
                f"(score: {score_int}/100). Context files may be stale or misleading, "
                f"causing agents to make wrong assumptions about your codebase structure."
            )
        else:
            score_meaning = (
                f"Significant gaps found. "
                f"Agents working on `{project}` will likely struggle — score {score_int}/100 "
                f"indicates that context files are missing, stale, or actively misleading. "
                f"Agents may navigate to wrong paths, run invalid commands, or produce "
                f"inconsistent results."
            )

        # ------ Key Findings Explained ------
        finding_lines: list[str] = []
        seen_cats: set[str] = set()

        # Check for low coderace
        for key, val in tool_scores.items():
            if "coderace" in key.lower() or "benchmark" in key.lower():
                if isinstance(val, (int, float)) and float(val) < 70:
                    finding_lines.append(f"- **Low benchmark score ({val}):** {DEFAULT_CODERACE_LOW}")
                    break
                elif isinstance(val, str) and val in ("fail", "error"):
                    finding_lines.append(f"- **Benchmark failure:** {DEFAULT_CODERACE_LOW}")
                    break

        for f in findings[:5]:
            cat = (f.get("type") or f.get("category") or "").lower()
            if cat in seen_cats:
                continue
            seen_cats.add(cat)
            plain = FINDING_PLAIN.get(cat)
            if plain:
                label = cat.replace("-", " ").title()
                finding_lines.append(f"- **{label}:** {plain}")
            if len(finding_lines) >= 3:
                break

        if not finding_lines:
            if composite >= TIER_A:
                finding_lines.append(
                    "- No significant issues detected. Your context files are accurate and well-maintained."
                )
            else:
                finding_lines.append(
                    "- Run `agentkit suggest` for a detailed breakdown of specific issues."
                )

        # ------ Top 3 Next Steps ------
        next_steps = _template_next_steps(composite, findings, tool_scores)

        # ------ If You Do Nothing Else ------
        one_thing = _template_one_thing(composite, findings, tool_scores)

        report_lines = [
            f"# Agent Quality Coaching Report — `{project}`",
            f"**Score:** {score_int}/100 · **Tier:** {tier}",
            "",
            "## What This Score Means",
            score_meaning,
            "",
            "## Key Findings Explained",
        ]
        report_lines.extend(finding_lines)
        report_lines += [
            "",
            "## Top 3 Next Steps",
        ]
        for i, step in enumerate(next_steps[:3], 1):
            report_lines.append(f"{i}. {step}")
        report_lines += [
            "",
            "## If You Do Nothing Else",
            one_thing,
            "",
            "---",
            "*Generated by agentkit explain (template mode — set ANTHROPIC_API_KEY for LLM coaching)*",
        ]
        return "\n".join(report_lines)

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def explain(self, report: dict) -> str:
        """Full pipeline: build_prompt → call_llm → return markdown coaching report."""
        prompt = self.build_prompt(report)
        llm_result = self.call_llm(prompt)
        if llm_result and llm_result.strip():
            return llm_result
        return self.template_explain(report)

    def explain_run_result(self, result: dict) -> str:
        """Accept a RunResult dict (from agentkit run) directly."""
        return self.explain(result)


# ------------------------------------------------------------------
# Template helpers
# ------------------------------------------------------------------

def _template_next_steps(
    composite: float, findings: list[dict], tool_scores: dict
) -> list[str]:
    steps: list[str] = []

    # Critical findings first
    for f in findings:
        cat = (f.get("type") or f.get("category") or "").lower()
        sev = (f.get("severity") or "").lower()
        if sev == "critical" or cat in ("path-rot", "year-rot"):
            if cat == "path-rot":
                steps.append(
                    "Fix broken file paths in your context file — run `agentkit suggest --fix` "
                    "to identify and remove invalid path references."
                )
            elif cat == "year-rot":
                steps.append(
                    "Update stale year references in your context file — run `agentkit suggest --fix` "
                    "to auto-apply year updates."
                )
            if len(steps) >= 2:
                break

    # Bloat
    for f in findings:
        cat = (f.get("type") or f.get("category") or "").lower()
        if cat == "bloat" and len(steps) < 3:
            steps.append(
                "Trim your context file — remove sections that don't directly help agents "
                "navigate or understand your codebase. Aim for under 2000 tokens."
            )

    # Low composite → generate context file
    if composite < TIER_C and len(steps) < 3:
        steps.append(
            "Run `agentkit init` to generate a fresh CLAUDE.md — your current context "
            "may be missing or too sparse for agents to work effectively."
        )

    # Benchmark
    for key, val in tool_scores.items():
        if "coderace" in key.lower() or "benchmark" in key.lower():
            if (isinstance(val, (int, float)) and float(val) < 70) or val in ("fail", "error"):
                if len(steps) < 3:
                    steps.append(
                        "Improve code navigability — add clear module structure, inline comments "
                        "at key entry points, and explicit architecture notes to your context file."
                    )
                break

    # Generic fill
    if len(steps) < 3:
        if composite >= TIER_A:
            steps.append(
                "Set up `agentkit ci` to track your score over time and catch regressions "
                "before they impact agent performance."
            )
        elif composite >= TIER_B:
            steps.append(
                "Run `agentkit suggest` weekly to catch new stale references before they "
                "accumulate into larger context debt."
            )
        else:
            steps.append(
                "Add an AGENTS.md or CLAUDE.md with your project's key architecture decisions, "
                "entry points, and common agent tasks."
            )

    if len(steps) < 3:
        steps.append(
            "Run `agentkit run` with `--benchmark` to get a full picture of how agents "
            "perform on real tasks in your codebase."
        )

    return steps[:3]


def _template_one_thing(
    composite: float, findings: list[dict], tool_scores: dict
) -> str:
    # Find the most critical finding
    for f in findings:
        cat = (f.get("type") or f.get("category") or "").lower()
        sev = (f.get("severity") or "").lower()
        if sev == "critical":
            plain = FINDING_PLAIN.get(cat, "")
            label = cat.replace("-", " ")
            if plain:
                return (
                    f"Fix the `{label}` issue first — {plain.lower().rstrip('.')}. "
                    f"This single change will have the most immediate impact on agent reliability."
                )

    if composite < TIER_C:
        return (
            "Create or regenerate your context file with `agentkit init`. "
            "A well-written CLAUDE.md is the single highest-leverage improvement "
            "you can make for AI agent performance."
        )
    if composite < TIER_B:
        return (
            "Run `agentkit suggest --fix` to apply safe auto-fixes to your context file. "
            "Most quick wins are automated and take under a minute."
        )
    return (
        "Keep your context file updated as your codebase evolves — "
        "stale context is the #1 source of agent errors in well-maintained repos."
    )
