"""Dark-theme HTML renderer for the daily agent-ready leaderboard."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from agentkit_cli import __version__

_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.card {
    max-width: 960px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
h1 { font-size: 1.6rem; color: #58a6ff; margin-bottom: 0.25rem; }
.subtitle { font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.summary {
    display: flex; gap: 1.5rem; margin-bottom: 1.5rem;
    padding: 1rem; background: #0d1117;
    border-radius: 6px; border: 1px solid #21262d;
}
.stat { text-align: center; flex: 1; }
.stat-value { font-size: 2rem; font-weight: bold; color: #58a6ff; }
.stat-label { font-size: 0.75rem; color: #8b949e; margin-top: 0.25rem; }
table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; font-size: 0.88rem; }
th { text-align: left; color: #8b949e; padding: 0.5rem 0.75rem; border-bottom: 1px solid #30363d; }
td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; vertical-align: top; }
td a { color: #58a6ff; text-decoration: none; }
td a:hover { text-decoration: underline; }
.rank { color: #8b949e; font-weight: bold; width: 3rem; }
.badge-gold   { color: #ffd700; font-size: 1.1rem; }
.badge-silver { color: #c0c0c0; font-size: 1.1rem; }
.badge-bronze { color: #cd7f32; font-size: 1.1rem; }
.score-high { color: #3fb950; font-weight: bold; }
.score-mid  { color: #d29922; }
.score-low  { color: #f85149; }
.score-na   { color: #8b949e; }
.finding    { color: #8b949e; font-size: 0.80rem; margin-top: 0.2rem; }
.repo-name  { font-weight: bold; }
.footer {
    font-size: 0.75rem; color: #8b949e; text-align: center; margin-top: 1rem;
    padding-top: 1rem; border-top: 1px solid #21262d;
}
.footer a { color: #58a6ff; text-decoration: none; }
.cta {
    text-align: center; margin: 1.5rem 0;
    padding: 0.75rem; background: #0d1117;
    border: 1px solid #30363d; border-radius: 6px; font-size: 0.85rem; color: #8b949e;
}
.cta code { color: #58a6ff; }
"""

_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
_MEDAL_CLASSES = {1: "badge-gold", 2: "badge-silver", 3: "badge-bronze"}


def _score_class(score: Optional[float]) -> str:
    if score is None:
        return "score-na"
    if score >= 80:
        return "score-high"
    if score >= 60:
        return "score-mid"
    return "score-low"


def _format_date(d: date) -> str:
    """Format date as 'March 19, 2026'."""
    return d.strftime("%B %-d, %Y")


def render_leaderboard_html(
    leaderboard,
    generated_at: Optional[datetime] = None,
) -> str:
    """Render a DailyLeaderboard to dark-theme HTML.

    Parameters
    ----------
    leaderboard:
        DailyLeaderboard dataclass instance.
    generated_at:
        Override timestamp (defaults to leaderboard.generated_at).

    Returns
    -------
    str: Complete self-contained HTML document.
    """
    repos = leaderboard.repos
    ts = generated_at or leaderboard.generated_at
    ts_str = ts.strftime("%Y-%m-%d %H:%M UTC")
    date_str = _format_date(leaderboard.date)
    title = f"Agent-Ready Repos — {date_str}"

    # Summary stats
    scores = [r.composite_score for r in repos]
    avg_score: Optional[float] = (sum(scores) / len(scores)) if scores else None
    avg_disp = f"{avg_score:.0f}" if avg_score is not None else "N/A"
    top_repo = repos[0].full_name if repos else "N/A"

    rows_html = ""
    for r in repos:
        medal_html = ""
        if r.rank in _MEDALS:
            cls = _MEDAL_CLASSES[r.rank]
            rows_html += (
                f"<tr>"
                f"<td class='rank'><span class='{cls}'>{_MEDALS[r.rank]}</span></td>"
                f"<td>"
                f"<div class='repo-name'><a href='{r.url}' target='_blank' rel='noopener'>{r.full_name}</a></div>"
                f"<div class='finding'>{r.top_finding}</div>"
                f"</td>"
                f"<td>⭐ {r.stars:,}</td>"
                f"<td class='{_score_class(r.composite_score)}'>{int(round(r.composite_score))}</td>"
                f"<td style='color:#8b949e'>{r.language or '—'}</td>"
                f"</tr>\n"
            )
        else:
            rows_html += (
                f"<tr>"
                f"<td class='rank'>#{r.rank}</td>"
                f"<td>"
                f"<div class='repo-name'><a href='{r.url}' target='_blank' rel='noopener'>{r.full_name}</a></div>"
                f"<div class='finding'>{r.top_finding}</div>"
                f"</td>"
                f"<td>⭐ {r.stars:,}</td>"
                f"<td class='{_score_class(r.composite_score)}'>{int(round(r.composite_score))}</td>"
                f"<td style='color:#8b949e'>{r.language or '—'}</td>"
                f"</tr>\n"
            )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
  <h1>{title}</h1>
  <p class="subtitle">Generated by agentkit-cli v{__version__} | {ts_str}</p>

  <div class="summary">
    <div class="stat">
      <div class="stat-value">{len(repos)}</div>
      <div class="stat-label">Repos Ranked</div>
    </div>
    <div class="stat">
      <div class="stat-value">{avg_disp}</div>
      <div class="stat-label">Avg Score</div>
    </div>
    <div class="stat">
      <div class="stat-value" style="font-size:0.9rem;padding-top:.6rem">{top_repo}</div>
      <div class="stat-label">Top Scorer</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>Repo</th>
        <th>Stars</th>
        <th>Score</th>
        <th>Language</th>
      </tr>
    </thead>
    <tbody>
{rows_html}    </tbody>
  </table>

  <div class="cta">
    Run your own: <code>agentkit daily --share</code>
  </div>

  <div class="footer">
    <a href="https://pypi.org/project/agentkit-cli/" target="_blank" rel="noopener">agentkit-cli v{__version__}</a>
    &nbsp;|&nbsp; pip install agentkit-cli &nbsp;|&nbsp; agentkit daily --share --quiet
  </div>
</div>
</body>
</html>
"""
    return html
