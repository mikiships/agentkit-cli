from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentkit_cli.clarify import ClarifyAssumption, ClarifyEngine, ClarifyItem


@dataclass(frozen=True)
class ResolveDecision:
    code: str
    title: str
    status: str
    answer: str
    source_section: str
    kind: str
    rationale: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "title": self.title,
            "status": self.status,
            "answer": self.answer,
            "source_section": self.source_section,
            "kind": self.kind,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ResolveAssumptionUpdate:
    code: str
    statement: str
    status: str
    reason: str = ""
    replacement: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "statement": self.statement,
            "status": self.status,
            "reason": self.reason,
            "replacement": self.replacement,
        }


@dataclass(frozen=True)
class ResolveResult:
    schema_version: str
    project_path: str
    answers_path: str
    execution_recommendation: str
    recommendation_reason: str
    resolved_questions: list[ResolveDecision] = field(default_factory=list)
    remaining_blockers: list[ResolveDecision] = field(default_factory=list)
    remaining_follow_ups: list[ResolveDecision] = field(default_factory=list)
    confirmed_assumptions: list[ResolveAssumptionUpdate] = field(default_factory=list)
    superseded_assumptions: list[ResolveAssumptionUpdate] = field(default_factory=list)
    unresolved_assumptions: list[ResolveAssumptionUpdate] = field(default_factory=list)
    answers_summary: dict[str, int] = field(default_factory=dict)
    source_clarify: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_path": self.project_path,
            "answers_path": self.answers_path,
            "execution_recommendation": self.execution_recommendation,
            "recommendation_reason": self.recommendation_reason,
            "resolved_questions": [item.to_dict() for item in self.resolved_questions],
            "remaining_blockers": [item.to_dict() for item in self.remaining_blockers],
            "remaining_follow_ups": [item.to_dict() for item in self.remaining_follow_ups],
            "confirmed_assumptions": [item.to_dict() for item in self.confirmed_assumptions],
            "superseded_assumptions": [item.to_dict() for item in self.superseded_assumptions],
            "unresolved_assumptions": [item.to_dict() for item in self.unresolved_assumptions],
            "answers_summary": dict(self.answers_summary),
            "source_clarify": self.source_clarify,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class ResolveEngine:
    def __init__(self) -> None:
        self._clarify = ClarifyEngine()

    def build(self, project_dir: str | Path, *, answers_path: str | Path, target: str = "generic") -> ResolveResult:
        project = Path(project_dir).expanduser().resolve()
        answers_file = Path(answers_path).expanduser().resolve()
        if not answers_file.exists() or not answers_file.is_file():
            raise FileNotFoundError(f"Answers file not found: {answers_file}")
        clarify = self._clarify.build(project, target=target)
        answers_payload = json.loads(answers_file.read_text(encoding="utf-8"))
        decisions = self._normalize_answers(answers_payload)
        assumption_updates = self._normalize_assumptions(answers_payload)

        questions = self._question_index(clarify)
        resolved_questions, remaining_blockers, remaining_follow_ups = self._resolve_questions(questions, decisions)
        confirmed_assumptions, superseded_assumptions, unresolved_assumptions = self._resolve_assumptions(clarify.assumptions, assumption_updates)
        recommendation, reason = self._recommendation(remaining_blockers, unresolved_assumptions)

        summary = {
            "resolved_questions": len(resolved_questions),
            "remaining_blockers": len(remaining_blockers),
            "remaining_follow_ups": len(remaining_follow_ups),
            "confirmed_assumptions": len(confirmed_assumptions),
            "superseded_assumptions": len(superseded_assumptions),
            "unresolved_assumptions": len(unresolved_assumptions),
        }
        return ResolveResult(
            schema_version="agentkit.resolve.v1",
            project_path=str(project),
            answers_path=str(answers_file),
            execution_recommendation=recommendation,
            recommendation_reason=reason,
            resolved_questions=resolved_questions,
            remaining_blockers=remaining_blockers,
            remaining_follow_ups=remaining_follow_ups,
            confirmed_assumptions=confirmed_assumptions,
            superseded_assumptions=superseded_assumptions,
            unresolved_assumptions=unresolved_assumptions,
            answers_summary=summary,
            source_clarify=clarify.to_dict(),
        )

    def render_markdown(self, result: ResolveResult) -> str:
        lines = [
            f"# Resolved packet: {Path(result.project_path).name}",
            "",
            f"- Schema: `{result.schema_version}`",
            f"- Project: `{result.project_path}`",
            f"- Answers: `{result.answers_path}`",
            f"- Recommendation: `{result.execution_recommendation}`",
            f"- Reason: {result.recommendation_reason}",
            "",
            "## Summary",
            "",
        ]
        for key, value in result.answers_summary.items():
            lines.append(f"- {key.replace('_', ' ').capitalize()}: {value}")
        self._render_decisions(lines, "Resolved questions", result.resolved_questions, empty="- None.")
        self._render_decisions(lines, "Remaining blockers", result.remaining_blockers, empty="- None.")
        self._render_decisions(lines, "Remaining follow-ups", result.remaining_follow_ups, empty="- None.")
        self._render_assumptions(lines, "Confirmed assumptions", result.confirmed_assumptions)
        self._render_assumptions(lines, "Superseded assumptions", result.superseded_assumptions)
        self._render_assumptions(lines, "Unresolved assumptions", result.unresolved_assumptions)
        return "\n".join(lines).rstrip() + "\n"

    def _render_decisions(self, lines: list[str], heading: str, items: list[ResolveDecision], *, empty: str) -> None:
        lines.extend(["", f"## {heading}", ""])
        if not items:
            lines.append(empty)
            return
        for item in items:
            lines.append(f"### {item.title}")
            lines.append("")
            lines.append(f"- Code: {item.code}")
            lines.append(f"- Status: {item.status}")
            lines.append(f"- Source section: {item.source_section}")
            lines.append(f"- Answer: {item.answer}")
            if item.rationale:
                lines.append(f"- Rationale: {item.rationale}")
            lines.append("")

    def _render_assumptions(self, lines: list[str], heading: str, items: list[ResolveAssumptionUpdate]) -> None:
        lines.extend(["", f"## {heading}", ""])
        if not items:
            lines.append("- None.")
            return
        for item in items:
            lines.append(f"### {item.statement}")
            lines.append("")
            lines.append(f"- Code: {item.code}")
            lines.append(f"- Status: {item.status}")
            if item.reason:
                lines.append(f"- Reason: {item.reason}")
            if item.replacement:
                lines.append(f"- Replacement: {item.replacement}")
            lines.append("")

    def _normalize_answers(self, payload: dict[str, Any]) -> list[dict[str, str]]:
        answers = payload.get("answers") or []
        normalized = []
        for item in answers:
            code = str(item.get("code", "")).strip()
            if not code:
                continue
            normalized.append({
                "code": code,
                "status": str(item.get("status", "resolved")).strip().lower(),
                "answer": str(item.get("answer", "")).strip(),
                "rationale": str(item.get("rationale", "")).strip(),
            })
        return sorted(normalized, key=lambda item: (item["code"], item["status"], item["answer"], item["rationale"]))

    def _normalize_assumptions(self, payload: dict[str, Any]) -> dict[str, dict[str, str]]:
        raw = payload.get("assumptions") or {}
        updates: dict[str, dict[str, str]] = {}
        for code in sorted(raw):
            item = raw[code] or {}
            updates[str(code)] = {
                "status": str(item.get("status", "unresolved")).strip().lower(),
                "reason": str(item.get("reason", "")).strip(),
                "replacement": str(item.get("replacement", "")).strip(),
            }
        return updates

    def _question_index(self, clarify) -> dict[str, tuple[str, ClarifyItem]]:
        indexed: dict[str, tuple[str, ClarifyItem]] = {}
        for section, items in (
            ("blocking_questions", clarify.blocking_questions),
            ("follow_up_questions", clarify.follow_up_questions),
            ("contradictions", clarify.contradictions),
        ):
            for item in items:
                indexed[item.code] = (section, item)
        return indexed

    def _resolve_questions(self, questions: dict[str, tuple[str, ClarifyItem]], decisions: list[dict[str, str]]) -> tuple[list[ResolveDecision], list[ResolveDecision], list[ResolveDecision]]:
        resolved: list[ResolveDecision] = []
        blockers: list[ResolveDecision] = []
        follow_ups: list[ResolveDecision] = []
        resolved_codes: set[str] = set()
        for decision in decisions:
            matched = questions.get(decision["code"])
            if not matched:
                continue
            section, item = matched
            row = ResolveDecision(
                code=item.code,
                title=item.title,
                status=decision["status"],
                answer=decision["answer"],
                source_section=section,
                kind="question",
                rationale=decision["rationale"],
            )
            if decision["status"] in {"resolved", "answered", "confirmed"}:
                resolved.append(row)
                resolved_codes.add(item.code)
            else:
                target = follow_ups if section == "follow_up_questions" and decision["status"] not in {"contradictory", "blocked"} else blockers
                target.append(row)
                resolved_codes.add(item.code)
        for code, (section, item) in sorted(questions.items(), key=lambda pair: (pair[0], pair[1][0], pair[1][1].title)):
            if code in resolved_codes:
                continue
            row = ResolveDecision(
                code=item.code,
                title=item.title,
                status="unanswered",
                answer="",
                source_section=section,
                kind="question",
                rationale="No answer was provided for this clarify item.",
            )
            if section == "follow_up_questions":
                follow_ups.append(row)
            else:
                blockers.append(row)
        resolved.sort(key=lambda item: (item.code, item.title, item.answer, item.status))
        blockers.sort(key=lambda item: (item.code, item.status, item.title, item.answer))
        follow_ups.sort(key=lambda item: (item.code, item.status, item.title, item.answer))
        return resolved, blockers, follow_ups

    def _resolve_assumptions(self, assumptions: list[ClarifyAssumption], updates: dict[str, dict[str, str]]) -> tuple[list[ResolveAssumptionUpdate], list[ResolveAssumptionUpdate], list[ResolveAssumptionUpdate]]:
        confirmed: list[ResolveAssumptionUpdate] = []
        superseded: list[ResolveAssumptionUpdate] = []
        unresolved: list[ResolveAssumptionUpdate] = []
        for item in sorted(assumptions, key=lambda value: (value.code, value.statement)):
            update = updates.get(item.code, {"status": "unresolved", "reason": "", "replacement": ""})
            row = ResolveAssumptionUpdate(
                code=item.code,
                statement=item.statement,
                status=update["status"],
                reason=update["reason"],
                replacement=update["replacement"],
            )
            if update["status"] == "confirmed":
                confirmed.append(row)
            elif update["status"] == "superseded":
                superseded.append(row)
            else:
                unresolved.append(row)
        return confirmed, superseded, unresolved

    def _recommendation(self, remaining_blockers: list[ResolveDecision], unresolved_assumptions: list[ResolveAssumptionUpdate]) -> tuple[str, str]:
        if remaining_blockers:
            return "pause", "Open clarify items or contradictory answers still block execution."
        if unresolved_assumptions:
            return "proceed-with-assumptions", "Questions are resolved, but at least one assumption still needs explicit acknowledgment."
        return "proceed", "All clarify items were resolved and assumptions were either confirmed or superseded."
