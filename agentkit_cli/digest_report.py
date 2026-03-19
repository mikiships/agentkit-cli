"""agentkit digest_report — dark-theme HTML renderer for DigestReport."""
from __future__ import annotations

from typing import Optional

from agentkit_cli.digest import DigestReport, ProjectDigest


_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.container { max-width: 900px; margin: 0 auto; }
h1 { color: #58a6ff; font-size: 1.6rem; margin-bottom: 0.25rem; }
h2 { color: #58a6ff; font-size: 1.1rem; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid #30363d; padding-bottom: 0.4rem; }
.meta { font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.trend-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: bold;
    margin-left: 0.5rem;
}
.badge-improving { background: #1a3a1a; color: #3fb950; border: 1px solid #3fb950; }
.badge-stable    { background: #1a2a3a; color: #58a6ff; border: 1px solid #58a6ff; }
.badge-regressing{ background: #3a1a1a; color: #f85149; border: 1px solid #f85149; }
.stats-row { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    min-width: 150px;
    text-align: center;
}
.stat-value { font-size: 2rem; font-weight: bold; color: #58a6ff; }
.stat-label { font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; }
table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
th { text-align: left; color: #8b949e; font-weight: normal; padding: 0.4rem 0.6rem; border-bottom: 1px solid #30363d; font-size: 0.85rem; }
td { padding: 0.5rem 0.6rem; border-bottom: 1px solid #21262d; font-size: 0.9rem; }
tr:hover td { background: #161b22; }
.delta-pos { color: #3fb950; font-weight: bold; }
.delta-neg { color: #f85149; font-weight: bold; }
.delta-neutral { color: #8b949e; }
.panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.panel-regression { border-color: #f85149; background: #1a0e0e; }
.panel-improvement { border-color: #3fb950; background: #0e1a0e; }
.panel h3 { font-size: 0.95rem; margin-bottom: 0.5rem; }
.panel h3.reg { color: #f85149; }
.panel h3.imp { color: #3fb950; }
.chart-bar-wrap { margin-bottom: 0.5rem; }
.chart-label { font-size: 0.8rem; color: #8b949e; display: inline-block; width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; vertical-align: middle; }
.chart-bar-outer { display: inline-block; vertical-align: middle; width: calc(100% - 260px); background: #21262d; border-radius: 3px; height: 14px; margin: 0 0.5rem; }
.chart-bar-inner { height: 100%; border-radius: 3px; background: #58a6ff; }
.chart-score { font-size: 0.8rem; color: #e6edf3; display: inline-block; vertical-align: middle; width: 60px; }
ul.actions { list-style: none; padding: 0; }
ul.actions li { padding: 0.3rem 0; border-bottom: 1px solid #21262d; font-size: 0.9rem; color: #e6edf3; }
ul.actions li::before { content: "→ "; color: #58a6ff; }
.footer { font-size: 0.75rem; color: #8b949e; margin-top: 2rem; text-align: center; }
"""


def _trend_badge(trend: str) -> str:
    label = {"improving": "↑ Improving", "stable": "→ Stable", "regressing": "↓ Regressing"}.get(trend, trend)
    cls = {"improving": "badge-improving", "stable": "badge-stable", "regressing": "badge-regressing"}.get(trend, "badge-stable")
    return f'<span class="trend-badge {cls}">{label}</span>'


def _delta_html(delta: Optional[float]) -> str:
    if delta is None:
        return '<span class="delta-neutral">—</span>'
    if delta > 0:
        return f'<span class="delta-pos">+{delta:.1f}</span>'
    if delta < 0:
        return f'<span class="delta-neg">{delta:.1f}</span>'
    return f'<span class="delta-neutral">{delta:.1f}</span>'


def _bar_chart(projects: list[ProjectDigest]) -> str:
    if not projects:
        return "<p style='color:#8b949e'>No project data.</p>"
    lines = []
    for p in projects:
        score = p.score_end if p.score_end is not None else 0.0
        pct = min(max(score, 0), 100)
        lines.append(
            f'<div class="chart-bar-wrap">'
            f'<span class="chart-label" title="{p.name}">{p.name}</span>'
            f'<span class="chart-bar-outer"><span class="chart-bar-inner" style="width:{pct}%"></span></span>'
            f'<span class="chart-score">{score:.1f}</span>'
            f"</div>"
        )
    return "\n".join(lines)


class DigestReportRenderer:
    """Render a DigestReport as a dark-theme self-contained HTML page."""

    def render(self, report: DigestReport) -> str:
        period_str = (
            f"{report.period_start.strftime('%Y-%m-%d')} → {report.period_end.strftime('%Y-%m-%d')}"
        )

        header = f"""
        <h1>agentkit quality digest {_trend_badge(report.overall_trend)}</h1>
        <p class="meta">Period: {period_str}</p>
        <div class="stats-row">
          <div class="stat-card"><div class="stat-value">{report.projects_tracked}</div><div class="stat-label">Projects</div></div>
          <div class="stat-card"><div class="stat-value">{report.runs_in_period}</div><div class="stat-label">Runs</div></div>
          <div class="stat-card"><div class="stat-value">{report.coverage_pct:.0f}%</div><div class="stat-label">Coverage</div></div>
          <div class="stat-card"><div class="stat-value">{len(report.improvements)}</div><div class="stat-label">Improved</div></div>
          <div class="stat-card"><div class="stat-value">{len(report.regressions)}</div><div class="stat-label">Regressed</div></div>
        </div>
        """

        # Trend bar chart
        chart_section = f"<h2>Score Trend</h2><div class='panel'>{_bar_chart(report.per_project)}</div>"

        # Per-project table
        rows = []
        for p in report.per_project:
            score_start = f"{p.score_start:.1f}" if p.score_start is not None else "—"
            score_end = f"{p.score_end:.1f}" if p.score_end is not None else "—"
            rows.append(
                f"<tr><td>{p.name}</td><td>{score_start}</td><td>{score_end}</td>"
                f"<td>{_delta_html(p.delta)}</td><td>{p.runs}</td><td>{p.status}</td></tr>"
            )
        table_html = (
            "<table><thead><tr><th>Project</th><th>Start</th><th>End</th>"
            "<th>Delta</th><th>Runs</th><th>Status</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        ) if rows else "<p style='color:#8b949e'>No projects.</p>"
        projects_section = f"<h2>Per-Project Summary</h2>{table_html}"

        # Regressions
        reg_items = "".join(
            f"<tr><td>{r[0]}</td><td>{r[1]:.1f}</td><td>{r[2]:.1f}</td><td>{r[3]}</td></tr>"
            for r in report.regressions
        )
        reg_table = (
            "<table><thead><tr><th>Project</th><th>From</th><th>To</th><th>Timestamp</th></tr></thead><tbody>"
            + reg_items + "</tbody></table>"
        ) if report.regressions else "<p>None in this period.</p>"
        regressions_section = (
            f"<h2>Regressions</h2>"
            f"<div class='panel panel-regression'><h3 class='reg'>⚠ Regressed Projects</h3>{reg_table}</div>"
        )

        # Improvements
        imp_items = "".join(
            f"<tr><td>{r[0]}</td><td>{r[1]:.1f}</td><td>{r[2]:.1f}</td><td>{r[3]}</td></tr>"
            for r in report.improvements
        )
        imp_table = (
            "<table><thead><tr><th>Project</th><th>From</th><th>To</th><th>Timestamp</th></tr></thead><tbody>"
            + imp_items + "</tbody></table>"
        ) if report.improvements else "<p>None in this period.</p>"
        improvements_section = (
            f"<h2>Improvements</h2>"
            f"<div class='panel panel-improvement'><h3 class='imp'>✓ Improved Projects</h3>{imp_table}</div>"
        )

        # Top actions
        action_items = "".join(f"<li>{a}</li>" for a in report.top_actions)
        actions_section = (
            f"<h2>Top Action Items</h2>"
            f"<ul class='actions'>{action_items if action_items else '<li>No recurring suggestions detected.</li>'}</ul>"
        )

        body = (
            f"<div class='container'>{header}{chart_section}"
            f"{projects_section}{regressions_section}{improvements_section}"
            f"{actions_section}"
            f"<div class='footer'>Generated by agentkit-cli digest</div></div>"
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit Quality Digest</title>
<style>{_CSS}</style>
</head>
<body>{body}</body>
</html>"""
