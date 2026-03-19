"""agentkit user-improve HTML report renderer."""
from __future__ import annotations

import os
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.user_improve import UserImproveReport, UserImproveResult
from agentkit_cli.share import upload_scorecard


_GRADE_COLORS = {"A": "#3fb950", "B": "#4493f8", "C": "#e3b341", "D": "#f85149"}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0d1117;
  color: #c9d1d9;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  padding: 2rem;
}
.container { max-width: 960px; margin: 0 auto; }
.header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 1.5rem;
}
.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px solid #30363d;
  object-fit: cover;
}
.avatar-placeholder {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 2px solid #30363d;
  background: #21262d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: #8b949e;
}
.header-info h1 { font-size: 1.6rem; color: #e6edf3; }
.header-info p { color: #8b949e; font-size: 0.9rem; margin-top: 0.3rem; }
.summary-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.stat-card {
  flex: 1;
  min-width: 140px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}
.stat-card .label {
  font-size: 0.75rem;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stat-card .value {
  font-size: 1.8rem;
  font-weight: bold;
  margin-top: 0.25rem;
  color: #3fb950;
}
.stat-card .value.neutral { color: #4493f8; }
.stat-card .value.warn { color: #e3b341; }
.repo-cards { display: flex; flex-direction: column; gap: 1rem; }
.repo-card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
}
.repo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.repo-card-header a {
  color: #4493f8;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
}
.repo-card-header a:hover { text-decoration: underline; }
.lift-badge {
  font-size: 0.85rem;
  font-weight: bold;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  background: rgba(63, 185, 80, 0.15);
  color: #3fb950;
  border: 1px solid rgba(63, 185, 80, 0.3);
}
.lift-badge.zero {
  background: rgba(139, 148, 158, 0.15);
  color: #8b949e;
  border-color: rgba(139, 148, 158, 0.3);
}
.lift-badge.negative {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
  border-color: rgba(248, 81, 73, 0.3);
}
.score-bars {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
  align-items: center;
}
.score-bar-wrap { flex: 1; }
.score-bar-label {
  font-size: 0.75rem;
  color: #8b949e;
  margin-bottom: 0.3rem;
}
.score-bar-track {
  height: 8px;
  background: #21262d;
  border-radius: 4px;
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}
.score-bar-fill.before { background: #e3b341; }
.score-bar-fill.after { background: #3fb950; }
.score-num {
  font-size: 0.85rem;
  font-weight: bold;
  min-width: 32px;
  text-align: right;
}
.files-row {
  font-size: 0.8rem;
  color: #8b949e;
  margin-top: 0.5rem;
}
.files-row span { color: #c9d1d9; }
.error-msg {
  font-size: 0.8rem;
  color: #f85149;
  margin-top: 0.4rem;
}
.skipped-badge {
  font-size: 0.75rem;
  color: #8b949e;
  background: #21262d;
  border-radius: 8px;
  padding: 0.15rem 0.5rem;
  margin-left: 0.5rem;
}
.footer {
  margin-top: 2rem;
  text-align: center;
  font-size: 0.75rem;
  color: #8b949e;
}
.footer a { color: #4493f8; text-decoration: none; }
"""


def _lift_badge_class(lift: float) -> str:
    if lift > 0:
        return "lift-badge"
    if lift == 0:
        return "lift-badge zero"
    return "lift-badge negative"


def _lift_sign(lift: float) -> str:
    if lift >= 0:
        return f"+{lift:.1f}"
    return f"{lift:.1f}"


def _render_repo_card(result: UserImproveResult) -> str:
    skipped_html = '<span class="skipped-badge">skipped</span>' if result.skipped else ""
    lift_class = _lift_badge_class(result.lift)
    lift_text = _lift_sign(result.lift)
    repo_name = result.full_name.split("/")[-1] if "/" in result.full_name else result.full_name

    before_pct = min(100, max(0, int(result.before_score)))
    after_pct = min(100, max(0, int(result.after_score)))

    files_gen = ", ".join(result.files_generated) if result.files_generated else "none"
    files_hard = ", ".join(result.files_hardened) if result.files_hardened else "none"

    errors_html = ""
    if result.errors:
        errors_html = f'<div class="error-msg">⚠ {"; ".join(result.errors)}</div>'

    return f"""
<div class="repo-card">
  <div class="repo-card-header">
    <div>
      <a href="{result.repo_url}" target="_blank" rel="noopener">{result.full_name}</a>{skipped_html}
    </div>
    <span class="{lift_class}">{lift_text} pts</span>
  </div>
  <div class="score-bars">
    <div class="score-bar-wrap">
      <div class="score-bar-label">Before</div>
      <div class="score-bar-track">
        <div class="score-bar-fill before" style="width:{before_pct}%"></div>
      </div>
    </div>
    <div class="score-num" style="color:#e3b341">{result.before_score:.0f}</div>
    <div class="score-bar-wrap">
      <div class="score-bar-label">After</div>
      <div class="score-bar-track">
        <div class="score-bar-fill after" style="width:{after_pct}%"></div>
      </div>
    </div>
    <div class="score-num" style="color:#3fb950">{result.after_score:.0f}</div>
  </div>
  <div class="files-row">
    Generated: <span>{files_gen}</span> &bull; Hardened: <span>{files_hard}</span>
  </div>
  {errors_html}
</div>"""


class UserImproveHTMLRenderer:
    """Render a UserImproveReport as a dark-theme HTML report."""

    def render(self, report: UserImproveReport, timestamp: Optional[str] = None) -> str:
        """Return a pure HTML string."""
        from datetime import datetime, timezone
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        # Header avatar
        if report.avatar_url:
            avatar_html = f'<img class="avatar" src="{report.avatar_url}" alt="@{report.user}">'
        else:
            avatar_html = f'<div class="avatar-placeholder">👤</div>'

        # Summary stats
        stats = report.summary_stats
        avg_lift = stats.get("avg_lift", 0.0)
        avg_lift_class = "value" if avg_lift > 0 else ("value warn" if avg_lift == 0 else "value")
        total_files = stats.get("total_files_generated", 0) + stats.get("total_files_hardened", 0)

        summary_html = f"""
<div class="summary-bar">
  <div class="stat-card">
    <div class="label">Repos Improved</div>
    <div class="value neutral">{report.improved}</div>
  </div>
  <div class="stat-card">
    <div class="label">Avg Lift</div>
    <div class="{avg_lift_class}">{_lift_sign(avg_lift)} pts</div>
  </div>
  <div class="stat-card">
    <div class="label">Total Files</div>
    <div class="value neutral">{total_files}</div>
  </div>
  <div class="stat-card">
    <div class="label">Skipped</div>
    <div class="value warn">{report.skipped}</div>
  </div>
</div>"""

        # Repo cards
        cards_html = "\n".join(_render_repo_card(r) for r in report.results) or "<p style='color:#8b949e'>No repos processed.</p>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>agentkit user-improve — @{report.user}</title>
  <style>{_CSS}</style>
</head>
<body>
<div class="container">
  <div class="header">
    {avatar_html}
    <div class="header-info">
      <h1>@{report.user}</h1>
      <p>Agent-readiness improvement report &bull; {timestamp}</p>
      <p>{report.total_repos} total repos &bull; {report.improved} improved &bull; {report.skipped} skipped</p>
    </div>
  </div>

  {summary_html}

  <div class="repo-cards">
    {cards_html}
  </div>

  <div class="footer">
    <p>Analyzed by <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli v{__version__}</a> &bull; {timestamp}</p>
  </div>
</div>
</body>
</html>"""


def upload_user_improve_report(html: str, api_key: Optional[str] = None) -> Optional[str]:
    """Upload HTML report to here.now. Returns URL or None on failure."""
    return upload_scorecard(html, api_key=api_key)
