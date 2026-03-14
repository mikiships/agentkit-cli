"""agentkit CLI entry point."""
from __future__ import annotations

import typer
from typing import List, Optional
from pathlib import Path

from agentkit_cli.commands.init_cmd import init_command
from agentkit_cli.commands.run_cmd import run_command
from agentkit_cli.commands.status_cmd import status_command
from agentkit_cli.commands.doctor_cmd import doctor_command
from agentkit_cli.commands.ci import ci_command
from agentkit_cli.commands.watch import watch_command
from agentkit_cli.commands.demo_cmd import demo_command
from agentkit_cli.commands.report_cmd import report_command
from agentkit_cli.publish import publish_command
from agentkit_cli.commands.badge_cmd import badge_command
from agentkit_cli.commands.readme_cmd import readme_command
from agentkit_cli.commands.compare_cmd import compare_command
from agentkit_cli.commands.suggest_cmd import suggest_command
from agentkit_cli.commands.summary_cmd import summary_command
from agentkit_cli.commands.history_cmd import history_command

app = typer.Typer(
    name="agentkit",
    help="Unified CLI for the Agent Quality Toolkit (agentmd, coderace, agentlint, agentreflect).",
    add_completion=False,
)


@app.command("init")
def init(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project root"),
) -> None:
    """Initialize agentkit in a project. Creates .agentkit.yaml and checks for quartet tools."""
    init_command(path=path)


@app.command("run")
def run(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    skip: Optional[List[str]] = typer.Option(None, "--skip", help="Steps to skip: generate, lint, benchmark, reflect"),
    benchmark: bool = typer.Option(False, "--benchmark", help="Include benchmark step (off by default)"),
    json_output: bool = typer.Option(False, "--json", help="Emit summary as JSON"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Notes for agentreflect"),
    ci: bool = typer.Option(False, "--ci", help="CI mode: plain output, exit 1 on failure"),
    publish: bool = typer.Option(False, "--publish", help="Publish HTML report to here.now after run"),
    inject_readme: bool = typer.Option(False, "--readme", help="Inject/update badge in README.md after run"),
    no_history: bool = typer.Option(False, "--no-history", help="Skip recording scores to history DB"),
) -> None:
    """Run the full Agent Quality pipeline sequentially."""
    run_command(path=path, skip=skip, benchmark=benchmark, json_output=json_output, notes=notes, ci=ci, publish=publish, inject_readme=inject_readme, no_history=no_history)


@app.command("doctor")
def doctor(
    json_output: bool = typer.Option(False, "--json", help="Emit results as JSON"),
    category: Optional[str] = typer.Option(None, "--category", help="Filter to one category: repo, toolchain, context, publish"),
    fail_on: str = typer.Option("fail", "--fail-on", help="Exit non-zero when any check at this level or above fails: warn|fail"),
    no_fail_exit: bool = typer.Option(False, "--no-fail-exit", help="Always exit 0, regardless of check results"),
) -> None:
    """Preflight check: verify repo health, toolchain, context, and publish readiness."""
    doctor_command(json_output=json_output, category=category, fail_on=fail_on, no_fail_exit=no_fail_exit)


@app.command("status")
def status(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    json_output: bool = typer.Option(False, "--json", help="Emit status as JSON"),
) -> None:
    """Show health status of toolkit and current project."""
    status_command(path=path, json_output=json_output)


@app.command("ci")
def ci(
    python_version: str = typer.Option("3.12", "--python-version", help="Python version for the workflow"),
    benchmark: bool = typer.Option(False, "--benchmark", help="Include coderace benchmark step"),
    min_score: Optional[int] = typer.Option(None, "--min-score", help="Gate on maintainer rubric score"),
    output_dir: Path = typer.Option(Path(".github/workflows"), "--output-dir", help="Where to write the workflow file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print to stdout instead of writing file"),
) -> None:
    """Generate a GitHub Actions workflow that runs the agentkit pipeline on every PR."""
    ci_command(
        python_version=python_version,
        benchmark=benchmark,
        min_score=min_score,
        output_dir=output_dir,
        dry_run=dry_run,
    )


@app.command("demo")
def demo(
    task: Optional[str] = typer.Option(None, "--task", help="Coderace task to benchmark (default: auto-pick)"),
    agents: Optional[str] = typer.Option(None, "--agents", help="Comma-separated agents, e.g. claude,codex"),
    skip_benchmark: bool = typer.Option(False, "--skip-benchmark", help="Skip coderace benchmark step"),
    json_output: bool = typer.Option(False, "--json", help="Emit results as JSON"),
) -> None:
    """Zero-config demo: shows the toolkit in action without any setup."""
    demo_command(task=task, agents=agents, skip_benchmark=skip_benchmark, json_output=json_output)


@app.command("report")
def report(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to analyse"),
    json_output: bool = typer.Option(False, "--json", help="Emit results as JSON to stdout"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to write HTML report (default: ./agentkit-report.html)"),
    open_browser: bool = typer.Option(False, "--open", help="Auto-open the HTML report in the default browser"),
    publish: bool = typer.Option(False, "--publish", help="Publish HTML report to here.now after generation"),
    inject_readme: bool = typer.Option(False, "--readme", help="Inject/update badge in README.md after report"),
) -> None:
    """Run all toolkit checks and generate a self-contained HTML quality report."""
    report_command(path=path, json_output=json_output, output=output, open_browser=open_browser, publish=publish, inject_readme=inject_readme)


@app.command("publish")
def publish(
    html_path: Optional[Path] = typer.Argument(None, help="Path to HTML report (default: ./agentkit-report.html)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON with url and expires_in"),
    quiet: bool = typer.Option(False, "--quiet", help="Only print the URL"),
) -> None:
    """Publish an HTML report to here.now and return a shareable URL."""
    publish_command(html_path=html_path, json_output=json_output, quiet=quiet)


@app.command("badge")
def badge(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    json_output: bool = typer.Option(False, "--json", help="Emit badge info as JSON"),
    score_override: Optional[int] = typer.Option(None, "--score", help="Use this score instead of computing it"),
) -> None:
    """Generate a shields.io-compatible badge showing the project's agent quality score."""
    badge_command(path=path, json_output=json_output, score_override=score_override)


@app.command("readme")
def readme(
    readme_path: Optional[Path] = typer.Option(None, "--readme", help="Path to README.md (default: ./README.md)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without modifying the file"),
    remove: bool = typer.Option(False, "--remove", help="Remove the injected badge section"),
    section_header: str = typer.Option("## Agent Quality", "--section-header", help="Section header to use"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    score_override: Optional[int] = typer.Option(None, "--score", help="Use this score instead of computing it"),
) -> None:
    """Inject or update the agent quality badge in README.md."""
    readme_command(
        readme=readme_path,
        dry_run=dry_run,
        remove=remove,
        section_header=section_header,
        path=path,
        score_override=score_override,
    )


@app.command("compare")
def compare(
    ref1: str = typer.Argument("HEAD~1", help="Base ref (older)"),
    ref2: str = typer.Argument("HEAD", help="Head ref (newer)"),
    tools: Optional[List[str]] = typer.Option(None, "--tools", help="Tools to compare (default: all quartet)"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON"),
    quiet: bool = typer.Option(False, "--quiet", help="Only print IMPROVED/NEUTRAL/DEGRADED verdict"),
    ci_mode: bool = typer.Option(False, "--ci", help="Exit 1 if verdict is DEGRADED"),
    min_delta: Optional[float] = typer.Option(None, "--min-delta", help="Fail if net delta is below this value"),
    files: bool = typer.Option(False, "--files", help="Show per-file score breakdown"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
) -> None:
    """Compare agent quality scores between two git refs."""
    compare_command(
        ref1=ref1,
        ref2=ref2,
        tools=tools,
        json_output=json_output,
        quiet=quiet,
        ci_mode=ci_mode,
        min_delta=min_delta,
        files=files,
        path=path,
    )


@app.command("suggest")
def suggest(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project root (default: cwd)"),
    show_all: bool = typer.Option(False, "--all", help="Show all findings, not just top 5"),
    fix: bool = typer.Option(False, "--fix", help="Auto-apply safe fixes (year-rot, trailing-whitespace, duplicate-blank-lines)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="With --fix, show diff without applying"),
    json_output: bool = typer.Option(False, "--json", help="Emit findings as JSON to stdout"),
) -> None:
    """Show prioritized action list from agentlint findings. Optionally auto-fix safe issues."""
    suggest_command(path=path, show_all=show_all, fix=fix, dry_run=dry_run, json_output=json_output)


@app.command("summary")
def summary(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to analyse"),
    json_input: Optional[Path] = typer.Option(None, "--json-input", help="Path to existing agentkit JSON results"),
) -> None:
    """Generate a maintainer-facing markdown summary."""
    summary_command(path=path, json_input=json_input)


@app.command("history")
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of runs to show"),
    tool: Optional[str] = typer.Option(None, "--tool", "-t", help="Filter to one tool"),
    project: Optional[str] = typer.Option(None, "--project", help="Override project name"),
    graph: bool = typer.Option(False, "--graph", help="Show ASCII sparkline trend"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    clear: bool = typer.Option(False, "--clear", help="Delete history for this project"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation for --clear"),
    all_projects: bool = typer.Option(False, "--all-projects", help="Show history for all projects"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Show agent quality score history and trends."""
    history_command(
        limit=limit,
        tool=tool,
        project=project,
        graph=graph,
        json_output=json_output,
        clear=clear,
        yes=yes,
        all_projects=all_projects,
        db_path=db_path,
    )


@app.command("watch")
def watch(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to watch"),
    extensions: Optional[List[str]] = typer.Option(None, "--extensions", help="File extensions to watch (e.g. .py,.md)"),
    debounce: float = typer.Option(2.0, "--debounce", help="Debounce delay in seconds"),
    ci: bool = typer.Option(False, "--ci", help="Run pipeline in CI mode on changes"),
) -> None:
    """Watch the project for changes and re-run the pipeline automatically."""
    watch_command(path=path, extensions=extensions, debounce=debounce, ci=ci)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
) -> None:
    if version:
        from agentkit_cli import __version__
        typer.echo(f"agentkit-cli v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


if __name__ == "__main__":
    app()
