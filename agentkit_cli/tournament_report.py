"""Dark-theme HTML report for `agentkit tournament`."""
from __future__ import annotations

import os
import sys
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.tournament import TournamentResult, StandingEntry
from agentkit_cli.publish import (
    PublishError,
    _json_post,
    _put_file,
    _finalize,
    HERENOW_API_BASE,
)

_TOURNAMENT_CSS = """
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
.winner-banner {
    background: #1f3a1f;
    border: 1px solid #3fb950;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.winner-banner .trophy { font-size: 2rem; }
.winner-banner .winner-name { font-size: 1.4rem; font-weight: bold; color: #3fb950; margin: 0.25rem 0; }
.winner-banner .winner-score { font-size: 0.9rem; color: #8b949e; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 1.5rem; }
th { text-align: left; color: #8b949e; padding: 0.5rem 0.75rem; border-bottom: 2px solid #30363d; }
td { padding: 0.4rem 0.75rem; border-bottom: 1px solid #21262d; }
tr:hover td { background: #161b22; }
.rank-1 td { color: #3fb950; font-weight: bold; }
.rank-cell { color: #8b949e; font-size: 0.8rem; }
.wl { font-family: monospace; }
.grade-A { color: #3fb950; font-weight: bold; }
.grade-B { color: #58a6ff; }
.grade-C { color: #d29922; }
.grade-D { color: #f0883e; }
.grade-F { color: #f85149; }
.matrix-table { font-size: 0.75rem; }
.matrix-table th, .matrix-table td { padding: 0.3rem 0.5rem; text-align: center; border: 1px solid #30363d; }
.matrix-table th { background: #161b22; }
.cell-win { background: #1f3a1f; color: #3fb950; font-weight: bold; }
.cell-loss { background: #2d0e0e; color: #f85149; }
.cell-tie { background: #1a1a2e; color: #d29922; }
.cell-self { background: #30363d; color: #8b949e; }
.cell-error { color: #8b949e; }
.footer { font-size: 0.75rem; color: #8b949e; text-align: center; margin-top: 1.5rem; }
.footer a { color: #58a6ff; text-decoration: none; }
"""


def _grade(avg_score: float) -> str:
    if avg_score >= 90:
        return "A"
    if avg_score >= 80:
        return "B"
    if avg_score >= 70:
        return "C"
    if avg_score >= 60:
        return "D"
    return "F"


def _short_name(repo: str) -> str:
    return repo.split("/")[-1]


def _standings_table_html(standings: list[StandingEntry]) -> str:
    rows = ""
    for s in standings:
        g = _grade(s.avg_score)
        grade_class = f"grade-{g}"
        rank_class = "rank-1" if s.rank == 1 else ""
        trophy = "🏆 " if s.rank == 1 else ""
        rows += f"""<tr class="{rank_class}">
  <td class="rank-cell">{s.rank}</td>
  <td>{trophy}{_short_name(s.repo)}</td>
  <td class="wl">{s.wins}-{s.losses}</td>
  <td>{s.avg_score:.1f}</td>
  <td class="{grade_class}">{g}</td>
</tr>\n"""
    return f"""<table>
<tr><th>#</th><th>Repo</th><th>W-L</th><th>Avg Score</th><th>Grade</th></tr>
{rows}
</table>"""


def _matrix_table_html(result: TournamentResult) -> str:
    repos = result.repos
    # Build lookup: (left, right) -> duel
    duel_map: dict[tuple[str, str], object] = {}
    for round_duels in result.rounds:
        for d in round_duels:
            duel_map[(d.left_target, d.right_target)] = d  # type: ignore[assignment]
            duel_map[(d.right_target, d.left_target)] = d  # type: ignore[assignment]

    # Header row
    header_cells = "<th></th>" + "".join(
        f"<th>{_short_name(r)}</th>" for r in repos
    )

    rows = ""
    for row_repo in repos:
        cells = f"<td><strong>{_short_name(row_repo)}</strong></td>"
        for col_repo in repos:
            if row_repo == col_repo:
                cells += '<td class="cell-self">—</td>'
                continue
            d = duel_map.get((row_repo, col_repo))
            if d is None:
                cells += '<td class="cell-error">?</td>'
                continue
            # Determine result from row_repo's perspective
            if d.left_target == row_repo:  # type: ignore[union-attr]
                outcome = d.winner  # type: ignore[union-attr]
                score = d.left_score  # type: ignore[union-attr]
            else:
                if d.winner == "left":  # type: ignore[union-attr]
                    outcome = "right"
                elif d.winner == "right":  # type: ignore[union-attr]
                    outcome = "left"
                else:
                    outcome = d.winner  # type: ignore[union-attr]
                score = d.right_score  # type: ignore[union-attr]

            score_str = f"{int(round(score))}" if score is not None else "?"
            if outcome == "left":  # row_repo won
                cells += f'<td class="cell-win">W {score_str}</td>'
            elif outcome == "right":  # row_repo lost
                cells += f'<td class="cell-loss">L {score_str}</td>'
            elif outcome == "tie":
                cells += f'<td class="cell-tie">T {score_str}</td>'
            else:
                cells += '<td class="cell-error">err</td>'
        rows += f"<tr>{cells}</tr>\n"

    return f"""<table class="matrix-table">
<tr>{header_cells}</tr>
{rows}
</table>"""


def generate_tournament_html(result: TournamentResult) -> str:
    """Generate a standalone dark-theme HTML tournament report."""
    n_repos = len(result.repos)
    n_duels = result.total_duels
    winner_short = _short_name(result.winner)

    # Winner's avg score
    winner_entry = next(
        (s for s in result.standings if s.repo == result.winner), None
    )
    winner_score_str = (
        f"{winner_entry.avg_score:.1f}/100 avg · {winner_entry.wins}W-{winner_entry.losses}L"
        if winner_entry
        else ""
    )

    standings_html = _standings_table_html(result.standings)
    matrix_html = _matrix_table_html(result)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agent-Readiness Tournament — {n_repos} repos</title>
<style>{_TOURNAMENT_CSS}</style>
</head>
<body>
<div class="container">
  <h1>Agent-Readiness Tournament</h1>
  <div class="subtitle">{n_repos} repos &bull; {n_duels} duels &bull; {result.timestamp}</div>

  <div class="winner-banner">
    <div class="trophy">🏆</div>
    <div class="winner-name">Winner: {winner_short}</div>
    <div class="winner-score">{winner_score_str}</div>
  </div>

  <h2>Standings</h2>
  {standings_html}

  <h2>Match Results</h2>
  {matrix_html}

  <div class="footer">
    Analyzed by
    <a href="https://pypi.org/project/agentkit-cli/">agentkit-cli v{__version__}</a>
    &bull; {result.timestamp}
  </div>
</div>
</body>
</html>"""
    return html


def publish_tournament(result: TournamentResult) -> Optional[str]:
    """Generate tournament HTML and upload to here.now. Returns URL or None on failure."""
    html = generate_tournament_html(result)
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
        print(f"Warning: tournament publish failed: {exc}", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"Warning: tournament publish failed unexpectedly: {exc}", file=sys.stderr)
        return None
