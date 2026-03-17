"""agentkit harden command — analyze and auto-remediate agent context files."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.redteam_scorer import RedTeamScorer
from agentkit_cli.redteam_fixer import RedTeamFixer
from agentkit_cli.harden_report import save_harden_html

console = Console()

_CONTEXT_FILE_NAMES = ("CLAUDE.md", "AGENTS.md", "SYSTEM.md", "claude.md", "agents.md", "system.md")


def _detect_context_file(path: Path) -> Optional[Path]:
    """Auto-detect a context file in the given directory."""
    if path.is_file():
        return path
    for name in _CONTEXT_FILE_NAMES:
        candidate = path / name
        if candidate.exists():
            return candidate
    return None


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def harden_command(
    path: Optional[Path],
    output: Optional[Path],
    dry_run: bool,
    report: bool,
    share: bool,
    json_output: bool,
) -> None:
    """Analyze a context file, apply all safe remediations, and report score lift."""
    target = (path or Path(".")).resolve()

    # Auto-detect context file
    ctx_path = _detect_context_file(target)
    if ctx_path is None:
        if json_output:
            print(json.dumps({"error": f"No context file found in {target}"}))
        else:
            console.print(f"[red]Error:[/red] No context file found in {target}")
            console.print(f"[dim]Looking for: {', '.join(_CONTEXT_FILE_NAMES)}[/dim]")
        raise typer.Exit(code=1)

    # Score original
    scorer = RedTeamScorer(n_per_category=3)
    original_report = scorer.score_resistance(ctx_path)

    # Determine output path for hardened file
    write_path = output if output else ctx_path

    # Apply all remediations
    fixer = RedTeamFixer()
    if output:
        # When --output is specified, always dry_run the original, then write to output
        fix_result = fixer.apply_all(ctx_path, dry_run=True)
        if not dry_run:
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(fix_result.fixed_text, encoding="utf-8")
    else:
        fix_result = fixer.apply_all(ctx_path, dry_run=dry_run)

    # Score the fixed version
    if not dry_run:
        rescore_path = output if output else ctx_path
        fixed_report = scorer.score_resistance(rescore_path)
    else:
        # Score in-memory fixed text
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tf:
            tf.write(fix_result.fixed_text)
            tmp_name = tf.name
        try:
            fixed_report = scorer.score_resistance(Path(tmp_name))
        finally:
            Path(tmp_name).unlink(missing_ok=True)

    if json_output:
        out = {
            "context_path": str(ctx_path),
            "original_score": original_report.score_overall,
            "fixed_score": fixed_report.score_overall,
            "delta": round(fixed_report.score_overall - original_report.score_overall, 1),
            "rules_applied": fix_result.rules_applied,
            "backup_path": fix_result.backup_path,
            "output_path": str(output) if output else str(ctx_path),
            "dry_run": dry_run,
        }
        if share:
            share_url = _do_share(original_report, fixed_report, fix_result, ctx_path)
            if share_url:
                out["share_url"] = share_url
        print(json.dumps(out, indent=2))
        return

    # Rich output
    console.print()
    mode_label = " [yellow](dry run)[/yellow]" if dry_run else ""
    console.print(f"[bold]agentkit harden[/bold]  [dim]{ctx_path}[/dim]{mode_label}")
    console.print()

    orig_score = original_report.score_overall
    fixed_score = fixed_report.score_overall
    delta = fixed_score - orig_score
    orig_color = _score_color(orig_score)
    fixed_color = _score_color(fixed_score)
    delta_color = "green" if delta > 0 else ("red" if delta < 0 else "dim")
    delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"

    console.print(
        f"  Score: [{orig_color}]{orig_score:.0f}[/{orig_color}]"
        f" → [{fixed_color}]{fixed_score:.0f}[/{fixed_color}]"
        f"  [{delta_color}]({delta_str})[/{delta_color}]"
        f"  Grade: {original_report.grade} → {fixed_report.grade}"
    )
    console.print()

    # Category table
    table = Table(title="Category Scores", show_header=True, header_style="bold dim")
    table.add_column("Category", style="bold")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Status", justify="center")

    for cat_str in original_report.score_by_category:
        before = original_report.score_by_category[cat_str]
        after = fixed_report.score_by_category.get(cat_str, before)
        d = after - before
        label = cat_str.replace("_", " ").title()
        b_color = _score_color(before)
        a_color = _score_color(after)
        d_color = "green" if d > 0 else "dim"
        d_str = f"+{d:.0f}" if d > 0 else f"{d:.0f}"
        was_applied = cat_str in fix_result.rules_applied
        status = "[green]✓ Fixed[/green]" if was_applied else "[dim]—[/dim]"
        table.add_row(
            label,
            f"[{b_color}]{before:.0f}[/{b_color}]",
            f"[{a_color}]{after:.0f}[/{a_color}]",
            f"[{d_color}]{d_str}[/{d_color}]",
            status,
        )
    console.print(table)
    console.print()

    if fix_result.rules_applied:
        console.print(f"[green]Applied {len(fix_result.rules_applied)} remediation(s):[/green]")
        for r in fix_result.rules_applied:
            console.print(f"  ✓ {r.replace('_', ' ').title()}")
    else:
        console.print("[green]Already hardened — no changes needed.[/green]")

    if fix_result.backup_path:
        console.print(f"\n[dim]Backup: {fix_result.backup_path}[/dim]")
    if output and not dry_run:
        console.print(f"[dim]Hardened file written to: {output}[/dim]")
    if dry_run:
        console.print("\n[yellow]Dry run: no files were modified.[/yellow]")
    console.print()

    # --report
    if report:
        html_path = save_harden_html(
            original_report, fixed_report, fix_result, context_path=str(ctx_path)
        )
        console.print(f"[dim]HTML report: {html_path}[/dim]")

    # --share
    if share:
        share_url = _do_share(original_report, fixed_report, fix_result, ctx_path)
        if share_url:
            console.print(f"[green]Shared:[/green] {share_url}")
        else:
            console.print("[yellow]Share failed[/yellow]")


def _do_share(original_report, fixed_report, fix_result, ctx_path) -> Optional[str]:
    """Upload harden HTML report to here.now."""
    try:
        html_path = save_harden_html(
            original_report, fixed_report, fix_result, context_path=str(ctx_path)
        )
        from agentkit_cli.publish import publish_report
        api_key = os.environ.get("HERENOW_API_KEY")
        return publish_report(original_report, api_key=api_key)
    except Exception:
        return None
