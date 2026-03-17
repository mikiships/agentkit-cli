"""agentkit track report — dark-theme HTML report for PR tracking."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from agentkit_cli.pr_tracker import TrackedPRStatus


_STATUS_COLORS = {
    "merged": "#22c55e",   # green
    "open": "#eab308",     # yellow
    "closed": "#ef4444",   # red
    "unknown": "#6b7280",  # gray
}


def generate_html_report(
    statuses: List[TrackedPRStatus],
    version: str = "0.40.0",
    title: str = "PR Campaign Tracker",
) -> str:
    """Generate a dark-theme HTML report for the given tracked PR statuses."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    merged = sum(1 for s in statuses if s.status == "merged")
    open_ = sum(1 for s in statuses if s.status == "open")
    closed = sum(1 for s in statuses if s.status == "closed")
    total = len(statuses)
    merge_rate = round(merged / total * 100, 1) if total > 0 else 0.0

    # Group by campaign
    campaigns: dict[str, list[TrackedPRStatus]] = {}
    for s in statuses:
        key = s.campaign_id or "(no campaign)"
        campaigns.setdefault(key, []).append(s)

    rows_html = _build_rows(statuses)
    campaign_sections = _build_campaign_sections(campaigns) if len(campaigns) > 1 else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{title} — {now}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0f172a; color: #e2e8f0; font-family: ui-monospace, 'Cascadia Code', monospace; padding: 2rem; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.25rem; color: #f8fafc; }}
    .subtitle {{ color: #94a3b8; font-size: 0.875rem; margin-bottom: 2rem; }}
    .stats {{ display: flex; gap: 1.5rem; margin-bottom: 2rem; flex-wrap: wrap; }}
    .stat-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 1rem 1.5rem; min-width: 140px; }}
    .stat-label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }}
    .stat-value {{ font-size: 2rem; font-weight: 700; margin-top: 0.25rem; }}
    .stat-merged {{ color: #22c55e; }}
    .stat-open {{ color: #eab308; }}
    .stat-closed {{ color: #ef4444; }}
    .stat-rate {{ color: #38bdf8; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
    th {{ text-align: left; padding: 0.75rem 1rem; background: #1e293b; color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #334155; }}
    td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #1e293b; font-size: 0.875rem; }}
    tr:hover td {{ background: #1e293b; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
    .badge-merged {{ background: #14532d; color: #22c55e; }}
    .badge-open {{ background: #713f12; color: #eab308; }}
    .badge-closed {{ background: #7f1d1d; color: #ef4444; }}
    .badge-unknown {{ background: #1f2937; color: #6b7280; }}
    a {{ color: #38bdf8; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    h2 {{ font-size: 1.1rem; color: #cbd5e1; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
    footer {{ color: #475569; font-size: 0.75rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #1e293b; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="subtitle">Generated {now}</div>

  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Merged</div>
      <div class="stat-value stat-merged">{merged}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Open</div>
      <div class="stat-value stat-open">{open_}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Closed</div>
      <div class="stat-value stat-closed">{closed}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Merge Rate</div>
      <div class="stat-value stat-rate">{merge_rate}%</div>
    </div>
  </div>

{campaign_sections if campaign_sections else _build_table(rows_html)}

  <footer>
    agentkit-cli v{version} · Uploaded {now}
  </footer>
</body>
</html>"""

    return html


def _status_badge(status: str) -> str:
    css = f"badge-{status}" if status in ("merged", "open", "closed") else "badge-unknown"
    return f'<span class="badge {css}">{status}</span>'


def _build_row(s: TrackedPRStatus) -> str:
    pr_link = ""
    if s.pr_url:
        pr_num = f"#{s.pr_number}" if s.pr_number else "PR"
        pr_link = f'<a href="{s.pr_url}" target="_blank">{pr_num}</a>'
    elif s.pr_number:
        pr_link = f"#{s.pr_number}"
    else:
        pr_link = "-"

    submitted_short = s.submitted_at[:10] if s.submitted_at else "-"

    return (
        f"<tr>"
        f"<td>{s.repo}</td>"
        f"<td>{pr_link}</td>"
        f"<td>{_status_badge(s.status)}</td>"
        f"<td>{s.days_open}</td>"
        f"<td>{s.review_comments}</td>"
        f"<td>{submitted_short}</td>"
        f"</tr>"
    )


def _build_rows(statuses: List[TrackedPRStatus]) -> str:
    return "\n    ".join(_build_row(s) for s in statuses)


def _table_header() -> str:
    return """  <table>
    <thead>
      <tr>
        <th>Repo</th>
        <th>PR #</th>
        <th>Status</th>
        <th>Days Open</th>
        <th>Reviews</th>
        <th>Submitted</th>
      </tr>
    </thead>
    <tbody>"""


def _build_table(rows_html: str) -> str:
    return f"""{_table_header()}
    {rows_html}
    </tbody>
  </table>"""


def _build_campaign_sections(campaigns: dict[str, list[TrackedPRStatus]]) -> str:
    parts = []
    for campaign_id, statuses in sorted(campaigns.items()):
        rows = _build_rows(statuses)
        section = f"""  <h2>Campaign: {campaign_id}</h2>
{_build_table(rows)}"""
        parts.append(section)
    return "\n".join(parts)
