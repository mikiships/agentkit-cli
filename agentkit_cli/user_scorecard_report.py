"""agentkit user-scorecard HTML report renderer."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.user_scorecard import UserScorecardResult, RepoResult

# ---------------------------------------------------------------------------
# Grade colors  (A=green, B=blue, C=yellow, D=red) per contract spec
# ---------------------------------------------------------------------------

_GRADE_COLORS = {
    "A": "#3fb950",  # green
    "B": "#58a6ff",  # blue
    "C": "#d29922",  # yellow
    "D": "#f85149",  # red
}


def _grade_color(grade: str) -> str:
    return _GRADE_COLORS.get(grade, "#8b949e")


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class UserScorecardReportRenderer:
    """Generate a self-contained dark-theme HTML profile card for a user scorecard."""

    def render(
        self,
        result: UserScorecardResult,
        timestamp: Optional[str] = None,
    ) -> str:
        """Render the HTML report. Returns a self-contained HTML string."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        username = result.username
        grade = result.grade
        grade_color = _grade_color(grade)
        avg_score = result.avg_score

        # Header / avatar
        avatar_url = f"https://github.com/{username}.png"
        profile_url = f"https://github.com/{username}"

        # Stats panel
        stats_html = f"""
    <div class="stats-panel">
      <div class="stat">
        <span class="stat-value">{result.analyzed_repos}</span>
        <span class="stat-label">Repos Analyzed</span>
      </div>
      <div class="stat">
        <span class="stat-value">{avg_score:.1f}</span>
        <span class="stat-label">Avg Score</span>
      </div>
      <div class="stat">
        <span class="stat-value">{result.context_coverage_pct:.0f}%</span>
        <span class="stat-label">Context Coverage</span>
      </div>
      <div class="stat">
        <span class="stat-value" style="color:{grade_color}">{grade}</span>
        <span class="stat-label">Overall Grade</span>
      </div>
    </div>"""

        # Ranked repo table
        repo_rows = ""
        for rank, repo in enumerate(result.all_repos, 1):
            score_val = repo.score
            score_str = f"{score_val:.0f}" if score_val is not None else "—"
            score_pct = f"{score_val:.0f}" if score_val is not None else "0"
            repo_grade = repo.grade
            repo_grade_color = _grade_color(repo_grade)
            context_icon = "✓" if repo.has_context else "✗"
            context_class = "has-context" if repo.has_context else "no-context"
            repo_url = f"https://github.com/{repo.full_name}"
            bar_width = score_val if score_val is not None else 0

            repo_rows += f"""
        <tr>
          <td class="rank">{rank}</td>
          <td class="repo-name">
            <a href="{repo_url}" target="_blank">{repo.full_name}</a>
          </td>
          <td class="score-cell">
            <div class="score-bar-wrap">
              <div class="score-bar" style="width:{bar_width}%"></div>
              <span class="score-num">{score_str}</span>
            </div>
          </td>
          <td>
            <span class="grade-badge" style="color:{repo_grade_color};border-color:{repo_grade_color}">{repo_grade}</span>
          </td>
          <td class="{context_class}">{context_icon}</td>
        </tr>"""

        # Bottom repos (needs improvement)
        improve_section = ""
        if result.bottom_repos:
            improve_items = ""
            for repo in result.bottom_repos:
                score_str = f"{repo.score:.0f}" if repo.score is not None else "—"
                cmd = f"agentkit analyze github:{repo.full_name}"
                improve_items += f"""
        <div class="improve-item">
          <div class="improve-repo">
            <a href="https://github.com/{repo.full_name}" target="_blank">{repo.full_name}</a>
            <span class="improve-score">score: {score_str}</span>
          </div>
          <code class="improve-cmd">{cmd}</code>
        </div>"""

            improve_section = f"""
    <div class="section-header">Needs Improvement</div>
    <div class="improve-section">
      {improve_items}
    </div>"""

        css = self._css()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent Quality Profile — @{username}</title>
<style>{css}</style>
</head>
<body>
<div class="card">

  <div class="header">
    <img class="avatar" src="{avatar_url}" alt="@{username} avatar" width="80" height="80">
    <div class="header-info">
      <h1>
        <a href="{profile_url}" target="_blank">@{username}</a>
      </h1>
      <div class="header-sub">Agent Quality Profile</div>
    </div>
    <div class="overall-grade" style="color:{grade_color};border-color:{grade_color}">
      {grade}
    </div>
  </div>

  {stats_html}

  <div class="section-header">Ranked Repositories</div>
  <table class="repo-table">
    <thead>
      <tr>
        <th>#</th>
        <th>Repository</th>
        <th>Score</th>
        <th>Grade</th>
        <th>Context</th>
      </tr>
    </thead>
    <tbody>
      {repo_rows}
    </tbody>
  </table>

  {improve_section}

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
  max-width: 860px;
  margin: 0 auto;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 2rem;
}
/* Header */
.header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #30363d;
}
.avatar {
  border-radius: 50%;
  border: 2px solid #30363d;
  flex-shrink: 0;
}
.header-info { flex: 1; }
h1 { font-size: 1.5rem; color: #e6edf3; }
h1 a { color: #58a6ff; text-decoration: none; }
h1 a:hover { text-decoration: underline; }
.header-sub { color: #8b949e; font-size: 0.85rem; margin-top: 0.25rem; }
.overall-grade {
  font-size: 2.5rem;
  font-weight: 900;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid;
  border-radius: 6px;
  flex-shrink: 0;
}
/* Stats */
.stats-panel {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.75rem;
}
.stat { display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 80px; }
.stat-value { font-size: 1.4rem; font-weight: 700; color: #e6edf3; }
.stat-label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.25rem; }
/* Section header */
.section-header {
  font-size: 0.8rem;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.75rem;
}
/* Repo table */
.repo-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.75rem;
  font-size: 0.875rem;
}
.repo-table th {
  text-align: left;
  color: #8b949e;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #30363d;
  font-weight: 400;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.repo-table td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #21262d;
  vertical-align: middle;
}
.repo-table tr:hover td { background: #1c2128; }
.rank { color: #8b949e; width: 2rem; text-align: center; }
.repo-name a { color: #58a6ff; text-decoration: none; }
.repo-name a:hover { text-decoration: underline; }
/* Score bar */
.score-cell { min-width: 140px; }
.score-bar-wrap {
  position: relative;
  background: #21262d;
  border-radius: 3px;
  height: 18px;
  display: flex;
  align-items: center;
  overflow: hidden;
}
.score-bar {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  background: #1f6feb;
  border-radius: 3px;
  opacity: 0.6;
  transition: width 0.3s;
}
.score-num {
  position: relative;
  z-index: 1;
  padding: 0 0.5rem;
  font-size: 0.8rem;
  color: #e6edf3;
  font-weight: 600;
}
/* Grade badge */
.grade-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border: 1px solid;
  border-radius: 4px;
  font-weight: 700;
  font-size: 0.8rem;
}
/* Context icons */
.has-context { color: #3fb950; font-weight: 700; }
.no-context { color: #8b949e; }
/* Improve section */
.improve-section { margin-bottom: 1.75rem; }
.improve-item {
  background: #0d1117;
  border: 1px solid #21262d;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
}
.improve-repo { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem; }
.improve-repo a { color: #58a6ff; text-decoration: none; }
.improve-score { color: #8b949e; font-size: 0.8rem; }
.improve-cmd {
  display: block;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 4px;
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  color: #79c0ff;
  font-family: 'Courier New', Courier, monospace;
  word-break: break-all;
}
/* Footer */
.footer {
  font-size: 0.75rem;
  color: #8b949e;
  text-align: center;
  padding-top: 1rem;
  border-top: 1px solid #21262d;
}
.footer a { color: #58a6ff; text-decoration: none; }
"""
