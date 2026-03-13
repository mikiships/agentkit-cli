"""agentkit compare — diff agent quality scores between two git refs."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import box

from agentkit_cli.tools import is_installed, INSTALL_HINTS
from agentkit_cli.utils.git_utils import Worktree, git_root, changed_files, GitError, resolve_ref

console = Console()

# Quartet tools and the CLI invocations that produce a numeric score on stdout/stderr.
# Each returns a score 0–100.  We capture and parse the output.
SCORE_TOOLS = {
    "agentlint": ["check-context", "{context_file}"],
    "agentreflect": ["score", "--path", "{cwd}"],
    "coderace": ["score", "{cwd}"],
    "agentmd": ["score", "{cwd}"],
}

IMPROVED_THRESHOLD = 5
DEGRADED_THRESHOLD = -5


def _extract_score(output: str) -> Optional[float]:
    """Parse a numeric score (0-100) from tool output.

    Tries several common patterns:
      - JSON key 'score'
      - 'Score: N' / 'score: N'
      - A bare float/int on its own line
    """
    # Try JSON first
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                data = json.loads(line)
                if "score" in data:
                    return float(data["score"])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
    try:
        data = json.loads(output)
        if isinstance(data, dict) and "score" in data:
            return float(data["score"])
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    import re
    # score: N or Score: N
    m = re.search(r"\bscore[:\s]+([0-9]+(?:\.[0-9]+)?)", output, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # Last resort: a standalone number on its own line
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        try:
            val = float(stripped)
            if 0 <= val <= 100:
                return val
        except ValueError:
            pass
    return None


def _run_tool_for_score(tool: str, cwd: Path) -> dict:
    """Run a quartet tool against a worktree directory, return score dict."""
    if not is_installed(tool):
        return {
            "tool": tool,
            "status": "skipped",
            "reason": f"not installed — {INSTALL_HINTS.get(tool, f'pip install {tool}')}",
            "score": None,
        }

    context_file = cwd / "CLAUDE.md"
    args_template = SCORE_TOOLS[tool]
    args = [
        a.replace("{cwd}", str(cwd)).replace("{context_file}", str(context_file))
        for a in args_template
    ]

    import shutil
    tool_path = shutil.which(tool)
    if not tool_path:
        return {"tool": tool, "status": "skipped", "reason": "not found in PATH", "score": None}

    start = time.monotonic()
    try:
        result = subprocess.run(
            [tool_path] + args,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=120,
        )
        duration = round(time.monotonic() - start, 2)
        output = (result.stdout + result.stderr).strip()
        score = _extract_score(output)
        return {
            "tool": tool,
            "status": "ok" if result.returncode == 0 else "error",
            "score": score,
            "duration": duration,
            "output": output[:500],
        }
    except subprocess.TimeoutExpired:
        return {"tool": tool, "status": "timeout", "score": None, "reason": "timed out after 120s"}
    except Exception as e:
        return {"tool": tool, "status": "error", "score": None, "reason": str(e)}


def _score_ref(ref: str, tools: list[str], repo_root: Path) -> dict[str, dict]:
    """Check out ref via worktree, run all tools, return {tool: result}."""
    results: dict[str, dict] = {}
    try:
        with Worktree(ref, repo_root) as wt_path:
            for tool in tools:
                results[tool] = _run_tool_for_score(tool, wt_path)
    except GitError as e:
        for tool in tools:
            results[tool] = {"tool": tool, "status": "error", "score": None, "reason": str(e)}
    return results


def _compute_verdict(net_delta: Optional[float]) -> str:
    if net_delta is None:
        return "NEUTRAL"
    if net_delta > IMPROVED_THRESHOLD:
        return "IMPROVED"
    if net_delta < DEGRADED_THRESHOLD:
        return "DEGRADED"
    return "NEUTRAL"


def compare_command(
    ref1: str = typer.Argument("HEAD~1", help="Base ref (older)"),
    ref2: str = typer.Argument("HEAD", help="Head ref (newer)"),
    tools: Optional[List[str]] = typer.Option(
        None, "--tools", help="Comma-separated tools to compare (default: all quartet)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON"),
    quiet: bool = typer.Option(False, "--quiet", help="Only print IMPROVED/NEUTRAL/DEGRADED verdict"),
    ci_mode: bool = typer.Option(False, "--ci", help="Exit 1 if verdict is DEGRADED"),
    min_delta: Optional[float] = typer.Option(
        None, "--min-delta", help="Fail if net delta is below this value (CI mode)"
    ),
    files: bool = typer.Option(False, "--files", help="Show per-file score breakdown"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory (default: git root)"),
) -> None:
    """Compare agent quality scores between two git refs."""
    # Resolve project root
    try:
        repo_root = git_root(str(path) if path else None)
    except GitError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # Resolve tool list
    active_tools = list(SCORE_TOOLS.keys())
    if tools:
        # Support comma-separated or repeated flag
        flat: list[str] = []
        for t in tools:
            flat.extend(x.strip() for x in t.split(",") if x.strip())
        unknown = [t for t in flat if t not in SCORE_TOOLS]
        if unknown:
            console.print(f"[yellow]Warning:[/yellow] Unknown tools ignored: {', '.join(unknown)}")
        active_tools = [t for t in flat if t in SCORE_TOOLS] or active_tools

    if not quiet and not json_output:
        console.print(f"\n[bold]agentkit compare[/bold]  {ref1} → {ref2}\n")

    # Score both refs
    scores_ref1 = _score_ref(ref1, active_tools, repo_root)
    scores_ref2 = _score_ref(ref2, active_tools, repo_root)

    # Compute deltas
    deltas: list[dict] = []
    numeric_deltas: list[float] = []
    for tool in active_tools:
        r1 = scores_ref1[tool]
        r2 = scores_ref2[tool]
        s1 = r1.get("score")
        s2 = r2.get("score")
        if s1 is not None and s2 is not None:
            delta = s2 - s1
            numeric_deltas.append(delta)
        else:
            delta = None
        deltas.append({"tool": tool, "score_ref1": s1, "score_ref2": s2, "delta": delta})

    net_delta = (sum(numeric_deltas) / len(numeric_deltas)) if numeric_deltas else None
    verdict = _compute_verdict(net_delta)

    # --files: changed file list
    changed: list[str] = []
    if files:
        try:
            changed = changed_files(ref1, ref2, cwd=str(repo_root))
        except Exception:
            changed = []

    # Build output
    if quiet:
        typer.echo(verdict)
    elif json_output:
        output = {
            "ref1": ref1,
            "ref2": ref2,
            "verdict": verdict,
            "net_delta": round(net_delta, 2) if net_delta is not None else None,
            "tools": deltas,
        }
        if files:
            output["changed_files"] = changed
        print(json.dumps(output, indent=2))
    else:
        # Rich table
        table = Table(title=f"Score Comparison: {ref1} → {ref2}", box=box.ROUNDED, show_header=True)
        table.add_column("Tool", style="bold")
        table.add_column(f"{ref1}", justify="right")
        table.add_column(f"{ref2}", justify="right")
        table.add_column("Δ Delta", justify="right")

        for d in deltas:
            s1 = f"{d['score_ref1']:.1f}" if d["score_ref1"] is not None else "N/A"
            s2 = f"{d['score_ref2']:.1f}" if d["score_ref2"] is not None else "N/A"
            if d["delta"] is None:
                delta_str = "[yellow]N/A[/yellow]"
            elif d["delta"] > 0:
                delta_str = f"[green]+{d['delta']:.1f}[/green]"
            elif d["delta"] < 0:
                delta_str = f"[red]{d['delta']:.1f}[/red]"
            else:
                delta_str = "[dim]0.0[/dim]"
            table.add_row(d["tool"], s1, s2, delta_str)

        console.print(table)

        if net_delta is not None:
            net_str = f"{net_delta:+.1f}"
            color = "green" if net_delta > IMPROVED_THRESHOLD else ("red" if net_delta < DEGRADED_THRESHOLD else "yellow")
            console.print(f"\nNet delta: [{color}]{net_str}[/{color}]")
        else:
            console.print("\n[yellow]Net delta: N/A (no scores available)[/yellow]")

        verdict_color = {"IMPROVED": "green", "NEUTRAL": "yellow", "DEGRADED": "red"}[verdict]
        console.print(f"Verdict:   [{verdict_color}]{verdict}[/{verdict_color}]\n")

        if files and changed:
            console.print(f"[dim]Changed files ({len(changed)}):[/dim]")
            for f in changed[:20]:
                console.print(f"  [dim]{f}[/dim]")
            if len(changed) > 20:
                console.print(f"  [dim]... and {len(changed) - 20} more[/dim]")

    # CI exit code logic
    effective_min_delta = min_delta if min_delta is not None else (0.0 if ci_mode else None)
    if ci_mode or min_delta is not None:
        failed = False
        if verdict == "DEGRADED":
            failed = True
        if effective_min_delta is not None and net_delta is not None and net_delta < effective_min_delta:
            failed = True
        if failed:
            raise typer.Exit(code=1)
