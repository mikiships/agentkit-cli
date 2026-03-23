"""agentkit weekly digest engine — assembles a DigestReport from local history."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from agentkit_cli.history import HistoryDB


_PLACEHOLDER_REPOS = [
    {"repo": "psf/requests", "score": 85.0, "grade": "A"},
    {"repo": "pallets/flask", "score": 78.0, "grade": "B+"},
    {"repo": "tiangolo/fastapi", "score": 82.0, "grade": "A-"},
]


def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 80:
        return "A-"
    if score >= 75:
        return "B+"
    if score >= 70:
        return "B"
    if score >= 65:
        return "B-"
    if score >= 60:
        return "C+"
    if score >= 55:
        return "C"
    return "D"


@dataclass
class DigestReport:
    top_repos: list  # list of {repo, score, grade}
    week_stats: dict  # {total_analyses, avg_score, top_scorer}
    generated_at: str  # ISO timestamp string


class WeeklyDigestEngine:
    """Assembles a DigestReport from HistoryDB data for the last N days."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db = HistoryDB(db_path=db_path)

    def generate(self, since_days: int = 7) -> DigestReport:
        """Generate a DigestReport for the last `since_days` days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        cutoff_str = cutoff.isoformat()

        rows = self._get_rows_since(cutoff_str)

        if not rows:
            return DigestReport(
                top_repos=list(_PLACEHOLDER_REPOS),
                week_stats={"total_analyses": 0, "avg_score": 0.0, "top_scorer": ""},
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        week_stats = self._compute_week_stats(rows)
        top_repos = self._compute_top_repos(rows)

        return DigestReport(
            top_repos=top_repos,
            week_stats=week_stats,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _get_rows_since(self, cutoff_str: str) -> list[dict]:
        """Fetch all 'overall' tool rows newer than cutoff."""
        try:
            with self._db._connect() as conn:
                rows = conn.execute(
                    "SELECT project, score FROM runs WHERE tool = 'overall' AND ts >= ? ORDER BY ts DESC",
                    (cutoff_str,),
                ).fetchall()
            return [{"project": r["project"], "score": r["score"]} for r in rows]
        except Exception:
            return []

    def _compute_week_stats(self, rows: list[dict]) -> dict:
        scores = [r["score"] for r in rows]
        total = len(rows)
        avg = round(sum(scores) / total, 1) if total else 0.0
        top_scorer = ""
        if rows:
            best = max(rows, key=lambda r: r["score"])
            top_scorer = best["project"]
        return {"total_analyses": total, "avg_score": avg, "top_scorer": top_scorer}

    def _compute_top_repos(self, rows: list[dict], limit: int = 5) -> list[dict]:
        """Return top repos by average score, deduplicated."""
        from collections import defaultdict
        scores_by_project: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            scores_by_project[r["project"]].append(r["score"])

        ranked = []
        for project, scores in scores_by_project.items():
            avg = round(sum(scores) / len(scores), 1)
            ranked.append({"repo": project, "score": avg, "grade": _score_to_grade(avg)})

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked[:limit] if ranked else list(_PLACEHOLDER_REPOS)
