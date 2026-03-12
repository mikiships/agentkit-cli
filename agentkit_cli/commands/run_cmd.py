"""agentkit run command — sequential pipeline runner."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.tools import is_installed, run_tool, INSTALL_HINTS
from agentkit_cli.config import find_project_root, save_last_run

console = Console()

STEP_TOOL_MAP = {
    "generate": "agentmd",
    "lint": "agentlint",
    "benchmark": "coderace",
    "reflect": "agentreflect",
}


def _run_step(name: str, tool: str, args: list[str], cwd: str) -> dict:
    """Execute one pipeline step; return result dict."""
    start = time.monotonic()
    if not is_installed(tool):
        return {
            "step": name,
            "tool": tool,
            "status": "skipped",
            "reason": f"not installed — {INSTALL_HINTS.get(tool, f'pip install {tool}')}",
            "duration": 0.0,
            "output": "",
        }
    try:
        result = run_tool(tool, args, cwd=cwd)
        duration = time.monotonic() - start
        success = result.returncode == 0
        return {
            "step": name,
            "tool": tool,
            "status": "pass" if success else "fail",
            "returncode": result.returncode,
            "duration": round(duration, 2),
            "output": (result.stdout + result.stderr).strip(),
        }
    except Exception as e:
        return {
            "step": name,
            "tool": tool,
            "status": "error",
            "reason": str(e),
            "duration": round(time.monotonic() - start, 2),
            "output": "",
        }


def run_command(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to run against"),
    skip: Optional[List[str]] = typer.Option(None, "--skip", help="Steps to skip: generate, lint, benchmark, reflect"),
    benchmark: bool = typer.Option(False, "--benchmark", help="Include benchmark step (skipped by default)"),
    json_output: bool = typer.Option(False, "--json", help="Output summary JSON"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes passed to agentreflect"),
) -> None:
    """Run the full Agent Quality pipeline."""
    root = path or find_project_root()
    cwd_str = str(root)
    skip_set = set(s.lower() for s in (skip or []))

    # Benchmark is opt-in
    if not benchmark:
        skip_set.add("benchmark")

    console.print(f"\n[bold]agentkit run[/bold] — project: {root}\n")

    context_file = root / "CLAUDE.md"
    results = []

    # Step 1: generate
    if "generate" not in skip_set:
        console.print("[dim]→ agentmd generate ...[/dim]")
        r = _run_step("generate", "agentmd", ["generate", cwd_str], cwd_str)
        results.append(r)
    else:
        results.append({"step": "generate", "tool": "agentmd", "status": "skipped", "reason": "user skipped", "duration": 0.0})

    # Step 2: lint context file
    if "lint" not in skip_set:
        lint_args = ["check-context", str(context_file)] if context_file.exists() else ["check-context", cwd_str]
        console.print("[dim]→ agentlint check-context ...[/dim]")
        r = _run_step("lint-context", "agentlint", lint_args, cwd_str)
        results.append(r)

        # Step 3: lint diffs
        console.print("[dim]→ agentlint (diff) ...[/dim]")
        r2 = _run_step("lint-diff", "agentlint", [cwd_str], cwd_str)
        results.append(r2)
    else:
        results.append({"step": "lint-context", "tool": "agentlint", "status": "skipped", "reason": "user skipped", "duration": 0.0})
        results.append({"step": "lint-diff", "tool": "agentlint", "status": "skipped", "reason": "user skipped", "duration": 0.0})

    # Step 4: benchmark (opt-in)
    if "benchmark" not in skip_set:
        console.print("[dim]→ coderace benchmark ...[/dim]")
        r = _run_step("benchmark", "coderace", ["benchmark", cwd_str], cwd_str)
        results.append(r)
    else:
        results.append({"step": "benchmark", "tool": "coderace", "status": "skipped", "reason": "opt-in only (use --benchmark)", "duration": 0.0})

    # Step 5: reflect
    if "reflect" not in skip_set:
        reflect_args = ["generate", "--notes", notes or "agentkit run completed", cwd_str]
        console.print("[dim]→ agentreflect generate ...[/dim]")
        r = _run_step("reflect", "agentreflect", reflect_args, cwd_str)
        results.append(r)
    else:
        results.append({"step": "reflect", "tool": "agentreflect", "status": "skipped", "reason": "user skipped", "duration": 0.0})

    # Display table
    table = Table(title="Pipeline Results", show_header=True)
    table.add_column("Step", style="bold")
    table.add_column("Tool")
    table.add_column("Status")
    table.add_column("Duration")
    table.add_column("Notes", max_width=50)

    status_colors = {"pass": "green", "fail": "red", "skipped": "yellow", "error": "red"}

    for r in results:
        status = r.get("status", "unknown")
        color = status_colors.get(status, "white")
        duration = f"{r.get('duration', 0):.2f}s" if r.get("duration") else ""
        note = r.get("reason", "") or (r.get("output", "")[:60] if r.get("output") else "")
        table.add_row(
            r["step"],
            r.get("tool", ""),
            f"[{color}]{status}[/{color}]",
            duration,
            note,
        )

    console.print()
    console.print(table)

    # Save last run
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": cwd_str,
        "steps": results,
        "total": len(results),
        "passed": sum(1 for r in results if r.get("status") == "pass"),
        "failed": sum(1 for r in results if r.get("status") == "fail"),
        "skipped": sum(1 for r in results if r.get("status") == "skipped"),
    }
    try:
        save_last_run(summary, root)
    except Exception:
        pass

    if json_output:
        console.print("\n[bold]JSON Output:[/bold]")
        print(json.dumps(summary, indent=2))

    # Final status
    if summary["failed"] > 0:
        console.print(f"\n[red]Pipeline completed with {summary['failed']} failure(s).[/red]")
        raise typer.Exit(code=1)
    else:
        console.print(f"\n[green]Pipeline complete.[/green] {summary['passed']} passed, {summary['skipped']} skipped.\n")
