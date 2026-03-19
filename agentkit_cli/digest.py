"""agentkit digest — weekly/daily quality digest across all tracked projects."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from agentkit_cli.history import HistoryDB


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ProjectDigest:
    name: str
    score_start: Optional[float]
    score_end: Optional[float]
    delta: Optional[float]
    runs: int
    status: str  # "improving" | "stable" | "regressing" | "no_data"


@dataclass
class DigestReport:
    period_start: datetime
    period_end: datetime
    projects_tracked: int
    runs_in_period: int
    overall_trend: str  # "improving" | "stable" | "regressing"
    per_project: list[ProjectDigest] = field(default_factory=list)
    regressions: list[tuple] = field(default_factory=list)
    improvements: list[tuple] = field(default_factory=list)
    top_actions: list[str] = field(default_factory=list)
    coverage_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "projects_tracked": self.projects_tracked,
            "runs_in_period": self.runs_in_period,
            "overall_trend": self.overall_trend,
            "per_project": [
                {
                    "name": p.name,
                    "score_start": p.score_start,
                    "score_end": p.score_end,
                    "delta": p.delta,
                    "runs": p.runs,
                    "status": p.status,
                }
                for p in self.per_project
            ],
            "regressions": [
                {"project": r[0], "from_score": r[1], "to_score": r[2], "timestamp": r[3]}
                for r in self.regressions
            ],
            "improvements": [
                {"project": r[0], "from_score": r[1], "to_score": r[2], "timestamp": r[3]}
                for r in self.improvements
            ],
            "top_actions": self.top_actions,
            "coverage_pct": self.coverage_pct,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_REGRESSION_THRESHOLD = -5.0
_IMPROVEMENT_THRESHOLD = 5.0


def _project_status(delta: Optional[float]) -> str:
    if delta is None:
        return "no_data"
    if delta >= _IMPROVEMENT_THRESHOLD:
        return "improving"
    if delta <= _REGRESSION_THRESHOLD:
        return "regressing"
    return "stable"


def _overall_trend(per_project: list[ProjectDigest]) -> str:
    deltas = [p.delta for p in per_project if p.delta is not None]
    if not deltas:
        return "stable"
    avg = sum(deltas) / len(deltas)
    if avg >= _IMPROVEMENT_THRESHOLD:
        return "improving"
    if avg <= _REGRESSION_THRESHOLD:
        return "regressing"
    return "stable"


def _extract_top_actions(rows: list[dict], top_n: int = 5) -> list[str]:
    """Extract most common suggestion strings from findings JSON stored in runs."""
    counts: dict[str, int] = {}
    for row in rows:
        findings_raw = row.get("findings")
        if not findings_raw:
            continue
        try:
            findings = json.loads(findings_raw) if isinstance(findings_raw, str) else findings_raw
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(findings, list):
            for item in findings:
                if isinstance(item, str) and item.strip():
                    key = item.strip()
                    counts[key] = counts.get(key, 0) + 1
                elif isinstance(item, dict):
                    msg = item.get("message") or item.get("text") or item.get("suggestion") or ""
                    if msg:
                        counts[msg.strip()] = counts.get(msg.strip(), 0) + 1
    return [k for k, _ in sorted(counts.items(), key=lambda x: -x[1])[:top_n]]


class DigestEngine:
    """Read-only engine that generates a DigestReport from HistoryDB."""

    def __init__(self, db_path: Optional[Path] = None, period_days: int = 7) -> None:
        self._db = HistoryDB(db_path=db_path)
        self.period_days = period_days

    def generate(self, projects: Optional[list[str]] = None) -> DigestReport:
        """Generate a DigestReport for the configured period.

        Args:
            projects: optional list of project names to filter. None = all.

        Returns:
            DigestReport (never raises on empty data).
        """
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=self.period_days)

        # All known projects (for coverage calculation)
        all_projects = self._db.get_all_projects()
        if projects:
            # filter to requested projects only
            target_projects = [p for p in all_projects if p in projects]
        else:
            target_projects = list(all_projects)

        projects_tracked = len(target_projects)

        # Fetch all runs in period across target projects
        period_runs = self._get_period_runs(period_start, target_projects)
        runs_in_period = len(period_runs)

        # Coverage: % of target projects with ≥1 run in period
        projects_with_runs = set(r["project"] for r in period_runs)
        coverage_pct = (
            round(len(projects_with_runs) / projects_tracked * 100, 1)
            if projects_tracked > 0
            else 0.0
        )

        # Per-project digest
        per_project: list[ProjectDigest] = []
        regressions: list[tuple] = []
        improvements: list[tuple] = []

        for proj in target_projects:
            proj_runs = [r for r in period_runs if r["project"] == proj]
            proj_runs_sorted = sorted(proj_runs, key=lambda r: r["ts"])

            if not proj_runs_sorted:
                per_project.append(
                    ProjectDigest(
                        name=proj,
                        score_start=None,
                        score_end=None,
                        delta=None,
                        runs=0,
                        status="no_data",
                    )
                )
                continue

            score_start = proj_runs_sorted[0]["score"]
            score_end = proj_runs_sorted[-1]["score"]
            delta = round(score_end - score_start, 1) if len(proj_runs_sorted) > 1 else 0.0
            status = _project_status(delta)

            per_project.append(
                ProjectDigest(
                    name=proj,
                    score_start=score_start,
                    score_end=score_end,
                    delta=delta,
                    runs=len(proj_runs_sorted),
                    status=status,
                )
            )

            # Detect significant regressions / improvements
            if delta is not None and delta <= _REGRESSION_THRESHOLD:
                regressions.append((proj, score_start, score_end, proj_runs_sorted[-1]["ts"]))
            elif delta is not None and delta >= _IMPROVEMENT_THRESHOLD:
                improvements.append((proj, score_start, score_end, proj_runs_sorted[-1]["ts"]))

        overall = _overall_trend(per_project)

        # Top actions from findings
        top_actions = _extract_top_actions(period_runs)

        return DigestReport(
            period_start=period_start,
            period_end=now,
            projects_tracked=projects_tracked,
            runs_in_period=runs_in_period,
            overall_trend=overall,
            per_project=per_project,
            regressions=regressions,
            improvements=improvements,
            top_actions=top_actions,
            coverage_pct=coverage_pct,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_period_runs(self, since: datetime, projects: list[str]) -> list[dict]:
        """Fetch all runs since `since` for the given projects (read-only)."""
        if not projects:
            return []
        since_iso = since.isoformat()
        # Use HistoryDB's connection directly via get_history with high limit,
        # then filter by ts. We query per project to stay within the existing API.
        all_rows: list[dict] = []
        for proj in projects:
            rows = self._db.get_history(project=proj, limit=1000)
            for row in rows:
                if row["ts"] >= since_iso:
                    # Also fetch findings via direct SQL if available
                    all_rows.append(row)
        # Also grab findings column via direct query
        # The public get_history doesn't return findings — do a low-level read
        try:
            all_rows = self._get_period_runs_with_findings(since_iso, projects)
        except Exception:  # noqa: BLE001
            pass  # fall back to rows without findings
        return all_rows

    def _get_period_runs_with_findings(self, since_iso: str, projects: list[str]) -> list[dict]:
        """Direct SQL query to include findings column."""
        import sqlite3

        db_path = self._db._path  # type: ignore[attr-defined]
        if not db_path.exists():
            return []
        placeholders = ",".join("?" for _ in projects)
        sql = (
            f"SELECT id, ts, project, tool, score, details, label, findings "
            f"FROM runs WHERE ts >= ? AND project IN ({placeholders}) ORDER BY ts ASC"
        )
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(sql, [since_iso] + list(projects)).fetchall()
        finally:
            conn.close()
        result = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "ts": row["ts"],
                    "project": row["project"],
                    "tool": row["tool"],
                    "score": row["score"],
                    "details": row["details"],
                    "label": row["label"],
                    "findings": row["findings"],
                }
            )
        return result
