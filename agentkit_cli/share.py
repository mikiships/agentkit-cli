"""agentkit share — score card HTML generation and here.now upload."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.publish import (
    PublishError,
    _json_post,
    _put_file,
    _finalize,
    HERENOW_API_BASE,
)


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.card {
    max-width: 700px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
h1 { font-size: 1.4rem; color: #58a6ff; margin-bottom: 0.25rem; }
.ref { font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.hero {
    text-align: center;
    padding: 1.5rem 0;
    margin-bottom: 1.5rem;
    border-top: 1px solid #30363d;
    border-bottom: 1px solid #30363d;
}
.hero-score {
    font-size: 5rem;
    font-weight: bold;
    line-height: 1;
}
.score-green { color: #3fb950; }
.score-yellow { color: #d29922; }
.score-red { color: #f85149; }
.hero-label { font-size: 0.9rem; color: #8b949e; margin-top: 0.5rem; }
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
}
th {
    text-align: left;
    color: #8b949e;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #30363d;
}
td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #21262d; }
.tool-name { color: #e6edf3; }
.indicator-pass { color: #3fb950; }
.indicator-fail { color: #f85149; }
.indicator-na { color: #8b949e; }
.footer { font-size: 0.75rem; color: #8b949e; text-align: center; }
.footer a { color: #58a6ff; text-decoration: none; }
"""


def _score_class(score: Optional[float]) -> str:
    if score is None:
        return "score-yellow"
    if score >= 80:
        return "score-green"
    if score >= 60:
        return "score-yellow"
    return "score-red"


def _indicator(score: Optional[float]) -> tuple[str, str]:
    """Return (symbol, css_class) for a tool score."""
    if score is None:
        return "–", "indicator-na"
    if score >= 60:
        return "✓", "indicator-pass"
    return "✗", "indicator-fail"


def generate_scorecard_html(
    score_result: dict,
    project_name: str = "unknown",
    ref: str = "unknown",
    timestamp: Optional[str] = None,
    no_scores: bool = False,
    repo_url: Optional[str] = None,
    repo_name: Optional[str] = None,
) -> str:
    """Generate a standalone dark-theme HTML score card.

    Args:
        score_result: Dict from agentkit score/report with keys like
            'composite', 'breakdown' or individual tool keys.
        project_name: Display name for the project.
        ref: Git ref or tag (e.g. 'main', 'v1.2.3').
        timestamp: ISO timestamp string; defaults to now (UTC).
        no_scores: If True, hide raw numbers (show pass/fail only).
        repo_url: Optional URL of the analyzed repository (shown in header).
        repo_name: Optional name of the analyzed repository (overrides project_name in header).

    Returns:
        A self-contained HTML string.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Extract composite score
    composite: Optional[float] = None
    for key in ("composite", "score", "total_score"):
        v = score_result.get(key)
        if v is not None:
            try:
                composite = float(v)
            except (TypeError, ValueError):
                pass
            break

    # Extract per-tool scores
    tool_scores: dict[str, Optional[float]] = {}
    breakdown = score_result.get("breakdown") or {}
    known_tools = ["agentmd", "agentlint", "coderace", "agentreflect"]
    for tool in known_tools:
        val = breakdown.get(tool) or score_result.get(tool)
        if val is not None:
            try:
                tool_scores[tool] = float(val)
            except (TypeError, ValueError):
                tool_scores[tool] = None
        else:
            # Only include tool if it appears at all
            pass

    # If no breakdown, try top-level tool keys
    if not tool_scores:
        for tool in known_tools:
            v = score_result.get(tool)
            if v is not None:
                try:
                    tool_scores[tool] = float(v)
                except (TypeError, ValueError):
                    tool_scores[tool] = None

    # Build composite display
    if composite is not None and not no_scores:
        hero_text = str(int(round(composite)))
    elif composite is not None:
        sym, _ = _indicator(composite)
        hero_text = sym
    else:
        hero_text = "?"

    hero_class = _score_class(composite)

    # Build tool rows
    rows_html = ""
    for tool, score in tool_scores.items():
        sym, ind_class = _indicator(score)
        if no_scores or score is None:
            score_cell = f'<span class="{ind_class}">{sym}</span>'
        else:
            score_cell = f"{int(round(score))}"
        rows_html += (
            f"<tr>"
            f'<td class="tool-name">{tool}</td>'
            f"<td>{score_cell}</td>"
            f'<td class="{ind_class}">{sym}</td>'
            f"</tr>\n"
        )

    table_section = ""
    if rows_html:
        table_section = f"""
    <table>
      <tr><th>Tool</th><th>{'Pass/Fail' if no_scores else 'Score'}</th><th>Status</th></tr>
      {rows_html}
    </table>"""

    # Build repo header section
    display_name = repo_name or project_name
    if repo_url and not repo_url.startswith((".", "/", "~")):
        # Format repo link for external repos
        if repo_url.startswith("github:"):
            repo_href = "https://github.com/" + repo_url[7:]
        elif repo_url.startswith("http"):
            repo_href = repo_url.rstrip(".git")
        else:
            repo_href = f"https://github.com/{repo_url}"
        repo_header = f'<h1><a href="{repo_href}" style="color:#58a6ff;text-decoration:none;">{display_name}</a></h1>'
    else:
        repo_header = f"<h1>{display_name}</h1>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentkit score card — {display_name}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
  {repo_header}
  <div class="ref">ref: {ref} &bull; {timestamp}</div>

  <div class="hero">
    <div class="hero-score {hero_class}">{hero_text}</div>
    <div class="hero-label">{'composite score / 100' if not no_scores else 'overall quality'}</div>
  </div>

  {table_section}

  <div class="footer">
    Analyzed by
    <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli v{__version__}</a>
    &bull; <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli on PyPI</a>
    &bull; {timestamp}
  </div>
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Sweep scorecard
# ---------------------------------------------------------------------------

def generate_sweep_scorecard_html(
    results: list,
    timestamp: Optional[str] = None,
) -> str:
    """Generate a combined scorecard for multiple targets (sweep).

    Args:
        results: List of dicts with keys: target, score, grade, status, error (optional).
        timestamp: ISO timestamp string; defaults to now (UTC).

    Returns:
        A self-contained HTML string.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows_html = ""
    for rank, r in enumerate(results, 1):
        target = r.get("target", "")
        score = r.get("score")
        grade = r.get("grade") or "—"
        status = r.get("status", "")
        error = r.get("error") or ""

        score_str = str(int(round(score))) if score is not None else "—"
        sc = _score_class(score)
        if status == "succeeded":
            status_cell = '<span class="indicator-pass">✓</span>'
        else:
            status_cell = '<span class="indicator-fail">✗</span>'

        rows_html += (
            f"<tr>"
            f"<td>{rank}</td>"
            f'<td class="tool-name">{target}</td>'
            f'<td class="{sc}">{score_str}</td>'
            f"<td>{grade}</td>"
            f"<td>{status_cell}</td>"
            f"<td>{error}</td>"
            f"</tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentkit sweep scorecard</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
  <h1>agentkit sweep</h1>
  <div class="ref">{len(results)} target(s) analyzed &bull; {timestamp}</div>

  <table>
    <tr>
      <th>#</th><th>Target</th><th>Score</th><th>Grade</th><th>Status</th><th>Error</th>
    </tr>
    {rows_html}
  </table>

  <div class="footer">
    Analyzed by
    <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli v{__version__}</a>
    &bull; <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli on PyPI</a>
    &bull; {timestamp}
  </div>
</div>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_scorecard(html: str, api_key: Optional[str] = None) -> Optional[str]:
    """Upload HTML score card to here.now. Returns URL or None on failure.

    Anonymous (no api_key): expires in 24h.
    With HERENOW_API_KEY: persistent.
    """
    if api_key is None:
        api_key = os.environ.get("HERENOW_API_KEY") or None

    content = html.encode("utf-8")
    headers: dict = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        step1_body = {"files": [{"path": "index.html", "contentType": "text/html; charset=utf-8", "size": len(content)}]}
        step1_resp = _json_post(f"{HERENOW_API_BASE}/publish", step1_body, headers)

        # Response shape: {"siteUrl": "...", "upload": {"versionId": "...", "uploads": [...], "finalizeUrl": "..."}}
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

    except PublishError as e:
        import sys
        print(f"Warning: score card upload failed: {e}", file=sys.stderr)
        return None
    except Exception as e:
        import sys
        print(f"Warning: score card upload failed unexpectedly: {e}", file=sys.stderr)
        return None
