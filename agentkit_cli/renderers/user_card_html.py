"""agentkit user-card HTML renderer — compact embeddable agent-readiness card."""
from __future__ import annotations

from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.user_card import UserCardResult
from agentkit_cli.share import upload_scorecard


_GRADE_COLORS = {
    "A": "#3fb950",
    "B": "#4493f8",
    "C": "#e3b341",
    "D": "#f85149",
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0d1117;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 12px;
  width: 400px;
  overflow: hidden;
  color: #c9d1d9;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid #30363d;
  background: #0d1117;
}
.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid #30363d;
  object-fit: cover;
}
.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #21262d;
  border: 2px solid #30363d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: #8b949e;
}
.user-info { flex: 1; }
.user-info .handle {
  font-size: 1rem;
  font-weight: 600;
  color: #e6edf3;
}
.user-info .subtitle {
  font-size: 0.78rem;
  color: #8b949e;
  margin-top: 0.15rem;
}
.grade-badge {
  font-size: 1.6rem;
  font-weight: 700;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stats-row {
  display: flex;
  padding: 1rem 1.5rem;
  gap: 0;
  border-bottom: 1px solid #30363d;
}
.stat {
  flex: 1;
  text-align: center;
  padding: 0.4rem 0;
}
.stat + .stat {
  border-left: 1px solid #21262d;
}
.stat .value {
  font-size: 1.3rem;
  font-weight: 700;
  color: #e6edf3;
  line-height: 1.2;
}
.stat .label {
  font-size: 0.7rem;
  color: #8b949e;
  margin-top: 0.15rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.top-repo {
  padding: 0.9rem 1.5rem;
  border-bottom: 1px solid #30363d;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}
.top-repo .label { color: #8b949e; white-space: nowrap; }
.top-repo .repo-chip {
  background: #21262d;
  border: 1px solid #30363d;
  border-radius: 20px;
  padding: 0.2rem 0.65rem;
  color: #58a6ff;
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}
.top-repo .score-chip {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 20px;
  padding: 0.2rem 0.65rem;
  font-size: 0.8rem;
  margin-left: auto;
  white-space: nowrap;
}
.footer {
  padding: 0.7rem 1.5rem;
  font-size: 0.72rem;
  color: #484f58;
  text-align: center;
}
.footer a { color: #58a6ff; text-decoration: none; }
"""


class UserCardHTMLRenderer:
    """Render a compact dark-theme HTML agent-readiness card."""

    def render(self, result: UserCardResult, share_url: Optional[str] = None) -> str:
        grade = result.grade
        grade_color = _GRADE_COLORS.get(grade, "#8b949e")
        avg_score_str = f"{result.avg_score:.0f}"
        coverage_str = f"{result.context_coverage_pct:.0f}%"
        ready_str = f"{result.agent_ready_count}/{result.analyzed_repos}"

        # Avatar
        if result.avatar_url:
            avatar_html = (
                f'<img class="avatar" src="{result.avatar_url}" '
                f'alt="@{result.username}" width="48" height="48" '
                f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
                f'<div class="avatar-placeholder" style="display:none">👤</div>'
            )
        else:
            avatar_html = '<div class="avatar-placeholder">👤</div>'

        # Top repo section
        if result.top_repo_name:
            top_score_str = f"{result.top_repo_score:.0f}/100"
            top_repo_section = f"""
  <div class="top-repo">
    <span class="label">Top:</span>
    <span class="repo-chip">{result.top_repo_name}</span>
    <span class="score-chip" style="color:{grade_color}">{top_score_str}</span>
  </div>"""
        else:
            top_repo_section = ""

        # Embed comment
        embed_comment = ""
        if share_url:
            embed_comment = f"\n<!-- Markdown embed: ![Agent-Readiness Card]({share_url}) -->"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>@{result.username} — Agent-Readiness Card</title>
  <style>{_CSS}</style>
</head>
<body>{embed_comment}
<div class="card">
  <div class="card-header">
    {avatar_html}
    <div class="user-info">
      <div class="handle">@{result.username}</div>
      <div class="subtitle">Agent-Readiness Card</div>
    </div>
    <div class="grade-badge" style="background:{grade_color}22;color:{grade_color};border:2px solid {grade_color}55">{grade}</div>
  </div>
  <div class="stats-row">
    <div class="stat">
      <div class="value" style="color:{grade_color}">{avg_score_str}</div>
      <div class="label">Avg Score</div>
    </div>
    <div class="stat">
      <div class="value">{coverage_str}</div>
      <div class="label">Context</div>
    </div>
    <div class="stat">
      <div class="value">{ready_str}</div>
      <div class="label">Agent-Ready</div>
    </div>
    <div class="stat">
      <div class="value">{result.total_repos}</div>
      <div class="label">Total Repos</div>
    </div>
  </div>{top_repo_section}
  <div class="footer">
    Powered by <a href="https://agentkit.dev">agentkit-cli</a> v{__version__}
  </div>
</div>
</body>
</html>"""
        return html


def upload_user_card(html: str) -> Optional[str]:
    """Upload user-card HTML to here.now. Returns the URL or None on failure."""
    return upload_scorecard(html)
