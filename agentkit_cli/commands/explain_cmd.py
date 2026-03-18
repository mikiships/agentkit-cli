"""agentkit explain command — LLM-powered coaching report."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agentkit_cli.explain import ExplainEngine, _extract_composite, _score_tier

console = Console()


def _parse_sections(markdown: str) -> dict:
    """Parse the four coaching sections from LLM/template markdown output."""
    sections = {
        "what_this_score_means": "",
        "key_findings_explained": "",
        "top_3_next_steps": "",
        "if_you_do_nothing_else": "",
    }
    # Map heading text → key
    heading_map = {
        "what this score means": "what_this_score_means",
        "key findings explained": "key_findings_explained",
        "top 3 next steps": "top_3_next_steps",
        "if you do nothing else": "if_you_do_nothing_else",
    }
    current_key: Optional[str] = None
    buf: list[str] = []

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("# "):
            # Save previous section
            if current_key:
                sections[current_key] = "\n".join(buf).strip()
            # Find new key
            heading = stripped.lstrip("# ").strip().lower()
            current_key = heading_map.get(heading)
            buf = []
        else:
            buf.append(line)

    if current_key:
        sections[current_key] = "\n".join(buf).strip()

    return sections


def _extract_recommendations(next_steps_text: str) -> list[str]:
    """Extract numbered recommendations from the top-3-next-steps section."""
    recs: list[str] = []
    for line in next_steps_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Match "1. text" or "- text"
        if line[0].isdigit() and len(line) > 2 and line[1] in ".):":
            recs.append(line[2:].strip())
        elif line.startswith("- "):
            recs.append(line[2:].strip())
        elif line.startswith("* "):
            recs.append(line[2:].strip())
    return recs


def explain_command(
    path: Optional[Path] = None,
    report_path: Optional[str] = None,
    model: str = "claude-3-5-haiku-20241022",
    no_llm: bool = False,
    json_output: bool = False,
    output: Optional[Path] = None,
) -> None:
    """Run agentkit explain: produce a coaching report for a project or report JSON."""

    engine = ExplainEngine(model=model)

    # ------------------------------------------------------------------ Load report
    if report_path:
        try:
            report = engine.load_report(report_path)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Report file not found: {report_path}")
            raise typer.Exit(code=1)
        except (json.JSONDecodeError, ValueError) as exc:
            console.print(f"[red]Error:[/red] Invalid report JSON: {exc}")
            raise typer.Exit(code=1)
    else:
        # Run agentkit run inline to generate the report
        root = Path(path).resolve() if path else Path.cwd()
        try:
            from agentkit_cli.commands.run_cmd import run_command as _run_command
            import io
            from contextlib import redirect_stdout

            # Capture JSON output from run
            captured = io.StringIO()
            # We run with a custom import trick to get the summary dict
            report = _inline_run(root)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Could not run analysis: {exc}")
            raise typer.Exit(code=1)

    # ------------------------------------------------------------------ Generate explanation
    if no_llm:
        explanation = engine.template_explain(report)
    else:
        explanation = engine.explain(report)

    # ------------------------------------------------------------------ Parse sections
    sections = _parse_sections(explanation)
    composite = _extract_composite(report)
    tier = _score_tier(composite)
    project = report.get("project", str(path or Path.cwd()))

    # ------------------------------------------------------------------ JSON output
    if json_output:
        recs = _extract_recommendations(sections.get("top_3_next_steps", ""))
        one_thing = sections.get("if_you_do_nothing_else", "")
        out = {
            "project": project,
            "score": composite,
            "tier": tier,
            "explanation": explanation,
            "recommendations": recs,
            "one_thing": one_thing,
        }
        print(json.dumps(out, indent=2))
        if output:
            output.write_text(explanation, encoding="utf-8")
        return

    # ------------------------------------------------------------------ Rich console output
    console.print()
    console.print(
        Panel(
            f"[bold]Score:[/bold] {int(round(composite))}/100  [bold]Tier:[/bold] {tier}  "
            f"[bold]Project:[/bold] {project}",
            title="[bold cyan]agentkit explain[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()
    console.print(Markdown(explanation))
    console.print()

    # ------------------------------------------------------------------ Write to file
    if output:
        output.write_text(explanation, encoding="utf-8")
        console.print(f"[dim]Coaching report written to {output}[/dim]")


def _inline_run(root: Path) -> dict:
    """Run agentkit pipeline inline and return summary dict."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main", "run", "--json", "--path", str(root)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    stdout = result.stdout.strip()
    if stdout:
        # Find JSON block
        start = stdout.find("{")
        if start >= 0:
            return json.loads(stdout[start:])
    # Fallback: return minimal report
    return {"project": str(root), "total": 0, "passed": 0, "failed": 0}
