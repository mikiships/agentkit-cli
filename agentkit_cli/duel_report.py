"""Dark-theme HTML report for `agentkit duel`."""
from __future__ import annotations

import os
import sys
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.duel import DuelResult
from agentkit_cli.publish import (
    PublishError,
    _json_post,
    _put_file,
    _finalize,
    HERENOW_API_BASE,
)

_DUEL_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #1e1e1e;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.container {
    max-width: 960px;
    margin: 0 auto;
}
h1 {
    font-size: 1.6rem;
    color: #58a6ff;
    text-align: center;
    margin-bottom: 0.5rem;
}
.subtitle {
    text-align: center;
    font-size: 0.85rem;
    color: #8b949e;
    margin-bottom: 2rem;
}
.duel-grid {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 1.5rem;
    align-items: start;
    margin-bottom: 2rem;
}
.repo-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1.5rem;
}
.repo-card.winner-card {
    border-color: #3fb950;
    box-shadow: 0 0 12px rgba(63, 185, 80, 0.2);
}
.repo-name {
    font-size: 1.1rem;
    font-weight: bold;
    color: #e6edf3;
    margin-bottom: 0.25rem;
    word-break: break-all;
}
.repo-score {
    font-size: 3.5rem;
    font-weight: bold;
    line-height: 1;
    margin: 0.75rem 0 0.25rem;
}
.score-green { color: #3fb950; }
.score-yellow { color: #d29922; }
.score-red { color: #f85149; }
.repo-grade {
    font-size: 1rem;
    color: #8b949e;
    margin-bottom: 1rem;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
th {
    text-align: left;
    color: #8b949e;
    padding: 0.4rem 0.5rem;
    border-bottom: 1px solid #30363d;
}
td { padding: 0.4rem 0.5rem; border-bottom: 1px solid #21262d; }
.tool-name { color: #e6edf3; }
.pass { color: #3fb950; }
.fail { color: #f85149; }
.na { color: #8b949e; }
.center-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
}
.vs-badge {
    font-size: 1.4rem;
    font-weight: bold;
    color: #8b949e;
}
.winner-badge {
    background: #1f3a1f;
    border: 1px solid #3fb950;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    text-align: center;
}
.winner-badge .label { font-size: 0.75rem; color: #8b949e; margin-bottom: 0.25rem; }
.winner-badge .name { font-size: 1rem; font-weight: bold; color: #3fb950; }
.winner-badge .delta { font-size: 0.85rem; color: #8b949e; margin-top: 0.25rem; }
.tie-badge {
    background: #1a1a2e;
    border: 1px solid #d29922;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    text-align: center;
    color: #d29922;
    font-weight: bold;
}
.error-note {
    background: #2d0e0e;
    border: 1px solid #f85149;
    border-radius: 6px;
    padding: 0.75rem;
    font-size: 0.8rem;
    color: #f85149;
    margin-top: 0.75rem;
    word-break: break-word;
}
.footer {
    font-size: 0.75rem;
    color: #8b949e;
    text-align: center;
    margin-top: 1.5rem;
}
.footer a { color: #58a6ff; text-decoration: none; }
@media (max-width: 700px) {
    .duel-grid { grid-template-columns: 1fr; }
    .center-col { flex-direction: row; flex-wrap: wrap; justify-content: center; }
}
"""


def _score_class(score: Optional[float]) -> str:
    if score is None:
        return "score-yellow"
    if score >= 80:
        return "score-green"
    if score >= 60:
        return "score-yellow"
    return "score-red"


def _tool_rows(breakdown: dict) -> str:
    rows = ""
    tools = ["agentmd", "agentlint", "coderace", "agentreflect"]
    for tool in tools:
        info = breakdown.get(tool)
        if info is None:
            continue
        score = info.get("score")
        status = info.get("status", "")
        if score is not None:
            try:
                score_str = str(int(round(float(score))))
                css = "pass" if float(score) >= 60 else "fail"
                sym = "✓" if float(score) >= 60 else "✗"
            except (TypeError, ValueError):
                score_str = "—"
                css = "na"
                sym = "–"
        else:
            score_str = "—"
            css = "na" if status == "skipped" else ("pass" if status == "pass" else "fail")
            sym = "✓" if status == "pass" else ("–" if status == "skipped" else "✗")
        rows += (
            f"<tr>"
            f'<td class="tool-name">{tool}</td>'
            f"<td>{score_str}</td>"
            f'<td class="{css}">{sym}</td>'
            f"</tr>\n"
        )
    return rows


def _repo_card_html(
    target: str,
    repo_name: str,
    score: Optional[float],
    grade: str,
    breakdown: dict,
    error: Optional[str],
    is_winner: bool,
) -> str:
    score_str = str(int(round(score))) if score is not None else "?"
    sc = _score_class(score)
    grade_str = grade or "—"
    winner_class = " winner-card" if is_winner else ""
    rows = _tool_rows(breakdown)
    table_html = ""
    if rows:
        table_html = f"""
    <table>
      <tr><th>Tool</th><th>Score</th><th>Status</th></tr>
      {rows}
    </table>"""
    error_html = ""
    if error:
        error_html = f'<div class="error-note">Error: {error}</div>'
    return f"""<div class="repo-card{winner_class}">
  <div class="repo-name">{repo_name}</div>
  <div style="font-size:0.75rem;color:#8b949e;">{target}</div>
  <div class="repo-score {sc}">{score_str}</div>
  <div class="repo-grade">Grade: {grade_str}</div>
  {table_html}
  {error_html}
</div>"""


def generate_duel_html(result: DuelResult) -> str:
    """Generate a standalone dark-theme HTML duel report."""
    left_is_winner = result.winner == "left"
    right_is_winner = result.winner == "right"

    left_card = _repo_card_html(
        result.left_target,
        result.left_repo_name or result.left_target.split("/")[-1],
        result.left_score,
        result.left_grade,
        result.left_breakdown,
        result.left_error,
        left_is_winner,
    )
    right_card = _repo_card_html(
        result.right_target,
        result.right_repo_name or result.right_target.split("/")[-1],
        result.right_score,
        result.right_grade,
        result.right_breakdown,
        result.right_error,
        right_is_winner,
    )

    if result.winner == "tie":
        center_html = f"""<div class="tie-badge">🤝 TIE<br><span style="font-size:0.8rem;color:#8b949e;">Within 5 points</span></div>"""
    elif result.winner in ("left", "right"):
        winner_name = (
            result.left_repo_name if result.winner == "left" else result.right_repo_name
        ) or result.winner
        delta_str = f"+{int(round(result.delta))} pts" if result.delta is not None else ""
        center_html = f"""<div class="winner-badge">
  <div class="label">WINNER</div>
  <div class="name">🏆 {winner_name}</div>
  <div class="delta">{delta_str}</div>
</div>"""
    else:
        center_html = '<div class="error-note">Both sides failed</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentkit duel — {result.left_repo_name} vs {result.right_repo_name}</title>
<style>{_DUEL_CSS}</style>
</head>
<body>
<div class="container">
  <h1>agentkit duel</h1>
  <div class="subtitle">{result.left_repo_name} vs {result.right_repo_name} &bull; {result.timestamp}</div>

  <div class="duel-grid">
    {left_card}
    <div class="center-col">
      <div class="vs-badge">VS</div>
      {center_html}
    </div>
    {right_card}
  </div>

  <div class="footer">
    Analyzed by
    <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli v{__version__}</a>
    &bull; <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli on PyPI</a>
    &bull; {result.timestamp}
  </div>
</div>
</body>
</html>"""
    return html


def publish_duel(result: DuelResult) -> Optional[str]:
    """Generate duel HTML and upload to here.now. Returns URL or None on failure."""
    html = generate_duel_html(result)
    content = html.encode("utf-8")
    api_key = os.environ.get("HERENOW_API_KEY") or None
    headers: dict = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        step1_body = {
            "files": [
                {
                    "path": "index.html",
                    "contentType": "text/html; charset=utf-8",
                    "size": len(content),
                }
            ]
        }
        step1_resp = _json_post(f"{HERENOW_API_BASE}/publish", step1_body, headers)

        upload_info = step1_resp.get("upload") or {}
        upload_urls = upload_info.get("uploads") or step1_resp.get("uploadUrls") or []
        finalize_url = upload_info.get("finalizeUrl") or step1_resp.get("finalizeUrl")
        version_id = upload_info.get("versionId")
        public_url = step1_resp.get("siteUrl") or step1_resp.get("url")

        if not upload_urls or not finalize_url:
            raise PublishError(f"Unexpected response from publish API: {step1_resp}")

        for entry in upload_urls:
            upload_url = entry.get("url")
            if not upload_url:
                raise PublishError(f"Missing upload URL in response: {entry}")
            _put_file(upload_url, content, "text/html; charset=utf-8")

        finalize_resp = _finalize(finalize_url, version_id=version_id)
        if not public_url:
            public_url = finalize_resp.get("url") or finalize_resp.get("siteUrl")
        if not public_url:
            raise PublishError(f"No URL in finalize response: {finalize_resp}")

        return public_url

    except PublishError as exc:
        print(f"Warning: duel publish failed: {exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"Warning: duel publish failed unexpectedly: {exc}", file=sys.stderr)
        return None
