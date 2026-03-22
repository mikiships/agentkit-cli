"""agentkit weekly engine — 7-day quality digest across tracked projects.

Reads the SQLite history DB (shared with `agentkit history`) to surface:
- Per-project score trends over the past week
- Portfolio-wide summary stats
- Top improving/regressing projects
- Common findings & recommended actions
- Tweet-ready summary text
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from agentkit_cli.history import HistoryDB

_DEFAULT_DB = Path.home() / ".config" / "agentkit" / "history.db"

_REGRESSION_THRESHOLD = -5.0
_IMPROVEMENT_THRESHOLD = 5.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class WeeklyProjectStat:
    """Score statistics for one project over the report window."""

    name: str
    score_start: Optional[float]
    score_end: Optional[float]
    delta: Optional[float]
    runs: int
    status: str  # "improving" | "stable" | "regressing" | "no_data"
    top_finding: Optional[str] = None


@dataclass
class WeeklyReport:
    """Full weekly report data."""

    period_start: datetime
    period_end: datetime
    projects_tracked: int
    runs_in_period: int
    overall_trend: str  # "improving" | "stable" | "regressing"
    per_project: list[WeeklyProjectStat] = field(default_factory=list)
    top_improvements: list[WeeklyProjectStat] = field(default_factory=list)
    top_regressions: list[WeeklyProjectStat] = field(default_factory=list)
    common_findings: list[str] = field(default_factory=list)
    top_actions: list[str] = field(default_factory=list)
    tweet_text: str = ""
    avg_score: Optional[float] = None
    coverage_pct: float = 0.0

    def to_dict(self) -> dict:
        def _stat(p: WeeklyProjectStat) -> dict:
            return {
                "name": p.name,
                "score_start": p.score_start,
                "score_end": p.score_end,
                "delta": p.delta,
                "runs": p.runs,
                "status": p.status,
                "top_finding": p.top_finding,
            }

        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "projects_tracked": self.projects_tracked,
            "runs_in_period": self.runs_in_period,
            "overall_trend": self.overall_trend,
            "avg_score": self.avg_score,
            "coverage_pct": self.coverage_pct,
            "per_project": [_stat(p) for p in self.per_project],
            "top_improvements": [_stat(p) for p in self.top_improvements],
            "top_regressions": [_stat(p) for p in self.top_regressions],
            "common_findings": self.common_findings,
            "top_actions": self.top_actions,
            "tweet_text": self.tweet_text,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _project_status(delta: Optional[float]) -> str:
    if delta is None:
        return "no_data"
    if delta >= _IMPROVEMENT_THRESHOLD:
        return "improving"
    if delta <= _REGRESSION_THRESHOLD:
        return "regressing"
    return "stable"


def _overall_trend(stats: list[WeeklyProjectStat]) -> str:
    improving = sum(1 for s in stats if s.status == "improving")
    regressing = sum(1 for s in stats if s.status == "regressing")
    if improving > regressing:
        return "improving"
    if regressing > improving:
        return "regressing"
    return "stable"


def _extract_top_actions(runs: list[dict], top_n: int = 5) -> list[str]:
    """Extract most common actionable findings from the findings JSON column."""
    from collections import Counter

    counter: Counter = Counter()
    for run in runs:
        findings_raw = run.get("findings")
        if not findings_raw:
            continue
        try:
            findings = json.loads(findings_raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(findings, list):
            for f in findings:
                if isinstance(f, dict):
                    action = f.get("action") or f.get("title") or f.get("message")
                    if action and isinstance(action, str):
                        counter[action.strip()] += 1
                elif isinstance(f, str):
                    counter[f.strip()] += 1
    return [item for item, _ in counter.most_common(top_n)]


def _extract_common_findings(runs: list[dict], min_projects: int = 2, top_n: int = 5) -> list[str]:
    """Findings appearing in at least *min_projects* distinct projects."""
    from collections import Counter, defaultdict

    finding_projects: dict[str, set] = defaultdict(set)
    for run in runs:
        project = run.get("project", "")
        findings_raw = run.get("findings")
        if not findings_raw or not project:
            continue
        try:
            findings = json.loads(findings_raw)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(findings, list):
            for f in findings:
                key = None
                if isinstance(f, dict):
                    key = f.get("title") or f.get("message") or f.get("action")
                elif isinstance(f, str):
                    key = f
                if key:
                    finding_projects[key.strip()].add(project)

    common = [(k, len(v)) for k, v in finding_projects.items() if len(v) >= min_projects]
    common.sort(key=lambda x: -x[1])
    return [k for k, _ in common[:top_n]]


def _make_tweet(report: "WeeklyReport") -> str:
    """Generate a tweet-ready summary (≤280 chars)."""
    trend_emoji = {"improving": "📈", "regressing": "📉", "stable": "➡️"}.get(
        report.overall_trend, "➡️"
    )
    avg_str = f"{report.avg_score:.1f}" if report.avg_score is not None else "N/A"
    week_str = report.period_start.strftime("%b %d")
    tweet = (
        f"agentkit weekly {week_str} {trend_emoji}\n"
        f"{report.projects_tracked} projects · avg score {avg_str} · "
        f"{report.runs_in_period} runs\n"
        f"Trend: {report.overall_trend}\n"
        "#agentkit #devtools"
    )
    if len(tweet) > 280:
        tweet = tweet[:277] + "..."
    return tweet


class WeeklyReportEngine:
    """Generate a 7-day quality digest from the agentkit history DB."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB
        self._db = HistoryDB(db_path=self._db_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        days: int = 7,
        projects: Optional[list[str]] = None,
    ) -> WeeklyReport:
        """Generate the weekly report for the last *days* days."""
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(days=days)

        all_projects = projects or self._db.get_all_projects()
        if not all_projects:
            return WeeklyReport(
                period_start=period_start,
                period_end=now,
                projects_tracked=0,
                runs_in_period=0,
                overall_trend="stable",
            )

        period_runs = self._get_period_runs(since=period_start, projects=all_projects)
        runs_in_period = len(period_runs)

        per_project: list[WeeklyProjectStat] = []
        all_end_scores: list[float] = []

        for proj in all_projects:
            proj_runs = sorted(
                [r for r in period_runs if r.get("project") == proj and r.get("tool") == "overall"],
                key=lambda r: r["ts"],
            )
            if not proj_runs:
                per_project.append(
                    WeeklyProjectStat(
                        name=proj,
                        score_start=None,
                        score_end=None,
                        delta=None,
                        runs=0,
                        status="no_data",
                    )
                )
                continue

            score_start = proj_runs[0]["score"]
            score_end = proj_runs[-1]["score"]
            delta = round(score_end - score_start, 1) if len(proj_runs) > 1 else 0.0
            status = _project_status(delta)
            all_end_scores.append(score_end)

            # Top finding from most recent run
            top_finding = self._extract_top_finding(proj_runs[-1])

            per_project.append(
                WeeklyProjectStat(
                    name=proj,
                    score_start=score_start,
                    score_end=score_end,
                    delta=delta,
                    runs=len(proj_runs),
                    status=status,
                    top_finding=top_finding,
                )
            )

        overall_trend = _overall_trend(per_project)
        avg_score = (
            round(sum(all_end_scores) / len(all_end_scores), 1)
            if all_end_scores
            else None
        )

        projects_with_data = sum(1 for p in per_project if p.status != "no_data")
        coverage_pct = (
            round(projects_with_data / len(per_project) * 100, 1) if per_project else 0.0
        )

        top_improvements = sorted(
            [p for p in per_project if p.status == "improving"],
            key=lambda p: -(p.delta or 0),
        )[:5]
        top_regressions = sorted(
            [p for p in per_project if p.status == "regressing"],
            key=lambda p: (p.delta or 0),
        )[:5]

        common_findings = _extract_common_findings(period_runs)
        top_actions = _extract_top_actions(period_runs)

        report = WeeklyReport(
            period_start=period_start,
            period_end=now,
            projects_tracked=len(all_projects),
            runs_in_period=runs_in_period,
            overall_trend=overall_trend,
            per_project=per_project,
            top_improvements=top_improvements,
            top_regressions=top_regressions,
            common_findings=common_findings,
            top_actions=top_actions,
            avg_score=avg_score,
            coverage_pct=coverage_pct,
        )
        report.tweet_text = _make_tweet(report)
        return report

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _extract_top_finding(self, run: dict) -> Optional[str]:
        findings_raw = run.get("findings")
        if not findings_raw:
            # Try details
            details_raw = run.get("details")
            if details_raw:
                try:
                    details = json.loads(details_raw)
                    if isinstance(details, dict):
                        findings = details.get("findings", [])
                        if findings and isinstance(findings, list):
                            f = findings[0]
                            if isinstance(f, dict):
                                return f.get("title") or f.get("message") or f.get("action")
                            return str(f)
                except (json.JSONDecodeError, TypeError):
                    pass
            return None
        try:
            findings = json.loads(findings_raw)
        except (json.JSONDecodeError, TypeError):
            return None
        if isinstance(findings, list) and findings:
            f = findings[0]
            if isinstance(f, dict):
                return f.get("title") or f.get("message") or f.get("action")
            return str(f)
        return None

    def _get_period_runs(self, since: datetime, projects: list[str]) -> list[dict]:
        """Fetch all runs since *since* for the given projects."""
        if not projects:
            return []
        if not self._db_path.exists():
            return []
        try:
            return self._get_period_runs_sql(since.isoformat(), projects)
        except Exception:
            # Fallback: use public API
            result = []
            since_iso = since.isoformat()
            for proj in projects:
                rows = self._db.get_history(project=proj, limit=1000)
                for row in rows:
                    if row.get("ts", "") >= since_iso:
                        result.append(row)
            return result

    def _get_period_runs_sql(self, since_iso: str, projects: list[str]) -> list[dict]:
        """Direct SQL to include findings column."""
        placeholders = ",".join("?" for _ in projects)
        sql = (
            "SELECT id, ts, project, tool, score, details, label, findings "
            "FROM runs WHERE ts >= ? AND project IN ({}) ORDER BY ts ASC".format(
                placeholders
            )
        )
        conn = sqlite3.connect(str(self._db_path))
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
                    "label": row.get("label"),
                    "findings": row.get("findings"),
                }
            )
        return result
