"""agentkit API server — FastAPI REST interface to the agentkit analysis pipeline."""
from __future__ import annotations

import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False

from agentkit_cli import __version__
from agentkit_cli.history import HistoryDB

_START_TIME = time.time()


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _badge_color(score: float) -> str:
    if score >= 90:
        return "brightgreen"
    if score >= 70:
        return "yellow"
    if score >= 50:
        return "orange"
    return "red"


def _get_latest_for_repo(db: HistoryDB, owner: str, repo: str) -> Optional[dict]:
    project = f"github:{owner}/{repo}"
    rows = db.get_history(project=project, tool="overall", limit=1)
    return rows[0] if rows else None


def _is_stale(ts_str: str, max_age_seconds: int = 86400) -> bool:
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age > max_age_seconds
    except Exception:
        return True


def create_app(db: Optional[HistoryDB] = None) -> "FastAPI":
    """Create and return the FastAPI application."""
    if not _FASTAPI_AVAILABLE:
        raise ImportError("fastapi is required. Run: pip install agentkit-cli[api]")

    app = FastAPI(
        title="agentkit API",
        description="REST API for agentkit-cli analysis pipeline",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _db: HistoryDB = db or HistoryDB()

    @app.get("/")
    def health() -> dict:
        uptime = time.time() - _START_TIME
        return {
            "status": "ok",
            "version": __version__,
            "uptime_seconds": round(uptime, 1),
        }

    @app.get("/analyze/{owner}/{repo}")
    def analyze(owner: str, repo: str) -> dict:
        """Analyze a GitHub repo. Uses DB cache; triggers fresh analysis if stale/missing."""
        project = f"github:{owner}/{repo}"
        row = _get_latest_for_repo(_db, owner, repo)

        if row is None or _is_stale(row["ts"]):
            # Trigger fresh analysis
            try:
                result = subprocess.run(
                    ["agentkit", "analyze", f"github:{owner}/{repo}", "--json"],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    raise HTTPException(status_code=500, detail=f"Analysis failed: {result.stderr.strip()}")
            except FileNotFoundError:
                raise HTTPException(status_code=500, detail="agentkit CLI not found in PATH")
            except subprocess.TimeoutExpired:
                raise HTTPException(status_code=500, detail="Analysis timed out")
            # Re-fetch from DB
            row = _get_latest_for_repo(_db, owner, repo)

        if row is None:
            raise HTTPException(status_code=404, detail=f"No data for {owner}/{repo}")

        score = float(row["score"])
        return {
            "repo": f"{owner}/{repo}",
            "score": score,
            "grade": _grade(score),
            "last_analyzed": row["ts"],
            "details": row.get("details"),
        }

    @app.get("/score/{owner}/{repo}")
    def score(owner: str, repo: str) -> dict:
        """Lightweight score lookup — DB only, no fresh analysis."""
        row = _get_latest_for_repo(_db, owner, repo)
        if row is None:
            raise HTTPException(status_code=404, detail=f"No score found for {owner}/{repo}")
        s = float(row["score"])
        return {
            "repo": f"{owner}/{repo}",
            "score": s,
            "grade": _grade(s),
            "last_analyzed": row["ts"],
        }

    @app.get("/badge/{owner}/{repo}")
    def badge(owner: str, repo: str) -> dict:
        """shields.io-compatible badge endpoint."""
        row = _get_latest_for_repo(_db, owner, repo)
        if row is None:
            raise HTTPException(status_code=404, detail=f"No score found for {owner}/{repo}")
        s = float(row["score"])
        g = _grade(s)
        return {
            "schemaVersion": 1,
            "label": "agent score",
            "message": f"{int(s)}/{g}",
            "color": _badge_color(s),
        }

    @app.get("/trending")
    def trending(
        limit: int = Query(10, ge=1, le=100),
        min_score: float = Query(0.0, ge=0.0, le=100.0),
    ) -> dict:
        """Top repos by score from history DB."""
        rows = _db.get_history(limit=500)
        # Deduplicate: keep latest per project
        seen: dict[str, dict] = {}
        for row in rows:
            proj = row["project"]
            if proj not in seen:
                seen[proj] = row
        repos = [
            {
                "repo": proj.replace("github:", ""),
                "score": float(r["score"]),
                "grade": _grade(float(r["score"])),
                "last_analyzed": r["ts"],
            }
            for proj, r in seen.items()
            if float(r["score"]) >= min_score
        ]
        repos.sort(key=lambda x: x["score"], reverse=True)
        return {"repos": repos[:limit], "total": len(repos)}

    @app.get("/history/{owner}/{repo}")
    def history(owner: str, repo: str) -> dict:
        """Score history for a repo."""
        project = f"github:{owner}/{repo}"
        rows = _db.get_history(project=project, limit=50)
        if not rows:
            raise HTTPException(status_code=404, detail=f"No history for {owner}/{repo}")
        entries = [
            {"timestamp": r["ts"], "score": float(r["score"]), "grade": _grade(float(r["score"]))}
            for r in rows
        ]
        return {"repo": f"{owner}/{repo}", "history": entries}

    @app.get("/leaderboard")
    def leaderboard(limit: int = Query(20, ge=1, le=100)) -> dict:
        """Top repos by score with grade badges."""
        rows = _db.get_history(limit=1000)
        seen: dict[str, dict] = {}
        for row in rows:
            proj = row["project"]
            if proj not in seen:
                seen[proj] = row
        repos = [
            {
                "repo": proj.replace("github:", ""),
                "score": float(r["score"]),
                "grade": _grade(float(r["score"])),
                "last_analyzed": r["ts"],
            }
            for proj, r in seen.items()
        ]
        repos.sort(key=lambda x: x["score"], reverse=True)
        return {"leaderboard": repos[:limit], "total": len(repos)}

    @app.get("/ui", response_class=HTMLResponse)
    def ui() -> str:
        """Dark-theme HTML status page."""
        uptime_s = int(time.time() - _START_TIME)
        uptime_str = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m {uptime_s % 60}s"
        rows = _db.get_history(limit=5)
        total_rows = _db.get_history(limit=9999)
        total_projects = len({r["project"] for r in total_rows})
        recent_html = ""
        for r in rows:
            score = float(r["score"])
            grade = _grade(score)
            recent_html += f"<tr><td>{r['project']}</td><td>{score:.1f}</td><td>{grade}</td><td>{r['ts'][:19]}</td></tr>"
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit API — v{__version__}</title>
<style>
  body {{ background: #0d1117; color: #c9d1d9; font-family: monospace; margin: 2em; }}
  h1 {{ color: #58a6ff; }} h2 {{ color: #8b949e; border-bottom: 1px solid #21262d; padding-bottom: .3em; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
  th, td {{ border: 1px solid #21262d; padding: .5em 1em; text-align: left; }}
  th {{ background: #161b22; color: #58a6ff; }}
  .badge {{ display: inline-block; background: #238636; color: #fff; border-radius: 4px; padding: 2px 8px; font-size: .85em; }}
  code {{ background: #161b22; padding: 2px 6px; border-radius: 3px; color: #79c0ff; }}
  a {{ color: #58a6ff; }}
</style>
</head>
<body>
<h1>🤖 agentkit API</h1>
<p>Version: <span class="badge">v{__version__}</span> &nbsp; Uptime: <code>{uptime_str}</code> &nbsp; Repos in DB: <strong>{total_projects}</strong></p>

<h2>Recent Analyses</h2>
<table>
  <tr><th>Repo</th><th>Score</th><th>Grade</th><th>Analyzed</th></tr>
  {recent_html or '<tr><td colspan="4">No data yet</td></tr>'}
</table>

<h2>Badge Embed</h2>
<p>Add to your README:</p>
<code>![Agent Score](http://localhost:8742/badge/owner/repo)</code>

<h2>Quick Links</h2>
<ul>
  <li><a href="/trending">/trending — top repos JSON</a></li>
  <li><a href="/leaderboard">/leaderboard — full leaderboard JSON</a></li>
  <li><a href="/">/health — server health JSON</a></li>
</ul>
</body>
</html>"""
        return html

    return app


# Module-level app instance (created lazily)
def _make_app() -> "FastAPI":  # pragma: no cover
    return create_app()
