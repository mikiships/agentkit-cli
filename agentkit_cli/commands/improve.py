"""agentkit improve command — end-to-end automated quality improvement."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def improve_command(
    target: Optional[str] = typer.Argument(None, help="Local path or github:owner/repo (default: current dir)"),
    no_generate: bool = typer.Option(False, "--no-generate", help="Skip CLAUDE.md generation step"),
    no_harden: bool = typer.Option(False, "--no-harden", help="Skip redteam hardening step"),
    min_lift: Optional[float] = typer.Option(None, "--min-lift", help="Exit 1 if score delta < N"),
    pr: bool = typer.Option(False, "--pr", help="Open a GitHub PR with changes after improving"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan what would be done without applying changes"),
    optimize_context: bool = typer.Option(False, "--optimize-context", help="Also run agentkit optimize inside the improve workflow"),
    json_output: bool = typer.Option(False, "--json", help="Output structured JSON result"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now and print URL"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write HTML report to file"),
) -> None:
    """Analyze → fix → re-analyze. Shows before/after score and what changed."""

    resolved_target = target or "."

    if dry_run:
        console.print("[bold cyan]Dry run[/bold cyan] — planning only, no changes applied.\n")

    # ------------------------------------------------------------------
    # Run the improvement engine
    # ------------------------------------------------------------------
    from agentkit_cli.improve_engine import ImproveEngine

    engine = ImproveEngine()

    try:
        plan = engine.run(
            resolved_target,
            no_generate=no_generate,
            no_harden=no_harden,
            dry_run=dry_run,
            optimize_context=optimize_context,
        )
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    if json_output:
        d = plan.as_dict()
        print(json.dumps(d, indent=2))
    else:
        _print_rich_output(plan, dry_run=dry_run)

    # ------------------------------------------------------------------
    # HTML report
    # ------------------------------------------------------------------
    if output or share:
        html = _render_html(plan)
        if output:
            output.write_text(html, encoding="utf-8")
            console.print(f"\n[dim]Report written to {output}[/dim]")
        if share:
            _do_share(html, console)

    # ------------------------------------------------------------------
    # Optional PR
    # ------------------------------------------------------------------
    if pr and not dry_run:
        _open_pr(resolved_target, plan, console)

    # ------------------------------------------------------------------
    # min-lift gate
    # ------------------------------------------------------------------
    if min_lift is not None and plan.delta < min_lift:
        console.print(
            f"\n[red]min-lift gate failed:[/red] delta {plan.delta:+.1f} < {min_lift}"
        )
        raise typer.Exit(code=1)


# ──────────────────────────────────────────────────────────
# Rich display
# ──────────────────────────────────────────────────────────

def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _print_rich_output(plan, *, dry_run: bool) -> None:
    from agentkit_cli.improve_engine import ImprovementPlan

    baseline_color = _score_color(plan.baseline_score)
    final_color = _score_color(plan.final_score)
    delta_sign = "+" if plan.delta >= 0 else ""
    delta_color = "green" if plan.delta > 0 else ("yellow" if plan.delta == 0 else "red")

    console.print()
    console.print(f"  Analyzing target...      baseline [{baseline_color}]{plan.baseline_score:.0f}/100[/{baseline_color}]")
    if not dry_run:
        console.print(f"  Re-analyzing...          final    [{final_color}]{plan.final_score:.0f}/100[/{final_color}]")
        console.print(f"                           [{delta_color}]▲ {delta_sign}{plan.delta:.1f} pts[/{delta_color}]")
    console.print()

    if plan.actions_taken:
        console.print("[bold]Actions taken:[/bold]")
        for a in plan.actions_taken:
            console.print(f"  [green]✓[/green] {a}")
        console.print()

    if plan.actions_skipped:
        console.print("[bold]Actions skipped:[/bold]")
        for a in plan.actions_skipped:
            console.print(f"  [yellow]✗[/yellow] {a}")
        console.print()


# ──────────────────────────────────────────────────────────
# HTML report
# ──────────────────────────────────────────────────────────

def _render_html(plan) -> str:
    """Generate the dark-theme improvement report HTML."""
    from pathlib import Path as _Path
    tmpl_path = _Path(__file__).parent.parent / "templates" / "improve_report.html"
    if tmpl_path.exists():
        tmpl = tmpl_path.read_text(encoding="utf-8")
    else:
        tmpl = _DEFAULT_TEMPLATE

    delta_sign = "+" if plan.delta >= 0 else ""
    actions_taken_html = "".join(
        f"<li>✓ {a}</li>" for a in plan.actions_taken
    ) or "<li><em>None</em></li>"
    actions_skipped_html = "".join(
        f"<li>✗ {a}</li>" for a in plan.actions_skipped
    ) or "<li><em>None</em></li>"

    import re
    repo_name = re.sub(r"^github:", "", plan.target).split("/")[-1] or plan.target

    return (
        tmpl
        .replace("{{REPO_NAME}}", repo_name)
        .replace("{{BASELINE}}", f"{plan.baseline_score:.0f}")
        .replace("{{FINAL}}", f"{plan.final_score:.0f}")
        .replace("{{DELTA}}", f"{delta_sign}{plan.delta:.1f}")
        .replace("{{ACTIONS_TAKEN}}", actions_taken_html)
        .replace("{{ACTIONS_SKIPPED}}", actions_skipped_html)
        .replace("{{TARGET}}", plan.target)
    )


def _do_share(html: str, cons: Console) -> None:
    try:
        from agentkit_cli.publish import publish_html, PublishError
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
            f.write(html)
            tmp_path = Path(f.name)
        api_key = os.environ.get("HERENOW_API_KEY") or None
        result = publish_html(tmp_path, api_key=api_key)
        url = result["url"]
        cons.print(f"\n[bold]Report published:[/bold] {url}")
        tmp_path.unlink(missing_ok=True)
    except Exception as e:
        cons.print(f"[yellow]Warning: share failed — {e}[/yellow]")


def _open_pr(target: str, plan, cons: Console) -> None:
    try:
        from agentkit_cli.commands.pr_cmd import pr_command
        from pathlib import Path as _Path
        pr_command(
            path=_Path(target) if not target.startswith("github:") else None,
            dry_run=False,
            json_output=False,
        )
    except Exception as e:
        cons.print(f"[yellow]Warning: PR submission failed — {e}[/yellow]")


# ──────────────────────────────────────────────────────────
# Inline fallback template (used if file missing in tests)
# ──────────────────────────────────────────────────────────

_DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>agentkit improve — {{REPO_NAME}}</title>
<style>
  :root { --bg: #0d1117; --card: #161b22; --border: #30363d; --green: #3fb950; --yellow: #d29922; --red: #f85149; --text: #c9d1d9; --dim: #8b949e; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; padding: 2rem; }
  h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
  .hero { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 2rem; margin-bottom: 2rem; }
  .score-row { display: flex; gap: 2rem; margin-top: 1rem; flex-wrap: wrap; }
  .score-card { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 1rem 1.5rem; min-width: 120px; }
  .score-card .label { font-size: 0.8rem; color: var(--dim); text-transform: uppercase; letter-spacing: 0.05em; }
  .score-card .value { font-size: 2rem; font-weight: bold; margin-top: 0.25rem; }
  .green { color: var(--green); } .yellow { color: var(--yellow); } .red { color: var(--red); }
  section { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; }
  section h2 { font-size: 1.1rem; margin-bottom: 1rem; color: var(--dim); }
  ul { list-style: none; padding: 0; }
  li { padding: 0.35rem 0; border-bottom: 1px solid var(--border); }
  li:last-child { border-bottom: none; }
  .dim { color: var(--dim); font-size: 0.85rem; }
</style>
</head>
<body>
<div class="hero">
  <h1>{{REPO_NAME}}</h1>
  <p class="dim">agentkit improve report &mdash; target: {{TARGET}}</p>
  <div class="score-row">
    <div class="score-card">
      <div class="label">Before</div>
      <div class="value yellow">{{BASELINE}}</div>
    </div>
    <div class="score-card">
      <div class="label">After</div>
      <div class="value green">{{FINAL}}</div>
    </div>
    <div class="score-card">
      <div class="label">Delta</div>
      <div class="value green">{{DELTA}} pts</div>
    </div>
  </div>
</div>
<section>
  <h2>What we did</h2>
  <ul>{{ACTIONS_TAKEN}}</ul>
</section>
<section>
  <h2>What&rsquo;s still open</h2>
  <ul>{{ACTIONS_SKIPPED}}</ul>
</section>
</body>
</html>
"""
