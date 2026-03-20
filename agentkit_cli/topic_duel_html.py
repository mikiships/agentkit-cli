"""agentkit topic-duel HTML report renderer — dark-theme side-by-side topic comparison."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.engines.topic_duel import TopicDuelResult
from agentkit_cli.topic_rank import TopicRankEntry

# ---------------------------------------------------------------------------
# Grade colors (consistent with topic_rank_html)
# ---------------------------------------------------------------------------

_GRADE_COLORS = {
    "A": "#3fb950",
    "B": "#58a6ff",
    "C": "#d29922",
    "D": "#f85149",
    "F": "#f85149",
}


def _grade_color(grade: str) -> str:
    return _GRADE_COLORS.get(grade, "#8b949e")


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def render_topic_duel_html(
    result: TopicDuelResult,
    timestamp: Optional[str] = None,
) -> str:
    """Render a dark-theme HTML report for a topic-duel result."""
    if timestamp is None:
        timestamp = result.timestamp or datetime.now(timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        )

    t1 = result.topic1
    t2 = result.topic2
    avg1 = result.topic1_avg_score
    avg2 = result.topic2_avg_score
    winner = result.overall_winner

    # Winner banner
    if winner == "topic1":
        banner_text = f"🏆 {t1} wins — avg {avg1:.1f} vs {avg2:.1f}"
        banner_color = "#3fb950"
    elif winner == "topic2":
        banner_text = f"🏆 {t2} wins — avg {avg2:.1f} vs {avg1:.1f}"
        banner_color = "#3fb950"
    else:
        banner_text = f"🤝 Tie — {t1} {avg1:.1f} vs {t2} {avg2:.1f}"
        banner_color = "#d29922"

    # Repo rows for a single topic column
    def _repo_rows(entries: list) -> str:
        rows = ""
        for e in entries:
            rc = _grade_color(e.grade)
            score_pct = min(e.score, 100)
            repo_url = f"https://github.com/{e.repo_full_name}"
            rows += f"""
        <tr>
          <td class="rank-cell">{e.rank}</td>
          <td class="repo-name-cell"><a href="{repo_url}" target="_blank">{e.repo_full_name}</a></td>
          <td class="score-cell">
            <div class="score-bar-wrap">
              <div class="score-bar" style="width:{score_pct:.0f}%"></div>
              <span class="score-num">{e.score:.1f}</span>
            </div>
          </td>
          <td><span class="grade-pill" style="color:{rc};border-color:{rc}">{e.grade}</span></td>
          <td class="stars-cell">⭐ {e.stars:,}</td>
        </tr>"""
        return rows or "<tr><td colspan='5' style='color:#8b949e;text-align:center;'>No repos found</td></tr>"

    rows1 = _repo_rows(result.topic1_result.entries)
    rows2 = _repo_rows(result.topic2_result.entries)

    # Dimension rows
    dim_rows = ""
    for dim in result.dimensions:
        dc = "#3fb950" if dim.winner != "tie" else "#d29922"
        w_label = {
            "topic1": f"<span style='color:#3fb950'>{t1}</span>",
            "topic2": f"<span style='color:#3fb950'>{t2}</span>",
            "tie": "<span style='color:#d29922'>tie</span>",
        }.get(dim.winner, "—")

        if dim.winner == "topic1":
            v1_str = f"<strong style='color:#3fb950'>{dim.topic1_value:.1f}</strong>"
            v2_str = f"<span style='color:#8b949e'>{dim.topic2_value:.1f}</span>"
        elif dim.winner == "topic2":
            v1_str = f"<span style='color:#8b949e'>{dim.topic1_value:.1f}</span>"
            v2_str = f"<strong style='color:#3fb950'>{dim.topic2_value:.1f}</strong>"
        else:
            v1_str = f"<span style='color:#d29922'>{dim.topic1_value:.1f}</span>"
            v2_str = f"<span style='color:#d29922'>{dim.topic2_value:.1f}</span>"

        dim_rows += f"""
      <tr>
        <td style="color:#8b949e">{dim.name.replace('_', ' ').title()}</td>
        <td style="text-align:right">{v1_str}</td>
        <td style="text-align:right">{v2_str}</td>
        <td style="text-align:center">{w_label}</td>
      </tr>"""

    avg1_color = _grade_color("A" if avg1 >= 80 else "B" if avg1 >= 65 else "C")
    avg2_color = _grade_color("A" if avg2 >= 80 else "B" if avg2 >= 65 else "C")

    css = _css()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Topic Duel: {t1} vs {t2}</title>
<style>{css}</style>
</head>
<body>
<div class="card">

  <div class="banner" style="border-color:{banner_color};color:{banner_color}">
    {banner_text}
  </div>

  <div class="header">
    <div class="header-col">
      <h2 style="color:#58a6ff">{t1}</h2>
      <div class="avg-score" style="color:{avg1_color}">{avg1:.1f}</div>
      <div class="avg-label">avg score / 100</div>
    </div>
    <div class="vs-sep">VS</div>
    <div class="header-col">
      <h2 style="color:#58a6ff">{t2}</h2>
      <div class="avg-score" style="color:{avg2_color}">{avg2:.1f}</div>
      <div class="avg-label">avg score / 100</div>
    </div>
  </div>

  <div class="cols">
    <div class="col">
      <div class="section-header">{t1} — Top Repos</div>
      <table class="repo-table">
        <thead><tr><th>#</th><th>Repo</th><th>Score</th><th>Grade</th><th>Stars</th></tr></thead>
        <tbody>{rows1}</tbody>
      </table>
    </div>
    <div class="col">
      <div class="section-header">{t2} — Top Repos</div>
      <table class="repo-table">
        <thead><tr><th>#</th><th>Repo</th><th>Score</th><th>Grade</th><th>Stars</th></tr></thead>
        <tbody>{rows2}</tbody>
      </table>
    </div>
  </div>

  <div class="section-header">Dimension Comparison</div>
  <table class="dim-table">
    <thead>
      <tr>
        <th>Dimension</th>
        <th style="text-align:right">{t1}</th>
        <th style="text-align:right">{t2}</th>
        <th style="text-align:center">Winner</th>
      </tr>
    </thead>
    <tbody>{dim_rows}</tbody>
  </table>

  <div class="footer">
    Generated by
    <a href="https://github.com/mikiships/agentkit-cli">agentkit-cli v{__version__}</a>
    &bull; {timestamp}
  </div>

</div>
</body>
</html>"""
    return html


def _css() -> str:
    return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.card {
    max-width: 1100px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
.banner {
    text-align: center;
    font-size: 1.2rem;
    font-weight: bold;
    border: 1px solid;
    border-radius: 6px;
    padding: 0.75rem 1.5rem;
    margin-bottom: 1.5rem;
}
.header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
    text-align: center;
}
.header-col { flex: 1; }
.vs-sep {
    font-size: 1.5rem;
    color: #8b949e;
    font-weight: bold;
}
h2 { font-size: 1.3rem; margin-bottom: 0.5rem; }
.avg-score { font-size: 2.5rem; font-weight: bold; }
.avg-label { font-size: 0.75rem; color: #8b949e; margin-top: 0.25rem; }
.cols {
    display: flex;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}
.col { flex: 1; }
.section-header {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
    border-bottom: 1px solid #30363d;
    padding-bottom: 0.4rem;
    margin-bottom: 0.75rem;
    margin-top: 1rem;
}
.repo-table, .dim-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 0.5rem;
}
.repo-table th, .dim-table th {
    text-align: left;
    font-size: 0.72rem;
    color: #8b949e;
    padding: 0.35rem 0.5rem;
    border-bottom: 1px solid #30363d;
}
.repo-table td, .dim-table td {
    padding: 0.4rem 0.5rem;
    border-bottom: 1px solid #21262d;
    vertical-align: middle;
    font-size: 0.82rem;
}
.rank-cell { color: #8b949e; width: 30px; text-align: center; }
.repo-name-cell a { color: #58a6ff; text-decoration: none; font-weight: 600; }
.repo-name-cell a:hover { text-decoration: underline; }
.score-cell { width: 140px; }
.score-bar-wrap { display: flex; align-items: center; gap: 0.4rem; }
.score-bar {
    height: 5px;
    background: #3fb950;
    border-radius: 3px;
    flex: 1;
    max-width: 80px;
}
.score-num { font-size: 0.8rem; color: #e6edf3; white-space: nowrap; }
.grade-pill {
    display: inline-block;
    border: 1px solid;
    border-radius: 4px;
    padding: 0.1rem 0.4rem;
    font-size: 0.75rem;
    font-weight: bold;
}
.stars-cell { white-space: nowrap; font-size: 0.8rem; color: #8b949e; }
.footer {
    font-size: 0.75rem;
    color: #8b949e;
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #30363d;
}
.footer a { color: #58a6ff; text-decoration: none; }
"""
