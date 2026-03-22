"""agentkit weekly HTML renderer — dark-theme weekly report."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.weekly_engine import WeeklyReport, WeeklyProjectStat


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "improving": "#3fb950",
    "regressing": "#f85149",
    "stable": "#8b949e",
    "no_data": "#484f58",
}

_TREND_EMOJI = {
    "improving": "📈",
    "regressing": "📉",
    "stable": "➡️",
}


def _status_color(status: str) -> str:
    return _STATUS_COLORS.get(status, "#8b949e")


def _delta_str(delta: Optional[float]) -> str:
    if delta is None:
        return "—"
    if delta > 0:
        return f"+{delta:.1f}"
    return f"{delta:.1f}"


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def render_weekly_html(
    report: WeeklyReport,
    timestamp: Optional[str] = None,
) -> str:
    """Render a dark-theme HTML report for a weekly digest."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    trend_emoji = _TREND_EMOJI.get(report.overall_trend, "➡️")
    week_label = (
        f"{report.period_start.strftime('%b %d')} – "
        f"{report.period_end.strftime('%b %d, %Y')}"
    )
    avg_score_str = f"{report.avg_score:.1f}" if report.avg_score is not None else "N/A"

    # Project rows
    project_rows = _render_project_rows(report.per_project)

    # Improvements section
    improvements_html = _render_highlights(report.top_improvements, "📈 Most Improved", "#3fb950")

    # Regressions section
    regressions_html = _render_highlights(report.top_regressions, "📉 Regressions", "#f85149")

    # Actions
    actions_html = _render_list_items(report.top_actions, "🔧 Top Recommended Actions")

    # Findings
    findings_html = _render_list_items(report.common_findings, "🔍 Common Findings")

    # Tweet block
    tweet_escaped = report.tweet_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>agentkit weekly — {week_label}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      font-size: 14px;
      line-height: 1.6;
      padding: 24px;
      max-width: 1100px;
      margin: 0 auto;
    }}
    h1 {{ font-size: 1.6rem; color: #e6edf3; margin-bottom: 4px; }}
    h2 {{ font-size: 1.1rem; color: #c9d1d9; margin: 20px 0 10px; border-bottom: 1px solid #21262d; padding-bottom: 6px; }}
    .subtitle {{ color: #8b949e; font-size: 0.875rem; margin-bottom: 20px; }}
    .stats-bar {{
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
      margin-bottom: 24px;
    }}
    .stat-pill {{
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 10px 16px;
      min-width: 120px;
    }}
    .stat-label {{ color: #8b949e; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
    .stat-value {{ font-size: 1.4rem; font-weight: 700; color: #e6edf3; margin-top: 2px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 24px;
      background: #161b22;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #21262d;
    }}
    th {{
      background: #21262d;
      color: #8b949e;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 10px 14px;
      text-align: left;
    }}
    td {{ padding: 9px 14px; border-bottom: 1px solid #21262d; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #1c2128; }}
    .status-pill {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.78rem;
      border: 1px solid;
      font-weight: 600;
    }}
    .delta-pos {{ color: #3fb950; font-weight: 600; }}
    .delta-neg {{ color: #f85149; font-weight: 600; }}
    .delta-zero {{ color: #8b949e; }}
    .highlight-section {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }}
    .highlight-card {{
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 8px;
      padding: 12px 16px;
      flex: 1;
      min-width: 200px;
    }}
    .highlight-card .proj-name {{ font-weight: 600; color: #e6edf3; }}
    .highlight-card .proj-delta {{ font-size: 1rem; font-weight: 700; margin-top: 4px; }}
    ul.action-list {{ list-style: none; padding: 0; margin-bottom: 20px; }}
    ul.action-list li {{
      background: #161b22;
      border: 1px solid #21262d;
      border-radius: 6px;
      padding: 8px 14px;
      margin-bottom: 6px;
      color: #c9d1d9;
    }}
    ul.action-list li::before {{ content: "→ "; color: #58a6ff; }}
    .tweet-block {{
      background: #161b22;
      border: 1px solid #21262d;
      border-left: 3px solid #58a6ff;
      border-radius: 8px;
      padding: 14px 16px;
      font-family: monospace;
      font-size: 0.875rem;
      color: #c9d1d9;
      white-space: pre-wrap;
      margin-bottom: 24px;
    }}
    .footer {{
      color: #484f58;
      font-size: 0.75rem;
      border-top: 1px solid #21262d;
      padding-top: 12px;
      margin-top: 24px;
    }}
  </style>
</head>
<body>
  <h1>agentkit weekly {trend_emoji}</h1>
  <p class="subtitle">{week_label} · generated {timestamp} · agentkit-cli v{__version__}</p>

  <div class="stats-bar">
    <div class="stat-pill">
      <div class="stat-label">Projects</div>
      <div class="stat-value">{report.projects_tracked}</div>
    </div>
    <div class="stat-pill">
      <div class="stat-label">Runs</div>
      <div class="stat-value">{report.runs_in_period}</div>
    </div>
    <div class="stat-pill">
      <div class="stat-label">Avg Score</div>
      <div class="stat-value">{avg_score_str}</div>
    </div>
    <div class="stat-pill">
      <div class="stat-label">Trend</div>
      <div class="stat-value" style="font-size:1rem">{report.overall_trend} {trend_emoji}</div>
    </div>
    <div class="stat-pill">
      <div class="stat-label">Coverage</div>
      <div class="stat-value">{report.coverage_pct:.0f}%</div>
    </div>
  </div>

  <h2>Project Score Changes</h2>
  {project_rows}

  {improvements_html}
  {regressions_html}
  {actions_html}
  {findings_html}

  <h2>🐦 Tweet-Ready Summary</h2>
  <div class="tweet-block">{tweet_escaped}</div>

  <div class="footer">
    Generated by agentkit-cli v{__version__} · {timestamp}
  </div>
</body>
</html>"""


def _render_project_rows(projects: list[WeeklyProjectStat]) -> str:
    if not projects:
        return "<p style='color:#8b949e'>No project data found.</p>"

    rows = ""
    for p in sorted(projects, key=lambda x: -(x.delta or 0)):
        sc = _status_color(p.status)
        start_str = f"{p.score_start:.1f}" if p.score_start is not None else "—"
        end_str = f"{p.score_end:.1f}" if p.score_end is not None else "—"
        d = p.delta or 0
        if p.delta is None:
            delta_cell = '<span class="delta-zero">—</span>'
        elif d > 0:
            delta_cell = f'<span class="delta-pos">+{d:.1f}</span>'
        elif d < 0:
            delta_cell = f'<span class="delta-neg">{d:.1f}</span>'
        else:
            delta_cell = '<span class="delta-zero">0.0</span>'

        status_label = p.status.replace("_", " ")
        finding_cell = p.top_finding or "—"

        rows += f"""
  <tr>
    <td style="font-weight:600;color:#e6edf3">{p.name}</td>
    <td>{start_str}</td>
    <td>{end_str}</td>
    <td>{delta_cell}</td>
    <td><span class="status-pill" style="color:{sc};border-color:{sc}">{status_label}</span></td>
    <td style="color:#8b949e">{p.runs}</td>
    <td style="color:#8b949e;max-width:300px;overflow:hidden;text-overflow:ellipsis">{finding_cell}</td>
  </tr>"""

    return f"""<table>
  <thead>
    <tr>
      <th>Project</th><th>Start</th><th>End</th><th>Delta</th>
      <th>Status</th><th>Runs</th><th>Top Finding</th>
    </tr>
  </thead>
  <tbody>{rows}
  </tbody>
</table>"""


def _render_highlights(projects: list[WeeklyProjectStat], title: str, color: str) -> str:
    if not projects:
        return ""
    cards = ""
    for p in projects:
        d = p.delta or 0
        sign = "+" if d >= 0 else ""
        cards += f"""
    <div class="highlight-card">
      <div class="proj-name">{p.name}</div>
      <div class="proj-delta" style="color:{color}">{sign}{d:.1f}</div>
      <div style="color:#8b949e;font-size:0.8rem">{p.score_start:.1f} → {p.score_end:.1f}</div>
    </div>"""
    return f"""<h2>{title}</h2>
  <div class="highlight-section">{cards}
  </div>"""


def _render_list_items(items: list[str], title: str) -> str:
    if not items:
        return ""
    lis = "".join(f"<li>{item}</li>" for item in items)
    return f"""<h2>{title}</h2>
  <ul class="action-list">{lis}</ul>"""
