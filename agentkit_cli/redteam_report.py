"""Generate a dark-theme self-contained HTML report for agentkit redteam results."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.redteam_scorer import RedTeamReport

_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Courier New', Courier, monospace;
    min-height: 100vh;
    padding: 2rem;
}
.card {
    max-width: 960px;
    margin: 0 auto;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 2rem;
}
h1 { font-size: 1.6rem; color: #58a6ff; margin-bottom: 0.25rem; }
h2 { font-size: 1.1rem; color: #8b949e; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid #21262d; padding-bottom: 0.4rem; }
.subtitle { font-size: 0.85rem; color: #8b949e; margin-bottom: 1.5rem; }
.header-row { display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.5rem; }
.grade-badge {
    font-size: 2.5rem;
    font-weight: bold;
    width: 70px; height: 70px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.grade-A { background: #1a4731; color: #3fb950; border: 2px solid #3fb950; }
.grade-B { background: #1f3a1a; color: #56d364; border: 2px solid #56d364; }
.grade-C { background: #3a2e0a; color: #d29922; border: 2px solid #d29922; }
.grade-D { background: #3a1c0a; color: #db6d28; border: 2px solid #db6d28; }
.grade-F { background: #3a0c0c; color: #f85149; border: 2px solid #f85149; }
.score-big { font-size: 1.8rem; font-weight: bold; }
.score-green { color: #3fb950; }
.score-yellow { color: #d29922; }
.score-red { color: #f85149; }
.summary-stats {
    display: flex; gap: 1.5rem; flex-wrap: wrap;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: #0d1117;
    border-radius: 6px;
    border: 1px solid #21262d;
}
.stat { text-align: center; flex: 1; min-width: 100px; }
.stat-value { font-size: 1.5rem; font-weight: bold; color: #58a6ff; }
.stat-label { font-size: 0.75rem; color: #8b949e; margin-top: 0.2rem; }
.category-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.cat-card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 1rem;
}
.cat-name { font-size: 0.9rem; font-weight: bold; margin-bottom: 0.5rem; text-transform: capitalize; }
.progress-bar { background: #21262d; border-radius: 4px; height: 10px; overflow: hidden; margin-bottom: 0.35rem; }
.progress-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.fill-green { background: #3fb950; }
.fill-yellow { background: #d29922; }
.fill-red { background: #f85149; }
.cat-score { font-size: 0.8rem; color: #8b949e; }
.findings-list { list-style: none; margin: 0; padding: 0; }
.finding-item {
    padding: 0.6rem 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 4px;
    border-left: 3px solid #30363d;
    background: #0d1117;
    font-size: 0.82rem;
}
.finding-high { border-left-color: #f85149; }
.finding-medium { border-left-color: #d29922; }
.finding-critical { border-left-color: #f85149; background: #2a0c0c; }
.finding-rule { font-weight: bold; color: #58a6ff; margin-right: 0.5rem; }
.finding-cat { font-size: 0.75rem; color: #8b949e; margin-top: 0.2rem; }
.attack-section details { margin-bottom: 0.75rem; }
.attack-section summary {
    cursor: pointer;
    padding: 0.6rem 0.75rem;
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 4px;
    font-size: 0.85rem;
    color: #58a6ff;
    user-select: none;
}
.attack-section summary:hover { background: #161b22; }
.attack-body {
    padding: 0.75rem;
    border: 1px solid #21262d;
    border-top: none;
    border-radius: 0 0 4px 4px;
    font-size: 0.82rem;
    background: #0a0e13;
}
.attack-input {
    font-family: 'Courier New', monospace;
    background: #161b22;
    padding: 0.5rem;
    border-radius: 4px;
    margin: 0.5rem 0;
    white-space: pre-wrap;
    word-break: break-word;
    border: 1px solid #30363d;
    color: #f0883e;
}
.rec-list { list-style: none; padding: 0; counter-reset: rec-counter; }
.rec-item {
    counter-increment: rec-counter;
    padding: 0.65rem 0.75rem 0.65rem 2.5rem;
    margin-bottom: 0.5rem;
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 4px;
    font-size: 0.82rem;
    position: relative;
}
.rec-item::before {
    content: counter(rec-counter);
    position: absolute;
    left: 0.6rem;
    top: 0.65rem;
    background: #21262d;
    color: #8b949e;
    width: 1.4rem;
    height: 1.4rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
}
.rec-code {
    font-weight: bold;
    color: #58a6ff;
    margin-right: 0.4rem;
}
footer { margin-top: 2rem; text-align: center; color: #484f58; font-size: 0.75rem; }
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit redteam report — {project}</title>
<style>
{css}
</style>
</head>
<body>
<div class="card">
  <div class="header-row">
    <div class="grade-badge grade-{grade}">{grade}</div>
    <div>
      <h1>agentkit redteam</h1>
      <div class="subtitle">{path}</div>
      <div class="score-big {score_color_class}">{score}/100</div>
    </div>
  </div>

  <div class="summary-stats">
    <div class="stat">
      <div class="stat-value">{score}</div>
      <div class="stat-label">Overall Score</div>
    </div>
    <div class="stat">
      <div class="stat-value">{grade}</div>
      <div class="stat-label">Grade</div>
    </div>
    <div class="stat">
      <div class="stat-value">{finding_count}</div>
      <div class="stat-label">Findings</div>
    </div>
    <div class="stat">
      <div class="stat-value">{rec_count}</div>
      <div class="stat-label">Recommendations</div>
    </div>
  </div>

  <h2>Score by Category</h2>
  <div class="category-grid">
{category_cards}
  </div>

  <h2>Findings ({finding_count})</h2>
  <ul class="findings-list">
{finding_items}
  </ul>

  <h2>Attack Samples</h2>
  <div class="attack-section">
{attack_items}
  </div>

  <h2>Recommendations</h2>
  <ol class="rec-list">
{rec_items}
  </ol>

  <footer>Generated by agentkit-cli v{version} &bull; {timestamp}</footer>
</div>
</body>
</html>
"""


def _score_color_class(score: float) -> str:
    if score >= 80:
        return "score-green"
    if score >= 50:
        return "score-yellow"
    return "score-red"


def _fill_class(score: float) -> str:
    if score >= 80:
        return "fill-green"
    if score >= 50:
        return "fill-yellow"
    return "fill-red"


def _category_card(cat: str, score: float) -> str:
    label = cat.replace("_", " ").title()
    fill = _fill_class(score)
    return f"""\
    <div class="cat-card">
      <div class="cat-name">{label}</div>
      <div class="progress-bar">
        <div class="progress-fill {fill}" style="width:{score:.0f}%"></div>
      </div>
      <div class="cat-score">{score:.0f}/100</div>
    </div>"""


def _finding_item(f: dict) -> str:
    sev = f.get("severity", "medium")
    cls = f"finding-{sev}"
    cat = f.get("category", "").replace("_", " ").title()
    return (
        f'    <li class="finding-item {cls}">'
        f'<span class="finding-rule">{f.get("rule_id", "")}</span>'
        f'{f.get("description", "")}'
        f'<div class="finding-cat">{cat} — penalty: {f.get("penalty", 0):.0f}pts</div>'
        f'</li>'
    )


def _attack_item(a) -> str:
    cat = a.category.value.replace("_", " ").title()
    input_escaped = a.input_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""\
    <details>
      <summary>[{cat}] {a.description[:90]}</summary>
      <div class="attack-body">
        <strong>Input:</strong>
        <div class="attack-input">{input_escaped}</div>
        <strong>Expected behavior:</strong> {a.expected_behavior}
      </div>
    </details>"""


def _rec_item(rec: str) -> str:
    # Extract rule code if present
    code_match = __import__("re").match(r"^\[([A-Z0-9\-]+)\]", rec)
    if code_match:
        code = code_match.group(1)
        rest = rec[len(code_match.group(0)):].strip()
        return f'    <li class="rec-item"><span class="rec-code">[{code}]</span>{rest}</li>'
    return f'    <li class="rec-item">{rec}</li>'


def render_html(report: RedTeamReport) -> str:
    """Render a self-contained dark-theme HTML report."""
    project = Path(report.path).name or "unknown"
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    category_cards = "\n".join(
        _category_card(cat, score) for cat, score in report.score_by_category.items()
    )
    finding_items = "\n".join(_finding_item(f) for f in report.findings)
    if not finding_items:
        finding_items = '    <li class="finding-item">No findings — excellent security posture.</li>'

    attack_items = "\n".join(_attack_item(a) for a in report.attack_samples)
    if not attack_items:
        attack_items = "    <p style='color:#8b949e;font-size:0.85rem;'>No attack samples generated.</p>"

    rec_items = "\n".join(_rec_item(r) for r in report.recommendations)
    if not rec_items:
        rec_items = '    <li class="rec-item">No recommendations — context file is well-hardened.</li>'

    return _HTML_TEMPLATE.format(
        css=_CSS,
        project=project,
        path=report.path,
        grade=report.grade,
        score=f"{report.score_overall:.0f}",
        score_color_class=_score_color_class(report.score_overall),
        finding_count=len(report.findings),
        rec_count=len(report.recommendations),
        category_cards=category_cards,
        finding_items=finding_items,
        attack_items=attack_items,
        rec_items=rec_items,
        version=__version__,
        timestamp=timestamp,
    )


def save_html(report: RedTeamReport, output_path: Optional[Path] = None) -> Path:
    """Render and save HTML report. Returns the path written to."""
    html = render_html(report)
    if output_path is None:
        output_path = Path.cwd() / "agentkit-redteam-report.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


def publish_report(report: RedTeamReport, api_key: Optional[str] = None) -> str:
    """Publish the HTML report to here.now and return the public URL."""
    from agentkit_cli.publish import publish_html, PublishError

    html = render_html(report)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        tmp_path = Path(f.name)

    try:
        result = publish_html(tmp_path, api_key=api_key)
        return result["url"]
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass
