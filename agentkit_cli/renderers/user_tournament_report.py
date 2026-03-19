"""agentkit user-tournament HTML report renderer."""
from __future__ import annotations

from typing import Optional

from agentkit_cli.engines.user_tournament import TournamentResult
from agentkit_cli.publish import _json_post, _put_file, _finalize, HERENOW_API_BASE


_GRADE_COLORS = {"A": "#3fb950", "B": "#4493f8", "C": "#e3b341", "D": "#f85149"}


class UserTournamentReportRenderer:
    """Render a TournamentResult as a dark-theme HTML report."""

    def render(self, result: TournamentResult) -> str:
        """Return a pure HTML string (no file I/O)."""
        champion_standing = result.standings[0] if result.standings else None
        champion_grade = champion_standing.grade if champion_standing else "D"
        champion_color = _GRADE_COLORS.get(champion_grade, "#4493f8")
        champion_record = champion_standing.record() if champion_standing else "0-0"
        champion_avg = f"{champion_standing.avg_score:.1f}" if champion_standing else "0.0"

        # Standings rows
        rows_html = ""
        for s in result.standings:
            g_color = _GRADE_COLORS.get(s.grade, "#4493f8")
            rows_html += f"""
        <tr>
          <td>#{s.rank}</td>
          <td><a href="https://github.com/{s.handle}" style="color:#4493f8;">@{s.handle}</a></td>
          <td>{s.record()}</td>
          <td>{s.avg_score:.1f}</td>
          <td style="color:{g_color};font-weight:bold;">{s.grade}</td>
        </tr>"""

        # Match results
        matches_html = ""
        for mr in result.match_results:
            if hasattr(mr, "user1"):
                winner_label = ""
                if not mr.tied:
                    winner = mr.user1 if mr.overall_winner == "user1" else mr.user2
                    winner_label = f"<span style='color:#3fb950;'>🏆 @{winner}</span>"
                else:
                    winner_label = "<span style='color:#e3b341;'>Tie</span>"
                matches_html += f"""
        <div class="match">
          <span>@{mr.user1} vs @{mr.user2}</span> — {winner_label}
        </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Developer Agent-Readiness Tournament</title>
  <style>
    body {{ background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 24px; }}
    .container {{ max-width: 900px; margin: 0 auto; }}
    h1 {{ color: #4493f8; font-size: 2rem; margin-bottom: 4px; }}
    .subtitle {{ color: #8b949e; margin-bottom: 24px; }}
    .champion-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 24px; margin-bottom: 24px; display: flex; align-items: center; gap: 24px; }}
    .champion-avatar {{ width: 80px; height: 80px; border-radius: 50%; border: 2px solid {champion_color}; }}
    .champion-name {{ font-size: 1.5rem; font-weight: bold; color: {champion_color}; }}
    .grade-badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; background: {champion_color}; color: #0d1117; font-weight: bold; font-size: 1.1rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
    th {{ background: #161b22; color: #4493f8; padding: 12px 16px; text-align: left; border-bottom: 1px solid #30363d; }}
    td {{ padding: 10px 16px; border-bottom: 1px solid #21262d; }}
    tr:hover td {{ background: #161b22; }}
    .match {{ background: #161b22; border: 1px solid #21262d; border-radius: 4px; padding: 10px 16px; margin-bottom: 8px; }}
    .section-title {{ color: #8b949e; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin: 24px 0 12px; }}
    .footer {{ color: #8b949e; font-size: 0.8rem; margin-top: 32px; text-align: center; }}
  </style>
</head>
<body>
<div class="container">
  <h1>🏆 Developer Agent-Readiness Tournament</h1>
  <div class="subtitle">{result.timestamp} &mdash; {result.mode} &mdash; {len(result.participants)} participants</div>

  <div class="section-title">Champion</div>
  <div class="champion-card">
    <img class="champion-avatar" src="https://github.com/{result.champion}.png?size=80" alt="@{result.champion}" onerror="this.style.display='none'">
    <div>
      <div class="champion-name">@{result.champion}</div>
      <div style="margin-top:8px;">
        <span class="grade-badge">{champion_grade}</span>
        <span style="margin-left:12px;color:#8b949e;">{champion_record} record &mdash; avg {champion_avg}/100</span>
      </div>
    </div>
  </div>

  <div class="section-title">Standings</div>
  <table>
    <thead>
      <tr>
        <th>Rank</th><th>Handle</th><th>W-L</th><th>Avg Score</th><th>Grade</th>
      </tr>
    </thead>
    <tbody>{rows_html}
    </tbody>
  </table>

  <div class="section-title">Match Results</div>
  {matches_html}

  <div class="footer">Powered by agentkit-cli</div>
</div>
</body>
</html>"""
        return html


def publish_user_tournament(result: TournamentResult) -> Optional[str]:
    """Render and publish tournament report to here.now. Returns URL or None."""
    try:
        renderer = UserTournamentReportRenderer()
        html = renderer.render(result)
        payload = _json_post(
            f"{HERENOW_API_BASE}/api/v1/publish",
            {"files": [{"path": "index.html", "content_type": "text/html"}]},
        )
        upload_url = payload["files"][0]["upload_url"]
        pub_id = payload["id"]
        _put_file(upload_url, html.encode("utf-8"), "text/html")
        final = _finalize(f"{HERENOW_API_BASE}/api/v1/publish/{pub_id}/finalize")
        return final.get("url")
    except Exception:
        return None
