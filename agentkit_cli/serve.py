"""agentkit serve — lightweight local dashboard HTTP server."""
from __future__ import annotations

import importlib.metadata
import json
import sqlite3
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

DEFAULT_PORT = 7890
_DB_DIR = Path.home() / ".config" / "agentkit"
_DB_PATH = _DB_DIR / "history.db"

GRADE_THRESHOLDS = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
]


def _compute_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def _score_color(score: float) -> str:
    if score >= 80:
        return "#22c55e"  # green
    if score >= 60:
        return "#eab308"  # yellow
    return "#ef4444"  # red


def _get_version() -> str:
    try:
        return importlib.metadata.version("agentkit-cli")
    except Exception:
        try:
            from agentkit_cli import __version__
            return __version__
        except Exception:
            return "unknown"


def _query_latest_runs(db_path: Optional[Path] = None) -> list[dict]:
    """Return the latest run per project (across all tools) from the history DB."""
    path = Path(db_path) if db_path else _DB_PATH
    if not path.exists():
        return []
    try:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        # Get the latest overall score per project (tool='overall' preferred, else max ts)
        # We fetch latest per project per tool, then aggregate
        sql = """
            SELECT
                project,
                tool,
                score,
                ts,
                id,
                details
            FROM runs
            WHERE id IN (
                SELECT id FROM runs r2
                WHERE r2.project = runs.project AND r2.tool = runs.tool
                ORDER BY r2.ts DESC
                LIMIT 1
            )
            ORDER BY project, tool
        """
        rows = conn.execute(sql).fetchall()
        conn.close()

        # Group by project
        projects: dict[str, dict] = {}
        for row in rows:
            proj = row["project"]
            if proj not in projects:
                projects[proj] = {
                    "project": proj,
                    "tools": {},
                    "latest_ts": row["ts"],
                    "latest_id": row["id"],
                    "scores": [],
                }
            p = projects[proj]
            p["tools"][row["tool"]] = round(row["score"], 1)
            p["scores"].append(row["score"])
            if row["ts"] > p["latest_ts"]:
                p["latest_ts"] = row["ts"]
                p["latest_id"] = row["id"]

        # Build result list
        results = []
        for proj, data in sorted(projects.items()):
            scores = data["scores"]
            avg = sum(scores) / len(scores) if scores else 0.0
            # If there's an 'overall' tool key, use it; else average
            if "overall" in data["tools"]:
                overall = data["tools"]["overall"]
            else:
                overall = round(avg, 1)
            results.append({
                "project": proj,
                "score": round(overall, 1),
                "grade": _compute_grade(overall),
                "tools": data["tools"],
                "ts": data["latest_ts"],
                "run_id": data["latest_id"],
            })
        return results
    except Exception:
        return []


def _get_stats(rows: list[dict]) -> dict:
    total_runs = len(rows)
    unique_projects = len(set(r["project"] for r in rows))
    avg_score = round(sum(r["score"] for r in rows) / total_runs, 1) if total_runs else 0.0
    return {"total_runs": total_runs, "unique_projects": unique_projects, "avg_score": avg_score}


def _render_dashboard_html(db_path: Optional[Path] = None) -> str:
    """Generate the full dashboard HTML string."""
    rows = _query_latest_runs(db_path)
    stats = _get_stats(rows)
    version = _get_version()

    # Build table rows
    if rows:
        table_rows_html = ""
        for r in rows:
            color = _score_color(r["score"])
            # Format tools breakdown
            tools_str = ", ".join(
                f"{t}: {s}" for t, s in sorted(r["tools"].items())
            ) if r["tools"] else "—"
            # Format timestamp (shorten ISO string)
            ts = r["ts"][:19].replace("T", " ") if r["ts"] else "—"
            table_rows_html += f"""
            <tr>
                <td class="project">{r['project']}</td>
                <td style="color:{color};font-weight:bold;">{r['score']}</td>
                <td style="color:{color};">{r['grade']}</td>
                <td class="tools-cell">{tools_str}</td>
                <td class="ts">{ts}</td>
                <td class="run-id">#{r['run_id']}</td>
            </tr>"""
        table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>Project</th>
                    <th>Latest Score</th>
                    <th>Grade</th>
                    <th>Tools Run</th>
                    <th>Timestamp</th>
                    <th>Run ID</th>
                </tr>
            </thead>
            <tbody>{table_rows_html}
            </tbody>
        </table>"""
    else:
        table_html = """
        <div class="empty-state">
            <p>No runs yet. Try: <code>agentkit run --help</code></p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="30">
<title>agentkit Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #0f172a;
    color: #e2e8f0;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 14px;
    min-height: 100vh;
  }}
  header {{
    background: #1e293b;
    border-bottom: 1px solid #334155;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  header h1 {{
    font-size: 1.25rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.01em;
  }}
  header .badge {{
    background: #0ea5e9;
    color: #fff;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
  }}
  .refresh-btn {{
    background: #334155;
    color: #94a3b8;
    border: 1px solid #475569;
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    transition: background 0.15s;
  }}
  .refresh-btn:hover {{
    background: #475569;
    color: #e2e8f0;
  }}
  .summary-bar {{
    display: flex;
    gap: 16px;
    padding: 16px 24px;
    background: #1e293b;
    border-bottom: 1px solid #334155;
  }}
  .stat-card {{
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px 20px;
    min-width: 120px;
  }}
  .stat-card .label {{
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
  }}
  .stat-card .value {{
    font-size: 1.5rem;
    font-weight: 700;
    color: #f1f5f9;
  }}
  main {{
    padding: 24px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: #1e293b;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid #334155;
  }}
  thead tr {{
    background: #0f172a;
    border-bottom: 1px solid #334155;
  }}
  th {{
    padding: 10px 16px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  td {{
    padding: 12px 16px;
    border-bottom: 1px solid #1e293b;
    vertical-align: middle;
  }}
  tbody tr:last-child td {{
    border-bottom: none;
  }}
  tbody tr:hover {{
    background: #0f172a;
  }}
  .project {{
    font-weight: 600;
    color: #93c5fd;
  }}
  .tools-cell {{
    font-size: 12px;
    color: #94a3b8;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .ts {{
    font-size: 12px;
    color: #64748b;
    white-space: nowrap;
  }}
  .run-id {{
    font-size: 12px;
    color: #475569;
  }}
  .empty-state {{
    text-align: center;
    padding: 60px 24px;
    color: #64748b;
    background: #1e293b;
    border-radius: 8px;
    border: 1px dashed #334155;
  }}
  .empty-state code {{
    background: #0f172a;
    padding: 2px 6px;
    border-radius: 4px;
    color: #94a3b8;
    font-family: monospace;
  }}
  footer {{
    padding: 16px 24px;
    color: #475569;
    font-size: 12px;
    border-top: 1px solid #1e293b;
    margin-top: 24px;
  }}
</style>
</head>
<body>
<header>
  <h1>⚡ agentkit Dashboard</h1>
  <div style="display:flex;align-items:center;gap:10px;">
    <span class="badge">Live</span>
    <button class="refresh-btn" onclick="location.reload()">↻ Refresh</button>
  </div>
</header>
<div class="summary-bar">
  <div class="stat-card">
    <div class="label">Total Runs</div>
    <div class="value">{stats['total_runs']}</div>
  </div>
  <div class="stat-card">
    <div class="label">Projects</div>
    <div class="value">{stats['unique_projects']}</div>
  </div>
  <div class="stat-card">
    <div class="label">Avg Score</div>
    <div class="value">{stats['avg_score']}</div>
  </div>
</div>
<main>
  {table_html}
</main>
<footer>agentkit-cli v{version} &mdash; Dashboard auto-refreshes every 30s</footer>
<script>
  // Also set a JS fallback refresh every 30s
  setTimeout(function() {{ location.reload(); }}, 30000);
</script>
</body>
</html>"""
    return html


class AgenkitDashboard(BaseHTTPRequestHandler):
    """HTTP request handler for the agentkit dashboard."""

    db_path: Optional[Path] = None

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            html = _render_dashboard_html(self.db_path)
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/runs":
            rows = _query_latest_runs(self.db_path)
            body = json.dumps(rows).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        # Suppress default request logging
        pass


def start_server(
    port: int = DEFAULT_PORT,
    open_browser: bool = False,
    db_path: Optional[Path] = None,
) -> None:
    """Start the dashboard HTTP server (blocks until Ctrl-C)."""
    # Create a handler class with db_path bound
    handler_class = type(
        "BoundDashboard",
        (AgenkitDashboard,),
        {"db_path": db_path},
    )

    server = HTTPServer(("localhost", port), handler_class)
    url = f"http://localhost:{port}"

    print(f"agentkit Dashboard running at {url}")
    print("Press Ctrl-C to stop.")

    if open_browser:
        # Open browser in a thread so we don't block server start
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
