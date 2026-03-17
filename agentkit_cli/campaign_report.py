"""agentkit campaign report — dark-theme HTML generator for campaign results."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from agentkit_cli.campaign import CampaignResult

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
    max-width: 900px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
h1 { font-size: 1.5rem; color: #58a6ff; margin-bottom: 0.25rem; }
.meta { font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.totals {
    display: flex;
    gap: 2rem;
    padding: 1rem 0;
    margin-bottom: 1.5rem;
    border-top: 1px solid #30363d;
    border-bottom: 1px solid #30363d;
}
.total-item { text-align: center; }
.total-value { font-size: 2.5rem; font-weight: bold; color: #3fb950; }
.total-value.skip { color: #d29922; }
.total-value.fail { color: #f85149; }
.total-label { font-size: 0.75rem; color: #8b949e; margin-top: 0.25rem; }
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
.status-ok { color: #3fb950; }
.status-skip { color: #d29922; }
.status-fail { color: #f85149; }
a { color: #58a6ff; text-decoration: none; }
a:hover { text-decoration: underline; }
.footer {
    font-size: 0.75rem;
    color: #8b949e;
    text-align: center;
    padding-top: 1.5rem;
    border-top: 1px solid #30363d;
}
.cta {
    background: #1f2937;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.cta p { margin-bottom: 0.5rem; color: #8b949e; }
.cta a { font-size: 1rem; font-weight: bold; }
"""


def generate_campaign_html(result: CampaignResult) -> str:
    """Render a dark-theme HTML report for a campaign result."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows_html = ""
    for pr in result.submitted:
        repo_name = pr.repo.full_name
        stars = f"★ {pr.repo.stars:,}" if pr.repo.stars else "—"
        pr_link = f'<a href="{pr.pr_url}" target="_blank">{pr.pr_url}</a>' if pr.pr_url and pr.pr_url != "[DRY RUN]" else (pr.pr_url or "—")
        score_str = f"{pr.score_after:.1f}" if pr.score_after is not None else "—"
        rows_html += f"""
        <tr>
            <td>{repo_name}</td>
            <td>{stars}</td>
            <td class="status-ok">✅ PR opened</td>
            <td>{pr_link}</td>
            <td>{score_str}</td>
        </tr>"""

    for repo in result.skipped:
        repo_name = repo.full_name
        stars = f"★ {repo.stars:,}" if repo.stars else "—"
        rows_html += f"""
        <tr>
            <td>{repo_name}</td>
            <td>{stars}</td>
            <td class="status-skip">⏭ Skipped</td>
            <td>Already has context file</td>
            <td>—</td>
        </tr>"""

    for repo, err in result.failed:
        repo_name = repo.full_name
        stars = f"★ {repo.stars:,}" if repo.stars else "—"
        rows_html += f"""
        <tr>
            <td>{repo_name}</td>
            <td>{stars}</td>
            <td class="status-fail">❌ Failed</td>
            <td>{err[:80]}</td>
            <td>—</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit campaign report — {result.campaign_id}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
    <h1>🚀 agentkit campaign report</h1>
    <div class="meta">
        Campaign ID: <strong>{result.campaign_id}</strong> &nbsp;·&nbsp;
        Target: <strong>{result.target_spec}</strong> &nbsp;·&nbsp;
        File: <strong>{result.file}</strong> &nbsp;·&nbsp;
        Generated: {now}
    </div>

    <div class="totals">
        <div class="total-item">
            <div class="total-value">{len(result.submitted)}</div>
            <div class="total-label">PRs Opened</div>
        </div>
        <div class="total-item">
            <div class="total-value skip">{len(result.skipped)}</div>
            <div class="total-label">Skipped</div>
        </div>
        <div class="total-item">
            <div class="total-value fail">{len(result.failed)}</div>
            <div class="total-label">Failed</div>
        </div>
        <div class="total-item">
            <div class="total-value">{len(result.submitted) + len(result.skipped) + len(result.failed)}</div>
            <div class="total-label">Total Repos</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Repo</th>
                <th>Stars</th>
                <th>Status</th>
                <th>PR URL / Note</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="cta">
        <p>Want to run your own campaign? Help open source repos work better with AI agents.</p>
        <a href="https://pypi.org/project/agentkit-cli/" target="_blank">pip install agentkit-cli</a>
        &nbsp;→&nbsp;
        <code>agentkit campaign github:your-org</code>
    </div>

    <div class="footer">
        Generated by <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli</a> · 
        Contribute to open source AI readiness
    </div>
</div>
</body>
</html>"""


def publish_html(html: str, api_key: Optional[str] = None) -> Optional[str]:
    """Write HTML to a temp file and upload via publish_html. Returns URL or None."""
    import tempfile
    from pathlib import Path as _Path
    from agentkit_cli.publish import publish_html as _publish_html
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp_path = _Path(f.name)
    try:
        result = _publish_html(tmp_path, api_key=api_key)
        return result.get("url")
    finally:
        tmp_path.unlink(missing_ok=True)


def upload_campaign_report(result: CampaignResult) -> Optional[str]:
    """Generate HTML and upload to here.now. Returns URL or None."""
    api_key = os.environ.get("HERENOW_API_KEY")
    if not api_key:
        return None
    try:
        html = generate_campaign_html(result)
        return publish_html(html, api_key=api_key)
    except Exception:
        return None
