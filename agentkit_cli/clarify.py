from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agentkit_cli.bundle import BundleEngine, BundleGap, HandoffBundle
from agentkit_cli.taskpack import TaskpackEngine


_RECOMMENDATION_ORDER = {
    "pause": 0,
    "proceed-with-assumptions": 1,
    "proceed": 2,
}


@dataclass(frozen=True)
class ClarifyItem:
    priority: int
    code: str
    title: str
    question: str
    evidence: list[str] = field(default_factory=list)
    action: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "priority": self.priority,
            "code": self.code,
            "title": self.title,
            "question": self.question,
            "evidence": list(self.evidence),
            "action": self.action,
        }


@dataclass(frozen=True)
class ClarifyAssumption:
    code: str
    statement: str
    confidence: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "statement": self.statement,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ClarifyResult:
    schema_version: str
    project_path: str
    execution_recommendation: str
    recommendation_reason: str
    blocking_questions: list[ClarifyItem] = field(default_factory=list)
    follow_up_questions: list[ClarifyItem] = field(default_factory=list)
    assumptions: list[ClarifyAssumption] = field(default_factory=list)
    contradictions: list[ClarifyItem] = field(default_factory=list)
    upstream_status: dict[str, object] = field(default_factory=dict)
    source_bundle: dict[str, object] = field(default_factory=dict)
    source_taskpack: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_path": self.project_path,
            "execution_recommendation": self.execution_recommendation,
            "recommendation_reason": self.recommendation_reason,
            "blocking_questions": [item.to_dict() for item in self.blocking_questions],
            "follow_up_questions": [item.to_dict() for item in self.follow_up_questions],
            "assumptions": [item.to_dict() for item in self.assumptions],
            "contradictions": [item.to_dict() for item in self.contradictions],
            "upstream_status": self.upstream_status,
            "source_bundle": self.source_bundle,
            "source_taskpack": self.source_taskpack,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class ClarifyEngine:
    def __init__(self) -> None:
        self._bundle = BundleEngine()
        self._taskpack = TaskpackEngine()

    def build(self, project_dir: str | Path, *, target: str = "generic") -> ClarifyResult:
        root = Path(project_dir).expanduser().resolve()
        bundle = self._bundle.build(root)
        taskpack = self._taskpack.build(root, target=target)

        blocking_questions = self._blocking_questions(bundle)
        follow_up_questions = self._follow_up_questions(bundle, taskpack)
        contradictions = self._contradictions(bundle)
        assumptions = self._assumptions(bundle, taskpack)
        recommendation, reason = self._recommendation(bundle, blocking_questions, contradictions, assumptions)

        return ClarifyResult(
            schema_version="agentkit.clarify.v1",
            project_path=str(root),
            execution_recommendation=recommendation,
            recommendation_reason=reason,
            blocking_questions=blocking_questions,
            follow_up_questions=follow_up_questions,
            assumptions=assumptions,
            contradictions=contradictions,
            upstream_status=self._upstream_status(bundle),
            source_bundle=bundle.to_dict(),
            source_taskpack=taskpack.to_dict(),
        )

    def render_markdown(self, result: ClarifyResult) -> str:
        lines = [
            f"# Clarification brief: {Path(result.project_path).name}",
            "",
            f"- Schema: `{result.schema_version}`",
            f"- Project: `{result.project_path}`",
            f"- Recommendation: `{result.execution_recommendation}`",
            f"- Reason: {result.recommendation_reason}",
            "",
            "## Upstream status",
            "",
        ]
        for key, value in result.upstream_status.items():
            lines.append(f"- {key.replace('_', ' ').capitalize()}: {value}")
        self._render_items(lines, "Blocking questions", result.blocking_questions, empty="- None.")
        self._render_items(lines, "Follow-up questions", result.follow_up_questions, empty="- None.")
        lines.extend(["", "## Assumptions", ""])
        if result.assumptions:
            for item in result.assumptions:
                lines.append(f"### {item.statement}")
                lines.append("")
                lines.append(f"- Confidence: {item.confidence}")
                for evidence in item.evidence:
                    lines.append(f"- Evidence: {evidence}")
                lines.append("")
        else:
            lines.append("- None.")
        self._render_items(lines, "Contradictions", result.contradictions, empty="- None.")
        return "\n".join(lines).rstrip() + "\n"

    def _render_items(self, lines: list[str], heading: str, items: list[ClarifyItem], *, empty: str) -> None:
        lines.extend(["", f"## {heading}", ""])
        if not items:
            lines.append(empty)
            return
        for item in items:
            lines.append(f"### P{item.priority} {item.title}")
            lines.append("")
            lines.append(f"- Question: {item.question}")
            if item.action:
                lines.append(f"- Action: {item.action}")
            for evidence in item.evidence:
                lines.append(f"- Evidence: {evidence}")
            lines.append("")

    def _upstream_status(self, bundle: HandoffBundle) -> dict[str, object]:
        readiness = bundle.source_audit.get("readiness") or {}
        return {
            "source_ready": bool(readiness.get("ready_for_contract")),
            "source_blockers": int(readiness.get("blocker_count", 0)),
            "source_warnings": int(readiness.get("warning_count", 0)),
            "contract_mode": bundle.contract.mode,
            "contract_missing": bundle.contract.missing,
            "gap_count": len(bundle.gaps),
        }

    def _blocking_questions(self, bundle: HandoffBundle) -> list[ClarifyItem]:
        items: list[ClarifyItem] = []
        for gap in bundle.gaps:
            if gap.code not in {"missing_source", "source_not_ready", "missing_contract_artifact"}:
                continue
            items.append(
                ClarifyItem(
                    priority=1,
                    code=gap.code,
                    title=gap.title,
                    question=self._gap_question(gap),
                    evidence=[gap.detail],
                    action=gap.action,
                )
            )
        return self._sorted_items(items)

    def _follow_up_questions(self, bundle: HandoffBundle, taskpack) -> list[ClarifyItem]:
        items: list[ClarifyItem] = []
        for hint in bundle.architecture_map.get("hints") or []:
            if hint.get("kind") not in {"next_task", "risk", "work_surface"}:
                continue
            items.append(
                ClarifyItem(
                    priority=2,
                    code=f"hint_{hint.get('kind')}",
                    title=hint.get("title", "Repo hint"),
                    question=f"Does the implementation need to account for: {hint.get('detail', '').strip()}?",
                    evidence=[hint.get("detail", "")],
                    action="Confirm whether this hint changes scope, tests, or sequencing.",
                )
            )
        checklist = taskpack.execution.checklist if hasattr(taskpack, "execution") else []
        if checklist:
            items.append(
                ClarifyItem(
                    priority=3,
                    code="execution_checklist_review",
                    title="Execution checklist review",
                    question="Are the listed execution checks sufficient for this handoff, or do we need more target-specific validation?",
                    evidence=[item.label for item in checklist[:3]],
                    action="Tighten the handoff packet if any critical check is missing.",
                )
            )
        return self._sorted_items(items)

    def _contradictions(self, bundle: HandoffBundle) -> list[ClarifyItem]:
        findings = bundle.source_audit.get("findings") or []
        items = [
            ClarifyItem(
                priority=1,
                code=item.get("code", "contradiction"),
                title=item.get("title", "Potential contradictory guidance"),
                question="Which instruction is authoritative enough for the coding agent to follow?",
                evidence=[item.get("evidence", "")],
                action=item.get("suggestion", "Resolve the conflict before execution."),
            )
            for item in findings
            if item.get("code") == "contradiction"
        ]
        preview = bundle.contract.preview
        contradictory_pairs = self._find_preview_contradictions(preview)
        for left, right in contradictory_pairs:
            items.append(
                ClarifyItem(
                    priority=1,
                    code="contract_preview_contradiction",
                    title="Contract preview contradiction",
                    question="Which contract instruction should survive into execution?",
                    evidence=[left, right],
                    action="Rewrite the saved contract so it states one deterministic rule.",
                )
            )
        return self._sorted_items(items)

    def _assumptions(self, bundle: HandoffBundle, taskpack) -> list[ClarifyAssumption]:
        assumptions: list[ClarifyAssumption] = []
        summary = bundle.architecture_map.get("summary") or {}
        if summary.get("primary_language"):
            assumptions.append(
                ClarifyAssumption(
                    code="primary_language",
                    statement=f"Implementation likely centers on {summary['primary_language']} surfaces.",
                    confidence="medium",
                    evidence=[f"Repo map primary language: {summary['primary_language']}"] ,
                )
            )
        if bundle.contract.mode == "map-handoff-fallback":
            assumptions.append(
                ClarifyAssumption(
                    code="fallback_contract",
                    statement="Execution may proceed from repo-map context even though no saved contract artifact exists.",
                    confidence="low",
                    evidence=["Bundle fell back to the repo-map handoff prompt instead of a saved contract file."],
                )
            )
        notes = getattr(taskpack.execution, "notes", [])
        if notes:
            assumptions.append(
                ClarifyAssumption(
                    code="runner_notes",
                    statement="Target-specific runner notes are sufficient unless the user requests stricter execution policy.",
                    confidence="medium",
                    evidence=notes[:2],
                )
            )
        assumptions.sort(key=lambda item: (item.code, item.statement))
        return assumptions

    def _recommendation(self, bundle: HandoffBundle, blocking: list[ClarifyItem], contradictions: list[ClarifyItem], assumptions: list[ClarifyAssumption]) -> tuple[str, str]:
        if blocking or contradictions:
            return "pause", "Blocking gaps or contradictions remain unresolved in the handoff lane."
        low_confidence = sum(1 for item in assumptions if item.confidence == "low")
        warnings = int((bundle.source_audit.get("readiness") or {}).get("warning_count", 0))
        if low_confidence or warnings:
            return "proceed-with-assumptions", "The lane is usable, but at least one assumption or warning should be acknowledged before execution."
        return "proceed", "No blocking gaps or contradictions were detected across the bundle and taskpack surfaces."

    def _gap_question(self, gap: BundleGap) -> str:
        if gap.code == "missing_source":
            return "What canonical source of truth should the coding agent follow?"
        if gap.code == "source_not_ready":
            return "Which source-audit blockers must be fixed before drafting or executing the taskpack?"
        if gap.code == "missing_contract_artifact":
            return "Should we save an explicit all-day build contract before handing this work to a coding agent?"
        return f"How should we resolve: {gap.title}?"

    def _sorted_items(self, items: list[ClarifyItem]) -> list[ClarifyItem]:
        return sorted(items, key=lambda item: (item.priority, item.code, item.title, item.question, tuple(item.evidence)))

    def _find_preview_contradictions(self, text: str) -> list[tuple[str, str]]:
        if not text:
            return []
        directives = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith(("- ", "* ")) and not re.match(r"^\d+\.\s", line):
                continue
            statement = re.sub(r"^(-|\*|\d+\.)\s*", "", line).strip().lower()
            polarity = not statement.startswith(("do not ", "don't ", "never ", "avoid ", "skip ", "no "))
            normalized = re.sub(r"\b(do|always|must|should|only|just|be sure to|ensure|please)\b", "", statement)
            normalized = re.sub(r"[^a-z0-9 ]+", " ", normalized)
            normalized = re.sub(r"\s+", " ", normalized).strip()
            if normalized:
                directives.append((normalized, polarity, line))
        seen: dict[str, tuple[bool, str]] = {}
        conflicts: list[tuple[str, str]] = []
        for key, polarity, line in directives:
            prior = seen.get(key)
            if prior and prior[0] != polarity:
                conflicts.append((prior[1], line))
            else:
                seen[key] = (polarity, line)
        return sorted(set(conflicts))
