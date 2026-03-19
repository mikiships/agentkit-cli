"""agentkit benchmark_report — dark-theme HTML report for benchmark results."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.benchmark import BenchmarkReport
from agentkit_cli.publish import (
    PublishError,
    _json_post,
    _put_file,
    _finalize,
    HERENOW_API_BASE,
)


# ---------------------------------------------------------------------------
# CSS (dark theme, matching share.py aesthetic)
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.card {
    max-width: 900px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
h1 { font-size: 1.6rem; color: #58a6ff; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; color: #8b949e; margin: 1.5rem 0 0.75rem; }
.ref { font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.hero {
    text-align: center;
    padding: 1.5rem 0;
    margin-bottom: 1.5rem;
    border-top: 1px solid #30363d;
    border-bottom: 1px solid #30363d;
}
.hero-winner {
    font-size: 2.5rem;
    font-weight: bold;
    color: #3fb950;
    margin-bottom: 0.5rem;
}
.hero-label { font-size: 0.9rem; color: #8b949e; }
.stats-bar {
    display: flex;
    gap: 2rem;
    justify-content: center;
    padding: 1rem 0;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #30363d;
    flex-wrap: wrap;
}
.stat { text-align: center; }
.stat-value { font-size: 1.4rem; font-weight: bold; color: #58a6ff; }
.stat-label { font-size: 0.75rem; color: #8b949e; }
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
}
th {
    text-align: center;
    color: #8b949e;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #30363d;
}
th:first-child { text-align: left; }
td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; text-align: center; }
td:first-child { text-align: left; color: #e6edf3; }
.score-green { color: #3fb950; font-weight: bold; }
.score-yellow { color: #d29922; font-weight: bold; }
.score-red { color: #f85149; font-weight: bold; }
.score-na { color: #8b949e; }
.winner-row { background: #1c2128; }
.footer { font-size: 0.75rem; color: #8b949e; text-align: center; margin-top: 1.5rem; }
.footer a { color: #58a6ff; text-decoration: none; }
"""


def _score_class(score: Optional[float]) -> str:
    if score is None:
        return "score-na"
    if score >= 80:
        return "score-green"
    if score >= 50:
        return "score-yellow"
    return "score-red"


def _score_cell(score: Optional[float], duration: Optional[float] = None) -> str:
    if score is None:
        return '<span class="score-na">—</span>'
    cls = _score_class(score)
    dur_str = f" <small style='color:#8b949e'>({duration:.1f}s)</small>" if duration is not None else ""
    return f'<span class="{cls}">{score:.0f}</span>{dur_str}'


class BenchmarkReportRenderer:
    """Render a BenchmarkReport as dark-theme HTML."""

    def render(self, report: BenchmarkReport) -> str:
        """Return full HTML string."""
        winner = report.winner
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Summary stats
        winner_stats = report.summary.get(winner)
        best_score = winner_stats.mean_score if winner_stats else 0.0
        fastest_agent = min(report.summary.values(), key=lambda s: s.mean_duration).agent if report.summary else "—"

        # Task matrix
        tasks = report.config.tasks
        agents = report.config.agents
        ranked_agents = sorted(report.summary.values(), key=lambda s: (-s.mean_score, -s.win_rate))

        # Build task_scores lookup: (agent, task) -> (mean_score, mean_duration)
        from collections import defaultdict
        score_sums: dict = defaultdict(list)
        dur_sums: dict = defaultdict(list)
        for r in report.results:
            if r.error is None:
                score_sums[(r.agent, r.task)].append(r.score)
                dur_sums[(r.agent, r.task)].append(r.duration_s)

        task_avg: dict = {}
        task_dur: dict = {}
        for key, scores in score_sums.items():
            task_avg[key] = sum(scores) / len(scores)
            durs = dur_sums[key]
            task_dur[key] = sum(durs) / len(durs)

        # Matrix table rows
        matrix_rows = []
        for task in tasks:
            cells = f"<td>{task}</td>"
            for stats in ranked_agents:
                agent = stats.agent
                score = task_avg.get((agent, task))
                dur = task_dur.get((agent, task))
                cells += f"<td>{_score_cell(score, dur)}</td>"
            row_class = ""
            matrix_rows.append(f"<tr{row_class}>{cells}</tr>")

        # Aggregate table rows
        agg_rows = []
        for i, stats in enumerate(ranked_agents, 1):
            crown = " 👑" if stats.agent == winner else ""
            row_class = ' class="winner-row"' if stats.agent == winner else ""
            cls = _score_class(stats.mean_score)
            agg_rows.append(
                f"<tr{row_class}>"
                f"<td>{i}</td>"
                f"<td><strong>{stats.agent}{crown}</strong></td>"
                f"<td>{len(stats.task_scores)}</td>"
                f'<td><span class="{cls}">{stats.mean_score:.1f}</span></td>'
                f"<td>{stats.mean_duration:.1f}s</td>"
                f"<td>{stats.win_rate * 100:.0f}%</td>"
                f"</tr>"
            )

        agent_header_cells = "".join(f"<th>{s.agent}</th>" for s in ranked_agents)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent Benchmark: {report.project}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
  <h1>Agent Benchmark: {report.project}</h1>
  <p class="ref">Generated {now} · agentkit-cli v{__version__}</p>

  <div class="hero">
    <div class="hero-winner">👑 {winner}</div>
    <div class="hero-label">Top performing agent on {report.project}</div>
  </div>

  <div class="stats-bar">
    <div class="stat">
      <div class="stat-value">{winner}</div>
      <div class="stat-label">Winner</div>
    </div>
    <div class="stat">
      <div class="stat-value">{best_score:.0f}</div>
      <div class="stat-label">Best Mean Score</div>
    </div>
    <div class="stat">
      <div class="stat-value">{fastest_agent}</div>
      <div class="stat-label">Fastest Agent</div>
    </div>
    <div class="stat">
      <div class="stat-value">{len(tasks)}</div>
      <div class="stat-label">Tasks</div>
    </div>
  </div>

  <h2>Per-Task Matrix</h2>
  <table>
    <thead><tr><th>Task</th>{agent_header_cells}</tr></thead>
    <tbody>{"".join(matrix_rows)}</tbody>
  </table>

  <h2>Rankings</h2>
  <table>
    <thead><tr><th>Rank</th><th>Agent</th><th>Tasks</th><th>Mean Score</th><th>Mean Time</th><th>Win Rate</th></tr></thead>
    <tbody>{"".join(agg_rows)}</tbody>
  </table>

  <p class="footer">
    Generated by <a href="https://github.com/agentkit-cli/agentkit-cli">agentkit-cli</a> v{__version__}
  </p>
</div>
</body>
</html>"""
        return html


def publish_benchmark(report: BenchmarkReport) -> Optional[str]:
    """Render benchmark HTML and publish to here.now. Returns URL or None."""
    html = BenchmarkReportRenderer().render(report)
    content = html.encode("utf-8")
    api_key = os.environ.get("HERENOW_API_KEY") or None
    headers: dict = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        step1_body = {
            "files": [
                {
                    "path": "index.html",
                    "contentType": "text/html; charset=utf-8",
                    "size": len(content),
                }
            ]
        }
        step1_resp = _json_post(f"{HERENOW_API_BASE}/publish", step1_body, headers)
        upload_url = step1_resp["files"][0]["uploadUrl"]
        _put_file(upload_url, content, "text/html; charset=utf-8")
        site_id = step1_resp["siteId"]
        final = _finalize(site_id, headers)
        return final.get("url") or final.get("siteUrl") or None
    except Exception:
        return None
