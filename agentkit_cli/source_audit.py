from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agentkit_cli.context_projections import (
    ContextProjectionEngine,
    DETECTION_PRIORITY,
    FORMAT_AGENTKIT_SOURCE,
    source_path_for_format,
)


_REQUIRED_SECTIONS = (
    ("objective", ("objective", "overview", "goal", "purpose"), "Add a clear objective or overview section with the intended outcome."),
    ("scope", ("scope", "boundaries", "non-goals", "out of scope"), "Add scope and boundary guidance so agents know what not to touch."),
    ("constraints", ("rules", "constraints", "guardrails", "non-negotiable", "safety"), "Add explicit rules or constraints for the build."),
    ("validation", ("validation", "testing", "tests", "verification"), "Add validation or testing expectations agents must satisfy."),
    ("deliverables", ("deliverables", "handoff", "report", "output", "done"), "Add deliverables or handoff expectations so completion is concrete."),
)

_AMBIGUITY_PATTERNS = (
    ("tbd", re.compile(r"\b(TBD|TODO|FIXME|fill in|to be decided)\b", re.IGNORECASE), "Replace TODO/TBD placeholders with concrete instructions."),
    ("soft_language", re.compile(r"\b(maybe|perhaps|probably|usually|generally|as needed|if possible|where appropriate)\b", re.IGNORECASE), "Replace soft language with explicit rules or conditions."),
)

_NEGATION_PREFIXES = ("do not ", "don't ", "never ", "avoid ", "skip ", "no ")


@dataclass(frozen=True)
class SourceAuditFinding:
    code: str
    severity: str
    title: str
    evidence: str
    suggestion: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "title": self.title,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class SourceAuditReadiness:
    ready_for_contract: bool
    missing_required_sections: list[str] = field(default_factory=list)
    blocker_count: int = 0
    warning_count: int = 0
    summary: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "ready_for_contract": self.ready_for_contract,
            "missing_required_sections": list(self.missing_required_sections),
            "blocker_count": self.blocker_count,
            "warning_count": self.warning_count,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class SourceAuditResult:
    project_path: str
    source_path: Optional[str]
    source_format: Optional[str]
    used_fallback: bool
    section_checks: list[dict[str, object]]
    findings: list[SourceAuditFinding]
    readiness: SourceAuditReadiness

    def to_dict(self) -> dict[str, object]:
        return {
            "project_path": self.project_path,
            "source_path": self.source_path,
            "source_format": self.source_format,
            "used_fallback": self.used_fallback,
            "section_checks": [dict(item) for item in self.section_checks],
            "findings": [item.to_dict() for item in self.findings],
            "readiness": self.readiness.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class SourceAuditEngine:
    def __init__(self) -> None:
        self._projection_engine = ContextProjectionEngine()

    def detect_source(self, project_dir: str | Path) -> tuple[Optional[str], Optional[Path], bool]:
        root = Path(project_dir).expanduser().resolve()
        canonical = source_path_for_format(root, FORMAT_AGENTKIT_SOURCE)
        if canonical.exists():
            return FORMAT_AGENTKIT_SOURCE, canonical, False
        for fmt in DETECTION_PRIORITY:
            if fmt == FORMAT_AGENTKIT_SOURCE:
                continue
            candidate = source_path_for_format(root, fmt)
            if candidate.exists():
                return fmt, candidate, True
        detected = self._projection_engine.detect_source(root)
        if detected is None:
            return None, None, False
        fmt, path = detected
        return fmt, path, fmt != FORMAT_AGENTKIT_SOURCE

    def audit(self, project_dir: str | Path) -> SourceAuditResult:
        root = Path(project_dir).expanduser().resolve()
        source_format, source_path, used_fallback = self.detect_source(root)
        findings: list[SourceAuditFinding] = []
        if source_path is None:
            findings.append(SourceAuditFinding(
                code="missing_source",
                severity="error",
                title="No source file detected",
                evidence="Neither .agentkit/source.md nor a promoted legacy context file was found.",
                suggestion="Create .agentkit/source.md or promote an existing AGENTS.md/CLAUDE.md file before drafting a contract.",
            ))
            readiness = SourceAuditReadiness(
                ready_for_contract=False,
                missing_required_sections=[item[0] for item in _REQUIRED_SECTIONS],
                blocker_count=1,
                warning_count=0,
                summary="Blocked: no canonical or legacy source file was detected.",
            )
            return SourceAuditResult(str(root), None, None, used_fallback, [], findings, readiness)

        text = source_path.read_text(encoding="utf-8", errors="replace")
        section_checks = self._section_checks(text)
        findings.extend(self._section_findings(section_checks, used_fallback, source_path))
        findings.extend(self._ambiguity_findings(text))
        findings.extend(self._contradiction_findings(text))
        findings.sort(key=lambda item: (self._severity_rank(item.severity), item.code, item.title, item.evidence))
        readiness = self._build_readiness(section_checks, findings, used_fallback)
        return SourceAuditResult(
            project_path=str(root),
            source_path=str(source_path),
            source_format=source_format,
            used_fallback=used_fallback,
            section_checks=section_checks,
            findings=findings,
            readiness=readiness,
        )

    def render_markdown(self, result: SourceAuditResult) -> str:
        lines = [
            "# Source audit",
            "",
            f"- Project: `{result.project_path}`",
            f"- Source: `{result.source_path or 'missing'}`",
            f"- Format: `{result.source_format or 'unknown'}`",
            f"- Fallback mode: {'yes' if result.used_fallback else 'no'}",
            "",
            "## Contract readiness",
            "",
            f"- Ready for `agentkit contract`: {'yes' if result.readiness.ready_for_contract else 'no'}",
            f"- Blockers: {result.readiness.blocker_count}",
            f"- Warnings: {result.readiness.warning_count}",
            f"- Summary: {result.readiness.summary}",
            "",
            "## Section checks",
            "",
        ]
        for check in result.section_checks:
            status = "present" if check["present"] else "missing"
            lines.append(f"- {check['name']}: {status} ({check['evidence']})")
        if not result.section_checks:
            lines.append("- No source file sections available to inspect.")
        lines.extend(["", "## Findings", ""])
        if not result.findings:
            lines.append("- No findings. Source is structurally ready for contract drafting.")
        else:
            for finding in result.findings:
                lines.extend([
                    f"### [{finding.severity}] {finding.title}",
                    "",
                    f"- Evidence: {finding.evidence}",
                    f"- Suggested fix: {finding.suggestion}",
                    "",
                ])
        return "\n".join(lines).rstrip() + "\n"

    def _section_checks(self, text: str) -> list[dict[str, object]]:
        headings = self._extract_headings(text)
        checks: list[dict[str, object]] = []
        for name, keywords, _suggestion in _REQUIRED_SECTIONS:
            matched = [heading for heading in headings if any(keyword in heading.lower() for keyword in keywords)]
            present = bool(matched)
            evidence = ", ".join(matched[:2]) if matched else "no matching heading"
            checks.append({"name": name, "present": present, "evidence": evidence})
        return checks

    def _section_findings(self, checks: list[dict[str, object]], used_fallback: bool, source_path: Path) -> list[SourceAuditFinding]:
        findings: list[SourceAuditFinding] = []
        if used_fallback:
            findings.append(SourceAuditFinding(
                code="legacy_fallback",
                severity="warning",
                title="Using a legacy source file",
                evidence=f"Audit ran against {source_path.name} because .agentkit/source.md was missing.",
                suggestion="Promote the legacy file into .agentkit/source.md so later map/contract steps share one canonical source.",
            ))
        for check in checks:
            if not check["present"]:
                suggestion = next(item[2] for item in _REQUIRED_SECTIONS if item[0] == check["name"])
                findings.append(SourceAuditFinding(
                    code=f"missing_{check['name']}",
                    severity="error",
                    title=f"Missing required {check['name']} guidance",
                    evidence=str(check["evidence"]),
                    suggestion=suggestion,
                ))
        return findings

    def _ambiguity_findings(self, text: str) -> list[SourceAuditFinding]:
        findings: list[SourceAuditFinding] = []
        for code, pattern, suggestion in _AMBIGUITY_PATTERNS:
            matches = []
            for line in text.splitlines():
                if pattern.search(line):
                    snippet = line.strip()
                    if snippet:
                        matches.append(snippet)
                if len(matches) >= 2:
                    break
            if matches:
                findings.append(SourceAuditFinding(
                    code=code,
                    severity="warning",
                    title="Risky ambiguous guidance",
                    evidence=" | ".join(matches),
                    suggestion=suggestion,
                ))
        return findings

    def _contradiction_findings(self, text: str) -> list[SourceAuditFinding]:
        findings: list[SourceAuditFinding] = []
        directive_lines = [line.strip() for line in text.splitlines() if line.strip().startswith(("-", "*")) or re.match(r"^\d+\.\s", line.strip())]
        normalized: dict[str, tuple[bool, str]] = {}
        conflicts: list[tuple[str, str]] = []
        for line in directive_lines:
            statement = re.sub(r"^(-|\*|\d+\.)\s*", "", line).strip().lower()
            polarity, key = self._normalize_directive(statement)
            if not key:
                continue
            seen = normalized.get(key)
            if seen and seen[0] != polarity:
                conflicts.append((seen[1], line.strip()))
            else:
                normalized[key] = (polarity, line.strip())
        headings = self._extract_headings(text)
        heading_counts: dict[str, int] = {}
        for heading in headings:
            heading_counts[heading.lower()] = heading_counts.get(heading.lower(), 0) + 1
        for heading, count in sorted(heading_counts.items()):
            if count > 1:
                conflicts.append((heading, f"Duplicate heading appears {count} times"))
        deduped = []
        seen_pairs = set()
        for left, right in conflicts:
            key = (left, right)
            if key not in seen_pairs:
                seen_pairs.add(key)
                deduped.append((left, right))
        for left, right in deduped[:4]:
            findings.append(SourceAuditFinding(
                code="contradiction",
                severity="error",
                title="Potential contradictory guidance",
                evidence=f"{left} <> {right}",
                suggestion="Resolve the conflicting rules into one explicit instruction before handing the source to coding agents.",
            ))
        return findings

    def _build_readiness(self, checks: list[dict[str, object]], findings: list[SourceAuditFinding], used_fallback: bool) -> SourceAuditReadiness:
        missing = [str(check["name"]) for check in checks if not check["present"]]
        blocker_count = sum(1 for item in findings if item.severity == "error")
        warning_count = sum(1 for item in findings if item.severity == "warning")
        ready = blocker_count == 0 and not used_fallback
        if ready:
            summary = "Ready: source has the required structure for the map -> spec -> contract lane."
        elif blocker_count:
            summary = f"Blocked: fix {blocker_count} structural issue(s) before drafting a contract."
        else:
            summary = "Almost ready: promote the legacy source into .agentkit/source.md to make the lane canonical."
        return SourceAuditReadiness(ready, missing, blocker_count, warning_count, summary)

    def _extract_headings(self, text: str) -> list[str]:
        return [match.group(2).strip() for match in re.finditer(r"^(#{1,6})\s+(.*)$", text, re.MULTILINE)]

    def _normalize_directive(self, statement: str) -> tuple[bool, str]:
        polarity = True
        remainder = statement
        for prefix in _NEGATION_PREFIXES:
            if statement.startswith(prefix):
                polarity = False
                remainder = statement[len(prefix):]
                break
        remainder = re.sub(r"\b(do|always|must|should|only|just|be sure to|ensure|please)\b", "", remainder)
        remainder = re.sub(r"[^a-z0-9 ]+", " ", remainder)
        remainder = re.sub(r"\s+", " ", remainder).strip()
        return polarity, remainder

    def _severity_rank(self, severity: str) -> int:
        return {"error": 0, "warning": 1, "info": 2}.get(severity, 3)
