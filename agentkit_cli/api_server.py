"""agentkit API server — FastAPI REST interface to the agentkit analysis pipeline."""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel
    _FASTAPI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _FASTAPI_AVAILABLE = False

from agentkit_cli import __version__
from agentkit_cli.history import HistoryDB

_START_TIME = time.time()

# Concurrency limiter for /analyze
_MAX_CONCURRENT_ANALYSES = 5
_analysis_semaphore = threading.Semaphore(_MAX_CONCURRENT_ANALYSES)


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


def _grade_badge_css(grade: str) -> str:
    """Return CSS color for a grade badge."""
    colors = {"A": "#238636", "B": "#2ea043", "C": "#d29922", "D": "#da3633", "F": "#f85149"}
    return colors.get(grade, "#8b949e")


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


def _parse_repo_input(repo_str: str) -> tuple[str, str]:
    """Parse a repo string like 'github:owner/repo', 'owner/repo', or a GitHub URL.

    Returns (owner, repo) or raises ValueError.
    """
    repo_str = repo_str.strip()
    # Handle github: prefix
    if repo_str.startswith("github:"):
        repo_str = repo_str[len("github:"):]
    # Handle full GitHub URLs
    gh_url_match = re.match(
        r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?", repo_str
    )
    if gh_url_match:
        return gh_url_match.group(1), gh_url_match.group(2)
    # Handle owner/repo format
    parts = repo_str.split("/")
    if len(parts) == 2 and all(parts):
        return parts[0], parts[1]
    raise ValueError(f"Invalid repo format: {repo_str!r}. Use owner/repo or github:owner/repo")


def _run_analysis(owner: str, repo: str, timeout: int = 120) -> dict:
    """Run agentkit analyze subprocess. Returns parsed result dict."""
    start = time.monotonic()
    try:
        result = subprocess.run(
            ["agentkit", "analyze", f"github:{owner}/{repo}", "--json"],
            capture_output=True, text=True, timeout=timeout
        )
        elapsed = round(time.monotonic() - start, 2)
        if result.returncode != 0:
            return {"error": f"Analysis failed: {result.stderr.strip()}", "elapsed_seconds": elapsed}
        # Try to parse JSON output
        try:
            parsed = json.loads(result.stdout)
            parsed["elapsed_seconds"] = elapsed
            return parsed
        except json.JSONDecodeError:
            return {"raw_output": result.stdout.strip(), "elapsed_seconds": elapsed}
    except FileNotFoundError:
        return {"error": "agentkit CLI not found in PATH", "elapsed_seconds": 0}
    except subprocess.TimeoutExpired:
        elapsed = round(time.monotonic() - start, 2)
        return {"error": "Analysis timed out (120s)", "elapsed_seconds": elapsed}


class AnalyzeRequest(BaseModel):
    """Request body for POST /analyze."""
    repo: str


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
                    raise HTTPException(
                        status_code=500,
                        detail=f"Analysis failed: {result.stderr.strip()}"
                    )
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

    @app.post("/analyze")
    def analyze_post(body: AnalyzeRequest) -> dict:
        """Analyze a GitHub repo via POST. Supports concurrent limiting and caching."""
        try:
            owner, repo = _parse_repo_input(body.repo)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        # Check cache first (< 1h old = return cached)
        row = _get_latest_for_repo(_db, owner, repo)
        if row is not None and not _is_stale(row["ts"], max_age_seconds=3600):
            score = float(row["score"])
            tool_results = row.get("details") or {}
            return {
                "repo": f"{owner}/{repo}",
                "score": score,
                "grade": _grade(score),
                "tool_results": tool_results,
                "share_url": None,
                "elapsed_seconds": 0,
                "cached": True,
            }

        # Acquire semaphore (concurrency limit)
        acquired = _analysis_semaphore.acquire(timeout=5)
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="Too many concurrent analyses. Please try again shortly."
            )

        try:
            start = time.monotonic()
            try:
                result = subprocess.run(
                    ["agentkit", "analyze", f"github:{owner}/{repo}", "--json"],
                    capture_output=True, text=True, timeout=120
                )
            except FileNotFoundError:
                raise HTTPException(
                    status_code=500, detail="agentkit CLI not found in PATH"
                )
            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=504, detail="Analysis timed out (120s limit)"
                )

            elapsed = round(time.monotonic() - start, 2)

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Analysis failed: {result.stderr.strip()}"
                )
        finally:
            _analysis_semaphore.release()

        # Re-fetch from DB after analysis
        row = _get_latest_for_repo(_db, owner, repo)
        if row is None:
            # Analysis ran but didn't write to DB — parse stdout
            try:
                parsed = json.loads(result.stdout)
                score = float(parsed.get("score", 0))
                return {
                    "repo": f"{owner}/{repo}",
                    "score": score,
                    "grade": _grade(score),
                    "tool_results": parsed.get("tool_results", {}),
                    "share_url": parsed.get("share_url"),
                    "elapsed_seconds": elapsed,
                    "cached": False,
                }
            except (json.JSONDecodeError, TypeError):
                raise HTTPException(
                    status_code=500, detail="Analysis completed but produced no parseable results"
                )

        score = float(row["score"])
        tool_results = row.get("details") or {}
        share_url = None
        if os.environ.get("HERENOW_API_KEY"):
            share_url = f"https://here.now/agentkit/{owner}/{repo}"
        return {
            "repo": f"{owner}/{repo}",
            "score": score,
            "grade": _grade(score),
            "tool_results": tool_results,
            "share_url": share_url,
            "elapsed_seconds": elapsed,
            "cached": False,
        }

    @app.get("/analyze")
    def analyze_get_query(repo: str = Query(..., description="Repo in owner/repo or github:owner/repo format")) -> dict:
        """Analyze a GitHub repo via GET query param."""
        body = AnalyzeRequest(repo=repo)
        return analyze_post(body)

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

    @app.get("/recent")
    def recent(limit: int = Query(10, ge=1, le=100)) -> dict:
        """Return recent analyses from the history DB."""
        rows = _db.get_history(limit=limit)
        # Deduplicate: keep latest per project
        seen: dict[str, dict] = {}
        results = []
        for row in rows:
            proj = row["project"]
            if proj not in seen:
                seen[proj] = row
                s = float(row["score"])
                results.append({
                    "repo": proj.replace("github:", ""),
                    "score": s,
                    "grade": _grade(s),
                    "last_analyzed": row["ts"],
                })
        return {"analyses": results[:limit], "total": len(results)}

    @app.get("/ui", response_class=HTMLResponse)
    def ui() -> str:
        """Dark-theme interactive HTML page with repo analysis form."""
        uptime_s = int(time.time() - _START_TIME)
        uptime_str = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m {uptime_s % 60}s"
        rows = _db.get_history(limit=5)
        total_rows = _db.get_history(limit=9999)
        total_projects = len({r["project"] for r in total_rows})
        recent_html = ""
        for r in rows:
            s = float(r["score"])
            grade = _grade(s)
            recent_html += (
                f'<tr><td>{r["project"]}</td><td>{s:.1f}</td>'
                f'<td><span class="grade-badge" style="background:{_grade_badge_css(grade)}">'
                f'{grade}</span></td><td>{r["ts"][:19]}</td></tr>'
            )
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit API — v{__version__}</title>
<style>
  body {{ background: #0d1117; color: #c9d1d9; font-family: monospace; margin: 2em; max-width: 900px; margin: 2em auto; }}
  h1 {{ color: #58a6ff; }} h2 {{ color: #8b949e; border-bottom: 1px solid #21262d; padding-bottom: .3em; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
  th, td {{ border: 1px solid #21262d; padding: .5em 1em; text-align: left; }}
  th {{ background: #161b22; color: #58a6ff; }}
  .badge {{ display: inline-block; background: #238636; color: #fff; border-radius: 4px; padding: 2px 8px; font-size: .85em; }}
  .grade-badge {{ display: inline-block; color: #fff; border-radius: 4px; padding: 2px 8px; font-size: .85em; font-weight: bold; }}
  code {{ background: #161b22; padding: 2px 6px; border-radius: 3px; color: #79c0ff; }}
  a {{ color: #58a6ff; }}
  .form-section {{ background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 1.5em; margin: 1.5em 0; }}
  .form-section input[type="text"] {{ background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: .6em 1em; width: 60%; font-family: monospace; font-size: 1em; }}
  .form-section input[type="text"]::placeholder {{ color: #484f58; }}
  .form-section button {{ background: #238636; color: #fff; border: none; border-radius: 6px; padding: .6em 1.5em; font-size: 1em; cursor: pointer; margin-left: .5em; font-family: monospace; }}
  .form-section button:hover {{ background: #2ea043; }}
  .form-section button:disabled {{ background: #21262d; color: #484f58; cursor: not-allowed; }}
  #analyze-spinner {{ display: none; margin: 1em 0; color: #58a6ff; }}
  #analyze-error {{ display: none; margin: 1em 0; padding: 1em; background: #3d1418; border: 1px solid #f85149; border-radius: 6px; color: #f85149; }}
  #analyze-result {{ display: none; margin: 1em 0; padding: 1em; background: #0d1117; border: 1px solid #238636; border-radius: 6px; }}
  .result-score {{ font-size: 2em; font-weight: bold; color: #58a6ff; }}
  .result-grade {{ font-size: 1.5em; font-weight: bold; margin-left: .5em; }}
  .tool-breakdown {{ margin-top: 1em; }}
  .tool-breakdown dt {{ color: #8b949e; }}
  .tool-breakdown dd {{ color: #c9d1d9; margin-bottom: .5em; }}
  #recent-analyses {{ margin-top: 1em; }}
</style>
</head>
<body>
<h1>agentkit API</h1>
<p>Version: <span class="badge">v{__version__}</span> &nbsp; Uptime: <code>{uptime_str}</code> &nbsp; Repos in DB: <strong>{total_projects}</strong></p>

<div class="form-section">
  <h2 style="margin-top:0; border:none; padding:0;">Analyze a GitHub Repo</h2>
  <p style="color:#8b949e;">Enter a GitHub repo to get an agent-readiness score.</p>
  <form id="analyze-form" onsubmit="return submitAnalysis(event)">
    <input type="text" id="repo-input" name="repo" placeholder="owner/repo or https://github.com/owner/repo" required autocomplete="off" />
    <button type="submit" id="analyze-btn">Analyze</button>
  </form>
  <div id="analyze-spinner">Analyzing... this may take up to 2 minutes.</div>
  <div id="analyze-error"></div>
  <div id="analyze-result">
    <div>
      <span class="result-score" id="result-score"></span>
      <span class="result-grade" id="result-grade"></span>
      <span id="result-cached" style="display:none; color:#8b949e; margin-left:1em;">(cached)</span>
    </div>
    <p id="result-repo" style="color:#8b949e;"></p>
    <p id="result-elapsed" style="color:#484f58;"></p>
    <div class="tool-breakdown" id="result-tools"></div>
    <p id="result-share" style="display:none;"><a id="result-share-link" href="#">Share this result</a></p>
  </div>
</div>

<h2>Recent Analyses</h2>
<div id="recent-analyses">
<table id="recent-table">
  <tr><th>Repo</th><th>Score</th><th>Grade</th><th>Analyzed</th></tr>
  {recent_html or '<tr><td colspan="4">No data yet</td></tr>'}
</table>
</div>

<h2>Badge Embed</h2>
<p>Add to your README:</p>
<code>![Agent Score](http://localhost:8742/badge/owner/repo)</code>

<h2>Quick Links</h2>
<ul>
  <li><a href="/trending">/trending — top repos JSON</a></li>
  <li><a href="/leaderboard">/leaderboard — full leaderboard JSON</a></li>
  <li><a href="/recent">/recent — recent analyses JSON</a></li>
  <li><a href="/">/health — server health JSON</a></li>
</ul>

<script>
function submitAnalysis(e) {{
  e.preventDefault();
  var input = document.getElementById('repo-input');
  var btn = document.getElementById('analyze-btn');
  var spinner = document.getElementById('analyze-spinner');
  var errorDiv = document.getElementById('analyze-error');
  var resultDiv = document.getElementById('analyze-result');

  var repo = input.value.trim();
  if (!repo) return false;

  btn.disabled = true;
  spinner.style.display = 'block';
  errorDiv.style.display = 'none';
  resultDiv.style.display = 'none';

  fetch('/analyze', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{repo: repo}})
  }})
  .then(function(resp) {{
    if (!resp.ok) return resp.json().then(function(d) {{ throw new Error(d.detail || 'Analysis failed'); }});
    return resp.json();
  }})
  .then(function(data) {{
    spinner.style.display = 'none';
    btn.disabled = false;
    document.getElementById('result-score').textContent = data.score.toFixed(1);
    var gradeEl = document.getElementById('result-grade');
    gradeEl.textContent = data.grade;
    gradeEl.style.color = gradeColor(data.grade);
    document.getElementById('result-repo').textContent = data.repo;
    document.getElementById('result-elapsed').textContent = data.cached ? 'Cached result' : 'Completed in ' + data.elapsed_seconds + 's';
    var cachedEl = document.getElementById('result-cached');
    cachedEl.style.display = data.cached ? 'inline' : 'none';
    var toolsDiv = document.getElementById('result-tools');
    toolsDiv.innerHTML = '';
    if (data.tool_results && typeof data.tool_results === 'object') {{
      var dl = document.createElement('dl');
      for (var k in data.tool_results) {{
        var dt = document.createElement('dt');
        dt.textContent = k;
        dl.appendChild(dt);
        var dd = document.createElement('dd');
        var v = data.tool_results[k];
        dd.textContent = typeof v === 'object' ? JSON.stringify(v) : String(v);
        dl.appendChild(dd);
      }}
      toolsDiv.appendChild(dl);
    }}
    var shareP = document.getElementById('result-share');
    if (data.share_url) {{
      document.getElementById('result-share-link').href = data.share_url;
      shareP.style.display = 'block';
    }} else {{
      shareP.style.display = 'none';
    }}
    resultDiv.style.display = 'block';
    refreshRecent();
  }})
  .catch(function(err) {{
    spinner.style.display = 'none';
    btn.disabled = false;
    errorDiv.textContent = err.message || 'Analysis failed';
    errorDiv.style.display = 'block';
  }});

  return false;
}}

function gradeColor(grade) {{
  var colors = {{'A': '#238636', 'B': '#2ea043', 'C': '#d29922', 'D': '#da3633', 'F': '#f85149'}};
  return colors[grade] || '#8b949e';
}}

function refreshRecent() {{
  fetch('/recent?limit=10')
  .then(function(r) {{ return r.json(); }})
  .then(function(data) {{
    var tbody = '<tr><th>Repo</th><th>Score</th><th>Grade</th><th>Analyzed</th></tr>';
    if (data.analyses && data.analyses.length > 0) {{
      data.analyses.forEach(function(a) {{
        tbody += '<tr><td>' + a.repo + '</td><td>' + a.score.toFixed(1) + '</td><td><span class="grade-badge" style="background:' + gradeColor(a.grade) + '">' + a.grade + '</span></td><td>' + (a.last_analyzed || '').substring(0, 19) + '</td></tr>';
      }});
    }} else {{
      tbody += '<tr><td colspan="4">No data yet</td></tr>';
    }}
    document.getElementById('recent-table').innerHTML = tbody;
  }})
  .catch(function() {{}});
}}

// Auto-refresh recent analyses every 30 seconds
setInterval(refreshRecent, 30000);
</script>
</body>
</html>"""
        return html

    return app


# Module-level app instance (created lazily)
def _make_app() -> "FastAPI":  # pragma: no cover
    return create_app()
