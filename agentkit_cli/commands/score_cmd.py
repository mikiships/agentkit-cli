"""agentkit score command — compute composite agent quality score."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.composite import CompositeScoreEngine, CompositeResult
from agentkit_cli.config import find_project_root, load_last_run
from agentkit_cli.history import get_history

console = Console()


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _get_last_tool_score(project: str, tool: str) -> Optional[float]:
    """Fetch the most recent score for a tool from the history DB."""
    try:
        rows = get_history(project=project, tool=tool, limit=1)
        if rows:
            return float(rows[0]["score"])
    except Exception:
        pass
    return None


def _run_agentlint_fast(cwd: str) -> Optional[float]:
    """Run agentlint check-context fast (no LLM) and parse score."""
    from agentkit_cli.tools import is_installed, run_tool
    if not is_installed("agentlint"):
        return None
    try:
        context_file = Path(cwd) / "CLAUDE.md"
        args = ["check-context", str(context_file)] if context_file.exists() else ["check-context", cwd]
        result = run_tool("agentlint", args + ["--format", "json"], cwd=cwd)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                for key in ("score", "freshness_score", "total_score"):
                    v = data.get(key)
                    if v is not None:
                        return float(v)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
            # Fallback: pass = 100
            return 100.0
        return 0.0
    except Exception:
        return None


def score_command(
    path: Optional[Path],
    json_output: bool,
    breakdown: bool,
    ci: bool,
    min_score: int,
    profile: Optional[str] = None,
) -> None:
    """Compute and display the composite agent quality score."""
    # Apply config defaults
    from agentkit_cli.config import load_config
    from agentkit_cli.profiles import apply_profile
    cfg = load_config(path)
    if profile is not None:
        try:
            apply_profile(profile, cfg, cli_min_score=None if min_score == 70 else float(min_score))
        except ValueError as exc:
            from rich.console import Console as _Console
            _Console().print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=2)
    if min_score == 70 and cfg.gate.min_score is not None:
        min_score = int(cfg.gate.min_score)

    root = (path or find_project_root()).resolve()
    project = root.name

    # Gather tool scores: agentlint runs live; others from history DB
    tool_scores: dict[str, Optional[float]] = {}

    # Live agentlint
    lint_score = _run_agentlint_fast(str(root))
    tool_scores["agentlint"] = lint_score

    # History-based scores
    for tool in ("coderace", "agentmd", "agentreflect"):
        tool_scores[tool] = _get_last_tool_score(project, tool)

    # Optionally include redteam score if context file is present
    from agentkit_cli.redteam_scorer import RedTeamScorer as _RTScorer
    try:
        _rt_scorer = _RTScorer(n_per_category=1)
        _rt_report = _rt_scorer.score_resistance(root)
        if _rt_report.score_overall > 0:
            tool_scores["redteam"] = _rt_report.score_overall
    except Exception:
        pass

    engine = CompositeScoreEngine()

    try:
        result: CompositeResult = engine.compute(tool_scores)
    except ValueError as e:
        if json_output:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)

    score = result.score
    grade = result.grade

    # Load benchmark_result from last run if present
    benchmark_score: Optional[float] = None
    benchmark_winner: Optional[str] = None
    try:
        last_run = load_last_run(root)
        if last_run and "benchmark_result" in last_run:
            bm = last_run["benchmark_result"]
            benchmark_winner = bm.get("winner")
            summary_data = bm.get("summary", {})
            if benchmark_winner and benchmark_winner in summary_data:
                benchmark_score = summary_data[benchmark_winner].get("mean_score")
    except Exception:
        pass

    if json_output:
        out = {
            "score": score,
            "grade": grade,
            "components": result.components,
            "missing_tools": result.missing_tools,
        }
        if benchmark_score is not None:
            out["benchmark_score"] = benchmark_score
            out["benchmark_winner"] = benchmark_winner
        print(json.dumps(out, indent=2))
    else:
        color = _score_color(score)
        console.print()
        console.print(
            f"[bold]Agent Quality Score:[/bold] [{color}]{score:.0f}/100 ({grade})[/{color}]"
            f"  [dim]project: {project}[/dim]"
        )

        if breakdown:
            table = Table(title="Score Breakdown", show_header=True)
            table.add_column("Component", style="bold")
            table.add_column("Raw Score", justify="right")
            table.add_column("Weight", justify="right")
            table.add_column("Contribution", justify="right")

            for tool, data in sorted(result.components.items()):
                raw = data["raw_score"]
                weight = data["weight"]
                contribution = data["contribution"]
                raw_color = _score_color(raw)
                table.add_row(
                    tool,
                    f"[{raw_color}]{raw:.1f}[/{raw_color}]",
                    f"{weight * 100:.1f}%",
                    f"{contribution:.1f}",
                )

            console.print()
            console.print(table)

        if result.missing_tools:
            console.print(
                f"\n[dim]Missing tools (excluded from score): {', '.join(result.missing_tools)}[/dim]"
            )

        if benchmark_score is not None:
            bm_color = _score_color(benchmark_score)
            console.print(
                f"[dim]Benchmark score (winner: {benchmark_winner}):[/dim] "
                f"[{bm_color}]{benchmark_score:.0f}/100[/{bm_color}]"
            )

        # Harden recommendation: if redteam score is below 70
        try:
            rt_score = tool_scores.get("redteam")
            if rt_score is not None and rt_score < 70:
                estimated_lift = min(30, int((70 - rt_score) * 0.5))
                console.print(
                    f"\n[yellow]Security:[/yellow] Run [bold]`agentkit harden`[/bold] to improve "
                    f"security posture (+{estimated_lift} pts estimated). "
                    f"Current redteam score: {rt_score:.0f}/100."
                )
        except Exception:
            pass
        console.print()

    if ci and score < min_score:
        if not json_output:
            console.print(
                f"[red]CI gate failed: score {score:.0f} < min-score {min_score}[/red]"
            )
        raise typer.Exit(code=1)
