"""agentkit topic-rank HTML report renderer — dark-theme topic repo ranking."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.topic_rank import TopicRankResult

# ---------------------------------------------------------------------------
# Grade colors (consistent with user-rank-html / user-team)
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


def _score_to_grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    return "D"


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class TopicRankHTMLRenderer:
    """Generate a self-contained dark-theme HTML topic-rank report."""

    def render(
        self,
        result: TopicRankResult,
        timestamp: Optional[str] = None,
    ) -> str:
        if timestamp is None:
            timestamp = result.generated_at or datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            )

        topic = result.topic
        entries = result.entries

        # Mean score across entries
        mean_score = (
            round(sum(e.score for e in entries) / len(entries), 1) if entries else 0.0
        )
        mean_grade_color = _grade_color(_score_to_grade(mean_score))

        # Grade distribution
        grade_dist: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
        for e in entries:
            g = e.grade if e.grade in grade_dist else "D"
            grade_dist[g] += 1

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

        # Top scorer spotlight
        top_scorer_html = ""
        if entries:
            top = entries[0]
            tc = _grade_color(top.grade)
            repo_url = f"https://github.com/{top.repo_full_name}"
            top_scorer_html = f"""
    <div class="top-scorer-box">
      <span class="top-scorer-label">🏆 Top Repo</span>
      <a href="{repo_url}" target="_blank" class="top-scorer-name">{top.repo_full_name}</a>
      <span class="top-scorer-score" style="color:{tc}">{top.score:.1f} / 100 &nbsp; {top.grade}</span>
    </div>"""

        # Repo rows
        repo_rows = ""
        for entry in entries:
            rc = _grade_color(entry.grade)
            score_pct = min(entry.score, 100)
            repo_url = f"https://github.com/{entry.repo_full_name}"
            desc = entry.description[:60] + "…" if len(entry.description) > 60 else entry.description
            top_mark = " 🏆" if entry.rank == 1 else ""
            repo_rows += f"""
      <tr>
        <td class="rank-cell">{entry.rank}</td>
        <td class="repo-name-cell">
          <a href="{repo_url}" target="_blank">{entry.repo_full_name}</a>{top_mark}
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
        <td class="stars-cell">⭐ {entry.stars:,}</td>
        <td class="desc-cell">{desc or "<em style='color:#8b949e'>—</em>"}</td>
      </tr>"""

        css = self._css()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent-Ready Repos: {topic}</title>
<style>{css}</style>
</head>
<body>
<div class="card">

  <div class="header">
    <div class="header-info">
      <h1>{topic}</h1>
      <div class="header-sub">State of Agent Readiness — Top Repos</div>
      <div class="badge-count">{result.total_analyzed} repos analyzed</div>
    </div>
    <div class="mean-score-block">
      <div class="mean-score" style="color:{mean_grade_color}">{mean_score:.1f}</div>
      <div class="mean-score-label">Mean Score / 100</div>
    </div>
  </div>

  {top_scorer_html}

  <div class="section-header">Repo Rankings</div>
  <table class="repo-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Repo</th>
        <th>Score</th>
        <th>Grade</th>
        <th>Stars</th>
        <th>Description</th>
      </tr>
    </thead>
    <tbody>
      {repo_rows}
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
    max-width: 900px;
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
.badge-count {
    display: inline-block;
    margin-top: 0.4rem;
    font-size: 0.75rem;
    color: #58a6ff;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 0.1rem 0.6rem;
}
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
.repo-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
}
.repo-table th {
    text-align: left;
    font-size: 0.75rem;
    color: #8b949e;
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid #30363d;
}
.repo-table td {
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid #21262d;
    vertical-align: middle;
}
.rank-cell { color: #8b949e; width: 36px; text-align: center; }
.repo-name-cell a { color: #58a6ff; text-decoration: none; font-weight: 600; }
.repo-name-cell a:hover { text-decoration: underline; }
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
.stars-cell { white-space: nowrap; font-size: 0.85rem; color: #e6edf3; }
.desc-cell { font-size: 0.8rem; color: #8b949e; max-width: 240px; }
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
