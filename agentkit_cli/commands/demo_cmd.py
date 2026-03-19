"""agentkit demo command — zero-config first-run experience."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentkit_cli.tools import is_installed, run_tool

console = Console()


# ---------------------------------------------------------------------------
# Project detection
# ---------------------------------------------------------------------------

def detect_project_type(path: Path) -> str:
    """Detect project type from directory contents."""
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists() or (path / "requirements.txt").exists():
        return "python"
    if (path / "tsconfig.json").exists():
        return "typescript"
    if (path / "package.json").exists():
        return "javascript"
    return "generic"


def pick_demo_task(project_type: str) -> str:
    """Return the best built-in coderace task for the project type."""
    if project_type in ("typescript", "javascript"):
        return "refactor"
    return "bug-hunt"


# ---------------------------------------------------------------------------
# Agent detection
# ---------------------------------------------------------------------------

def detect_available_agents() -> list[str]:
    """Return list of AI agent binaries available in PATH."""
    agents = []
    for name in ("claude", "codex"):
        if shutil.which(name) is not None:
            agents.append(name)
    return agents


# ---------------------------------------------------------------------------
# Step runner (thin wrapper so tests can mock easily)
# ---------------------------------------------------------------------------

def _run_pipeline_step(tool: str, args: list[str], cwd: str) -> dict:
    """Run one pipeline step; return result dict."""
    start = time.monotonic()
    if not is_installed(tool):
        return {
            "tool": tool,
            "status": "skipped",
            "reason": f"{tool} not installed",
            "duration": 0.0,
            "output": "",
        }
    try:
        result = run_tool(tool, args, cwd=cwd)
        duration = time.monotonic() - start
        success = result.returncode == 0
        return {
            "tool": tool,
            "status": "pass" if success else "fail",
            "returncode": result.returncode,
            "duration": round(duration, 2),
            "output": (result.stdout + result.stderr).strip(),
        }
    except Exception as exc:
        return {
            "tool": tool,
            "status": "error",
            "reason": str(exc),
            "duration": round(time.monotonic() - start, 2),
            "output": "",
        }


def _run_benchmark_step(agent: str, task: str, cwd: str) -> dict:
    """Run coderace benchmark for a single agent; return result dict."""
    start = time.monotonic()
    if not is_installed("coderace"):
        return {
            "agent": agent,
            "task": task,
            "status": "skipped",
            "reason": "coderace not installed",
            "score": None,
            "duration": 0.0,
        }
    try:
        result = run_tool("coderace", ["benchmark", "--agent", agent, "--task", task, cwd], cwd=cwd)
        duration = time.monotonic() - start
        success = result.returncode == 0
        # Try to parse score from output (coderace may emit "score: N")
        score = None
        for line in (result.stdout + result.stderr).splitlines():
            if "score" in line.lower():
                parts = line.split()
                for p in parts:
                    try:
                        score = int(p)
                        break
                    except ValueError:
                        continue
        return {
            "agent": agent,
            "task": task,
            "status": "pass" if success else "fail",
            "score": score,
            "duration": round(duration, 2),
            "output": (result.stdout + result.stderr).strip(),
        }
    except Exception as exc:
        return {
            "agent": agent,
            "task": task,
            "status": "error",
            "reason": str(exc),
            "score": None,
            "duration": round(time.monotonic() - start, 2),
        }


# ---------------------------------------------------------------------------
# Demo record command
# ---------------------------------------------------------------------------

_DEMO_TAPE_CONTENT = """\
# demo.tape — VHS terminal recording for agentkit-cli
# Run with: vhs demo.tape
# Install VHS: brew install charmbracelet/tap/vhs

Output demo.gif

Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Dracula"

Type "pip install agentkit-cli" Sleep 500ms Enter
Sleep 2s

Type "agentkit quickstart" Sleep 500ms Enter
Sleep 15s

Type "agentkit run ." Sleep 500ms Enter
Sleep 10s

Type "agentkit benchmark" Sleep 500ms Enter
Sleep 8s
"""


def demo_record_command(output: Optional[str] = None) -> None:
    """Print VHS tape instructions for a terminal recording session."""
    tape_path = Path(output) if output else Path.cwd() / "demo.tape"

    console.print()
    console.print(Panel(
        "[bold cyan]agentkit demo --record[/bold cyan]\n"
        "[dim]Generates a VHS tape for terminal demo recording.[/dim]",
        border_style="cyan",
        expand=False,
    ))
    console.print()
    console.print(f"[bold]Writing VHS tape to:[/bold] {tape_path}")
    tape_path.write_text(_DEMO_TAPE_CONTENT)
    console.print(f"[green]✓[/green] {tape_path} created")
    console.print()
    console.print("[bold]To record the demo:[/bold]")
    console.print("  [dim]1. Install VHS:[/dim]  [cyan]brew install charmbracelet/tap/vhs[/cyan]")
    console.print("  [dim]2. Record:[/dim]        [cyan]vhs demo.tape[/cyan]")
    console.print("  [dim]3. Output:[/dim]        [cyan]demo.gif[/cyan] (place in README or docs/)")
    console.print()
    console.print("[bold]Alternatively with asciinema:[/bold]")
    console.print("  [dim]1. Install:[/dim]   [cyan]pip install asciinema[/cyan]")
    console.print("  [dim]2. Record:[/dim]    [cyan]asciinema rec demo.cast[/cyan]")
    console.print("  [dim]3. Play:[/dim]      [cyan]asciinema play demo.cast[/cyan]")
    console.print()
    console.print("[dim]VHS tape contents:[/dim]")
    console.print()
    for line in _DEMO_TAPE_CONTENT.splitlines():
        if line.startswith("#"):
            console.print(f"  [dim]{line}[/dim]")
        elif line:
            console.print(f"  [cyan]{line}[/cyan]")
        else:
            console.print()


# ---------------------------------------------------------------------------
# Main demo command
# ---------------------------------------------------------------------------

def demo_command(
    task: Optional[str] = None,
    agents: Optional[str] = None,
    skip_benchmark: bool = False,
    json_output: bool = False,
    record: bool = False,
    record_output: Optional[str] = None,
) -> None:
    """Zero-config first-run demo of the Agent Quality Toolkit."""
    if record:
        demo_record_command(output=record_output)
        return

    cwd = Path.cwd()

    # --- Header ---
    if not json_output:
        console.print()
        console.print(Panel(
            "[bold cyan]agentkit demo[/bold cyan] — Agent Quality Toolkit",
            border_style="cyan",
        ))

    # --- Project detection ---
    project_type = detect_project_type(cwd)
    selected_task = task or pick_demo_task(project_type)

    if not json_output:
        console.print(f"\n[bold]Detected project type:[/bold] {project_type}")
        console.print(f"[bold]Selected task:[/bold]         {selected_task}")

    # --- Agent detection ---
    if agents:
        agent_list = [a.strip() for a in agents.split(",") if a.strip()]
    else:
        agent_list = detect_available_agents()

    if not json_output:
        if agent_list:
            console.print(f"[bold]Agents found:[/bold]          {', '.join(agent_list)}")
        else:
            console.print(
                "\n[yellow]No agents found. Install Claude Code or Codex to enable benchmarking. "
                "Running pipeline without benchmark step...[/yellow]"
            )

    # --- Pipeline steps ---
    steps: list[dict] = []

    # generate
    if not json_output:
        console.print("\n[dim]→ agentmd generate ...[/dim]")
    r = _run_pipeline_step("agentmd", ["generate", str(cwd)], str(cwd))
    r["step"] = "generate"
    steps.append(r)

    # lint
    if not json_output:
        console.print("[dim]→ agentlint check-context ...[/dim]")
    context_file = cwd / "CLAUDE.md"
    lint_args = ["check-context", str(context_file)] if context_file.exists() else ["check-context", str(cwd)]
    r = _run_pipeline_step("agentlint", lint_args, str(cwd))
    r["step"] = "lint"
    steps.append(r)

    # reflect
    if not json_output:
        console.print("[dim]→ agentreflect generate ...[/dim]")
    r = _run_pipeline_step("agentreflect", ["generate", "--from-notes", "agentkit demo run"], str(cwd))
    r["step"] = "reflect"
    steps.append(r)

    # --- Benchmark ---
    benchmark_results: list[dict] = []
    if not skip_benchmark and agent_list:
        if not json_output:
            console.print(f"\n[dim]→ coderace benchmark ({', '.join(agent_list)}) ...[/dim]")
        for agent in agent_list:
            br = _run_benchmark_step(agent, selected_task, str(cwd))
            benchmark_results.append(br)

    # --- Rich output: pipeline summary table ---
    STATUS_SYMBOLS = {
        "pass": ("✓", "green"),
        "fail": ("✗", "red"),
        "skipped": ("⊘", "yellow"),
        "error": ("✗", "red"),
    }

    if not json_output:
        console.print()
        table = Table(title="Pipeline Steps", show_header=True)
        table.add_column("Step", style="bold")
        table.add_column("Status")
        table.add_column("Duration")

        for s in steps:
            status = s.get("status", "unknown")
            symbol, color = STATUS_SYMBOLS.get(status, (status, "white"))
            dur = s.get("duration", 0.0) or 0.0
            table.add_row(
                s.get("step", s.get("tool", "?")),
                f"[{color}]{symbol}[/{color}]",
                f"{dur:.2f}s" if dur else "",
            )
        console.print(table)

        # Benchmark table
        if benchmark_results:
            console.print()
            bt = Table(title="Benchmark Results", show_header=True)
            bt.add_column("Agent", style="bold")
            bt.add_column("Task")
            bt.add_column("Score")
            bt.add_column("Duration")

            best_score: Optional[int] = None
            for br in benchmark_results:
                sc = br.get("score")
                if sc is not None:
                    if best_score is None or sc > best_score:
                        best_score = sc

            for br in benchmark_results:
                sc = br.get("score")
                sc_str = str(sc) if sc is not None else "—"
                dur = br.get("duration", 0.0) or 0.0
                is_best = sc is not None and sc == best_score and best_score is not None
                agent_str = f"[green]{br['agent']}[/green]" if is_best else br["agent"]
                bt.add_row(agent_str, br["task"], sc_str, f"{dur:.2f}s" if dur else "")
            console.print(bt)

        # Footer hint
        console.print()
        console.print("[dim]Run [bold]agentkit init && agentkit run[/bold] to set up for your full project[/dim]")
        console.print()

    # --- JSON output ---
    if json_output:
        output = {
            "project_type": project_type,
            "task": selected_task,
            "agents": agent_list,
            "steps": [
                {
                    "step": s.get("step", s.get("tool")),
                    "status": s.get("status"),
                    "duration": s.get("duration"),
                }
                for s in steps
            ],
            "benchmark": benchmark_results,
        }
        print(json.dumps(output, indent=2))
