"""agentkit insights — cross-run pattern synthesis engine.

Reads the SQLite history DB (shared with `agentkit history`) to surface:
- Common findings across multiple repos
- Outlier repos (bottom quartile)
- Trending repos (recent score movement)
- Portfolio-level summary stats
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

_DEFAULT_DB = Path.home() / ".config" / "agentkit" / "history.db"


class InsightsEngine:
    """Synthesize patterns from the agentkit history DB."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._path = Path(db_path) if db_path else _DEFAULT_DB
        self._ensure_findings_column()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    def _db_exists(self) -> bool:
        return self._path.exists()

    def _ensure_findings_column(self) -> None:
        """Add findings column to runs table if not present (migration-safe)."""
        if not self._db_exists():
            return
        try:
            with self._connect() as conn:
                try:
                    conn.execute("ALTER TABLE runs ADD COLUMN findings TEXT")
                except sqlite3.OperationalError:
                    pass  # column already exists
        except Exception:
            pass

    def _all_runs(self) -> list[dict]:
        """Return all runs ordered oldest-first."""
        if not self._db_exists():
            return []
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id, ts, project, tool, score, details, findings, label "
                    "FROM runs ORDER BY ts ASC"
                ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            # findings column may not exist yet on very old DBs — fall back
            try:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT id, ts, project, tool, score, details, label "
                        "FROM runs ORDER BY ts ASC"
                    ).fetchall()
                result = []
                for r in rows:
                    d = dict(r)
                    d["findings"] = None
                    result.append(d)
                return result
            except Exception:
                return []
        except Exception:
            return []

    def _overall_runs(self) -> list[dict]:
        """Return only tool='overall' rows."""
        return [r for r in self._all_runs() if r.get("tool") == "overall"]

    def _runs_by_project(self) -> dict[str, list[dict]]:
        """Group overall runs by project, preserving chronological order."""
        groups: dict[str, list[dict]] = defaultdict(list)
        for run in self._overall_runs():
            groups[run["project"]].append(run)
        return dict(groups)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_common_findings(self, min_repos: int = 2) -> list[dict]:
        """Return findings that appear in at least *min_repos* distinct repos.

        Returns:
            List of dicts: {finding, repo_count, total_occurrences}
            sorted by repo_count desc.
        """
        runs = self._all_runs()
        if not runs:
            return []

        # finding → set of repos it appeared in
        finding_repos: dict[str, set] = defaultdict(set)
        finding_count: Counter = Counter()

        for run in runs:
            findings_raw = run.get("findings")
            if not findings_raw:
                # Try to parse from details field as fallback
                details_raw = run.get("details")
                if details_raw:
                    try:
                        details = json.loads(details_raw) if isinstance(details_raw, str) else details_raw
                        findings_list = details.get("findings", []) if isinstance(details, dict) else []
                    except (json.JSONDecodeError, AttributeError):
                        findings_list = []
                else:
                    findings_list = []
            else:
                try:
                    findings_list = json.loads(findings_raw) if isinstance(findings_raw, str) else findings_raw
                    if not isinstance(findings_list, list):
                        findings_list = []
                except (json.JSONDecodeError, TypeError):
                    findings_list = []

            repo = run.get("project", "")
            for finding in findings_list:
                if isinstance(finding, str):
                    key = finding
                elif isinstance(finding, dict):
                    key = finding.get("code") or finding.get("message") or str(finding)
                else:
                    continue
                finding_repos[key].add(repo)
                finding_count[key] += 1

        results = []
        for finding, repos in finding_repos.items():
            if len(repos) >= min_repos:
                results.append({
                    "finding": finding,
                    "repo_count": len(repos),
                    "total_occurrences": finding_count[finding],
                })

        results.sort(key=lambda x: (x["repo_count"], x["total_occurrences"]), reverse=True)
        return results

    def get_outliers(self, percentile: int = 25) -> list[dict]:
        """Return repos scoring in the bottom *percentile* of history.

        Returns:
            List of dicts: {project, latest_score, avg_score, run_count}
            sorted by latest_score asc.
        """
        by_project = self._runs_by_project()
        if not by_project:
            return []

        # Build per-project stats
        project_stats: list[dict] = []
        for project, runs in by_project.items():
            scores = [r["score"] for r in runs]
            latest = scores[-1]
            avg = sum(scores) / len(scores)
            project_stats.append({
                "project": project,
                "latest_score": round(latest, 1),
                "avg_score": round(avg, 1),
                "run_count": len(runs),
            })

        if not project_stats:
            return []

        # Compute percentile threshold against latest scores
        all_latest = sorted(s["latest_score"] for s in project_stats)
        cutoff_idx = max(0, int(len(all_latest) * percentile / 100) - 1)
        threshold = all_latest[cutoff_idx]

        outliers = [s for s in project_stats if s["latest_score"] <= threshold]
        outliers.sort(key=lambda x: x["latest_score"])
        return outliers

    def get_trending(self, window: int = 5) -> list[dict]:
        """Return repos with score change >10 between their last two runs.

        Args:
            window: look at only the most recent *window* runs per project.

        Returns:
            List of dicts: {project, previous_score, latest_score, delta, direction}
            sorted by abs(delta) desc.
        """
        by_project = self._runs_by_project()
        if not by_project:
            return []

        trending = []
        for project, runs in by_project.items():
            recent = runs[-window:] if len(runs) >= 2 else runs
            if len(recent) < 2:
                continue
            prev = recent[-2]["score"]
            latest = recent[-1]["score"]
            delta = round(latest - prev, 1)
            if abs(delta) > 10:
                trending.append({
                    "project": project,
                    "previous_score": round(prev, 1),
                    "latest_score": round(latest, 1),
                    "delta": delta,
                    "direction": "up" if delta > 0 else "down",
                })

        trending.sort(key=lambda x: abs(x["delta"]), reverse=True)
        return trending

    def get_portfolio_summary(self) -> dict[str, Any]:
        """Return high-level portfolio statistics.

        Returns:
            Dict with: avg_score, total_runs, unique_repos, top_issue,
                       best_repo, worst_repo
        """
        overall = self._overall_runs()

        if not overall:
            return {
                "avg_score": None,
                "total_runs": 0,
                "unique_repos": 0,
                "top_issue": None,
                "best_repo": None,
                "worst_repo": None,
            }

        unique_repos = list({r["project"] for r in overall})
        scores = [r["score"] for r in overall]
        avg_score = round(sum(scores) / len(scores), 1)

        # Best/worst by latest run per project
        by_project = self._runs_by_project()
        latest_per_project = {
            proj: runs[-1]["score"] for proj, runs in by_project.items()
        }
        best_repo = max(latest_per_project, key=lambda p: latest_per_project[p]) if latest_per_project else None
        worst_repo = min(latest_per_project, key=lambda p: latest_per_project[p]) if latest_per_project else None

        # Top issue from common findings
        common = self.get_common_findings(min_repos=1)
        top_issue = common[0]["finding"] if common else None

        return {
            "avg_score": avg_score,
            "total_runs": len(overall),
            "unique_repos": len(unique_repos),
            "top_issue": top_issue,
            "best_repo": best_repo,
            "worst_repo": worst_repo,
        }
