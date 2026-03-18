"""agentkit timeline — visual quality timeline from history DB."""
from __future__ import annotations

import statistics
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from agentkit_cli.history import HistoryDB

# Score tools recognized for per-tool breakdown
SCORE_TOOLS = ["agentlint", "coderace", "agentmd", "agentreflect"]
STREAK_THRESHOLD = 80.0


class TimelineEngine:
    """Load history runs and build chart-ready data structures."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db = HistoryDB(db_path=db_path)

    # ------------------------------------------------------------------
    # D1 core methods
    # ------------------------------------------------------------------

    def load_runs(self, project: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Query history DB and return runs sorted oldest-first.

        If project is None, loads all projects. Runs with tool='overall'
        are the primary composite score rows; per-tool rows carry breakdown.
        """
        rows = self._db.get_history(project=project, limit=limit)
        # get_history returns newest-first; reverse to oldest-first for chart ordering
        return list(reversed(rows))

    def build_chart_data(self, runs: list[dict]) -> dict:
        """Extract dates, composite scores, and per-tool scores from raw runs.

        Returns a dict with keys:
          dates        — list[str]  (ISO date strings, oldest-first)
          scores       — list[float|None]  (composite scores)
          per_tool     — dict[tool_name, list[float|None]]
          projects     — list[str]  (distinct project names in order of appearance)
          by_project   — dict[project_name, {dates, scores, per_tool}]
        """
        if not runs:
            return {
                "dates": [],
                "scores": [],
                "per_tool": {t: [] for t in SCORE_TOOLS},
                "projects": [],
                "by_project": {},
            }

        # Group by project
        project_map: dict[str, list[dict]] = {}
        for run in runs:
            p = run.get("project") or "unknown"
            project_map.setdefault(p, []).append(run)

        by_project: dict[str, dict] = {}
        for proj, proj_runs in project_map.items():
            by_project[proj] = self._build_project_chart(proj_runs)

        # Flatten: collect all dates and matching composite scores across projects
        all_dates: list[str] = []
        all_scores: list[float | None] = []
        seen: set[str] = set()

        # Merge overall-scored runs across all projects by date
        overall_rows = [r for r in runs if r.get("tool") in ("overall", None)]
        for row in overall_rows:
            ts = row.get("ts", "")
            d = ts[:10] if ts else ""
            key = f"{row.get('project')}|{ts}"
            if key not in seen:
                seen.add(key)
                all_dates.append(d)
                all_scores.append(row.get("score"))

        return {
            "dates": all_dates,
            "scores": all_scores,
            "per_tool": self._aggregate_per_tool(runs, all_dates),
            "projects": list(project_map.keys()),
            "by_project": by_project,
        }

    def _build_project_chart(self, proj_runs: list[dict]) -> dict:
        """Build chart data for a single project's runs."""
        overall_rows = [r for r in proj_runs if r.get("tool") in ("overall", None)]
        dates = [r.get("ts", "")[:10] for r in overall_rows]
        scores = [r.get("score") for r in overall_rows]

        per_tool: dict[str, list[float | None]] = {}
        for tool in SCORE_TOOLS:
            tool_by_date: dict[str, float | None] = {}
            for r in proj_runs:
                if r.get("tool") == tool:
                    d = r.get("ts", "")[:10]
                    tool_by_date[d] = r.get("score")
            per_tool[tool] = [tool_by_date.get(d) for d in dates]

        return {"dates": dates, "scores": scores, "per_tool": per_tool}

    def _aggregate_per_tool(
        self, runs: list[dict], dates: list[str]
    ) -> dict[str, list[float | None]]:
        """Build per-tool score lists aligned to the provided dates."""
        date_tool_score: dict[str, dict[str, float | None]] = {}
        for run in runs:
            tool = run.get("tool")
            if tool in SCORE_TOOLS:
                d = run.get("ts", "")[:10]
                date_tool_score.setdefault(d, {})[tool] = run.get("score")

        result: dict[str, list[float | None]] = {}
        for tool in SCORE_TOOLS:
            result[tool] = [date_tool_score.get(d, {}).get(tool) for d in dates]
        return result

    def compute_stats(self, runs: list[dict]) -> dict:
        """Compute summary statistics across a list of runs.

        Returns:
          min, max, avg — float (based on overall/composite scores)
          trend         — "improving" | "stable" | "declining"
          trend_delta   — float  (positive = improving)
          streak        — int  (consecutive runs above STREAK_THRESHOLD)
          run_count     — int
        """
        overall_scores = [
            r["score"]
            for r in runs
            if r.get("tool") in ("overall", None) and r.get("score") is not None
        ]

        if not overall_scores:
            return {
                "min": None,
                "max": None,
                "avg": None,
                "trend": "stable",
                "trend_delta": 0.0,
                "streak": 0,
                "run_count": 0,
            }

        mn = round(min(overall_scores), 1)
        mx = round(max(overall_scores), 1)
        avg = round(statistics.mean(overall_scores), 1)

        # Trend: compare average of last 3 vs first 3
        if len(overall_scores) >= 4:
            first_avg = statistics.mean(overall_scores[:3])
            last_avg = statistics.mean(overall_scores[-3:])
        elif len(overall_scores) >= 2:
            mid = len(overall_scores) // 2
            first_avg = statistics.mean(overall_scores[:mid] or overall_scores[:1])
            last_avg = statistics.mean(overall_scores[mid:] or overall_scores[-1:])
        else:
            first_avg = last_avg = overall_scores[0]

        delta = round(last_avg - first_avg, 1)
        if delta > 2:
            trend = "improving"
        elif delta < -2:
            trend = "declining"
        else:
            trend = "stable"

        # Streak: consecutive runs at end above threshold
        streak = 0
        for score in reversed(overall_scores):
            if score >= STREAK_THRESHOLD:
                streak += 1
            else:
                break

        return {
            "min": mn,
            "max": mx,
            "avg": avg,
            "trend": trend,
            "trend_delta": delta,
            "streak": streak,
            "run_count": len(overall_scores),
        }

    def build_full_payload(
        self,
        project: Optional[str] = None,
        limit: int = 100,
        since: Optional[str] = None,
    ) -> dict:
        """Convenience: load + filter + chart + stats in one call."""
        runs = self.load_runs(project=project, limit=limit)

        if since:
            runs = [r for r in runs if r.get("ts", "") >= since]

        chart = self.build_chart_data(runs)

        # Per-project stats
        if project:
            stats = self.compute_stats(runs)
        else:
            stats = self.compute_stats(runs)

        return {
            "project": project,
            "chart": chart,
            "stats": stats,
            "runs": runs,
        }
