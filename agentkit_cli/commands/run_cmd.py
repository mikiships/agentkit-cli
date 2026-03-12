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
    ci: bool = typer.Option(False, "--ci", help="CI mode: plain output, exit 1 on any failure"),
) -> None:
    """Run the full Agent Quality pipeline."""
    root = path or find_project_root()
    cwd_str = str(root)
    skip_set = set(s.lower() for s in (skip or []))

    # Benchmark is opt-in
    if not benchmark:
        skip_set.add("benchmark")

    # In CI mode, use a plain console (no Rich markup/spinners)
    ci_console = Console(highlight=False, markup=False) if ci else None
    active_console = ci_console if ci else console

    active_console.print(f"\nagentkit run — project: {root}\n" if ci else f"\n[bold]agentkit run[/bold] — project: {root}\n")

    context_file = root / "CLAUDE.md"
    results = []

    def _print(msg: str) -> None:
        if ci:
            # Strip Rich markup for CI plain output
            import re
            plain = re.sub(r'\[/?[^\]]+\]', '', msg)
            active_console.print(plain)
        else:
            active_console.print(msg)

    # Step 1: generate
    if "generate" not in skip_set:
        _print("[dim]→ agentmd generate ...[/dim]")
        r = _run_step("generate", "agentmd", ["generate", cwd_str], cwd_str)
        results.append(r)
    else:
        results.append({"step": "generate", "tool": "agentmd", "status": "skipped", "reason": "user skipped", "duration": 0.0})

    # Step 2: lint context file
    if "lint" not in skip_set:
        lint_args = ["check-context", str(context_file)] if context_file.exists() else ["check-context", cwd_str]
        _print("[dim]→ agentlint check-context ...[/dim]")
        r = _run_step("lint-context", "agentlint", lint_args, cwd_str)
        results.append(r)

        # Step 3: lint diffs
        _print("[dim]→ agentlint (diff) ...[/dim]")
        r2 = _run_step("lint-diff", "agentlint", ["check", "HEAD~1"], cwd_str)
        results.append(r2)
    else:
        results.append({"step": "lint-context", "tool": "agentlint", "status": "skipped", "reason": "user skipped", "duration": 0.0})
        results.append({"step": "lint-diff", "tool": "agentlint", "status": "skipped", "reason": "user skipped", "duration": 0.0})

    # Step 4: benchmark (opt-in)
    if "benchmark" not in skip_set:
        _print("[dim]→ coderace benchmark ...[/dim]")
        r = _run_step("benchmark", "coderace", ["benchmark", cwd_str], cwd_str)
        results.append(r)
    else:
        results.append({"step": "benchmark", "tool": "coderace", "status": "skipped", "reason": "opt-in only (use --benchmark)", "duration": 0.0})

    # Step 5: reflect
    if "reflect" not in skip_set:
        reflect_args = ["generate", "--from-notes", notes or "agentkit run completed"]
        _print("[dim]→ agentreflect generate ...[/dim]")
        r = _run_step("reflect", "agentreflect", reflect_args, cwd_str)
        results.append(r)
    else:
        results.append({"step": "reflect", "tool": "agentreflect", "status": "skipped", "reason": "user skipped", "duration": 0.0})

    # Build summary counts
    passed_count = sum(1 for r in results if r.get("status") == "pass")
    failed_count = sum(1 for r in results if r.get("status") == "fail")
    skipped_count = sum(1 for r in results if r.get("status") in ("skipped", "error"))
    total_count = len(results)

    # Display summary table
    STATUS_SYMBOLS = {
        "pass": ("✓ PASS", "green"),
        "fail": ("✗ FAIL", "red"),
        "skipped": ("⊘ SKIPPED", "yellow"),
        "error": ("✗ ERROR", "red"),
    }

    if ci:
        # Plain text summary for CI logs
        active_console.print("\nPipeline Summary:")
        for r in results:
            status = r.get("status", "unknown")
            symbol = STATUS_SYMBOLS.get(status, (status, "white"))[0]
            duration_s = r.get("duration", 0.0) or 0.0
            duration = f" ({duration_s:.2f}s)" if duration_s else ""
            active_console.print(f"  {r['step']:20s}  {symbol}{duration}")
    else:
        table = Table(title="Pipeline Summary", show_header=True)
        table.add_column("Step", style="bold")
        table.add_column("Status")
        table.add_column("Duration")
        table.add_column("Notes", max_width=60)

        for r in results:
            status = r.get("status", "unknown")
            symbol, color = STATUS_SYMBOLS.get(status, (status, "white"))
            duration_s = r.get("duration", 0.0) or 0.0
            duration = f"{duration_s:.2f}s" if duration_s else ""
            note = r.get("reason", "") or (r.get("output", "")[:60] if r.get("output") else "")
            table.add_row(
                r["step"],
                f"[{color}]{symbol}[/{color}]",
                duration,
                note,
            )

        console.print()
        console.print(table)

    active_console.print(f"\n{passed_count}/{total_count} steps passed" if ci else f"\n[bold]{passed_count}/{total_count} steps passed[/bold]")

    # Build structured step summaries
    # New contract format: {name, status, duration_ms, output_file}
    steps_new = [
        {
            "name": r["step"],
            "status": r.get("status", "unknown"),
            "duration_ms": int((r.get("duration", 0.0) or 0.0) * 1000),
            "output_file": None,
        }
        for r in results
    ]
    # Legacy format preserved for backwards compat
    steps_legacy = [
        {
            "step": r["step"],
            "status": r.get("status", "unknown"),
            "duration": r.get("duration", 0.0),
            "notes": r.get("reason", "") or (r.get("output", "")[:60] if r.get("output") else ""),
        }
        for r in results
    ]
    summary = {
        "success": failed_count == 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": cwd_str,
        # `steps` satisfies both old tests (list) and new contract format
        "steps": steps_new,
        "summary": {
            "steps": steps_legacy,
            "total": total_count,
            "passed": passed_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "result": "pass" if failed_count == 0 else "fail",
        },
        "total": total_count,
        "passed": passed_count,
        "failed": failed_count,
        "skipped": skipped_count,
    }
    try:
        save_last_run(summary, root)
    except Exception:
        pass

    if json_output:
        print(json.dumps(summary, indent=2))

    # Final status
    if failed_count > 0:
        if ci:
            active_console.print(f"\nPipeline completed with {failed_count} failure(s).")
        else:
            console.print(f"\n[red]Pipeline completed with {failed_count} failure(s).[/red]")
        raise typer.Exit(code=1)
    else:
        if ci:
            active_console.print(f"\nPipeline complete. {passed_count} passed, {skipped_count} skipped.\n")
        else:
            console.print(f"\n[green]Pipeline complete.[/green] {passed_count} passed, {skipped_count} skipped.\n")
