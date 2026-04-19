from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agentkit_cli.burn_adapters import BurnSession, BurnTurn, load_sessions


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class BurnFinding:
    finding_type: str
    severity: str
    title: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "severity": self.severity,
            "title": self.title,
            "evidence": self.evidence,
        }


@dataclass
class BurnReport:
    generated_at: str
    session_count: int
    turn_count: int
    total_cost_usd: float
    unknown_cost_turns: int
    estimated_cost_turns: int
    totals: dict[str, list[dict[str, Any]]]
    top_sessions: list[dict[str, Any]]
    findings: list[BurnFinding]
    sessions: list[BurnSession]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "session_count": self.session_count,
            "turn_count": self.turn_count,
            "total_cost_usd": self.total_cost_usd,
            "unknown_cost_turns": self.unknown_cost_turns,
            "estimated_cost_turns": self.estimated_cost_turns,
            "totals": self.totals,
            "top_sessions": self.top_sessions,
            "findings": [finding.to_dict() for finding in self.findings],
            "sessions": [session.to_dict() for session in self.sessions],
        }


class BurnAnalysisEngine:
    def load(self, path: Path | str) -> list[BurnSession]:
        return load_sessions(path)

    def analyze(
        self,
        sessions: list[BurnSession],
        since: Optional[str] = None,
        limit: Optional[int] = None,
        project: Optional[str] = None,
    ) -> BurnReport:
        filtered = self._filter_sessions(sessions, since=since, limit=limit, project=project)
        turns = [turn for session in filtered for turn in session.turns]
        total_cost = round(sum(turn.cost.amount_usd or 0.0 for turn in turns), 6)
        unknown_cost_turns = sum(1 for turn in turns if turn.cost.state == "unknown")
        estimated_cost_turns = sum(1 for turn in turns if turn.cost.estimated)
        totals = {
            "by_project": self._aggregate_turns(turns, lambda t: t.project_root or "unknown"),
            "by_model": self._aggregate_turns(turns, lambda t: t.model or "unknown"),
            "by_provider": self._aggregate_turns(turns, lambda t: t.provider or "unknown"),
            "by_task_label": self._aggregate_turns(turns, lambda t: t.task_label or "unlabeled"),
            "by_source": self._aggregate_turns(turns, lambda t: t.source or "unknown"),
        }
        top_sessions = self._top_sessions(filtered)
        findings = self._find_waste_patterns(filtered)
        return BurnReport(
            generated_at=datetime.utcnow().isoformat() + "Z",
            session_count=len(filtered),
            turn_count=len(turns),
            total_cost_usd=total_cost,
            unknown_cost_turns=unknown_cost_turns,
            estimated_cost_turns=estimated_cost_turns,
            totals=totals,
            top_sessions=top_sessions,
            findings=findings,
            sessions=filtered,
        )

    def _filter_sessions(self, sessions: list[BurnSession], since: Optional[str], limit: Optional[int], project: Optional[str]) -> list[BurnSession]:
        result = list(sessions)
        if since:
            result = [s for s in result if (s.started_at or "") >= since]
        if project:
            result = [s for s in result if (s.project_root or "") == project]
        result.sort(key=lambda s: ((s.started_at or ""), s.session_id))
        if limit is not None:
            result = result[-limit:]
        return result

    def _aggregate_turns(self, turns: list[BurnTurn], key_fn) -> list[dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"cost_usd": 0.0, "turns": 0, "tool_calls": 0})
        for turn in turns:
            bucket = buckets[key_fn(turn)]
            bucket["cost_usd"] += turn.cost.amount_usd or 0.0
            bucket["turns"] += 1
            bucket["tool_calls"] += sum(tool.call_count for tool in turn.tool_uses)
        rows = [
            {
                "key": key,
                "cost_usd": round(value["cost_usd"], 6),
                "turns": value["turns"],
                "tool_calls": value["tool_calls"],
            }
            for key, value in buckets.items()
        ]
        rows.sort(key=lambda row: (-row["cost_usd"], -row["turns"], row["key"]))
        return rows

    def _top_sessions(self, sessions: list[BurnSession]) -> list[dict[str, Any]]:
        rows = []
        for session in sessions:
            total_cost = round(sum(turn.cost.amount_usd or 0.0 for turn in session.turns), 6)
            tool_calls = sum(sum(tool.call_count for tool in turn.tool_uses) for turn in session.turns)
            rows.append({
                "session_id": session.session_id,
                "source": session.source,
                "project_root": session.project_root,
                "task_label": session.task_label,
                "turns": len(session.turns),
                "tool_calls": tool_calls,
                "cost_usd": total_cost,
            })
        rows.sort(key=lambda row: (-row["cost_usd"], -row["turns"], row["session_id"]))
        return rows[:10]

    def _find_waste_patterns(self, sessions: list[BurnSession]) -> list[BurnFinding]:
        findings: list[BurnFinding] = []
        for session in sessions:
            turns = session.turns
            session_cost = sum(turn.cost.amount_usd or 0.0 for turn in turns)
            expensive_no_tool = [turn for turn in turns if (turn.cost.amount_usd or 0.0) >= 0.02 and not turn.tool_uses]
            if expensive_no_tool:
                findings.append(BurnFinding(
                    finding_type="expensive_no_tool_turn",
                    severity="high" if len(expensive_no_tool) >= 2 else "medium",
                    title=f"{session.session_id} spent money on assistant-only turns",
                    evidence={"session_id": session.session_id, "count": len(expensive_no_tool), "cost_usd": round(sum(t.cost.amount_usd or 0.0 for t in expensive_no_tool), 6)},
                ))
            labels = [turn.task_label for turn in turns if turn.task_label and turn.task_label != "unlabeled"]
            repeated_labels = Counter(labels)
            retry_count = sum(count for _, count in repeated_labels.items() if count >= 3)
            if retry_count:
                findings.append(BurnFinding(
                    finding_type="retry_loop",
                    severity="high" if retry_count >= 4 else "medium",
                    title=f"{session.session_id} shows retry/edit-test-fix looping",
                    evidence={"session_id": session.session_id, "repeated_task_turns": retry_count, "task_labels": sorted(k for k, v in repeated_labels.items() if v >= 3)},
                ))
            one_shot_success = len(turns) <= 2 and any(turn.tool_uses for turn in turns)
            if not one_shot_success and len(turns) >= 4 and session_cost >= 0.04:
                findings.append(BurnFinding(
                    finding_type="low_one_shot_success",
                    severity="medium" if len(turns) < 6 else "high",
                    title=f"{session.session_id} needed many turns before landing",
                    evidence={"session_id": session.session_id, "turns": len(turns), "cost_usd": round(session_cost, 6)},
                ))
        findings.sort(key=lambda finding: (SEVERITY_ORDER.get(finding.severity, 9), -float(finding.evidence.get("cost_usd", 0.0)), finding.title))
        return findings
