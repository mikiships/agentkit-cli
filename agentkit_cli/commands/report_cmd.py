"""agentkit report command — run all toolkit checks and generate a quality report."""
from __future__ import annotations

import json
import subprocess
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli import __version__
from agentkit_cli.commands.badge_cmd import build_badge_url, build_markdown, score_to_color
from agentkit_cli.report_runner import (
    run_agentlint_check,
    run_agentmd_score,
    run_agentreflect_analyze,
    run_coderace_bench,
)
from agentkit_cli.tools import is_installed

console = Console()

TOOLS = ["agentlint", "agentmd", "coderace", "agentreflect"]

# ---------------------------------------------------------------------------
# Score helpers
# ---------------------------------------------------------------------------

def _score_color_css(score: Optional[float]) -> str:
    if score is None:
        return "#888888"
    if score >= 80:
        return "#4caf50"
    if score >= 50:
        return "#ffb300"
    return "#f44336"


def _score_label(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    return f"{int(round(score))}"


def _coverage_score(results: dict) -> float:
    """Percent of tools that ran successfully (not None)."""
    total = len(TOOLS)
    ran = sum(1 for k in TOOLS if results.get(k) is not None)
    return round(ran / total * 100)


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def run_all(path: str) -> dict:
    """Run all tool runners and return a results dict."""
    return {
        "agentlint": run_agentlint_check(path),
        "agentmd": run_agentmd_score(path),
        "coderace": run_coderace_bench(path),
        "agentreflect": run_agentreflect_analyze(path),
    }


def _tool_status(results: dict) -> list[dict]:
    statuses = []
    for tool in TOOLS:
        installed = is_installed(tool)
        result = results.get(tool)
        if not installed:
            status = "not_installed"
        elif result is None:
            status = "failed"
        else:
            status = "success"
        statuses.append({"tool": tool, "installed": installed, "status": status})
    return statuses


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit report — {project_name}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;line-height:1.6}}
.container{{max-width:1280px;margin:0 auto;padding:32px 24px}}
h1{{font-size:24px;font-weight:700;color:#f0f6fc;margin-bottom:4px}}
h2{{font-size:16px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;margin-top:0}}
h3{{font-size:15px;font-weight:600;color:#c9d1d9;margin-bottom:10px}}
.meta{{color:#8b949e;font-size:13px;margin-bottom:32px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-bottom:32px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px}}
.card.full{{grid-column:1/-1}}
.score-big{{font-size:48px;font-weight:700;line-height:1}}
.score-label{{font-size:13px;color:#8b949e;margin-top:4px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600}}
.badge-green{{background:#1a4731;color:#56d364}}
.badge-yellow{{background:#3d2900;color:#d29922}}
.badge-red{{background:#3d1a1a;color:#f85149}}
.badge-grey{{background:#21262d;color:#8b949e}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{color:#8b949e;font-weight:600;text-align:left;padding:8px 12px;border-bottom:1px solid #30363d}}
td{{padding:8px 12px;border-bottom:1px solid #21262d}}
tr:last-child td{{border-bottom:none}}
.status-ok{{color:#56d364}}
.status-warn{{color:#d29922}}
.status-err{{color:#f85149}}
.status-skip{{color:#8b949e}}
.section{{margin-bottom:32px}}
pre{{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:16px;overflow-x:auto;font-size:12px;color:#e6edf3}}
.footer{{color:#8b949e;font-size:12px;margin-top:48px;padding-top:16px;border-top:1px solid #21262d}}
</style>
</head>
<body>
<div class="container">
  <h1>agentkit report</h1>
  <div class="meta">Project: <strong>{project_name}</strong> &nbsp;·&nbsp; Generated: {date} &nbsp;·&nbsp; agentkit-cli v{version}</div>
  {badge_snippet}

  <!-- Summary row -->
  <div class="grid">
    <div class="card">
      <h2>Toolkit Coverage</h2>
      <div class="score-big" style="color:{coverage_color}">{coverage_score}%</div>
      <div class="score-label">{tools_run} of {tools_total} tools ran successfully</div>
    </div>
    {agentlint_summary_card}
    {agentmd_summary_card}
  </div>

  <!-- Pipeline status -->
  <div class="section">
    <div class="card">
      <h2>Pipeline Status</h2>
      <table>
        <thead><tr><th>Tool</th><th>Installed</th><th>Status</th></tr></thead>
        <tbody>{pipeline_rows}</tbody>
      </table>
    </div>
  </div>

  {agentlint_section}
  {agentmd_section}
  {coderace_section}
  {agentreflect_section}

  <div class="footer">Generated by agentkit-cli v{version} · agentkit report</div>
</div>
</body>
</html>
"""


def _badge(text: str, level: str = "grey") -> str:
    return f'<span class="badge badge-{level}">{text}</span>'


def _score_badge(score: Optional[float]) -> str:
    if score is None:
        return _badge("N/A")
    s = int(round(score))
    level = "green" if s >= 80 else ("yellow" if s >= 50 else "red")
    return _badge(str(s), level)


def _status_badge(status: str) -> str:
    mapping = {
        "success": ("success", "green"),
        "failed": ("failed", "red"),
        "not_installed": ("not installed", "grey"),
    }
    text, level = mapping.get(status, (status, "grey"))
    return _badge(text, level)


def _pipeline_rows(statuses: list[dict]) -> str:
    rows = []
    for s in statuses:
        installed_str = "✓" if s["installed"] else "✗"
        installed_class = "status-ok" if s["installed"] else "status-err"
        status_html = _status_badge(s["status"])
        rows.append(
            f'<tr><td>{s["tool"]}</td>'
            f'<td class="{installed_class}">{installed_str}</td>'
            f'<td>{status_html}</td></tr>'
        )
    return "\n".join(rows)


def _agentlint_summary_card(data: Optional[dict]) -> str:
    if data is None:
        return '<div class="card"><h2>Context Quality</h2><div style="color:#8b949e">agentlint not available</div></div>'
    score = data.get("score") or data.get("freshness_score") or data.get("total_score")
    color = _score_color_css(score)
    score_html = f'<div class="score-big" style="color:{color}">{_score_label(score)}</div>' if score is not None else '<div style="color:#8b949e">—</div>'
    return f'<div class="card"><h2>Context Quality</h2>{score_html}<div class="score-label">agentlint score</div></div>'


def _agentmd_summary_card(data) -> str:
    # Fix D4: agentmd can return a list of per-file scored dicts instead of a single dict
    if data is None:
        return '<div class="card"><h2>Context Docs</h2><div style="color:#8b949e">agentmd not available</div></div>'
    if isinstance(data, list):
        if not data:
            return '<div class="card"><h2>Context Docs</h2><div style="color:#8b949e">—</div><div class="score-label">0 files analyzed</div></div>'
        scores = [d.get("score") or d.get("total_score") or 0 for d in data if isinstance(d, dict)]
        score = round(sum(scores) / len(scores), 1) if scores else None
        subtitle = f"{len(data)} files analyzed"
    else:
        score = data.get("score") or data.get("total_score")
        subtitle = "agentmd score"
    color = _score_color_css(score)
    score_html = f'<div class="score-big" style="color:{color}">{_score_label(score)}</div>' if score is not None else '<div style="color:#8b949e">—</div>'
    return f'<div class="card"><h2>Context Docs</h2>{score_html}<div class="score-label">{subtitle}</div></div>'


def _agentlint_section(data: Optional[dict]) -> str:
    if data is None:
        return ""
    issues = data.get("issues") or data.get("errors") or []
    rows = ""
    for issue in issues[:20]:
        if isinstance(issue, dict):
            msg = issue.get("message") or issue.get("msg") or str(issue)
            sev = issue.get("severity") or issue.get("level") or "info"
            sev_class = "status-err" if "error" in sev.lower() else ("status-warn" if "warn" in sev.lower() else "")
            rows += f'<tr><td class="{sev_class}">{sev}</td><td>{msg}</td></tr>'
        else:
            rows += f'<tr><td></td><td>{issue}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="2" style="color:#56d364">No issues found</td></tr>'
    return f'''
<div class="section">
  <div class="card">
    <h2>Context Quality (agentlint)</h2>
    <table><thead><tr><th>Severity</th><th>Issue</th></tr></thead><tbody>{rows}</tbody></table>
  </div>
</div>'''


def _agentmd_section(data) -> str:
    if data is None:
        return ""
    # Handle list of per-file scored dicts (D4 fix)
    if isinstance(data, list):
        files = data
    else:
        files = data.get("files") or data.get("generated") or []
    rows = ""
    for f in files[:20]:
        if isinstance(f, dict):
            name = f.get("name") or f.get("file") or "?"
            size = f.get("size") or f.get("bytes") or "?"
            tier = f.get("tier") or f.get("type") or "?"
            rows += f'<tr><td>{name}</td><td>{size}</td><td>{tier}</td></tr>'
        else:
            rows += f'<tr><td colspan="3">{f}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="3" style="color:#8b949e">No file details available</td></tr>'
    return f'''
<div class="section">
  <div class="card">
    <h2>Context Generation (agentmd)</h2>
    <table><thead><tr><th>File</th><th>Size</th><th>Tier</th></tr></thead><tbody>{rows}</tbody></table>
  </div>
</div>'''


def _coderace_section(data: Optional[dict]) -> str:
    if data is None:
        return ""
    results = data.get("results") or data.get("agents") or []
    rows = ""
    best_score: Optional[float] = None
    for r in results:
        if isinstance(r, dict):
            sc = r.get("score")
            if sc is not None and (best_score is None or sc > best_score):
                best_score = sc
    for r in results[:20]:
        if isinstance(r, dict):
            agent = r.get("agent") or r.get("name") or "?"
            sc = r.get("score")
            is_best = sc is not None and sc == best_score
            agent_html = f'<strong style="color:#56d364">{agent} ★</strong>' if is_best else agent
            rows += f'<tr><td>{agent_html}</td><td>{_score_badge(sc)}</td></tr>'
        else:
            rows += f'<tr><td colspan="2">{r}</td></tr>'
    if not rows:
        rows = '<tr><td colspan="2" style="color:#8b949e">No benchmark data available</td></tr>'
    return f'''
<div class="section">
  <div class="card">
    <h2>Agent Benchmark (coderace)</h2>
    <table><thead><tr><th>Agent</th><th>Score</th></tr></thead><tbody>{rows}</tbody></table>
  </div>
</div>'''


def _agentreflect_section(data: Optional[dict]) -> str:
    if data is None:
        return ""
    # Fix D3: new format uses suggestions_md (markdown text); legacy keys kept as fallback
    summary = (
        data.get("suggestions_md")
        or data.get("summary")
        or data.get("reflection")
        or data.get("output")
        or ""
    )
    if not summary and isinstance(data, dict):
        summary = json.dumps(data, indent=2)
    summary_html = f'<pre>{summary[:2000]}</pre>' if summary else '<div style="color:#8b949e">No output</div>'
    return f'''
<div class="section">
  <div class="card">
    <h2>Agent Reflection (agentreflect)</h2>
    {summary_html}
  </div>
</div>'''


def _compute_overall_score(results: dict) -> int:
    """Compute overall badge score from results dict."""
    scores = []
    lint = results.get("agentlint")
    if lint:
        for key in ("score", "freshness_score", "total_score"):
            v = lint.get(key)
            if v is not None:
                try:
                    scores.append(min(100.0, max(0.0, float(v))))
                    break
                except (TypeError, ValueError):
                    pass
    md = results.get("agentmd")
    if md is not None:
        if isinstance(md, list):
            vals = [d.get("score") or d.get("total_score") or 0 for d in md if isinstance(d, dict)]
            if vals:
                scores.append(min(100.0, max(0.0, sum(vals) / len(vals))))
        else:
            for key in ("score", "total_score"):
                v = md.get(key)
                if v is not None:
                    try:
                        scores.append(min(100.0, max(0.0, float(v))))
                        break
                    except (TypeError, ValueError):
                        pass
    return int(round(sum(scores) / len(scores))) if scores else 0


def build_html(project_name: str, results: dict, statuses: list[dict]) -> str:
    tools_total = len(TOOLS)
    tools_run = sum(1 for k in TOOLS if results.get(k) is not None)
    coverage = round(tools_run / tools_total * 100)
    coverage_color = _score_color_css(coverage)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    overall_score = _compute_overall_score(results)
    badge_url = build_badge_url(overall_score)
    badge_md = build_markdown(badge_url)
    badge_snippet_html = f'<div style="margin-bottom:16px"><a href="{badge_url}"><img src="{badge_url}" alt="agent quality"></a> <code style="background:#161b22;padding:2px 6px;border-radius:4px;font-size:12px">{badge_md}</code></div>'

    return _HTML_TEMPLATE.format(
        project_name=project_name,
        date=date,
        version=__version__,
        coverage_score=coverage,
        coverage_color=coverage_color,
        tools_run=tools_run,
        tools_total=tools_total,
        agentlint_summary_card=_agentlint_summary_card(results.get("agentlint")),
        agentmd_summary_card=_agentmd_summary_card(results.get("agentmd")),
        pipeline_rows=_pipeline_rows(statuses),
        badge_snippet=badge_snippet_html,
        agentlint_section=_agentlint_section(results.get("agentlint")),
        agentmd_section=_agentmd_section(results.get("agentmd")),
        coderace_section=_coderace_section(results.get("coderace")),
        agentreflect_section=_agentreflect_section(results.get("agentreflect")),
    )


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def _llmstxt_card(cwd: Path) -> str:
    """Generate llms.txt card HTML for the report, if llms.txt exists."""
    llmstxt_path = cwd / "llms.txt"
    if not llmstxt_path.exists():
        return ""
    try:
        content = llmstxt_path.read_text(encoding="utf-8", errors="replace")
        sections = [l[3:] for l in content.splitlines() if l.startswith("## ")]
        link_count = content.count("](")
        size = len(content.encode("utf-8"))
        from agentkit_cli.llmstxt import score_llms_txt
        score = score_llms_txt(content)
        score_color = _score_color_css(float(score))
        sections_html = "".join(f"<li>{s}</li>" for s in sections)
        return f"""<div class="card" style="margin-top:24px">
<h2 style="color:#58a6ff">llms.txt</h2>
<div style="display:flex;gap:16px;align-items:center;margin-bottom:12px">
<div><span style="font-size:2rem;font-weight:bold;color:{score_color}">{score}</span><div style="color:#8b949e;font-size:12px">quality score</div></div>
<div style="color:#8b949e;font-size:13px">{len(sections)} sections &nbsp;·&nbsp; {link_count} links &nbsp;·&nbsp; {size:,} bytes</div>
</div>
<div style="color:#c9d1d9;font-size:13px"><b>Sections:</b><ul style="margin-left:16px">{sections_html}</ul></div>
</div>"""
    except Exception:
        return ""


def report_command(
    path: Optional[Path],
    json_output: bool,
    output: Optional[Path],
    open_browser: bool,
    publish: bool = False,
    inject_readme: bool = False,
    share: bool = False,
    llmstxt: bool = False,
) -> None:  # noqa: D401
    """Run all toolkit checks and generate an agent quality report."""
    cwd = path or Path.cwd()
    cwd = cwd.resolve()
    project_name = cwd.name

    if not json_output:
        console.print()
        console.print(Panel(
            f"[bold cyan]agentkit report[/bold cyan] — {project_name}",
            border_style="cyan",
        ))
        console.print("\n[dim]Running toolkit checks...[/dim]\n")

    results = run_all(str(cwd))
    statuses = _tool_status(results)

    if json_output:
        out = {
            "project": project_name,
            "version": __version__,
            "coverage": _coverage_score(results),
            "tools": statuses,
            "agentlint": results.get("agentlint"),
            "agentmd": results.get("agentmd"),
            "coderace": results.get("coderace"),
            "agentreflect": results.get("agentreflect"),
        }
        print(json.dumps(out, indent=2))
        return

    # Rich summary table
    table = Table(title="Tool Status", show_header=True)
    table.add_column("Tool", style="bold")
    table.add_column("Installed")
    table.add_column("Result")

    STATUS_ICON = {
        "success": ("[green]✓[/green]", "[green]success[/green]"),
        "failed": ("[red]✗[/red]", "[red]failed[/red]"),
        "not_installed": ("[yellow]⊘[/yellow]", "[yellow]not installed[/yellow]"),
    }
    for s in statuses:
        inst_icon = "[green]✓[/green]" if s["installed"] else "[red]✗[/red]"
        ic, rs = STATUS_ICON.get(s["status"], ("?", s["status"]))
        table.add_row(s["tool"], inst_icon, rs)
    console.print(table)

    coverage = _coverage_score(results)
    color = "green" if coverage >= 80 else ("yellow" if coverage >= 50 else "red")
    console.print(f"\n[{color}]Toolkit coverage: {coverage}%[/{color}] ({sum(1 for k in TOOLS if results.get(k) is not None)}/{len(TOOLS)} tools)\n")

    # Optionally generate llms.txt before building report
    if llmstxt:
        try:
            from agentkit_cli.llmstxt import LlmsTxtGenerator
            _lg = LlmsTxtGenerator()
            _li = _lg.scan_repo(str(cwd))
            _lc = _lg.generate_llms_txt(_li)
            (cwd / "llms.txt").write_text(_lc, encoding="utf-8")
            console.print(f"[bold]llms.txt generated:[/bold] {cwd / 'llms.txt'}")
        except Exception as _e:
            console.print(f"[yellow]Warning: llmstxt generation failed — {_e}[/yellow]")

    # Generate HTML
    html = build_html(project_name, results, statuses)
    # Append llmstxt card if llms.txt exists
    llmstxt_card_html = _llmstxt_card(cwd)
    if llmstxt_card_html:
        html = html.replace("</body>", f"{llmstxt_card_html}\n</body>")
    out_path = output or cwd / "agentkit-report.html"
    out_path.write_text(html, encoding="utf-8")
    console.print(f"[bold]Report saved:[/bold] {out_path}")

    if open_browser:
        webbrowser.open(out_path.as_uri())
        console.print("[dim]Opening in browser...[/dim]")

    if publish:
        from agentkit_cli.publish import publish_html, PublishError
        import os
        try:
            api_key = os.environ.get("HERENOW_API_KEY") or None
            result = publish_html(out_path, api_key=api_key)
            url = result["url"]
            console.print(f"[bold]Report published:[/bold] {url}")
            if result.get("anonymous"):
                console.print("[dim]Note: anonymous publish — link expires in 24h.[/dim]")
        except (PublishError, Exception) as e:
            console.print(f"[yellow]Warning: publish failed — {e}[/yellow]")
        # Always output badge markdown on --publish
        overall_score = _compute_overall_score(results)
        badge_url_pub = build_badge_url(overall_score)
        badge_md_pub = build_markdown(badge_url_pub)
        console.print(f"\n[bold]Add this badge to your README:[/bold]")
        console.print(f"  {badge_md_pub}")

    if inject_readme:
        from agentkit_cli.commands.readme_cmd import readme_command
        readme_command(
            readme=None,
            dry_run=False,
            remove=False,
            section_header="## Agent Quality",
            path=cwd,
            score_override=None,
        )

    if share:
        from agentkit_cli.share import generate_scorecard_html, upload_scorecard
        import os as _os
        try:
            _share_score_result = {
                "agentlint": results.get("agentlint"),
                "agentmd": results.get("agentmd"),
                "coderace": results.get("coderace"),
                "agentreflect": results.get("agentreflect"),
            }
            _share_html = generate_scorecard_html(
                score_result=_share_score_result,
                project_name=project_name,
                ref="unknown",
            )
            _share_api_key = _os.environ.get("HERENOW_API_KEY") or None
            _share_url = upload_scorecard(_share_html, api_key=_share_api_key)
            if _share_url:
                console.print(f"\n[bold]Score card:[/bold] {_share_url}")
        except Exception as _e:
            console.print(f"[yellow]Warning: share failed — {_e}[/yellow]")
