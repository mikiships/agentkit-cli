"""Dark-theme HTML cert report generator for agentkit certify."""
from __future__ import annotations

import html
from agentkit_cli.certify import CertResult

VERDICT_COLOR = {
    "PASS": "#238636",
    "WARN": "#d29922",
    "FAIL": "#da3633",
}
VERDICT_BG = {
    "PASS": "#1a3a25",
    "WARN": "#3a2f1a",
    "FAIL": "#3a1a1a",
}


def render_html_cert(result: CertResult, project_name: str = "project") -> str:
    """Render a dark-theme HTML cert card for the given CertResult."""
    v_color = VERDICT_COLOR.get(result.verdict, "#888")
    v_bg = VERDICT_BG.get(result.verdict, "#1a1a1a")
    project = html.escape(project_name)
    timestamp = html.escape(result.timestamp)
    verdict = html.escape(result.verdict)
    cert_id = html.escape(result.cert_id)
    sha256 = html.escape(result.sha256)

    rows = [
        ("Composite Score", result.score, _score_bar(result.score)),
        ("Redteam Resistance", result.redteam_score, _score_bar(result.redteam_score)),
        ("Context Freshness", result.freshness_score, _score_bar(result.freshness_score)),
        ("Tests Found", result.tests_found, ""),
    ]

    rows_html = "".join(
        f"""
        <tr>
          <td class="check-name">{html.escape(label)}</td>
          <td class="check-score">{value}</td>
          <td class="check-bar">{bar}</td>
        </tr>"""
        for label, value, bar in rows
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>agentkit cert — {project}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      min-height: 100vh;
      padding: 40px 16px;
    }}
    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      max-width: 600px;
      width: 100%;
      overflow: hidden;
    }}
    .card-header {{
      background: {v_bg};
      border-bottom: 1px solid #30363d;
      padding: 24px 28px;
    }}
    .card-header h1 {{
      font-size: 1.1rem;
      color: #8b949e;
      font-weight: 400;
      margin-bottom: 8px;
    }}
    .project-name {{
      font-size: 1.5rem;
      font-weight: 700;
      color: #e6edf3;
    }}
    .verdict-badge {{
      display: inline-block;
      background: {v_color};
      color: #fff;
      font-weight: 700;
      font-size: 1rem;
      padding: 4px 16px;
      border-radius: 20px;
      margin-top: 12px;
      letter-spacing: 0.05em;
    }}
    .cert-meta {{
      padding: 16px 28px;
      border-bottom: 1px solid #30363d;
      font-size: 0.85rem;
      color: #8b949e;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .cert-meta .cert-id {{
      font-family: monospace;
      color: #58a6ff;
      font-size: 0.95rem;
    }}
    .checks-table {{
      width: 100%;
      border-collapse: collapse;
    }}
    .checks-table th {{
      background: #1c2128;
      color: #8b949e;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 10px 28px;
      text-align: left;
    }}
    .checks-table td {{
      padding: 12px 28px;
      border-top: 1px solid #21262d;
    }}
    .check-name {{ color: #c9d1d9; font-weight: 500; }}
    .check-score {{ color: #e6edf3; font-weight: 700; font-size: 1rem; width: 60px; }}
    .check-bar {{ width: 180px; }}
    .bar-track {{
      background: #21262d;
      border-radius: 4px;
      height: 8px;
      width: 100%;
    }}
    .bar-fill {{
      background: {v_color};
      border-radius: 4px;
      height: 8px;
    }}
    .fingerprint {{
      padding: 16px 28px;
      border-top: 1px solid #30363d;
      font-size: 0.75rem;
      color: #8b949e;
      word-break: break-all;
      font-family: monospace;
    }}
    .fingerprint-label {{
      color: #58a6ff;
      font-weight: 600;
      margin-right: 8px;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <h1>agentkit certification report</h1>
      <div class="project-name">{project}</div>
      <div class="verdict-badge">{verdict}</div>
    </div>
    <div class="cert-meta">
      <span>Cert ID: <span class="cert-id">{cert_id}</span></span>
      <span>{timestamp}</span>
    </div>
    <table class="checks-table">
      <thead>
        <tr>
          <th>Check</th>
          <th>Score</th>
          <th>Bar</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    <div class="fingerprint">
      <span class="fingerprint-label">SHA256:</span>{sha256}
    </div>
  </div>
</body>
</html>"""


def _score_bar(score: int) -> str:
    """Return an HTML progress bar for a score 0-100."""
    pct = max(0, min(100, score))
    return f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
