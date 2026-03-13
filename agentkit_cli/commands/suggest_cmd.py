"""agentkit suggest command — prioritized action list from agentlint findings."""
from __future__ import annotations

import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.suggest_engine import (
    Finding,
    CONTEXT_FILE_PATTERNS,
    parse_agentlint_check_context,
    parse_agentlint_diff,
    prioritize,
)

console = Console()

SEVERITY_STYLES = {
    "critical": "bold red",
    "high": "orange3",
    "medium": "yellow",
    "low": "green",
}

# Context file globs to search for auto-fix
CONTEXT_GLOBS = ["CLAUDE.md", "AGENTS.md", ".agents/*.md"]


def _run_agentlint_check_context(path: Path) -> Optional[dict]:
    """Run agentlint check-context --json and return parsed JSON, or None on failure."""
    try:
        result = subprocess.run(
            ["agentlint", "check-context", str(path), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def _run_agentlint_diff(path: Path) -> Optional[dict]:
    """Run agentlint on recent git diff --json and return parsed JSON, or None on failure."""
    try:
        diff_result = subprocess.run(
            ["git", "-C", str(path), "diff", "HEAD~1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        diff_text = diff_result.stdout.strip()
        if not diff_text:
            return None
        result = subprocess.run(
            ["agentlint", "--json"],
            input=diff_text,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def _extract_score(check_context_json: Optional[dict]) -> Optional[int]:
    if not check_context_json:
        return None
    return (
        check_context_json.get("freshness_score")
        or check_context_json.get("score")
        or check_context_json.get("composite_score")
    )


# ---------------------------------------------------------------------------
# Auto-fix helpers
# ---------------------------------------------------------------------------

def _collect_context_files(path: Path) -> list[Path]:
    files: list[Path] = []
    for glob in CONTEXT_GLOBS:
        files.extend(path.glob(glob))
    return [f for f in files if f.is_file()]


def _fix_year_rot(text: str) -> str:
    import datetime
    current_year = datetime.datetime.now().year
    cutoff = current_year - 2

    def replace_year(m: re.Match) -> str:
        year = int(m.group(0))
        if year <= cutoff:
            return str(current_year)
        return m.group(0)

    return re.sub(r"\b(19|20)\d{2}\b", replace_year, text)


def _fix_trailing_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + ("\n" if text.endswith("\n") else "")


def _fix_duplicate_blank_lines(text: str) -> str:
    return re.sub(r"\n{4,}", "\n\n\n", text)


def _apply_fixes(text: str, fix_year: bool = True, fix_ws: bool = True, fix_blanks: bool = True) -> str:
    if fix_year:
        text = _fix_year_rot(text)
    if fix_ws:
        text = _fix_trailing_whitespace(text)
    if fix_blanks:
        text = _fix_duplicate_blank_lines(text)
    return text


def _unified_diff(original: str, modified: str, filename: str) -> str:
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(orig_lines, mod_lines, fromfile=f"a/{filename}", tofile=f"b/{filename}")
    )


def run_fixes(path: Path, dry_run: bool = False) -> list[str]:
    """Apply safe auto-fixes. Returns list of changed file paths."""
    files = _collect_context_files(path)
    changed: list[str] = []

    for fpath in files:
        try:
            original = fpath.read_text(encoding="utf-8")
        except Exception:
            continue
        modified = _apply_fixes(original)
        if modified == original:
            continue
        rel = str(fpath.relative_to(path))
        changed.append(rel)
        if dry_run:
            diff = _unified_diff(original, modified, rel)
            if diff:
                console.print(f"\n[bold]--- diff: {rel} ---[/bold]")
                console.print(diff)
        else:
            fpath.write_text(modified, encoding="utf-8")

    return changed


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

def suggest_command(
    path: Optional[Path] = None,
    show_all: bool = False,
    fix: bool = False,
    dry_run: bool = False,
    json_output: bool = False,
) -> None:
    """Prioritized action list from agentlint findings."""
    root = Path(path).resolve() if path else Path.cwd()

    # Gather findings
    cc_json = _run_agentlint_check_context(root)
    diff_json = _run_agentlint_diff(root)

    cc_findings = parse_agentlint_check_context(cc_json)
    diff_findings = parse_agentlint_diff(diff_json)
    all_findings = cc_findings + diff_findings

    score = _extract_score(cc_json)
    top_n = None if show_all else 5
    findings = prioritize(all_findings, top_n=top_n)

    # --json output
    if json_output:
        out = {
            "score": score,
            "findings": [
                {
                    "tool": f.tool,
                    "severity": f.severity,
                    "category": f.category,
                    "description": f.description,
                    "fix_hint": f.fix_hint,
                    "auto_fixable": f.auto_fixable,
                    "file": f.file,
                    "line": f.line,
                }
                for f in findings
            ],
        }
        print(json.dumps(out, indent=2))
        return

    # Score header
    critical_count = sum(1 for f in findings if f.severity == "critical")
    if score is not None:
        label = f"Current score: {score}/100"
        if critical_count:
            label += f" — [bold red]{critical_count} critical issue{'s' if critical_count != 1 else ''} found[/bold red]"
        console.print(f"\n{label}\n")

    if not findings:
        console.print("[green]No issues found.[/green]\n")
        if fix:
            console.print("\n[bold]Running auto-fixes…[/bold]")
            changed = run_fixes(root, dry_run=dry_run)
            if dry_run:
                if changed:
                    console.print(f"\n[yellow]Dry-run: {len(changed)} file(s) would be changed.[/yellow]")
                else:
                    console.print("[green]Dry-run: nothing to fix.[/green]")
            else:
                if changed:
                    for rel in changed:
                        console.print(f"  [green]Fixed[/green] {rel}")
                    console.print(f"\n[green]Fixed {len(changed)} file(s).[/green]")
                else:
                    console.print("[green]Nothing to fix.[/green]")
        return

    # Rich table
    table = Table(show_header=True, title="agentkit suggest — top findings")
    table.add_column("#", style="dim", width=3)
    table.add_column("Severity", width=10)
    table.add_column("Category", width=22)
    table.add_column("Description")
    table.add_column("Fix Hint")
    table.add_column("Auto-fix?", width=9)

    for i, f in enumerate(findings, 1):
        style = SEVERITY_STYLES.get(f.severity, "")
        sev_label = f"[{style}]{f.severity}[/{style}]" if style else f.severity
        auto = "[green]yes[/green]" if f.auto_fixable else "[dim]no[/dim]"
        table.add_row(str(i), sev_label, f.category, f.description, f.fix_hint, auto)

    console.print(table)

    if not show_all and len(all_findings) > len(findings):
        total = len(prioritize(all_findings))
        console.print(f"\n[dim]Showing top 5 of {total} findings. Use --all to see all.[/dim]\n")

    # --fix
    if fix:
        console.print("\n[bold]Running auto-fixes…[/bold]")
        changed = run_fixes(root, dry_run=dry_run)
        if dry_run:
            if changed:
                console.print(f"\n[yellow]Dry-run: {len(changed)} file(s) would be changed.[/yellow]")
            else:
                console.print("[green]Dry-run: nothing to fix.[/green]")
        else:
            if changed:
                for rel in changed:
                    console.print(f"  [green]Fixed[/green] {rel}")
                console.print(f"\n[green]Fixed {len(changed)} file(s).[/green]")
            else:
                console.print("[green]Nothing to fix.[/green]")
