"""agentkit repo-duel HTML renderer — dark-theme duel report."""
from __future__ import annotations

from agentkit_cli import __version__
from agentkit_cli.repo_duel import RepoDuelResult


_GRADE_COLORS = {
    "A": "#3fb950",
    "B": "#4493f8",
    "C": "#e3b341",
    "D": "#f85149",
    "F": "#f85149",
}

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0d1117;
  color: #c9d1d9;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100vh;
  padding: 2rem;
}
.container {
  max-width: 860px;
  margin: 0 auto;
}
h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #e6edf3;
  text-align: center;
  margin-bottom: 0.3rem;
}
.subtitle {
  text-align: center;
  color: #8b949e;
  font-size: 0.9rem;
  margin-bottom: 2rem;
}
.score-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}
.score-card {
  flex: 1;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 1.2rem 1.5rem;
  text-align: center;
}
.score-card .repo-name {
  font-size: 1rem;
  font-weight: 600;
  color: #4493f8;
  text-decoration: none;
  word-break: break-all;
}
.score-card .repo-name:hover { text-decoration: underline; }
.score-card .grade-badge {
  font-size: 2.5rem;
  font-weight: 800;
  margin: 0.5rem 0;
}
.score-card .score-num {
  font-size: 1.1rem;
  color: #8b949e;
}
.vs-sep {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  font-weight: 700;
  color: #8b949e;
  min-width: 48px;
}
table.dim-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 2rem;
  font-size: 0.9rem;
}
table.dim-table th {
  background: #161b22;
  color: #8b949e;
  font-weight: 600;
  padding: 0.7rem 1rem;
  text-align: left;
  border-bottom: 1px solid #30363d;
}
table.dim-table th:nth-child(2),
table.dim-table th:nth-child(3),
table.dim-table th:nth-child(4) { text-align: right; }
table.dim-table td {
  padding: 0.65rem 1rem;
  border-bottom: 1px solid #21262d;
}
table.dim-table td:nth-child(2),
table.dim-table td:nth-child(3),
table.dim-table td:nth-child(4) { text-align: right; }
table.dim-table tr:nth-child(even) td { background: #0d1117; }
table.dim-table tr:nth-child(odd) td { background: #161b22; }
.winner-cell { color: #3fb950; font-weight: 600; }
.loser-cell { color: #8b949e; }
.draw-cell { color: #e3b341; }
.winner-banner {
  background: #1f2d1f;
  border: 1px solid #3fb950;
  border-radius: 10px;
  padding: 1.2rem 1.5rem;
  text-align: center;
  font-size: 1.3rem;
  font-weight: 700;
  color: #3fb950;
  margin-bottom: 2rem;
}
.draw-banner {
  background: #1f1c10;
  border: 1px solid #e3b341;
  border-radius: 10px;
  padding: 1.2rem 1.5rem;
  text-align: center;
  font-size: 1.3rem;
  font-weight: 700;
  color: #e3b341;
  margin-bottom: 2rem;
}
footer {
  text-align: center;
  font-size: 0.78rem;
  color: #8b949e;
  margin-top: 2rem;
}
footer a { color: #4493f8; text-decoration: none; }
footer a:hover { text-decoration: underline; }
"""


def render_repo_duel_html(result: RepoDuelResult) -> str:
    """Render a standalone dark-theme HTML duel report."""
    gc1 = _GRADE_COLORS.get(result.repo1_grade, "#8b949e")
    gc2 = _GRADE_COLORS.get(result.repo2_grade, "#8b949e")

    def _repo_link(repo: str) -> str:
        slug = repo.replace("github:", "")
        if slug.startswith("http"):
            url = slug
            name = slug.rstrip("/").split("/")[-1].replace(".git", "")
        else:
            url = f"https://github.com/{slug}"
            name = slug
        return f'<a class="repo-name" href="{url}" target="_blank">{name}</a>'

    # Dimension table rows
    dim_rows = []
    for dim in result.dimension_results:
        name_label = dim.name.replace("_", " ").title()
        delta_str = f"{abs(dim.delta):.1f}"
        if dim.winner == "repo1":
            v1 = f'<span class="winner-cell">{dim.repo1_value:.1f}</span>'
            v2 = f'<span class="loser-cell">{dim.repo2_value:.1f}</span>'
            w = f'<span class="winner-cell">▲ +{delta_str}</span>'
        elif dim.winner == "repo2":
            v1 = f'<span class="loser-cell">{dim.repo1_value:.1f}</span>'
            v2 = f'<span class="winner-cell">{dim.repo2_value:.1f}</span>'
            w = f'<span class="winner-cell">▲ +{delta_str}</span>'
        else:
            v1 = f'<span class="draw-cell">{dim.repo1_value:.1f}</span>'
            v2 = f'<span class="draw-cell">{dim.repo2_value:.1f}</span>'
            w = '<span class="draw-cell">— draw</span>'
        dim_rows.append(f"<tr><td>{name_label}</td><td>{v1}</td><td>{w}</td><td>{v2}</td></tr>")

    dim_rows_html = "\n".join(dim_rows)

    # Winner banner
    if result.winner == "draw":
        banner = '<div class="draw-banner">🤝 Draw — evenly matched</div>'
    elif result.winner == "repo1":
        slug1 = result.repo1.replace("github:", "").rstrip("/").split("/")[-1].replace(".git", "")
        banner = f'<div class="winner-banner">🏆 {slug1} wins!</div>'
    else:
        slug2 = result.repo2.replace("github:", "").rstrip("/").split("/")[-1].replace(".git", "")
        banner = f'<div class="winner-banner">🏆 {slug2} wins!</div>'

    share_url_html = ""
    if result.share_url:
        share_url_html = f'<p>Share: <a href="{result.share_url}">{result.share_url}</a></p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Repo Duel — {result.repo1} vs {result.repo2}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
  <h1>⚔️ Repo Duel</h1>
  <p class="subtitle">Agent-readiness comparison · {result.run_date}</p>

  <div class="score-row">
    <div class="score-card">
      {_repo_link(result.repo1)}
      <div class="grade-badge" style="color:{gc1}">{result.repo1_grade}</div>
      <div class="score-num">{result.repo1_score:.1f} / 100</div>
    </div>
    <div class="vs-sep">vs</div>
    <div class="score-card">
      {_repo_link(result.repo2)}
      <div class="grade-badge" style="color:{gc2}">{result.repo2_grade}</div>
      <div class="score-num">{result.repo2_score:.1f} / 100</div>
    </div>
  </div>

  <table class="dim-table">
    <thead>
      <tr>
        <th>Dimension</th>
        <th>{result.repo1.replace("github:", "")}</th>
        <th>Edge</th>
        <th>{result.repo2.replace("github:", "")}</th>
      </tr>
    </thead>
    <tbody>
      {dim_rows_html}
    </tbody>
  </table>

  {banner}
  {share_url_html}

  <footer>
    Analyzed by <a href="https://github.com/mikiships/agentkit-cli">agentkit-cli</a> v{__version__}
  </footer>
</div>
</body>
</html>"""
    return html
