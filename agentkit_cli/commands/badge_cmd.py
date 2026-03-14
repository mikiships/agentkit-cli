"""agentkit badge command — generate shields.io-compatible README badge."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import typer
from rich.console import Console

from agentkit_cli.report_runner import (
    run_agentlint_check,
    run_agentmd_score,
    run_agentreflect_analyze,
    run_coderace_bench,
)
from agentkit_cli.composite import CompositeScoreEngine

console = Console()

# ---------------------------------------------------------------------------
# Badge helpers
# ---------------------------------------------------------------------------

SHIELDS_BASE = "https://img.shields.io/badge"


def score_to_color(score: int) -> str:
    """Map score to shields.io color name."""
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    if score >= 40:
        return "orange"
    return "red"


def build_badge_url(score: int) -> str:
    """Build shields.io static badge URL for the given score."""
    color = score_to_color(score)
    label = quote("agent quality", safe="")
    message = quote(f"{score}/100", safe="")
    return f"{SHIELDS_BASE}/{label}-{message}-{color}"


def build_markdown(badge_url: str, link_url: str = "https://github.com/mikiships/agentkit-cli") -> str:
    return f"[![agent quality]({badge_url})]({link_url})"


def build_html_snippet(badge_url: str, link_url: str = "https://github.com/mikiships/agentkit-cli") -> str:
    return f'<a href="{link_url}"><img src="{badge_url}" alt="agent quality"></a>'


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def _extract_agentlint_score(data: Optional[dict]) -> Optional[float]:
    if data is None:
        return None
    for key in ("score", "freshness_score", "total_score"):
        v = data.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def _extract_agentmd_score(data) -> Optional[float]:
    if data is None:
        return None
    if isinstance(data, list):
        if not data:
            return None
        scores = [d.get("score") or d.get("total_score") or 0 for d in data if isinstance(d, dict)]
        return round(sum(scores) / len(scores), 1) if scores else None
    for key in ("score", "total_score"):
        v = data.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return None


def _extract_coderace_score(data: Optional[dict]) -> Optional[float]:
    if data is None:
        return None
    results = data.get("results") or data.get("agents") or []
    if not results:
        return None
    scores = []
    for r in results:
        if isinstance(r, dict):
            s = r.get("score")
            if s is not None:
                try:
                    scores.append(float(s))
                except (TypeError, ValueError):
                    pass
    return max(scores) if scores else None


def compute_badge_score(path: str, tool: Optional[str] = None) -> dict:
    """Compute badge score.

    If tool is specified, returns that tool's score only.
    Otherwise computes composite score using CompositeScoreEngine.

    Returns dict with keys: score (int), sources (list), raw_scores (dict).
    """
    raw = {
        "agentlint": run_agentlint_check(path),
        "agentmd": run_agentmd_score(path),
        "coderace": run_coderace_bench(path),
        "agentreflect": run_agentreflect_analyze(path),
    }

    component_scores: dict[str, float] = {}

    lint_score = _extract_agentlint_score(raw["agentlint"])
    if lint_score is not None:
        component_scores["agentlint"] = min(100.0, max(0.0, lint_score))

    md_score = _extract_agentmd_score(raw["agentmd"])
    if md_score is not None:
        component_scores["agentmd"] = min(100.0, max(0.0, md_score))

    cr_score = _extract_coderace_score(raw["coderace"])
    if cr_score is not None:
        component_scores["coderace"] = min(100.0, max(0.0, cr_score))

    ar_data = raw.get("agentreflect")
    if ar_data is not None:
        ar_score = None
        if isinstance(ar_data, dict):
            for key in ("score", "total_score"):
                v = ar_data.get(key)
                if v is not None:
                    try:
                        ar_score = float(v)
                        break
                    except (TypeError, ValueError):
                        pass
        if ar_score is not None:
            component_scores["agentreflect"] = min(100.0, max(0.0, ar_score))

    if tool is not None:
        # Single-tool mode
        if tool in component_scores:
            final_score = int(round(component_scores[tool]))
        else:
            final_score = 0
        return {
            "score": final_score,
            "sources": [tool] if tool in component_scores else [],
            "raw_scores": component_scores,
            "mode": "single",
            "tool": tool,
        }

    # Composite score (default)
    if component_scores:
        tool_scores_input = {t: component_scores.get(t) for t in ("coderace", "agentlint", "agentmd", "agentreflect")}
        engine = CompositeScoreEngine()
        try:
            comp = engine.compute(tool_scores_input)
            final_score = int(round(comp.score))
            sources = list(comp.components.keys())
        except ValueError:
            avg = sum(component_scores.values()) / len(component_scores)
            final_score = int(round(avg))
            sources = list(component_scores.keys())
    else:
        final_score = 0
        sources = []

    return {
        "score": final_score,
        "sources": sources,
        "raw_scores": component_scores,
        "mode": "composite",
    }


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

def badge_command(
    path: Optional[Path],
    json_output: bool,
    score_override: Optional[int],
    tool: Optional[str] = None,
) -> None:
    """Generate a shields.io badge showing the project's agent quality score."""
    cwd = (path or Path.cwd()).resolve()

    if score_override is not None:
        score = max(0, min(100, score_override))
        sources: list[str] = ["override"]
    else:
        if not json_output:
            mode_str = f"single-tool ({tool})" if tool else "composite"
            console.print(f"\n[dim]Computing agent quality score ({mode_str})...[/dim]")
        result = compute_badge_score(str(cwd), tool=tool)
        score = result["score"]
        sources = result["sources"]

    color = score_to_color(score)
    badge_url = build_badge_url(score)
    md = build_markdown(badge_url)
    html = build_html_snippet(badge_url)

    if json_output:
        out = {
            "score": score,
            "color": color,
            "badge_url": badge_url,
            "markdown": md,
            "html": html,
            "sources": sources,
        }
        print(json.dumps(out, indent=2))
        return

    console.print()
    console.print(f"[bold]Agent Quality Score:[/bold] [{color}]{score}/100[/{color}]  (color: {color})")
    console.print()
    console.print(f"[bold]Badge URL:[/bold]")
    console.print(f"  {badge_url}")
    console.print()
    console.print(f"[bold]Markdown:[/bold]")
    console.print(f"  {md}")
    console.print()
    console.print(f"[bold]HTML:[/bold]")
    console.print(f"  {html}")
    if sources:
        console.print()
        console.print(f"[dim]Score sources: {', '.join(sources)}[/dim]")
    console.print()
