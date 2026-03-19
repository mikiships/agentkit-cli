"""agentkit quickstart command — fastest path to an impressive first result."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agentkit_cli.doctor import run_doctor
from agentkit_cli.tools import ToolAdapter, is_installed, QUARTET_TOOLS
from agentkit_cli.composite import CompositeScoreEngine
from agentkit_cli.share import generate_scorecard_html, upload_scorecard

console = Console()

_GRADE_COLORS = {"A": "bold green", "B": "green", "C": "yellow", "D": "red", "F": "bold red"}


def _grade_color(grade: str) -> str:
    return _GRADE_COLORS.get(grade, "white")


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _extract_findings(tool_results: dict) -> list[str]:
    """Extract up to 3 top findings from tool results."""
    findings: list[str] = []

    # From agentlint
    lint_result = tool_results.get("agentlint")
    if lint_result and isinstance(lint_result, dict):
        issues = lint_result.get("issues") or lint_result.get("findings") or []
        if isinstance(issues, list):
            for issue in issues[:2]:
                if isinstance(issue, dict):
                    msg = issue.get("message") or issue.get("description") or issue.get("msg") or str(issue)
                    findings.append(f"[agentlint] {msg[:80]}")
                elif isinstance(issue, str):
                    findings.append(f"[agentlint] {issue[:80]}")
        if not issues:
            count = lint_result.get("issue_count") or lint_result.get("total")
            if count is not None:
                findings.append(f"[agentlint] {count} issues found")

    # From agentmd
    md_result = tool_results.get("agentmd")
    if md_result and isinstance(md_result, dict):
        suggestions = md_result.get("suggestions") or md_result.get("findings") or []
        if isinstance(suggestions, list):
            for s in suggestions[:1]:
                if isinstance(s, dict):
                    msg = s.get("text") or s.get("message") or str(s)
                    findings.append(f"[agentmd] {msg[:80]}")
                elif isinstance(s, str):
                    findings.append(f"[agentmd] {s[:80]}")
        if not suggestions:
            score = md_result.get("score")
            if score is not None:
                findings.append(f"[agentmd] Documentation score: {score}")

    if not findings:
        findings.append("Run `agentkit run .` to see detailed findings.")

    return findings[:3]


def _run_fast_analysis(target_path: str, timeout: int) -> tuple[dict, dict]:
    """Run agentlint + agentmd with per-tool timeout. Returns (tool_scores, tool_results)."""
    adapter = ToolAdapter(timeout=timeout)
    tool_scores: dict[str, Optional[float]] = {}
    tool_results: dict = {}

    # agentlint
    if is_installed("agentlint"):
        result = adapter.agentlint_check_context(target_path)
        tool_results["agentlint"] = result
        if result and isinstance(result, dict):
            score = result.get("score")
            if score is None:
                # Derive from issue count
                issues = result.get("issues") or result.get("findings") or []
                count = len(issues) if isinstance(issues, list) else (result.get("issue_count") or 0)
                score = max(0.0, 100.0 - float(count) * 5)
            tool_scores["agentlint"] = float(score)
        else:
            tool_scores["agentlint"] = None
    else:
        tool_scores["agentlint"] = None

    # agentmd
    if is_installed("agentmd"):
        result = adapter.agentmd_score(target_path)
        tool_results["agentmd"] = result
        if result and isinstance(result, dict):
            score = result.get("score") or result.get("total_score")
            tool_scores["agentmd"] = float(score) if score is not None else None
        else:
            tool_scores["agentmd"] = None
    else:
        tool_scores["agentmd"] = None

    # Skip coderace (too slow for quickstart fast path)
    tool_scores["coderace"] = None

    # Skip agentreflect (also slow)
    tool_scores["agentreflect"] = None

    return tool_scores, tool_results


def quickstart_command(
    target: str = ".",
    no_share: bool = False,
    timeout: int = 30,
) -> None:
    """Run the fastest path to an impressive agentkit result.

    Detects the current project (or a GitHub URL), checks toolchain readiness,
    runs a fast composite score, and prints a beautiful summary.
    """
    start = time.monotonic()

    # Step 1: Header
    console.print()
    console.print(Panel(
        "[bold cyan]🚀 agentkit quickstart[/bold cyan]\n"
        "[dim]Your fastest path to an agent quality score.[/dim]",
        border_style="cyan",
        expand=False,
    ))
    console.print()

    # Resolve target path
    is_github = target.startswith("github:")
    if is_github:
        # Delegate to analyze for github targets — clone + run
        console.print(f"[dim]Cloning {target} …[/dim]")
        from agentkit_cli.analyze import analyze_target, parse_target
        try:
            _url, _repo = parse_target(target)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)
        try:
            analyze_result = analyze_target(target=target, timeout=timeout, no_generate=True)
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

        # Build tool_scores from analyze_result
        tool_scores: dict = {}
        tool_results: dict = {}
        for tool_name, tr in analyze_result.tools.items():
            tool_scores[tool_name] = tr.get("score")
        target_path = str(Path.cwd())
        project_name = analyze_result.repo_name
    else:
        target_path = str(Path(target).resolve())
        project_name = Path(target_path).name
        tool_scores = {}
        tool_results = {}

    # Step 2: Doctor check (summary only)
    console.print("[bold]Checking toolchain readiness…[/bold]")
    try:
        doctor_report = run_doctor(root=Path(target_path) if not is_github else None)
        ready_tools = [c for c in doctor_report.checks if c.category == "toolchain" and c.status == "ok"]
        total_tools = [c for c in doctor_report.checks if c.category == "toolchain"]
        n_ready = len(ready_tools)
        n_total = len(total_tools)
        if n_ready == n_total and n_total > 0:
            console.print(f"  [green]✓[/green] {n_ready} tools ready")
        else:
            console.print(f"  [yellow]⚠[/yellow] {n_ready}/{n_total} tools ready (degraded mode)")
    except Exception:
        console.print("  [yellow]⚠[/yellow] Doctor check skipped")

    console.print()

    # Step 3: Fast composite score
    if not is_github:
        console.print("[bold]Running fast analysis (agentlint + agentmd)…[/bold]")
        tool_scores, tool_results = _run_fast_analysis(target_path, timeout=timeout)

    # Compute composite
    engine = CompositeScoreEngine()
    try:
        composite = engine.compute(tool_scores)
        score = composite.score
        grade = composite.grade
        missing = composite.missing_tools
    except ValueError:
        # No tools available
        score = 0.0
        grade = "?"
        missing = list(QUARTET_TOOLS)
        composite = None

    elapsed = time.monotonic() - start

    # Step 4: Rich panel output
    findings = _extract_findings(tool_results) if not is_github else ["Run `agentkit run .` for detailed findings."]
    missing_note = ""
    if missing:
        # Only note tools that are actually not installed (not just skipped fast-path tools)
        actually_missing = [t for t in ["agentlint", "agentmd"] if not is_installed(t)]
        if actually_missing:
            missing_note = f"\n[dim]Missing tools: {', '.join(actually_missing)} — scores estimated from available tools.[/dim]"

    score_text = Text()
    score_text.append(f"  Score: ", style="bold")
    score_text.append(f"{score:.0f}/100", style=_score_color(score))
    score_text.append(f"  Grade: ", style="bold")
    score_text.append(f"{grade}", style=_grade_color(grade))
    score_text.append(f"  ({elapsed:.1f}s)\n\n", style="dim")
    score_text.append("  Top Findings:\n", style="bold")
    for f in findings:
        score_text.append(f"    • {f}\n", style="dim")
    score_text.append(missing_note)

    console.print(Panel(
        score_text,
        title=f"[bold]{project_name}[/bold]",
        border_style=_score_color(score),
        expand=False,
    ))

    # Step 5: Publish (share)
    _PAGES_URL = "https://mikiships.github.io/agentkit-cli/"
    console.print(f"[bold]Docs:[/bold] {_PAGES_URL}")

    if not no_share:
        api_key = os.environ.get("HERENOW_API_KEY") or None
        if not api_key:
            console.print("[dim](Skipping share — set HERENOW_API_KEY to publish a scorecard)[/dim]")
        else:
            try:
                score_dict: dict = {"composite": score}
                if composite:
                    for tool_name, comp_data in composite.components.items():
                        score_dict[tool_name] = comp_data.get("raw_score")
                html = generate_scorecard_html(
                    score_dict,
                    project_name=project_name,
                    ref=target,
                    repo_url=target if is_github else None,
                    repo_name=project_name,
                )
                share_url = upload_scorecard(html, api_key=api_key)
                if share_url:
                    console.print(f"\n[bold green]Score card:[/bold green] {share_url}")
                else:
                    console.print("\n[dim](Share unavailable — network or API error)[/dim]")
            except Exception:
                console.print("\n[dim](Share unavailable)[/dim]")

    # Step 6: Next steps
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  [cyan]agentkit run .[/cyan]                  -- full analysis")
    console.print(f"  [cyan]agentkit analyze github:owner/repo[/cyan]  -- analyze any public repo")
    console.print(f"  [cyan]agentkit benchmark[/cyan]                  -- compare Claude vs Codex on your tasks")
    console.print()
