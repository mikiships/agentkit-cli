"""agentkit redteam command — adversarial eval of agent context files."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.redteam_engine import AttackCategory
from agentkit_cli.redteam_scorer import RedTeamScorer
from agentkit_cli.redteam_report import save_html, publish_report

console = Console()


def _render_fix_table(original_report, fixed_report, result) -> None:
    """Render before/after fix table."""
    from agentkit_cli.redteam_fixer import FixResult
    table = Table(title="Remediation Results", show_header=True, header_style="bold dim")
    table.add_column("Category", style="bold")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Status", justify="center")

    for cat_str in original_report.score_by_category:
        before = original_report.score_by_category[cat_str]
        after = fixed_report.score_by_category.get(cat_str, before)
        delta = after - before
        label = cat_str.replace("_", " ").title()
        before_color = _score_color(before)
        after_color = _score_color(after)
        delta_color = "green" if delta > 0 else ("red" if delta < 0 else "dim")
        delta_str = f"+{delta:.0f}" if delta > 0 else f"{delta:.0f}"
        # Was this rule applied?
        was_applied = cat_str in result.rules_applied
        status = "[green]✓ Fixed[/green]" if was_applied else "[dim]—[/dim]"
        table.add_row(
            label,
            f"[{before_color}]{before:.0f}[/{before_color}]",
            f"[{after_color}]{after:.0f}[/{after_color}]",
            f"[{delta_color}]{delta_str}[/{delta_color}]",
            status,
        )
    console.print(table)
    console.print(
        f"\n  Overall: [{_score_color(original_report.score_overall)}]"
        f"{original_report.score_overall:.0f}[/{_score_color(original_report.score_overall)}]"
        f" → [{_score_color(fixed_report.score_overall)}]"
        f"{fixed_report.score_overall:.0f}[/{_score_color(fixed_report.score_overall)}]"
    )


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _grade_style(grade: str) -> str:
    return {"A": "bold green", "B": "green", "C": "yellow", "D": "yellow", "F": "bold red"}.get(grade, "white")


def redteam_command(
    path: Optional[Path],
    categories: Optional[str],
    attacks_per_category: int,
    json_output: bool,
    share: bool,
    min_score: Optional[int],
    output: Optional[Path],
    fix: bool = False,
    dry_run: bool = False,
) -> None:
    """Run adversarial eval on an agent context file and report resistance score."""
    target = (path or Path(".")).resolve()

    # Parse categories filter
    active_categories: Optional[List[AttackCategory]] = None
    if categories:
        active_categories = []
        for name in categories.split(","):
            name = name.strip().upper()
            try:
                active_categories.append(AttackCategory(name.lower()))
            except ValueError:
                # Try matching by name
                matched = [c for c in AttackCategory if c.name == name or c.value == name.lower()]
                if matched:
                    active_categories.extend(matched)
                else:
                    console.print(f"[yellow]Warning: unknown category '{name}', skipping[/yellow]")

    scorer = RedTeamScorer(n_per_category=attacks_per_category)
    report = scorer.score_resistance(target)

    # Filter attack samples if categories specified
    if active_categories:
        report.attack_samples = [a for a in report.attack_samples if a.category in active_categories]
        # Also filter score_by_category display
        report.score_by_category = {
            k: v for k, v in report.score_by_category.items()
            if AttackCategory(k) in active_categories
        }

    # --output: save HTML
    html_path: Optional[Path] = None
    if output:
        html_path = save_html(report, output)
    elif share:
        # Need to save to temp before publish
        html_path = save_html(report)

    # --share: upload
    share_url: Optional[str] = None
    if share:
        api_key = os.environ.get("HERENOW_API_KEY")
        try:
            from agentkit_cli.publish import PublishError
            share_url = publish_report(report, api_key=api_key)
        except Exception as e:
            if not json_output:
                console.print(f"[yellow]Share failed: {e}[/yellow]")

    if fix:
        # Determine the actual context file path
        from agentkit_cli.redteam_fixer import RedTeamFixer
        ctx_path = Path(report.path)
        fixer = RedTeamFixer()
        fix_result = fixer.apply(ctx_path, report, dry_run=dry_run)

        if fix_result.rules_applied:
            # Re-score the fixed file
            scorer2 = RedTeamScorer(n_per_category=attacks_per_category)
            fixed_report = scorer2.score_resistance(ctx_path if not dry_run else ctx_path)
            if dry_run:
                # Score the in-memory fixed text
                import tempfile, shutil
                with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tf:
                    tf.write(fix_result.fixed_text)
                    tmp_name = tf.name
                try:
                    fixed_report = scorer2.score_resistance(Path(tmp_name))
                finally:
                    Path(tmp_name).unlink(missing_ok=True)
        else:
            fixed_report = report

        if json_output:
            out = {
                "original_score": report.score_overall,
                "fixed_score": fixed_report.score_overall,
                "delta": round(fixed_report.score_overall - report.score_overall, 1),
                "rules_applied": fix_result.rules_applied,
                "backup_path": fix_result.backup_path,
                "dry_run": dry_run,
            }
            print(json.dumps(out, indent=2))
        else:
            console.print()
            mode_label = "[yellow](dry run)[/yellow]" if dry_run else ""
            console.print(f"[bold]agentkit redteam --fix[/bold]  [dim]{report.path}[/dim] {mode_label}")
            _render_fix_table(report, fixed_report, fix_result)
            if fix_result.backup_path:
                console.print(f"\n[dim]Backup saved: {fix_result.backup_path}[/dim]")
            if dry_run:
                console.print("\n[yellow]Dry run: no files were modified.[/yellow]")

        if min_score is not None and fixed_report.score_overall < min_score:
            raise typer.Exit(code=1)
        return

    if json_output:
        out = report.to_dict()
        if share_url:
            out["share_url"] = share_url
        if html_path:
            out["report_path"] = str(html_path)
        print(json.dumps(out, indent=2))
    else:
        _render_rich(report, share_url=share_url, html_path=html_path)

    # --min-score CI gate
    if min_score is not None and report.score_overall < min_score:
        if not json_output:
            console.print(
                f"\n[red]CI gate failed: score {report.score_overall:.0f} < min-score {min_score}[/red]"
            )
        raise typer.Exit(code=1)


def _render_rich(report, share_url=None, html_path=None) -> None:
    console.print()
    console.print(f"[bold]agentkit redteam[/bold]  [dim]{report.path}[/dim]")
    console.print()

    # Overall score + grade
    score_color = _score_color(report.score_overall)
    grade_style = _grade_style(report.grade)
    console.print(
        f"  Resistance Score: [{score_color}][bold]{report.score_overall:.0f}/100[/bold][/{score_color}]"
        f"  Grade: [{grade_style}]{report.grade}[/{grade_style}]"
    )
    console.print()

    # Category breakdown table
    table = Table(title="Category Scores", show_header=True, header_style="bold dim")
    table.add_column("Category", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Bar", min_width=20)
    table.add_column("Status", justify="center")

    for cat_str, cat_score in report.score_by_category.items():
        label = cat_str.replace("_", " ").title()
        color = _score_color(cat_score)
        bar_filled = int(cat_score / 5)
        bar = f"[{color}]{'█' * bar_filled}[/{color}]{'░' * (20 - bar_filled)}"
        status = "✓" if cat_score >= 80 else ("⚠" if cat_score >= 50 else "✗")
        status_style = "green" if cat_score >= 80 else ("yellow" if cat_score >= 50 else "red")
        table.add_row(label, f"[{color}]{cat_score:.0f}[/{color}]", bar, f"[{status_style}]{status}[/{status_style}]")

    console.print(table)
    console.print()

    # Attack samples (one per category)
    if report.attack_samples:
        console.print("[bold]Sample Attacks[/bold]")
        seen_cats: set = set()
        for attack in report.attack_samples:
            if attack.category in seen_cats:
                continue
            seen_cats.add(attack.category)
            cat_label = attack.category.value.replace("_", " ").title()
            truncated = attack.input_text[:120] + ("…" if len(attack.input_text) > 120 else "")
            console.print(f"  [dim][{cat_label}][/dim] {truncated}")
        console.print()

    # Top 3 recommendations
    if report.recommendations:
        console.print("[bold]Top Recommendations[/bold]")
        for i, rec in enumerate(report.recommendations[:3], 1):
            console.print(f"  {i}. {rec}")
        console.print()

    if share_url:
        console.print(f"[green]Report shared:[/green] {share_url}")
    if html_path:
        console.print(f"[dim]HTML report saved:[/dim] {html_path}")
    console.print()
