"""Dark-theme HTML timeline report for agentkit timeline."""
from __future__ import annotations

import html
import json
from typing import Optional

CHART_JS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"
CHART_JS_INTEGRITY = "sha256-oY/+2LMD8oBWTT7AMJY0dn5mAQrTOeKYGHLKSKuGkM="

TOOL_LABELS = {
    "agentlint": "Lint Score",
    "coderace": "Code Quality",
    "agentmd": "Context Freshness",
    "agentreflect": "Test Count",
}

TREND_ARROW = {
    "improving": "↑",
    "stable": "→",
    "declining": "↓",
}

TREND_COLOR = {
    "improving": "#238636",
    "stable": "#8b949e",
    "declining": "#da3633",
}

# One color per project line
LINE_COLORS = [
    "#58a6ff",
    "#3fb950",
    "#d29922",
    "#f78166",
    "#bc8cff",
    "#39d353",
]


def _safe(v: object) -> str:
    return html.escape(str(v)) if v is not None else ""


def _score_bar(score: Optional[float], width: int = 120) -> str:
    """Render a simple CSS bar for a 0-100 score."""
    if score is None:
        return '<span class="no-data">—</span>'
    pct = max(0, min(100, float(score)))
    color = "#238636" if pct >= 80 else "#d29922" if pct >= 60 else "#da3633"
    bar_w = int(pct * width / 100)
    return (
        f'<span class="bar-outer" style="width:{width}px">'
        f'<span class="bar-inner" style="width:{bar_w}px;background:{color}"></span>'
        f'</span>'
        f'<span class="bar-label">{pct:.0f}</span>'
    )


def render_html_timeline(
    payload: dict,
    project_name: Optional[str] = None,
) -> str:
    """Render a dark-theme HTML timeline report from a TimelineEngine payload."""
    chart = payload.get("chart", {})
    stats = payload.get("stats", {})
    by_project = chart.get("by_project", {})

    # Determine display title
    if project_name:
        title = _safe(project_name)
    elif len(by_project) == 1:
        title = _safe(list(by_project.keys())[0])
    elif by_project:
        title = f"{len(by_project)} projects"
    else:
        title = "All Projects"

    # Date range
    all_dates = chart.get("dates", [])
    date_range = ""
    if all_dates:
        date_range = f"{_safe(all_dates[0])} — {_safe(all_dates[-1])}"

    # Stats panel
    trend = stats.get("trend", "stable")
    trend_arrow = TREND_ARROW.get(trend, "→")
    trend_clr = TREND_COLOR.get(trend, "#8b949e")
    avg_score = stats.get("avg")
    mn = stats.get("min")
    mx = stats.get("max")
    streak = stats.get("streak", 0)
    run_count = stats.get("run_count", 0)

    avg_disp = f"{avg_score:.1f}" if avg_score is not None else "—"
    mn_disp = f"{mn:.1f}" if mn is not None else "—"
    mx_disp = f"{mx:.1f}" if mx is not None else "—"

    streak_html = ""
    if streak >= 3:
        streak_html = f'<span class="badge">{streak} runs above 80</span>'

    # Build Chart.js dataset JSON
    datasets = []
    for i, (proj, pdata) in enumerate(by_project.items()):
        color = LINE_COLORS[i % len(LINE_COLORS)]
        dates = pdata.get("dates", [])
        scores = pdata.get("scores", [])
        points = [
            {"x": d, "y": s}
            for d, s in zip(dates, scores)
            if s is not None
        ]
        datasets.append({
            "label": proj,
            "data": points,
            "borderColor": color,
            "backgroundColor": color + "33",
            "tension": 0.3,
            "fill": False,
            "pointRadius": 4,
        })

    chart_js_data = json.dumps({"datasets": datasets})

    # Per-tool sparkline rows
    sparkline_rows = ""
    per_tool_agg = chart.get("per_tool", {})
    for tool, label in TOOL_LABELS.items():
        values = [v for v in per_tool_agg.get(tool, []) if v is not None]
        if not values:
            continue
        avg_t = sum(values) / len(values)
        sparkline_rows += f"""
        <tr>
          <td class="tool-name">{_safe(label)}</td>
          <td class="tool-bar">{_score_bar(avg_t)}</td>
        </tr>"""

    if not sparkline_rows:
        sparkline_rows = '<tr><td colspan="2" class="no-data">No per-tool breakdown available</td></tr>'

    # Build project summary table rows
    summary_rows = ""
    for proj, pdata in by_project.items():
        scores = [s for s in pdata.get("scores", []) if s is not None]
        run_c = len(scores)
        latest = scores[-1] if scores else None
        latest_disp = f"{latest:.1f}" if latest is not None else "—"
        # Simple trend for this project
        if len(scores) >= 2:
            proj_delta = scores[-1] - scores[0]
            proj_trend = "↑" if proj_delta > 2 else "↓" if proj_delta < -2 else "→"
        else:
            proj_trend = "→"
        summary_rows += f"""
        <tr>
          <td>{_safe(proj)}</td>
          <td>{run_c}</td>
          <td>{latest_disp}</td>
          <td>{proj_trend}</td>
        </tr>"""

    if not summary_rows:
        summary_rows = '<tr><td colspan="4" class="no-data">No data</td></tr>'

    empty_notice = ""
    if not by_project:
        empty_notice = """
        <div class="empty-notice">
          No history found. Run <code>agentkit run</code> first.
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Quality Timeline — {title}</title>
  <script src="{CHART_JS_CDN}" integrity="{CHART_JS_INTEGRITY}" crossorigin="anonymous"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      padding: 32px 16px;
    }}
    h1 {{ font-size: 1.5rem; color: #e6edf3; margin-bottom: 4px; }}
    .subtitle {{ color: #8b949e; font-size: 0.9rem; margin-bottom: 24px; }}
    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 20px 24px;
      margin-bottom: 20px;
    }}
    .card h2 {{ font-size: 1rem; color: #8b949e; margin-bottom: 16px; font-weight: 500; }}
    .chart-container {{ position: relative; height: 300px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th {{ text-align: left; padding: 8px 10px; color: #8b949e; font-weight: 500; border-bottom: 1px solid #30363d; }}
    td {{ padding: 8px 10px; border-bottom: 1px solid #21262d; }}
    .tool-name {{ color: #8b949e; width: 160px; }}
    .bar-outer {{ display: inline-block; background: #21262d; border-radius: 3px; height: 10px; vertical-align: middle; }}
    .bar-inner {{ display: inline-block; height: 10px; border-radius: 3px; }}
    .bar-label {{ margin-left: 8px; color: #c9d1d9; font-size: 0.85rem; }}
    .no-data {{ color: #8b949e; font-style: italic; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 16px; }}
    .stat-item {{ text-align: center; }}
    .stat-value {{ font-size: 1.8rem; font-weight: 700; color: #e6edf3; }}
    .stat-label {{ font-size: 0.8rem; color: #8b949e; margin-top: 4px; }}
    .badge {{
      display: inline-block;
      background: #1a3a25;
      color: #3fb950;
      border: 1px solid #238636;
      border-radius: 20px;
      padding: 4px 14px;
      font-size: 0.85rem;
      margin-top: 8px;
    }}
    .trend-arrow {{ font-size: 2rem; font-weight: 700; }}
    footer {{ text-align: center; color: #484f58; font-size: 0.8rem; padding: 24px 0; }}
    .empty-notice {{
      text-align: center;
      color: #8b949e;
      padding: 40px;
      font-size: 1.1rem;
    }}
    .empty-notice code {{ color: #58a6ff; }}
    code {{ font-family: 'SF Mono', 'Fira Code', Consolas, monospace; }}
  </style>
</head>
<body>
  <h1>Agent Quality Timeline</h1>
  <div class="subtitle">Project: {title}{(" &nbsp;·&nbsp; " + date_range) if date_range else ""}</div>

  {empty_notice}

  {'<div class="card"><h2>Composite Score Over Time</h2><div class="chart-container"><canvas id="mainChart"></canvas></div></div>' if by_project else ""}

  <div class="card">
    <h2>Stats</h2>
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{mn_disp}</div>
        <div class="stat-label">Min</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{avg_disp}</div>
        <div class="stat-label">Avg</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{mx_disp}</div>
        <div class="stat-label">Max</div>
      </div>
      <div class="stat-item">
        <div class="trend-arrow" style="color:{trend_clr}">{trend_arrow}</div>
        <div class="stat-label">{_safe(trend.title())}</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{run_count}</div>
        <div class="stat-label">Runs</div>
      </div>
    </div>
    {streak_html}
  </div>

  <div class="card">
    <h2>Per-Tool Breakdown (avg)</h2>
    <table>
      <tbody>{sparkline_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Project Summary</h2>
    <table>
      <thead><tr><th>Project</th><th>Runs</th><th>Latest Score</th><th>Trend</th></tr></thead>
      <tbody>{summary_rows}</tbody>
    </table>
  </div>

  <footer>Generated by agentkit-cli v0.44.0</footer>

  <script>
  (function() {{
    var canvas = document.getElementById('mainChart');
    if (!canvas) return;
    var data = {chart_js_data};
    new Chart(canvas, {{
      type: 'line',
      data: data,
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        parsing: {{ xAxisKey: 'x', yAxisKey: 'y' }},
        scales: {{
          x: {{
            type: 'category',
            ticks: {{ color: '#8b949e' }},
            grid: {{ color: '#21262d' }}
          }},
          y: {{
            min: 0,
            max: 100,
            ticks: {{ color: '#8b949e' }},
            grid: {{ color: '#21262d' }}
          }}
        }},
        plugins: {{
          legend: {{ labels: {{ color: '#c9d1d9' }} }},
          tooltip: {{ mode: 'index' }}
        }}
      }}
    }});
  }})();
  </script>
</body>
</html>"""
