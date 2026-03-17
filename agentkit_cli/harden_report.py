"""HTML report generator for `agentkit harden` results."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agentkit_cli import __version__
from agentkit_cli.redteam_scorer import RedTeamReport
from agentkit_cli.redteam_fixer import FixResult


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
.score-row { display: flex; gap: 2rem; align-items: center; margin-bottom: 1.5rem; }
.score-big { font-size: 2rem; font-weight: bold; }
.score-green { color: #3fb950; }
.score-yellow { color: #d29922; }
.score-red { color: #f85149; }
.arrow { font-size: 1.5rem; color: #8b949e; }
table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
th { text-align: left; padding: 0.5rem; background: #21262d; color: #8b949e; font-size: 0.85rem; }
td { padding: 0.5rem; border-bottom: 1px solid #21262d; font-size: 0.9rem; }
.fix-applied { color: #3fb950; }
.fix-skipped { color: #8b949e; }
.delta-pos { color: #3fb950; }
.delta-zero { color: #8b949e; }
"""


def _score_class(score: float) -> str:
    if score >= 80:
        return "score-green"
    if score >= 50:
        return "score-yellow"
    return "score-red"


def generate_harden_html(
    original_report: RedTeamReport,
    fixed_report: RedTeamReport,
    fix_result: FixResult,
    context_path: str = "",
) -> str:
    """Generate a self-contained dark-theme HTML hardening report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    orig_score = original_report.score_overall
    fixed_score = fixed_report.score_overall
    delta = fixed_score - orig_score
    delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"

    orig_class = _score_class(orig_score)
    fixed_class = _score_class(fixed_score)

    rules_applied = fix_result.rules_applied
    rules_skipped = [
        f.category for f in fix_result.applied_fixes if f.was_already_present
    ]

    # Category breakdown rows
    cat_rows = []
    for cat in original_report.score_by_category:
        b = original_report.score_by_category[cat]
        a = fixed_report.score_by_category.get(cat, b)
        d = a - b
        label = cat.replace("_", " ").title()
        applied = cat in rules_applied
        d_str = f"+{d:.0f}" if d > 0 else f"{d:.0f}"
        d_class = "delta-pos" if d > 0 else "delta-zero"
        status = '<span class="fix-applied">✓ Fixed</span>' if applied else '<span class="fix-skipped">—</span>'
        cat_rows.append(
            f"<tr><td>{label}</td><td>{b:.0f}</td><td>{a:.0f}</td>"
            f'<td class="{d_class}">{d_str}</td><td>{status}</td></tr>'
        )
    cat_rows_html = "\n".join(cat_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>agentkit harden — {context_path}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="card">
  <h1>🛡️ agentkit harden</h1>
  <div class="subtitle">Context: {context_path} &nbsp;·&nbsp; {now} &nbsp;·&nbsp; agentkit v{__version__}</div>

  <div class="score-row">
    <div>
      <div style="font-size:0.8rem;color:#8b949e">Before</div>
      <div class="score-big {orig_class}">{orig_score:.0f}</div>
    </div>
    <div class="arrow">→</div>
    <div>
      <div style="font-size:0.8rem;color:#8b949e">After</div>
      <div class="score-big {fixed_class}">{fixed_score:.0f}</div>
    </div>
    <div>
      <div style="font-size:0.8rem;color:#8b949e">Delta</div>
      <div class="score-big delta-pos">{delta_str}</div>
    </div>
    <div>
      <div style="font-size:0.8rem;color:#8b949e">Rules Applied</div>
      <div class="score-big" style="color:#58a6ff">{len(rules_applied)}</div>
    </div>
  </div>

  <h2>Category Breakdown</h2>
  <table>
    <thead><tr><th>Category</th><th>Before</th><th>After</th><th>Delta</th><th>Status</th></tr></thead>
    <tbody>
      {cat_rows_html}
    </tbody>
  </table>

  <h2>Applied Remediations ({len(rules_applied)})</h2>
  <ul>
    {"".join(f'<li class="fix-applied">✓ {r.replace("_", " ").title()}</li>' for r in rules_applied) or "<li>None needed</li>"}
  </ul>

  <h2>Already Hardened ({len(rules_skipped)})</h2>
  <ul>
    {"".join(f'<li class="fix-skipped">— {r.replace("_", " ").title()}</li>' for r in rules_skipped) or "<li>None</li>"}
  </ul>
</div>
</body>
</html>"""
    return html


def save_harden_html(
    original_report: RedTeamReport,
    fixed_report: RedTeamReport,
    fix_result: FixResult,
    output_path: Optional[Path] = None,
    context_path: str = "",
) -> Path:
    html = generate_harden_html(original_report, fixed_report, fix_result, context_path=context_path)
    if output_path is None:
        fd, tmp = tempfile.mkstemp(prefix="agentkit-harden-", suffix=".html")
        os.close(fd)
        output_path = Path(tmp)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
