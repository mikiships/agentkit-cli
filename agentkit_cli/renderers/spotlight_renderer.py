"""SpotlightHTMLRenderer — dark-theme "Repo of the Day" HTML report."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentkit_cli.commands.spotlight_cmd import SpotlightResult

from agentkit_cli import __version__

# ---------------------------------------------------------------------------
# Grade → CSS color
# ---------------------------------------------------------------------------

_GRADE_COLORS = {
    "A": "#4caf50",
    "B": "#8bc34a",
    "C": "#ffb300",
    "D": "#ff7043",
    "F": "#f44336",
}

_SCORE_BG = {
    "A": "#1b5e20",
    "B": "#2e7d32",
    "C": "#4e342e",
    "D": "#bf360c",
    "F": "#b71c1c",
}


def _grade_color(grade: str) -> str:
    return _GRADE_COLORS.get(grade or "", "#aaaaaa")


def _grade_bg(grade: str) -> str:
    return _SCORE_BG.get(grade or "", "#333333")


def _score_bar(score: float, width: int = 200) -> str:
    pct = max(0.0, min(100.0, score))
    color = "#4caf50" if pct >= 80 else ("#ffb300" if pct >= 60 else "#f44336")
    return (
        f'<div style="background:#2a2a2a;border-radius:6px;height:14px;width:{width}px;overflow:hidden;">'
        f'<div style="width:{pct:.1f}%;background:{color};height:100%;border-radius:6px;"></div>'
        f"</div>"
    )


def _redteam_bar(resistance: float) -> str:
    pct = max(0.0, min(100.0, resistance))
    color = "#4caf50" if pct >= 70 else ("#ffb300" if pct >= 50 else "#f44336")
    return (
        f'<div style="background:#2a2a2a;border-radius:6px;height:14px;width:200px;overflow:hidden;">'
        f'<div style="width:{pct:.1f}%;background:{color};height:100%;border-radius:6px;"></div>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# SpotlightHTMLRenderer
# ---------------------------------------------------------------------------

class SpotlightHTMLRenderer:
    """Renders a SpotlightResult to a standalone dark-theme HTML string."""

    def render(self, result: "SpotlightResult") -> str:
        """Return complete HTML for the spotlight report."""
        grade = result.grade or "?"
        score = result.score
        score_str = f"{score:.1f}" if score is not None else "N/A"

        grade_col = _grade_color(grade)
        grade_bg_col = _grade_bg(grade)

        score_bar_html = _score_bar(score or 0) if score is not None else ""

        # Run date formatting
        try:
            dt = datetime.fromisoformat(result.run_date.replace("Z", "+00:00"))
            run_date_str = dt.strftime("%B %d, %Y")
        except Exception:
            run_date_str = result.run_date[:10]

        # Findings section
        findings_html = ""
        if result.top_findings:
            items = "".join(
                f'<li style="margin-bottom:8px;color:#ccc;">{_escape(f)}</li>'
                for f in result.top_findings[:5]
            )
            findings_html = f"""
            <div style="margin-top:28px;">
              <h3 style="color:#90caf9;margin-bottom:12px;font-size:14px;text-transform:uppercase;letter-spacing:1px;">Top Findings</h3>
              <ul style="list-style:none;padding:0;margin:0;">{items}</ul>
            </div>"""

        # RedTeam section
        redteam_html = ""
        if result.redteam_resistance is not None:
            rt = result.redteam_resistance
            rt_bar = _redteam_bar(rt)
            redteam_html = f"""
            <div style="margin-top:24px;padding:16px;background:#1a2636;border-radius:8px;border:1px solid #1e3a5f;">
              <h3 style="color:#90caf9;margin-bottom:10px;font-size:13px;text-transform:uppercase;letter-spacing:1px;">RedTeam Resistance</h3>
              <div style="display:flex;align-items:center;gap:12px;">
                {rt_bar}
                <span style="color:#eee;font-size:14px;">{rt:.1f} / 100</span>
              </div>
            </div>"""

        # Cert box
        cert_html = ""
        if result.cert_id:
            cert_html = f"""
            <div style="margin-top:16px;padding:14px 18px;background:#1b2a1b;border-radius:8px;border:1px solid #2e7d32;display:inline-block;">
              <span style="color:#81c784;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Certified ✓</span>
              <div style="color:#a5d6a7;font-family:monospace;font-size:15px;margin-top:4px;">CERT-{result.cert_id}</div>
            </div>"""

        # Stars + language
        meta_parts = []
        if result.repo_stars:
            meta_parts.append(f"★ {result.repo_stars:,}")
        if result.repo_language:
            meta_parts.append(result.repo_language)
        meta_str = "  ·  ".join(meta_parts)

        description_html = ""
        if result.repo_description:
            description_html = f'<p style="color:#aaa;margin:8px 0 0;font-size:14px;">{_escape(result.repo_description)}</p>'

        repo_url = f"https://github.com/{result.repo}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Repo Spotlight: {_escape(result.repo)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #121212;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 32px 16px;
  }}
  a {{ color: #90caf9; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div style="max-width:680px;margin:0 auto;">

  <!-- Header -->
  <div style="margin-bottom:8px;">
    <span style="color:#555;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Repo Spotlight · {run_date_str}</span>
  </div>

  <!-- Repo card -->
  <div style="background:#1e1e1e;border-radius:12px;padding:28px;border:1px solid #2a2a2a;margin-bottom:20px;">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;">
      <div>
        <h1 style="font-size:22px;color:#fff;font-weight:700;">
          <a href="{repo_url}" style="color:#fff;">{_escape(result.repo)}</a>
        </h1>
        {description_html}
        <div style="margin-top:10px;color:#777;font-size:13px;">{_escape(meta_str)}</div>
      </div>
      <!-- Grade badge -->
      <div style="text-align:center;min-width:72px;background:{grade_bg_col};border-radius:10px;padding:12px 16px;border:2px solid {grade_col};">
        <div style="font-size:32px;font-weight:900;color:{grade_col};line-height:1;">{grade}</div>
        <div style="font-size:12px;color:{grade_col};margin-top:2px;">{score_str}</div>
      </div>
    </div>

    <!-- Score bar -->
    <div style="margin-top:20px;">
      <div style="color:#888;font-size:12px;margin-bottom:6px;">Quality Score</div>
      <div style="display:flex;align-items:center;gap:12px;">
        {score_bar_html}
        <span style="color:#ccc;font-size:13px;">{score_str} / 100</span>
      </div>
    </div>

    {findings_html}
    {redteam_html}
    {cert_html}
  </div>

  <!-- Footer -->
  <div style="text-align:center;color:#444;font-size:12px;padding:16px 0;">
    Analyzed by <a href="https://github.com/mikiships/agentkit-cli">agentkit-cli v{__version__}</a>
  </div>
</div>
</body>
</html>"""
        return html


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
