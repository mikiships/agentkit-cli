"""suggest_engine.py — Prioritization logic for agentkit suggest."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

# Severity order (lowest index = highest priority)
SEVERITY_ORDER = ["critical", "high", "medium", "low"]

# Mapping of agentlint categories to severity
CATEGORY_SEVERITY: dict[str, str] = {
    # critical
    "year-rot": "critical",
    "path-rot": "critical",
    "mcp-security": "critical",
    # high
    "script-rot": "high",
    "stale-todo": "high",
    # medium
    "bloat": "medium",
    "multi-file-conflict": "medium",
    # low
    "trailing-whitespace": "low",
    "duplicate-blank-lines": "low",
    "cosmetic": "low",
}

# Which fixes are auto-applicable
AUTO_FIXABLE_CATEGORIES = {"year-rot", "trailing-whitespace", "duplicate-blank-lines"}

# Context file patterns (only these are safe to auto-fix)
CONTEXT_FILE_PATTERNS = re.compile(
    r"(CLAUDE\.md|AGENTS\.md|\.agents/[^/]+\.md)$",
    re.IGNORECASE,
)


@dataclass
class Finding:
    """A single prioritized finding from agentlint."""

    tool: str
    severity: str  # critical | high | medium | low
    category: str
    description: str
    fix_hint: str
    auto_fixable: bool = False
    file: Optional[str] = None
    line: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict)

    def severity_rank(self) -> int:
        try:
            return SEVERITY_ORDER.index(self.severity)
        except ValueError:
            return len(SEVERITY_ORDER)


def _severity_for_category(category: str) -> str:
    return CATEGORY_SEVERITY.get(category, "low")


def _auto_fixable(category: str, file: Optional[str]) -> bool:
    if category not in AUTO_FIXABLE_CATEGORIES:
        return False
    if category in ("trailing-whitespace", "duplicate-blank-lines", "year-rot"):
        # Only context files
        if file and not CONTEXT_FILE_PATTERNS.search(file):
            return False
    return True


def _make_finding(tool: str, raw: dict[str, Any]) -> Finding:
    """Build a Finding from a raw agentlint issue dict."""
    category = raw.get("type") or raw.get("category") or "cosmetic"
    severity = raw.get("severity") or _severity_for_category(category)
    description = raw.get("message") or raw.get("description") or str(raw)
    fix_hint = raw.get("fix_hint") or raw.get("hint") or _default_hint(category)
    file = raw.get("file") or raw.get("path")
    line = raw.get("line")
    auto_fix = _auto_fixable(category, file)
    return Finding(
        tool=tool,
        severity=severity,
        category=category,
        description=description,
        fix_hint=fix_hint,
        auto_fixable=auto_fix,
        file=file,
        line=line,
        raw=raw,
    )


def _default_hint(category: str) -> str:
    hints = {
        "year-rot": "Update stale year references to the current year.",
        "path-rot": "Fix or remove broken file references.",
        "mcp-security": "Review MCP tool permissions and remove unsafe entries.",
        "script-rot": "Update or remove broken script references.",
        "stale-todo": "Resolve or remove stale TODO comments blocking workflow.",
        "bloat": "Trim context files to reduce token bloat (score < 60).",
        "multi-file-conflict": "Resolve conflicting information across context files.",
        "trailing-whitespace": "Remove trailing whitespace from context files.",
        "duplicate-blank-lines": "Collapse consecutive blank lines to 2 or fewer.",
        "cosmetic": "Address cosmetic issue for cleaner context files.",
    }
    return hints.get(category, "Review and address this finding.")


def parse_agentlint_check_context(json_output: Any) -> list[Finding]:
    """Extract findings from agentlint check-context JSON output."""
    if not json_output:
        return []
    if isinstance(json_output, str):
        import json
        try:
            json_output = json.loads(json_output)
        except Exception:
            return []
    issues = (
        json_output.get("issues")
        or json_output.get("findings")
        or json_output.get("errors")
        or []
    )
    findings = []
    for raw in issues:
        if isinstance(raw, dict):
            findings.append(_make_finding("agentlint/check-context", raw))
    return findings


def parse_agentlint_diff(json_output: Any) -> list[Finding]:
    """Extract findings from agentlint diff analysis JSON output."""
    if not json_output:
        return []
    if isinstance(json_output, str):
        import json
        try:
            json_output = json.loads(json_output)
        except Exception:
            return []
    issues = (
        json_output.get("issues")
        or json_output.get("findings")
        or json_output.get("errors")
        or []
    )
    findings = []
    for raw in issues:
        if isinstance(raw, dict):
            findings.append(_make_finding("agentlint/diff", raw))
    return findings


def _dedup_key(f: Finding) -> tuple[str, str]:
    """Findings with same category + file count as one."""
    return (f.category, f.file or "")


def prioritize(findings: list[Finding], top_n: Optional[int] = None) -> list[Finding]:
    """Sort by severity, deduplicate, return top N."""
    if not findings:
        return []

    # Dedup: keep highest-severity finding per (category, file)
    seen: dict[tuple[str, str], Finding] = {}
    for f in findings:
        key = _dedup_key(f)
        if key not in seen or f.severity_rank() < seen[key].severity_rank():
            seen[key] = f

    deduped = list(seen.values())
    deduped.sort(key=lambda f: (f.severity_rank(), f.category))

    if top_n is not None:
        return deduped[:top_n]
    return deduped


def prioritize_findings(agentlint_output: Any) -> list[Finding]:
    """High-level entry point: accepts raw JSON from agentlint and returns prioritized findings."""
    if isinstance(agentlint_output, list):
        # Already a list of raw dicts
        findings = [_make_finding("agentlint", raw) for raw in agentlint_output if isinstance(raw, dict)]
    else:
        findings = parse_agentlint_check_context(agentlint_output)
    return prioritize(findings)
