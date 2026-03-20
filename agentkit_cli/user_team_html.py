"""agentkit user-team HTML report renderer — dark-theme team scorecard."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.user_team import TeamScorecardResult
from agentkit_cli.user_scorecard import UserScorecardResult

# ---------------------------------------------------------------------------
# Grade colors (consistent with user-scorecard/user-duel/user-tournament)
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

class TeamScorecardHTMLRenderer:
    """Generate a self-contained dark-theme HTML team scorecard report."""

    def render(
        self,
        result: TeamScorecardResult,
        timestamp: Optional[str] = None,
    ) -> str:
        if timestamp is None:
            timestamp = result.timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        org = result.org
        aggregate_grade = result.aggregate_grade
        aggregate_score = result.aggregate_score
        grade_color = _grade_color(aggregate_grade)

        # Grade distribution
        grade_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        for r in result.contributor_results:
            g = r.grade if r.grade in grade_counts else "D"
            grade_counts[g] += 1

        total = result.contributor_count or 1

        grade_dist_bars = ""
        for g in ("A", "B", "C", "D"):
            count = grade_counts[g]
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

        # Contributor rows (sorted by score desc)
        sorted_results = sorted(result.contributor_results, key=lambda r: r.avg_score, reverse=True)
        contributor_rows = ""
        for rank, r in enumerate(sorted_results, 1):
            avatar_url = f"https://github.com/{r.username}.png?size=40"
            profile_url = f"https://github.com/{r.username}"
            rc = _grade_color(r.grade)
            score_pct = min(r.avg_score, 100)
            top_badge = " 🏆" if r.username == result.top_scorer else ""
            contributor_rows += f"""
      <tr>
        <td class="rank-cell">{rank}</td>
        <td class="user-cell">
          <img class="avatar-sm" src="{avatar_url}" alt="{r.username}" width="32" height="32">
          <a href="{profile_url}" target="_blank">@{r.username}</a>{top_badge}
        </td>
        <td class="score-cell">
          <div class="score-bar-wrap">
            <div class="score-bar" style="width:{score_pct:.0f}%"></div>
            <span class="score-num">{r.avg_score:.1f}</span>
          </div>
        </td>
        <td>
          <span class="grade-pill" style="color:{rc};border-color:{rc}">{r.grade}</span>
        </td>
        <td class="repos-cell">{r.analyzed_repos}</td>
      </tr>"""

        # Top scorer callout
        top_scorer_html = ""
        if result.top_scorer:
            top_result = next((r for r in result.contributor_results if r.username == result.top_scorer), None)
            if top_result:
                tc = _grade_color(top_result.grade)
                top_scorer_html = f"""
    <div class="top-scorer-box">
      <span class="top-scorer-label">🏆 Top Scorer</span>
      <a href="https://github.com/{result.top_scorer}" target="_blank" class="top-scorer-name">@{result.top_scorer}</a>
      <span class="top-scorer-score" style="color:{tc}">{top_result.avg_score:.1f} / 100 &nbsp; {top_result.grade}</span>
    </div>"""

        css = self._css()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Team Agent-Readiness Scorecard — {org}</title>
<style>{css}</style>
</head>
<body>
<div class="card">

  <div class="header">
    <div class="header-info">
      <h1>{org}</h1>
      <div class="header-sub">Team Agent-Readiness Scorecard</div>
    </div>
    <div class="team-grade-block">
      <div class="team-grade" style="color:{grade_color};border-color:{grade_color}">{aggregate_grade}</div>
      <div class="team-score-label">Team Score: {aggregate_score:.1f}/100</div>
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
        <th>Repos</th>
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
.team-grade-block { text-align: center; }
.team-grade {
    font-size: 3.5rem;
    font-weight: bold;
    width: 80px;
    height: 80px;
    line-height: 80px;
    text-align: center;
    border: 3px solid;
    border-radius: 8px;
}
.team-score-label { font-size: 0.75rem; color: #8b949e; margin-top: 0.3rem; }
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
.repos-cell { color: #8b949e; text-align: center; }
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
