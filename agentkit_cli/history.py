"""agentkit history — SQLite-backed quality score store."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_DB_DIR = Path.home() / ".config" / "agentkit"


def _compute_trend(scores: list[float]) -> float:
    """Compute trend delta: avg(last 3) - avg(first 3). Returns float delta.

    For short arrays (< 4 scores), uses first half vs second half to avoid overlap.
    """
    if len(scores) < 2:
        return 0.0
    if len(scores) < 4:
        mid = len(scores) // 2
        first = scores[:mid] if mid > 0 else scores[:1]
        last = scores[mid:] if mid < len(scores) else scores[-1:]
    else:
        first = scores[:3]
        last = scores[-3:]
    return round(sum(last) / len(last) - sum(first) / len(first), 1)
_DB_PATH = _DB_DIR / "history.db"

_DDL = """
CREATE TABLE IF NOT EXISTS runs (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT    NOT NULL,
    project TEXT    NOT NULL,
    tool    TEXT    NOT NULL,
    score   REAL    NOT NULL,
    details TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_project ON runs(project);
CREATE INDEX IF NOT EXISTS idx_runs_ts      ON runs(ts DESC);
"""

_CAMPAIGNS_DDL = """
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    target_spec TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    completed_at TEXT,
    total_repos INTEGER DEFAULT 0,
    pr_count    INTEGER DEFAULT 0,
    skip_count  INTEGER DEFAULT 0,
    fail_count  INTEGER DEFAULT 0
);
"""

_MIGRATIONS = [
    "ALTER TABLE runs ADD COLUMN label TEXT",
    "CREATE INDEX IF NOT EXISTS idx_runs_label ON runs(label)",
    "ALTER TABLE runs ADD COLUMN findings TEXT",
    _CAMPAIGNS_DDL,
    "ALTER TABLE runs ADD COLUMN campaign_id TEXT REFERENCES campaigns(campaign_id)",
]


class HistoryDB:
    """Thin wrapper around a SQLite history database."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._path = Path(db_path) if db_path else _DB_PATH
        self._ensure_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_db(self) -> None:
        """Create the DB file and schema if missing."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_DDL)
        self._run_migrations()

    def _run_migrations(self) -> None:
        """Apply forward-only DDL migrations (idempotent)."""
        with self._connect() as conn:
            for sql in _MIGRATIONS:
                try:
                    conn.execute(sql)
                except sqlite3.OperationalError:
                    pass  # column already exists

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_run(
        self,
        project: str,
        tool: str,
        score: float,
        details: Optional[dict] = None,
        label: Optional[str] = None,
        findings: Optional[list] = None,
        campaign_id: Optional[str] = None,
    ) -> None:
        """Insert one run record."""
        ts = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details) if details is not None else None
        findings_json = json.dumps(findings) if findings is not None else None
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO runs (ts, project, tool, score, details, label, findings, campaign_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ts, project, tool, float(score), details_json, label, findings_json, campaign_id),
            )

    def get_history(
        self,
        project: Optional[str] = None,
        tool: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Return run rows newest-first.

        Args:
            project: filter by project name (None = all projects)
            tool:    filter by tool name (None = all tools)
            limit:   max rows to return
        """
        clauses: list[str] = []
        params: list = []

        if project is not None:
            clauses.append("project = ?")
            params.append(project)
        if tool is not None:
            clauses.append("tool = ?")
            params.append(tool)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)

        sql = f"SELECT id, ts, project, tool, score, details, label FROM runs {where} ORDER BY ts DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        result = []
        for row in rows:
            details_raw = row["details"]
            details = json.loads(details_raw) if details_raw else None
            result.append(
                {
                    "id": row["id"],
                    "ts": row["ts"],
                    "project": row["project"],
                    "tool": row["tool"],
                    "score": row["score"],
                    "details": details,
                    "label": row["label"],
                }
            )
        return result

    def get_all_projects(self) -> list[str]:
        """Return sorted list of distinct project names."""
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT project FROM runs ORDER BY project").fetchall()
        return [row["project"] for row in rows]

    def get_project_summary(self) -> list[dict]:
        """Return per-project latest overall score summary."""
        sql = """
        SELECT project,
               COUNT(*) AS run_count,
               MAX(ts)  AS last_ts,
               AVG(score) FILTER (WHERE tool = 'overall') AS avg_score,
               (SELECT score FROM runs r2
                WHERE r2.project = runs.project AND r2.tool = 'overall'
                ORDER BY ts DESC LIMIT 1) AS latest_score
        FROM runs
        GROUP BY project
        ORDER BY last_ts DESC
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]

    def get_leaderboard_data(
        self,
        tool: str = "overall",
        project: Optional[str] = None,
        since: Optional[str] = None,
        last_n: Optional[int] = None,
    ) -> list[dict]:
        """Return per-label leaderboard rows.

        Each row: {label, runs, avg_score, best, worst, trend, scores_asc}
        Rows with NULL label are grouped as 'default'.
        """
        clauses: list[str] = ["tool = ?"]
        params: list = [tool]

        if project is not None:
            clauses.append("project = ?")
            params.append(project)
        if since is not None:
            clauses.append("ts >= ?")
            params.append(since)

        where = "WHERE " + " AND ".join(clauses)
        sql = f"SELECT COALESCE(label, 'default') AS lbl, score, ts FROM runs {where} ORDER BY ts ASC"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        # Group by label
        from collections import defaultdict
        groups: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            groups[row["lbl"]].append(row["score"])

        results = []
        for lbl, scores in groups.items():
            if last_n is not None and last_n > 0:
                scores = scores[-last_n:]
            if not scores:
                continue
            avg = round(sum(scores) / len(scores), 1)
            best = round(max(scores), 1)
            worst = round(min(scores), 1)
            trend = _compute_trend(scores)
            results.append({
                "label": lbl,
                "runs": len(scores),
                "avg_score": avg,
                "best": best,
                "worst": worst,
                "trend": trend,
            })

        # Sort by avg descending
        results.sort(key=lambda r: r["avg_score"], reverse=True)
        return results

    def record_campaign(self, result: "CampaignResult") -> None:
        """Insert a campaign result into the campaigns table."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO campaigns
                    (campaign_id, target_spec, started_at, completed_at, total_repos, pr_count, skip_count, fail_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.campaign_id,
                    result.target_spec,
                    now,
                    now,
                    len(result.submitted) + len(result.skipped) + len(result.failed),
                    len(result.submitted),
                    len(result.skipped),
                    len(result.failed),
                ),
            )
            # Update any runs with this campaign_id
            conn.execute(
                "UPDATE runs SET campaign_id = ? WHERE campaign_id = ?",
                (result.campaign_id, result.campaign_id),
            )

    def get_campaigns(self, limit: int = 20) -> list[dict]:
        """Return campaign rows newest-first."""
        sql = "SELECT * FROM campaigns ORDER BY started_at DESC LIMIT ?"
        with self._connect() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
        return [dict(row) for row in rows]

    def get_campaign_runs(self, campaign_id: str) -> list[dict]:
        """Return all runs associated with a campaign_id."""
        sql = "SELECT * FROM runs WHERE campaign_id = ? ORDER BY ts DESC"
        with self._connect() as conn:
            rows = conn.execute(sql, (campaign_id,)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get("details"):
                try:
                    d["details"] = json.loads(d["details"])
                except Exception:
                    pass
            result.append(d)
        return result

    def clear_history(self, project: Optional[str] = None) -> int:
        """Delete history rows. Returns count deleted."""
        if project is not None:
            with self._connect() as conn:
                cur = conn.execute("DELETE FROM runs WHERE project = ?", (project,))
                return cur.rowcount
        else:
            with self._connect() as conn:
                cur = conn.execute("DELETE FROM runs")
                return cur.rowcount


# ---------------------------------------------------------------------------
# Module-level convenience that shields callers from DB errors
# ---------------------------------------------------------------------------

_default_db: Optional[HistoryDB] = None


def _get_db() -> HistoryDB:
    global _default_db
    if _default_db is None:
        _default_db = HistoryDB()
    return _default_db


def record_run(
    project: str,
    tool: str,
    score: float,
    details: Optional[dict] = None,
    db: Optional[HistoryDB] = None,
    label: Optional[str] = None,
    findings: Optional[list] = None,
) -> None:
    """Record one run (silently ignores errors)."""
    try:
        (db or _get_db()).record_run(project, tool, score, details, label=label, findings=findings)
    except Exception as exc:  # pragma: no cover
        print(f"[agentkit history] DEBUG: failed to record run: {exc}", file=sys.stderr)


def get_history(
    project: Optional[str] = None,
    tool: Optional[str] = None,
    limit: int = 20,
    db: Optional[HistoryDB] = None,
) -> list[dict]:
    return (db or _get_db()).get_history(project=project, tool=tool, limit=limit)


def clear_history(
    project: Optional[str] = None,
    db: Optional[HistoryDB] = None,
) -> int:
    return (db or _get_db()).clear_history(project=project)
