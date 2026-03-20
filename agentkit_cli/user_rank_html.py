"""agentkit user-rank HTML report renderer — dark-theme topic contributor ranking."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.user_rank import UserRankResult

# ---------------------------------------------------------------------------
# Grade colors (consistent with user-scorecard/user-team)
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
# Renderer
# ---------------------------------------------------------------------------

class UserRankHTMLRenderer:
    """Generate a self-contained dark-theme HTML user-rank report."""

    def render(
        self,
        result: UserRankResult,
        timestamp: Optional[str] = None,
    ) -> str:
        if timestamp is None:
            timestamp = result.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        topic = result.topic
        mean_score = result.mean_score
        mean_grade_color = _grade_color(_score_to_grade(mean_score))

        # Grade distribution bars
        grade_dist = result.grade_distribution
        total = sum(grade_dist.values()) or 1
        grade_dist_bars = ""
        for g in ("A", "B", "C", "D"):
            count = grade_dist.get(g, 0)
            pct = (count / total * 100) if total > 0 else 0
            gc = _grade_color(g)
            grade_dist_bars += f"""
      <div class="dist-row">
        <span class="dist-label" style="color:{gc}">{g}</span>
        <div class="dist-bar-track">
          <div class="dist-bar" style="width:{pct:.0f}%;background:{gc}"></div>
        </div>
        <span class="dist-count">{count}</span>
      </div>"""

        # Contributor rows (already sorted by rank)
        contributor_rows = ""
        for entry in result.contributors:
            rc = _grade_color(entry.grade)
            score_pct = min(entry.score, 100)
            profile_url = f"https://github.com/{entry.username}"
            top_badge = " 🏆" if entry.username == result.top_scorer else ""
            top_repo_html = f'<a href="https://github.com/{entry.username}/{entry.top_repo}" target="_blank">{entry.top_repo}</a>' if entry.top_repo else "<em style='color:#8b949e'>—</em>"
            contributor_rows += f"""
      <tr>
        <td class="rank-cell">{entry.rank}</td>
        <td class="user-cell">
          <img class="avatar-sm" src="{entry.avatar_url}" alt="{entry.username}" width="32" height="32">
          <a href="{profile_url}" target="_blank">@{entry.username}</a>{top_badge}
        </td>
        <td class="score-cell">
          <div class="score-bar-wrap">
            <div class="score-bar" style="width:{score_pct:.0f}%"></div>
            <span class="score-num">{entry.score:.1f}</span>
          </div>
        </td>
        <td>
          <span class="grade-pill" style="color:{rc};border-color:{rc}">{entry.grade}</span>
        </td>
        <td class="repo-cell">{top_repo_html}</td>
      </tr>"""

        # Top scorer spotlight
        top_scorer_html = ""
        if result.top_scorer:
            top_entry = next((e for e in result.contributors if e.username == result.top_scorer), None)
            if top_entry:
                tc = _grade_color(top_entry.grade)
                top_scorer_html = f"""
    <div class="top-scorer-box">
      <span class="top-scorer-label">🏆 Top Scorer</span>
      <a href="https://github.com/{result.top_scorer}" target="_blank" class="top-scorer-name">@{result.top_scorer}</a>
      <span class="top-scorer-score" style="color:{tc}">{top_entry.score:.1f} / 100 &nbsp; {top_entry.grade}</span>
    </div>"""

        css = self._css()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>State of Agent Readiness in {topic}</title>
<style>{css}</style>
</head>
<body>
<div class="card">

  <div class="header">
    <div class="header-info">
      <h1>{topic}</h1>
      <div class="header-sub">State of Agent Readiness — Top Contributors</div>
    </div>
    <div class="mean-score-block">
      <div class="mean-score" style="color:{mean_grade_color}">{mean_score:.1f}</div>
      <div class="mean-score-label">Mean Score / 100</div>
    </div>
  </div>

  {top_scorer_html}

  <div class="section-header">Contributor Rankings</div>
  <table class="contrib-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Contributor</th>
        <th>Score</th>
        <th>Grade</th>
        <th>Top Repo</th>
      </tr>
    </thead>
    <tbody>
      {contributor_rows}
    </tbody>
  </table>

  <div class="section-header">Grade Distribution</div>
  <div class="grade-dist">
    {grade_dist_bars}
  </div>

  <div class="footer">
    Generated by
    <a href="https://github.com/mikiships/agentkit-cli">agentkit-cli v{__version__}</a>
    &bull; {timestamp}
  </div>

</div>
</body>
</html>"""
        return html

    def _css(self) -> str:
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
    max-width: 800px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
.header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
}
.header-info { flex: 1; }
h1 { font-size: 1.6rem; color: #58a6ff; margin-bottom: 0.25rem; }
.header-sub { font-size: 0.85rem; color: #8b949e; }
.mean-score-block { text-align: center; }
.mean-score {
    font-size: 3rem;
    font-weight: bold;
    width: 90px;
    height: 80px;
    line-height: 80px;
    text-align: center;
}
.mean-score-label { font-size: 0.75rem; color: #8b949e; margin-top: 0.3rem; }
.top-scorer-box {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 0.75rem 1rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.top-scorer-label { color: #8b949e; font-size: 0.85rem; }
.top-scorer-name { color: #58a6ff; font-weight: bold; text-decoration: none; }
.top-scorer-name:hover { text-decoration: underline; }
.top-scorer-score { margin-left: auto; font-size: 0.9rem; font-weight: bold; }
.section-header {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
    border-bottom: 1px solid #30363d;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
    margin-top: 1.5rem;
}
.contrib-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
}
.contrib-table th {
    text-align: left;
    font-size: 0.75rem;
    color: #8b949e;
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid #30363d;
}
.contrib-table td {
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid #21262d;
    vertical-align: middle;
}
.rank-cell { color: #8b949e; width: 36px; text-align: center; }
.user-cell { display: flex; align-items: center; gap: 0.5rem; }
.user-cell a { color: #58a6ff; text-decoration: none; }
.user-cell a:hover { text-decoration: underline; }
.avatar-sm { border-radius: 50%; }
.score-cell { width: 200px; }
.score-bar-wrap { display: flex; align-items: center; gap: 0.5rem; }
.score-bar {
    height: 6px;
    background: #3fb950;
    border-radius: 3px;
    flex: 1;
    max-width: 140px;
}
.score-num { font-size: 0.85rem; color: #e6edf3; white-space: nowrap; }
.grade-pill {
    display: inline-block;
    border: 1px solid;
    border-radius: 4px;
    padding: 0.1rem 0.5rem;
    font-size: 0.8rem;
    font-weight: bold;
}
.repo-cell a { color: #58a6ff; text-decoration: none; font-size: 0.85rem; }
.repo-cell a:hover { text-decoration: underline; }
.grade-dist { margin-bottom: 1rem; }
.dist-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}
.dist-label { width: 20px; font-weight: bold; font-size: 0.9rem; }
.dist-bar-track {
    flex: 1;
    background: #21262d;
    border-radius: 3px;
    height: 10px;
    overflow: hidden;
}
.dist-bar { height: 100%; border-radius: 3px; }
.dist-count { color: #8b949e; font-size: 0.8rem; width: 24px; text-align: right; }
.footer {
    font-size: 0.75rem;
    color: #8b949e;
    text-align: center;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #30363d;
}
.footer a { color: #58a6ff; text-decoration: none; }
.footer a:hover { text-decoration: underline; }
"""


def _score_to_grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"
