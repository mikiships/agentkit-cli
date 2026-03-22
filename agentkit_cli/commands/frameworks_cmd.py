"""agentkit frameworks command — detect frameworks and check agent context coverage."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli import __version__
from agentkit_cli.frameworks import FrameworkDetector, FrameworkChecker, FrameworkCoverage

console = Console()


def _score_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def frameworks_command(
    path: Path = Path("."),
    context_file: Optional[Path] = None,
    min_score: int = 60,
    json_output: bool = False,
    quiet: bool = False,
    share: bool = False,
    generate: bool = False,
) -> None:
    """Detect frameworks and check agent context coverage."""
    root = Path(path).resolve()

    detector = FrameworkDetector()
    checker = FrameworkChecker()

    frameworks = detector.detect(root)

    # Resolve context file
    ctx_file: Optional[Path] = None
    if context_file is not None:
        ctx_file = Path(context_file).resolve()
    else:
        ctx_file = checker.find_context_file(root)

    coverages: list[FrameworkCoverage] = checker.check_all(frameworks, root=root, context_file=ctx_file)

    below_threshold = [cov.framework for cov in coverages if cov.score < min_score]
    overall_score = round(sum(cov.score for cov in coverages) / len(coverages)) if coverages else 0

    # --generate: append missing sections
    if generate and ctx_file is not None:
        _run_generate(ctx_file, coverages, min_score)
    elif generate and ctx_file is None:
        if not json_output and not quiet:
            console.print("[yellow]Warning: no context file found. Cannot generate sections.[/yellow]")

    if json_output:
        data = {
            "project_path": str(root),
            "context_file": str(ctx_file) if ctx_file else None,
            "detected_frameworks": [
                {
                    "name": cov.framework,
                    "confidence": next(
                        (fw.confidence for fw in frameworks if fw.name == cov.framework), "unknown"
                    ),
                    "score": cov.score,
                    "missing_required": cov.missing_required,
                    "missing_nice_to_have": cov.missing_nice_to_have,
                }
                for cov in coverages
            ],
            "overall_score": overall_score,
            "below_threshold": below_threshold,
            "version": __version__,
        }
        print(json.dumps(data, indent=2))
        return

    if quiet:
        n = len(frameworks)
        nb = len(below_threshold)
        typer.echo(f"{n} frameworks detected, {nb} below threshold (< {min_score})")
        return

    # Rich table output
    project_name = root.name
    table = Table(title=f"Detected Frameworks in {project_name}", show_header=True, header_style="bold")
    table.add_column("Framework", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Missing")

    if not frameworks:
        console.print(f"\n[dim]No frameworks detected in {root}[/dim]\n")
        return

    for cov in coverages:
        fw = next((f for f in frameworks if f.name == cov.framework), None)
        confidence = fw.confidence if fw else "unknown"
        fw_label = f"{cov.framework} ({confidence})"
        score_str = f"{cov.score}/100"
        sc = _score_color(cov.score)
        missing_parts = cov.missing_required + cov.missing_nice_to_have
        missing_str = ", ".join(missing_parts) if missing_parts else "—"
        table.add_row(fw_label, f"[{sc}]{score_str}[/{sc}]", missing_str)

    console.print()
    console.print(table)

    nb = len(below_threshold)
    threshold_msg = ""
    if nb > 0:
        below_names = ", ".join(f"{n} ({s})" for n, s in ((cov.framework, cov.score) for cov in coverages if cov.score < min_score))
        threshold_msg = f", {nb} below threshold ({below_names} < {min_score})"

    console.print(
        f"\n[bold]Overall:[/bold] {len(frameworks)} framework(s) detected{threshold_msg}"
    )
    if ctx_file:
        console.print(f"[dim]Context file: {ctx_file}[/dim]")
    else:
        console.print("[yellow]No CLAUDE.md / AGENTS.md found.[/yellow]")

    if below_threshold:
        console.print(
            "[dim]Run [bold]agentkit frameworks --generate[/bold] to add missing sections.[/dim]"
        )
    console.print()

    if share:
        try:
            from agentkit_cli.share import generate_scorecard_html, upload_scorecard
            html = _make_share_html(frameworks, coverages, project_name, overall_score)
            url = upload_scorecard(html)
            if url:
                console.print(f"[bold green]Report published:[/bold green] {url}")
            else:
                console.print("[yellow]Share failed (check HERENOW_API_KEY)[/yellow]", err=True)
        except Exception as e:
            console.print(f"[yellow]Share error: {e}[/yellow]", err=True)


def _run_generate(ctx_file: Path, coverages: list[FrameworkCoverage], min_score: int) -> None:
    """Append missing framework sections to context file."""
    from agentkit_cli.framework_templates import get_template

    current = ctx_file.read_text(encoding="utf-8") if ctx_file.exists() else ""
    added: list[str] = []

    for cov in coverages:
        if cov.score >= min_score:
            continue
        fw_name = cov.framework
        # Idempotency check: skip if heading already exists
        if f"## {fw_name}" in current:
            continue
        template = get_template(fw_name)
        if template:
            current = current.rstrip() + "\n\n" + template
            added.append(fw_name)

    if added:
        ctx_file.write_text(current, encoding="utf-8")
        console.print(
            f"[bold green]Generated sections for:[/bold green] {', '.join(added)}"
        )
    else:
        console.print("[dim]No new sections needed.[/dim]")


def _make_share_html(frameworks, coverages, project_name, overall_score) -> str:
    rows = ""
    for cov in coverages:
        rows += f"<tr><td>{cov.framework}</td><td>{cov.score}/100</td></tr>"
    return f"""<!DOCTYPE html>
<html><head><title>{project_name} - agentkit frameworks</title></head>
<body>
<h1>{project_name} — Framework Coverage</h1>
<p>Overall score: {overall_score}/100</p>
<table border="1"><tr><th>Framework</th><th>Score</th></tr>{rows}</table>
</body></html>"""
