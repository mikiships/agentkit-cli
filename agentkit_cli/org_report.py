"""Dark-theme HTML report for `agentkit org`."""
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

_ORG_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #1e1e1e;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.container { max-width: 1100px; margin: 0 auto; }
h1 { font-size: 1.6rem; color: #58a6ff; text-align: center; margin-bottom: 0.5rem; }
h2 { font-size: 1.1rem; color: #8b949e; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid #30363d; padding-bottom: 0.4rem; }
.subtitle { text-align: center; font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.stats-row {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.stat-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    text-align: center;
    min-width: 120px;
}
.stat-value { font-size: 2rem; font-weight: bold; color: #58a6ff; }
.stat-label { font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; }
.top-repo-banner {
    background: #1f3a1f;
    border: 1px solid #3fb950;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.top-repo-banner .trophy { font-size: 2rem; }
.top-repo-banner .top-name { font-size: 1.4rem; font-weight: bold; color: #3fb950; margin: 0.25rem 0; }
.top-repo-banner .top-score { font-size: 0.9rem; color: #8b949e; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 1.5rem; }
th { text-align: left; color: #8b949e; padding: 0.5rem 0.75rem; border-bottom: 2px solid #30363d; }
td { padding: 0.4rem 0.75rem; border-bottom: 1px solid #21262d; }
tr:hover td { background: #161b22; }
.rank-1 td { color: #3fb950; font-weight: bold; }
.rank-cell { color: #8b949e; font-size: 0.8rem; }
.grade-A { color: #3fb950; font-weight: bold; }
.grade-B { color: #58a6ff; }
.grade-C { color: #d29922; }
.grade-D { color: #f0883e; }
.grade-F { color: #f85149; }
.score-green { color: #3fb950; }
.score-yellow { color: #d29922; }
.score-red { color: #f85149; }
.score-na { color: #8b949e; }
.footer { font-size: 0.75rem; color: #8b949e; text-align: center; margin-top: 1.5rem; }
.footer a { color: #58a6ff; text-decoration: none; }
"""


def _grade(score: Optional[float]) -> str:
    if score is None:
        return "-"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _score_class(score: Optional[float]) -> str:
    if score is None:
        return "score-na"
    if score >= 80:
        return "score-green"
    if score >= 60:
        return "score-yellow"
    return "score-red"


class OrgReport:
    """Generate a dark-theme HTML report for an org analysis."""

    def __init__(self, owner: str, results: list[dict]) -> None:
        self.owner = owner
        self.results = results

    def render(self) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ok_results = [r for r in self.results if r.get("score") is not None]
        avg_score = sum(r["score"] for r in ok_results) / len(ok_results) if ok_results else 0.0
        top_repo = ok_results[0] if ok_results else None

        # Most common finding
        finding_counts: dict[str, int] = {}
        for r in self.results:
            f = r.get("top_finding", "")
            if f:
                finding_counts[f] = finding_counts.get(f, 0) + 1
        most_common_finding = max(finding_counts, key=finding_counts.get) if finding_counts else ""  # type: ignore[arg-type]

        stats_html = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-value">{len(self.results)}</div><div class="stat-label">Repos</div></div>
  <div class="stat-card"><div class="stat-value">{len(ok_results)}</div><div class="stat-label">Analyzed</div></div>
  <div class="stat-card"><div class="stat-value">{avg_score:.1f}</div><div class="stat-label">Avg Score</div></div>
</div>"""

        top_banner = ""
        if top_repo:
            top_name = top_repo.get("full_name", top_repo.get("repo", ""))
            top_score = top_repo.get("score", 0)
            top_grade = _grade(top_score)
            top_banner = f"""
<div class="top-repo-banner">
  <div class="trophy">🏆</div>
  <div class="top-name">{top_name}</div>
  <div class="top-score">Score: {top_score:.1f} | Grade: {top_grade}</div>
</div>"""

        # Table rows
        rows = ""
        for r in self.results:
            rank = r.get("rank", "")
            full_name = r.get("full_name", r.get("repo", ""))
            score = r.get("score")
            grade_str = _grade(score)
            grade_class = f"grade-{grade_str}" if grade_str != "-" else "score-na"
            score_class = _score_class(score)
            score_str = f"{score:.1f}" if score is not None else "-"
            top_finding = r.get("top_finding", "") or ""
            rank_class = "rank-1" if rank == 1 else ""
            rows += f"""<tr class="{rank_class}">
  <td class="rank-cell">{rank}</td>
  <td>{full_name}</td>
  <td class="{score_class}">{score_str}</td>
  <td class="{grade_class}">{grade_str}</td>
  <td>{top_finding[:80]}</td>
</tr>\n"""

        common_finding_html = f"<p style='color:#8b949e;font-size:0.85rem;'>Most common finding: <em>{most_common_finding[:100]}</em></p>" if most_common_finding else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentkit org — {self.owner}</title>
<style>{_ORG_CSS}</style>
</head>
<body>
<div class="container">
  <h1>agentkit org — {self.owner}</h1>
  <p class="subtitle">Analysis date: {now}</p>
  {stats_html}
  {top_banner}
  <h2>Ranked Repos</h2>
  <table>
    <tr><th>#</th><th>Repo</th><th>Score</th><th>Grade</th><th>Top Finding</th></tr>
    {rows}
  </table>
  {common_finding_html}
  <div class="footer">
    Generated by <a href="https://github.com/agentkit-cli/agentkit-cli">agentkit-cli</a> v{__version__}
  </div>
</div>
</body>
</html>"""


def publish_org_report(owner: str, results: list[dict]) -> Optional[str]:
    """Generate and upload org report to here.now. Returns URL or None."""
    from agentkit_cli.share import upload_scorecard
    report = OrgReport(owner=owner, results=results)
    html = report.render()
    return upload_scorecard(html)
