"""agentkit CLI entry point."""
from __future__ import annotations

import typer
from typing import List, Optional
from pathlib import Path

from agentkit_cli.commands.quickstart_cmd import quickstart_command
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
from agentkit_cli.commands.leaderboard_cmd import leaderboard_command
from agentkit_cli.commands.score_cmd import score_command
from agentkit_cli.commands.share_cmd import share_command
from agentkit_cli.commands.analyze_cmd import analyze_command
from agentkit_cli.commands.sweep_cmd import sweep_command
from agentkit_cli.commands.gate_cmd import gate_command
from agentkit_cli.commands.setup_ci_cmd import setup_ci_command
from agentkit_cli.commands.release_check_cmd import release_check_command
from agentkit_cli.commands.notify_cmd import notify_app
from agentkit_cli.commands.config_cmd import config_app
from agentkit_cli.commands.profile_cmd import profile_app
from agentkit_cli.commands.insights_cmd import insights_command
from agentkit_cli.commands.trending_cmd import trending_command
from agentkit_cli.commands.duel_cmd import duel_command
from agentkit_cli.commands.tournament_cmd import tournament_command
from agentkit_cli.commands.org_cmd import org_command
from agentkit_cli.commands.serve_cmd import serve_command
from agentkit_cli.commands.pr_cmd import pr_command
from agentkit_cli.commands.campaign_cmd import campaign_command
from agentkit_cli.commands.track_cmd import track_command
from agentkit_cli.commands.redteam_cmd import redteam_command
from agentkit_cli.commands.harden_cmd import harden_command
from agentkit_cli.commands.certify_cmd import certify_app
from agentkit_cli.commands.timeline_cmd import timeline_command
from agentkit_cli.commands.explain_cmd import explain_command
from agentkit_cli.commands.improve import improve_command
from agentkit_cli.commands.monitor import monitor_app
from agentkit_cli.commands.webhook import webhook_app
from agentkit_cli.commands.checks_cmd import checks_app
from agentkit_cli.commands.llmstxt_cmd import llmstxt_command
from agentkit_cli.commands.migrate_cmd import migrate_command
from agentkit_cli.commands.sync_cmd import sync_command
from agentkit_cli.commands.search_cmd import search_command
from agentkit_cli.commands.benchmark_cmd import benchmark_command
from agentkit_cli.serve import DEFAULT_PORT

app = typer.Typer(
    name="agentkit",
    help="Unified CLI for the Agent Quality Toolkit (agentmd, coderace, agentlint, agentreflect).",
    add_completion=False,
)
app.add_typer(notify_app, name="notify")
app.add_typer(config_app, name="config")
app.add_typer(profile_app, name="profile")
app.add_typer(certify_app, name="certify")
app.add_typer(monitor_app, name="monitor")
app.add_typer(webhook_app, name="webhook")
app.add_typer(checks_app, name="checks")


@app.command("timeline")
def timeline(
    project: Optional[str] = typer.Option(None, "--project", help="Filter to one project (default: all)"),
    limit: int = typer.Option(50, "--limit", help="Max runs to show (default: 50)"),
    since: Optional[str] = typer.Option(None, "--since", help="Only runs after this date (YYYY-MM-DD)"),
    output: Path = typer.Option(Path("timeline.html"), "--output", "-o", help="Write HTML to file (default: timeline.html)"),
    share: bool = typer.Option(False, "--share", help="Publish to here.now and print URL"),
    json_output: bool = typer.Option(False, "--json", help="Output raw chart data as JSON"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Generate a dark-theme HTML quality timeline from history DB."""
    timeline_command(
        project=project,
        limit=limit,
        since=since,
        output=output,
        share=share,
        json_output=json_output,
        db_path=db_path,
    )


@app.command("quickstart")
def quickstart(
    target: str = typer.Argument(".", help="Local path or github:owner/repo"),
    no_share: bool = typer.Option(False, "--no-share", help="Skip publishing the score card"),
    timeout: int = typer.Option(30, "--timeout", help="Per-tool timeout in seconds (default 30)"),
) -> None:
    """🚀 Fastest path to an impressive agentkit result. Run this first."""
    quickstart_command(target=target, no_share=no_share, timeout=timeout)


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
    label: Optional[str] = typer.Option(None, "--label", help="Tag this run with a label (e.g. model name) for leaderboard comparison"),
    notify_slack: Optional[str] = typer.Option(None, "--notify-slack", help="Slack webhook URL (or set AGENTKIT_NOTIFY_SLACK)"),
    notify_discord: Optional[str] = typer.Option(None, "--notify-discord", help="Discord webhook URL (or set AGENTKIT_NOTIFY_DISCORD)"),
    notify_webhook: Optional[str] = typer.Option(None, "--notify-webhook", help="Generic JSON webhook URL (or set AGENTKIT_NOTIFY_WEBHOOK)"),
    notify_on: str = typer.Option("fail", "--notify-on", help="When to notify: fail|always"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Quality profile to use (strict|balanced|minimal)"),
    share: bool = typer.Option(False, "--share", help="Upload a score card to here.now after run and print the URL"),
    release_check: bool = typer.Option(False, "--release-check", help="Verify release surfaces after pipeline completes"),
    record_findings: bool = typer.Option(False, "--record-findings", help="Store agentlint findings in history DB for insights"),
    serve: bool = typer.Option(False, "--serve", help="Print dashboard URL after run completes"),
    run_redteam: bool = typer.Option(False, "--redteam", help="Run adversarial eval after pipeline completes"),
    run_harden: bool = typer.Option(False, "--harden", help="Run harden on detected context file after pipeline"),
    run_timeline: bool = typer.Option(False, "--timeline", help="Generate timeline HTML after run completes"),
    run_explain: bool = typer.Option(False, "--explain", help="Generate LLM coaching report after pipeline completes"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Use template-based explanation (offline, no API key needed)"),
    run_improve: bool = typer.Option(False, "--improve", help="After run, auto-improve if score < threshold"),
    improve_no_generate: bool = typer.Option(False, "--improve-no-generate", help="Skip context generation in --improve"),
    improve_no_harden: bool = typer.Option(False, "--improve-no-harden", help="Skip hardening in --improve"),
    improve_threshold: float = typer.Option(80.0, "--improve-threshold", help="Score threshold below which --improve runs (default 80)"),
    webhook_notify: bool = typer.Option(False, "--webhook-notify", help="POST result to configured webhook URL after run"),
    checks: Optional[bool] = typer.Option(None, "--checks/--no-checks", help="Post a GitHub Check Run (default: auto-detect GitHub Actions env)"),
    run_llmstxt: bool = typer.Option(False, "--llmstxt", help="Generate llms.txt after pipeline completes"),
    run_migrate: bool = typer.Option(False, "--migrate", help="Auto-generate missing context format files before analysis"),
    run_digest: bool = typer.Option(False, "--digest", help="Print a quality digest for this project after the run"),
    agent_benchmark: bool = typer.Option(False, "--agent-benchmark", help="Run cross-agent benchmark after pipeline and include result in output"),
) -> None:
    """Run the full Agent Quality pipeline sequentially."""
    run_command(path=path, skip=skip, benchmark=benchmark, json_output=json_output, notes=notes, ci=ci, publish=publish, inject_readme=inject_readme, no_history=no_history, label=label, notify_slack=notify_slack, notify_discord=notify_discord, notify_webhook=notify_webhook, notify_on=notify_on, profile=profile, share=share, record_findings=record_findings, harden=run_harden, timeline=run_timeline, explain=run_explain, no_llm=no_llm, improve=run_improve, improve_no_generate=improve_no_generate, improve_no_harden=improve_no_harden, improve_threshold=improve_threshold, webhook_notify=webhook_notify, checks=checks, llmstxt=run_llmstxt, migrate=run_migrate, agent_benchmark=agent_benchmark)
    if run_digest:
        from agentkit_cli.digest import DigestEngine
        from agentkit_cli.digest_report import DigestReportRenderer
        import os
        proj_name = (path or Path(".")).resolve().name
        engine = DigestEngine(period_days=7)
        digest_report = engine.generate(projects=[proj_name])
        typer.echo(f"\n[digest] {proj_name}: trend={digest_report.overall_trend}, runs={digest_report.runs_in_period}, coverage={digest_report.coverage_pct:.0f}%")
        for p in digest_report.per_project:
            if p.score_end is not None:
                typer.echo(f"  score: {p.score_end:.1f} (delta: {p.delta:+.1f})" if p.delta is not None else f"  score: {p.score_end:.1f}")
    if serve:
        from agentkit_cli.serve import DEFAULT_PORT
        typer.echo(f"Dashboard: http://localhost:{DEFAULT_PORT}")
    if release_check:
        from agentkit_cli.release_check import run_release_check
        from agentkit_cli.commands.release_check_cmd import _render_table
        result = run_release_check(path=path or None)
        _render_table(result)
    if run_redteam:
        redteam_command(
            path=path,
            categories=None,
            attacks_per_category=3,
            json_output=json_output,
            share=False,
            min_score=None,
            output=None,
        )


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
    record: bool = typer.Option(False, "--record", help="Generate VHS tape for terminal recording"),
    record_output: Optional[str] = typer.Option(None, "--record-output", help="Path for generated demo.tape"),
) -> None:
    """Zero-config demo: shows the toolkit in action without any setup."""
    demo_command(task=task, agents=agents, skip_benchmark=skip_benchmark, json_output=json_output,
                 record=record, record_output=record_output)


@app.command("report")
def report(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to analyse"),
    json_output: bool = typer.Option(False, "--json", help="Emit results as JSON to stdout"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to write HTML report (default: ./agentkit-report.html)"),
    open_browser: bool = typer.Option(False, "--open", help="Auto-open the HTML report in the default browser"),
    publish: bool = typer.Option(False, "--publish", help="Publish HTML report to here.now after generation"),
    inject_readme: bool = typer.Option(False, "--readme", help="Inject/update badge in README.md after report"),
    share: bool = typer.Option(False, "--share", help="Upload a score card to here.now after report and print the URL"),
    report_llmstxt: bool = typer.Option(False, "--llmstxt", help="Include llms.txt card in report and generate llms.txt if missing"),
    report_digest: bool = typer.Option(False, "--digest", help="Append a quality digest section to the report output"),
) -> None:
    """Run all toolkit checks and generate a self-contained HTML quality report."""
    report_command(path=path, json_output=json_output, output=output, open_browser=open_browser, publish=publish, inject_readme=inject_readme, share=share, llmstxt=report_llmstxt)
    if report_digest:
        from agentkit_cli.digest import DigestEngine
        proj_name = (path or Path(".")).resolve().name
        engine = DigestEngine(period_days=7)
        digest_report = engine.generate(projects=[proj_name])
        typer.echo(f"\n[digest] {proj_name}: trend={digest_report.overall_trend}, runs={digest_report.runs_in_period}")


@app.command("share")
def share(
    report: Optional[Path] = typer.Option(None, "--report", help="Path to a saved JSON report file"),
    project: Optional[str] = typer.Option(None, "--project", help="Override project name"),
    no_scores: bool = typer.Option(False, "--no-scores", help="Hide raw numbers; show pass/fail only"),
    json_output: bool = typer.Option(False, "--json", help='Output {"url": "...", "score": N} instead of plain text'),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory (default: cwd)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="here.now API key (overrides HERENOW_API_KEY env var)", envvar="HERENOW_API_KEY"),
) -> None:
    """Generate a shareable score card and upload it to here.now."""
    share_command(report=report, project=project, no_scores=no_scores, json_output=json_output, path=path, api_key=api_key)


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
    tool: Optional[str] = typer.Option(None, "--tool", help="Show single-tool score instead of composite (e.g. coderace, agentlint, agentmd, agentreflect)"),
) -> None:
    """Generate a shields.io-compatible badge showing the project's agent quality score."""
    badge_command(path=path, json_output=json_output, score_override=score_override, tool=tool)


@app.command("score")
def score(
    path: Optional[Path] = typer.Argument(None, help="Project directory (default: cwd)"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
    breakdown: bool = typer.Option(False, "--breakdown", help="Show per-component score table"),
    ci: bool = typer.Option(False, "--ci", help="Exit 1 if score < min-score"),
    min_score: int = typer.Option(70, "--min-score", help="CI gate threshold (default: 70)"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Quality profile to use (strict|balanced|minimal)"),
) -> None:
    """Compute composite agent quality score (0-100) from all toolkit tools."""
    score_command(path=path, json_output=json_output, breakdown=breakdown, ci=ci, min_score=min_score, profile=profile)


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
    campaigns: bool = typer.Option(False, "--campaigns", help="Show campaign-grouped summary"),
    campaign_id: Optional[str] = typer.Option(None, "--campaign-id", help="Show all PRs from a specific campaign"),
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
        campaigns=campaigns,
        campaign_id=campaign_id,
    )


@app.command("leaderboard")
def leaderboard(
    by: str = typer.Option("overall", "--by", help="Score dimension: overall, agentmd, agentlint, coderace, agentreflect"),
    project: Optional[str] = typer.Option(None, "--project", help="Filter by project name (default: cwd basename)"),
    last: Optional[int] = typer.Option(None, "--last", help="Only use the most recent N runs per label"),
    since: Optional[str] = typer.Option(None, "--since", help="Filter by recency: '7d' or 'YYYY-MM-DD'"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Show a ranked leaderboard of agent runs grouped by --label tags."""
    leaderboard_command(by=by, project=project, last=last, since=since, json_output=json_output, db_path=db_path)


@app.command("analyze")
def analyze(
    target: str = typer.Argument(..., help="Target: github:owner/repo, https://github.com/..., owner/repo, or ./local-path"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    keep: bool = typer.Option(False, "--keep", help="Keep temp clone dir after analysis (prints path)"),
    publish: bool = typer.Option(False, "--publish", help="Publish HTML report to here.now after analysis"),
    timeout: int = typer.Option(120, "--timeout", help="Clone + analysis timeout in seconds"),
    no_generate: bool = typer.Option(False, "--no-generate", help="Skip agentmd generate; only score what's there"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Quality profile to use (strict|balanced|minimal)"),
    share: bool = typer.Option(False, "--share", help="Upload a score card to here.now after analysis and print the URL"),
    record_findings: bool = typer.Option(False, "--record-findings", help="Store agentlint findings in history DB for insights"),
) -> None:
    """Analyze any GitHub repo (or local path) for agent quality. Zero setup required."""
    analyze_command(
        target=target,
        json_output=json_output,
        keep=keep,
        publish=publish,
        timeout=timeout,
        no_generate=no_generate,
        profile=profile,
        share=share,
        record_findings=record_findings,
    )


@app.command("sweep")
def sweep(
    targets: Optional[List[str]] = typer.Argument(None, help="Targets to analyze in order"),
    targets_file: Optional[Path] = typer.Option(None, "--targets-file", help="File containing one target per line"),
    keep: bool = typer.Option(False, "--keep", help="Keep temp clone dirs after analysis"),
    publish: bool = typer.Option(False, "--publish", help="Publish HTML report to here.now after each analysis"),
    timeout: int = typer.Option(120, "--timeout", help="Clone + analysis timeout in seconds"),
    no_generate: bool = typer.Option(False, "--no-generate", help="Skip agentmd generate; only score what's there"),
    sort_by: str = typer.Option("score", "--sort-by", help="Sort results by: score, name, or grade"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Show only top N results in table output"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Quality profile to use (strict|balanced|minimal)"),
    share: bool = typer.Option(False, "--share", help="Upload a combined score card to here.now after sweep and print the URL"),
) -> None:
    """Analyze multiple GitHub repos or local paths in one batch."""
    sweep_command(
        targets=targets or [],
        targets_file=targets_file,
        keep=keep,
        publish=publish,
        timeout=timeout,
        no_generate=no_generate,
        sort_by=sort_by,
        limit=limit,
        json_output=json_output,
        profile=profile,
        share=share,
    )


@app.command("gate")
def gate(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
    min_score: Optional[float] = typer.Option(None, "--min-score", help="Fail if the composite score is below this threshold"),
    baseline_report: Optional[Path] = typer.Option(None, "--baseline-report", help="Path to a prior agentkit report --json artifact"),
    max_drop: Optional[float] = typer.Option(None, "--max-drop", help="Fail if the score drops by more than this many points from baseline"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON output"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to write the JSON payload"),
    job_summary: bool = typer.Option(False, "--job-summary", help="Write a markdown verdict block to GITHUB_STEP_SUMMARY"),
    notify_slack: Optional[str] = typer.Option(None, "--notify-slack", help="Slack webhook URL (or set AGENTKIT_NOTIFY_SLACK)"),
    notify_discord: Optional[str] = typer.Option(None, "--notify-discord", help="Discord webhook URL (or set AGENTKIT_NOTIFY_DISCORD)"),
    notify_webhook: Optional[str] = typer.Option(None, "--notify-webhook", help="Generic JSON webhook URL (or set AGENTKIT_NOTIFY_WEBHOOK)"),
    notify_on: str = typer.Option("fail", "--notify-on", help="When to notify: fail|always"),
    profile: Optional[str] = typer.Option(None, "--profile", help="Quality profile to use (strict|balanced|minimal)"),
    release_check: bool = typer.Option(False, "--release-check", help="Add release surface verification to gate checks"),
    checks: Optional[bool] = typer.Option(None, "--checks/--no-checks", help="Post a GitHub Check Run (default: auto-detect GitHub Actions env)"),
) -> None:
    """Fail the build when agent quality falls below your policy thresholds."""
    if release_check:
        from agentkit_cli.release_check import run_release_check
        from agentkit_cli.commands.release_check_cmd import _render_table
        rc_result = run_release_check(path=path or None)
        _render_table(rc_result)
    gate_command(
        path=path,
        min_score=min_score,
        baseline_report=baseline_report,
        max_drop=max_drop,
        json_output=json_output,
        output=output,
        job_summary=job_summary,
        notify_slack=notify_slack,
        notify_discord=notify_discord,
        notify_webhook=notify_webhook,
        notify_on=notify_on,
        profile=profile,
        checks=checks,
    )


@app.command("setup-ci")
def setup_ci(
    min_score: int = typer.Option(70, "--min-score", help="Minimum score threshold to embed in generated gate command"),
    workflow_path: Optional[Path] = typer.Option(None, "--workflow-path", help="Path to write the workflow file (default: .github/workflows/agentkit-quality.yml)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing workflow file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print workflow to stdout without writing"),
    skip_baseline: bool = typer.Option(False, "--skip-baseline", help="Skip baseline report generation"),
    no_badge: bool = typer.Option(False, "--no-badge", help="Skip badge injection into README.md"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project root (default: git root or cwd)"),
) -> None:
    """One-command CI setup: write GitHub Actions workflow, generate baseline, inject README badge."""
    setup_ci_command(
        min_score=min_score,
        workflow_path=workflow_path,
        force=force,
        dry_run=dry_run,
        skip_baseline=skip_baseline,
        no_badge=no_badge,
        path=path,
    )


@app.command("release-check")
def release_check(
    path: Optional[Path] = typer.Argument(None, help="Project directory (default: cwd)"),
    version: Optional[str] = typer.Option(None, "--version", help="Version to check (default: from pyproject.toml/package.json)"),
    package: Optional[str] = typer.Option(None, "--package", help="Package name (default: from pyproject.toml/package.json)"),
    registry: str = typer.Option("auto", "--registry", help="Registry to check: pypi|npm|auto"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip the pytest/npm test step"),
    json_output: bool = typer.Option(False, "--json", help="Output structured JSON for CI integration"),
) -> None:
    """Verify the 4-part release surface: tests, git push, tag, and registry."""
    release_check_command(
        path=path,
        version=version,
        package=package,
        registry=registry,
        skip_tests=skip_tests,
        json_output=json_output,
    )


@app.command("trending")
def trending(
    period: str = typer.Option("week", "--period", help="Trending window: day|week|month"),
    topic: Optional[str] = typer.Option(None, "--topic", help="Filter by GitHub topic (e.g. ai-agent)"),
    limit: int = typer.Option(10, "--limit", help="Max repos to fetch (max 25)"),
    category: str = typer.Option("ai", "--category", help="Pre-defined category: ai|python|all"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now and print URL"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON instead of table"),
    no_analyze: bool = typer.Option(False, "--no-analyze", help="Skip agentkit analysis (fast mode)"),
    min_stars: int = typer.Option(100, "--min-stars", help="Filter repos below this star count"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub API token (or GITHUB_TOKEN env var)", envvar="GITHUB_TOKEN"),
) -> None:
    """Fetch trending GitHub repos and rank them by agent quality score."""
    trending_command(
        period=period,
        topic=topic,
        limit=limit,
        category=category,
        share=share,
        json_output=json_output,
        no_analyze=no_analyze,
        min_stars=min_stars,
        token=token,
    )


@app.command("insights")
def insights(
    db_path: Optional[Path] = typer.Option(None, "--db", help="Override history DB path"),
    common_findings: bool = typer.Option(False, "--common-findings", help="Show most common findings across repos"),
    outliers: bool = typer.Option(False, "--outliers", help="Show repos in the bottom quartile"),
    trending: bool = typer.Option(False, "--trending", help="Show repos with recent score movement"),
    all_sections: bool = typer.Option(False, "--all", help="Show all sections in one output"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON output"),
) -> None:
    """Synthesize patterns across agentkit analyze runs. What do your repos have in common?"""
    insights_command(
        db_path=db_path,
        common_findings=common_findings,
        outliers=outliers,
        trending=trending,
        all_sections=all_sections,
        json_output=json_output,
    )


@app.command("duel")
def duel(
    target1: str = typer.Argument(..., help="First target: github:owner/repo or local path"),
    target2: str = typer.Argument(..., help="Second target: github:owner/repo or local path"),
    share: bool = typer.Option(False, "--share/--no-share", help="Publish comparison to here.now"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON payload"),
    timeout: int = typer.Option(120, "--timeout", help="Per-repo analysis timeout in seconds"),
    keep: bool = typer.Option(False, "--keep", help="Keep cloned repos after analysis"),
) -> None:
    """Head-to-head agent-readiness comparison of two GitHub repos."""
    duel_command(
        target1=target1,
        target2=target2,
        share=share,
        json_output=json_output,
        timeout=timeout,
        keep=keep,
    )


@app.command("tournament")
def tournament(
    repos: List[str] = typer.Argument(..., help="Repos to include: github:owner/repo or local paths (4-16)"),
    share: bool = typer.Option(False, "--share/--no-share", help="Publish HTML report to here.now"),
    json_output: bool = typer.Option(False, "--json", help="Output full results as JSON"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress Rich output; show only final standings"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Run pairings concurrently (default: parallel)"),
    min_repos: int = typer.Option(4, "--min-repos", help="Minimum repos required (default: 4)"),
    max_repos: int = typer.Option(16, "--max-repos", help="Maximum repos allowed (default: 16)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write HTML report to this file"),
    timeout: int = typer.Option(120, "--timeout", help="Per-repo analysis timeout in seconds"),
    keep: bool = typer.Option(False, "--keep", help="Keep cloned repos after analysis"),
) -> None:
    """Run a round-robin tournament across N repos (4-16). Rank by win/loss record."""
    tournament_command(
        repos=list(repos),
        share=share,
        json_output=json_output,
        quiet=quiet,
        parallel=parallel,
        min_repos=min_repos,
        max_repos=max_repos,
        output=output,
        timeout=timeout,
        keep=keep,
    )


@app.command("org")
def org(
    target: str = typer.Argument(..., help="GitHub org or user to analyze: 'github:vercel' or 'vercel'"),
    include_forks: bool = typer.Option(False, "--include-forks", help="Include forked repos"),
    include_archived: bool = typer.Option(False, "--include-archived", help="Include archived repos"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Max repos to analyze"),
    parallel: int = typer.Option(3, "--parallel", help="Parallel analysis workers (default: 3)"),
    timeout: int = typer.Option(120, "--timeout", help="Per-repo timeout in seconds"),
    share: bool = typer.Option(False, "--share", help="Upload HTML report to here.now and print URL"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to file"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON output"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub API token (or set GITHUB_TOKEN env var)"),
    generate: bool = typer.Option(False, "--generate", help="Auto-generate CLAUDE.md for repos below threshold, then re-score and show before/after lift"),
    generate_only_below: int = typer.Option(80, "--generate-only-below", help="Only regenerate repos scoring below N (default: 80)"),
) -> None:
    """Score every public repo in a GitHub org or user account."""
    org_command(
        target=target,
        include_forks=include_forks,
        include_archived=include_archived,
        limit=limit,
        parallel=parallel,
        timeout=timeout,
        share=share,
        output=output,
        json_output=json_output,
        token=token,
        generate=generate,
        generate_only_below=generate_only_below,
    )


@app.command("serve")
def serve(
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Port to serve on (default: 7890)"),
    open_browser: bool = typer.Option(False, "--open", help="Auto-open browser after start"),
    json_output: bool = typer.Option(False, "--json", help="Print server URL as JSON and exit"),
    once: bool = typer.Option(False, "--once", help="Render dashboard once to stdout and exit"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
    live: bool = typer.Option(False, "--live", help="Poll DB every 5s and push SSE refresh events"),
) -> None:
    """Start a local web dashboard showing all toolkit runs."""
    serve_command(port=port, open_browser=open_browser, json_output=json_output, once=once, db_path=db_path, live=live)


@app.command("pr")
def pr(
    target: str = typer.Argument(..., help="Target repo in format github:owner/repo"),
    file: str = typer.Option("CLAUDE.md", "--file", "-f", help="Context file to generate (CLAUDE.md or AGENTS.md)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing context file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without making any git or API calls"),
    pr_title: str = typer.Option("feat: add CLAUDE.md for AI coding agents", "--pr-title", help="Custom PR title"),
    pr_body_file: Optional[Path] = typer.Option(None, "--pr-body-file", help="Path to custom PR body markdown file"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Submit a CLAUDE.md (or AGENTS.md) PR to a public GitHub repository."""
    pr_command(
        target=target,
        file=file,
        force=force,
        dry_run=dry_run,
        pr_title=pr_title,
        pr_body_file=pr_body_file,
        json_output=json_output,
    )


@app.command("campaign")
def campaign(
    target: str = typer.Argument("", help="Target spec: github:owner, topic:TOPIC, repos-file:PATH, or leave blank with --from-search"),
    limit: int = typer.Option(5, "--limit", help="Max repos to target [default: 5]"),
    language: Optional[str] = typer.Option(None, "--language", help="Filter by language (e.g. python, typescript)"),
    min_stars: int = typer.Option(100, "--min-stars", help="Minimum stars threshold [default: 100]"),
    file: str = typer.Option("CLAUDE.md", "--file", help="Context file name to generate [default: CLAUDE.md]"),
    force: bool = typer.Option(False, "--force", help="Submit PR even if context file exists"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would happen, no PRs opened"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON instead of rich table"),
    no_filter: bool = typer.Option(False, "--no-filter", help="Skip the 'already has context file' check"),
    skip_pr: bool = typer.Option(False, "--skip-pr", help="Only discover repos, don't submit PRs"),
    share: bool = typer.Option(False, "--share", help="Generate and upload a shareable campaign report"),
    from_search: Optional[str] = typer.Option(None, "--from-search", help="Auto-discover repos via agentkit search before submitting PRs (provide search query)"),
    topic: Optional[str] = typer.Option(None, "--topic", help="Topic filter for --from-search"),
) -> None:
    """Submit CLAUDE.md PRs to multiple repos in one command."""
    effective_target = target

    if from_search is not None:
        # Run search to find missing-context repos, then use them as targets
        from agentkit_cli.search import SearchEngine
        from agentkit_cli.campaign import RepoSpec
        console = __import__("rich.console", fromlist=["Console"]).Console()
        console.print(f"[bold]--from-search:[/bold] discovering repos for [cyan]{from_search!r}[/cyan]…")
        engine = SearchEngine()
        results = engine.search(
            query=from_search,
            language=language,
            min_stars=min_stars if min_stars > 0 else None,
            topic=topic,
            limit=limit,
            missing_only=True,
        )
        if not results:
            console.print("[yellow]No repos found via search. Exiting.[/yellow]")
            raise typer.Exit(code=0)
        # Write a temp targets file and use repos-file: target
        import tempfile, os
        specs = [{"owner": r.owner, "repo": r.repo, "stars": r.stars, "language": r.language} for r in results]
        tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        import json as _json
        tmpfile.write(_json.dumps(specs))
        tmpfile.close()
        effective_target = f"repos-file:{tmpfile.name}"
        console.print(f"  Found {len(results)} repos. Running campaign…\n")

    if not effective_target:
        typer.echo("Error: provide a target argument or --from-search QUERY", err=True)
        raise typer.Exit(code=1)

    campaign_command(
        target=effective_target,
        limit=limit,
        language=language,
        min_stars=min_stars,
        file=file,
        force=force,
        dry_run=dry_run,
        json_output=json_output,
        no_filter=no_filter,
        skip_pr=skip_pr,
        share=share,
    )


@app.command("track")
def track(
    campaign_id: Optional[str] = typer.Option(None, "--campaign-id", help="Filter to a specific campaign"),
    limit: int = typer.Option(20, "--limit", help="Max PRs to show (default 20)"),
    all_prs: bool = typer.Option(False, "--all", help="Show all tracked PRs (no limit)"),
    json_output: bool = typer.Option(False, "--json", help="Output structured JSON"),
    share: bool = typer.Option(False, "--share", help="Upload dark-theme HTML report to here.now"),
) -> None:
    """Track PR status for campaign-submitted pull requests."""
    track_command(
        campaign_id=campaign_id,
        limit=limit,
        all_prs=all_prs,
        json_output=json_output,
        share=share,
    )


@app.command("redteam")
def redteam(
    path: Optional[Path] = typer.Argument(None, help="Project directory to analyze (default: cwd)"),
    categories: Optional[str] = typer.Option(None, "--categories", help="Comma-separated categories to test (default: all)"),
    attacks_per_category: int = typer.Option(3, "--attacks-per-category", help="Attack samples per category (default: 3)"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
    share: bool = typer.Option(False, "--share", help="Upload HTML report to here.now and print URL"),
    min_score: Optional[int] = typer.Option(None, "--min-score", help="Exit 1 if overall score < N (CI gate)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save HTML report to file"),
    fix: bool = typer.Option(False, "--fix", help="Auto-patch detected vulnerabilities in place"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what --fix would change without writing"),
) -> None:
    """Adversarial eval: score how well your agent context file resists attacks. CI-gate ready."""
    redteam_command(
        path=path,
        categories=categories,
        attacks_per_category=attacks_per_category,
        json_output=json_output,
        share=share,
        min_score=min_score,
        output=output,
        fix=fix,
        dry_run=dry_run,
    )


@app.command("harden")
def harden(
    path: Optional[Path] = typer.Argument(None, help="Context file or directory (default: cwd)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write hardened file to this path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without writing"),
    report: bool = typer.Option(False, "--report", help="Generate dark-theme HTML report"),
    share: bool = typer.Option(False, "--share", help="Upload report to here.now and return URL"),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON output"),
) -> None:
    """Analyze and auto-harden an agent context file. Applies all safe remediations and shows score lift."""
    harden_command(path=path, output=output, dry_run=dry_run, report=report, share=share, json_output=json_output)


@app.command("watch")
def watch(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory to watch"),
    extensions: Optional[List[str]] = typer.Option(None, "--extensions", help="File extensions to watch (e.g. .py,.md)"),
    debounce: float = typer.Option(2.0, "--debounce", help="Debounce delay in seconds"),
    ci: bool = typer.Option(False, "--ci", help="Run pipeline in CI mode on changes"),
    serve: bool = typer.Option(False, "--serve", help="Also start the dashboard HTTP server"),
    port: int = typer.Option(DEFAULT_PORT, "--port", help="Dashboard port (used with --serve)"),
) -> None:
    """Watch the project for changes and re-run the pipeline automatically."""
    watch_command(path=path, extensions=extensions, debounce=debounce, ci=ci, serve=serve, port=port)


@app.command("explain")
def explain(
    path: Optional[Path] = typer.Argument(None, help="Project directory (default: cwd)"),
    report: Optional[str] = typer.Option(None, "--report", help="Load from existing report JSON file"),
    model: str = typer.Option("claude-3-5-haiku-20241022", "--model", help="LLM model to use"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Force template-based explanation (offline, no API key needed)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON with score, tier, explanation, recommendations"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write markdown coaching report to file"),
) -> None:
    """Generate an LLM-powered coaching report explaining your agent quality scores."""
    explain_command(
        path=path,
        report_path=report,
        model=model,
        no_llm=no_llm,
        json_output=json_output,
        output=output,
    )


@app.command("improve")
def improve(
    target: Optional[str] = typer.Argument(None, help="Local path or github:owner/repo (default: current dir)"),
    no_generate: bool = typer.Option(False, "--no-generate", help="Skip CLAUDE.md generation step"),
    no_harden: bool = typer.Option(False, "--no-harden", help="Skip redteam hardening step"),
    min_lift: Optional[float] = typer.Option(None, "--min-lift", help="Exit 1 if score delta < N"),
    pr: bool = typer.Option(False, "--pr", help="Open a GitHub PR with changes after improving"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan without applying changes"),
    json_output: bool = typer.Option(False, "--json", help="Output structured JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write HTML report to file"),
) -> None:
    """Analyze → fix → re-analyze. Shows before/after score and what changed."""
    improve_command(
        target=target,
        no_generate=no_generate,
        no_harden=no_harden,
        min_lift=min_lift,
        pr=pr,
        dry_run=dry_run,
        json_output=json_output,
        share=share,
        output=output,
    )


@app.command("migrate")
def migrate(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    from_format: Optional[str] = typer.Option(None, "--from", help="Source format: agents-md, claude-md, llmstxt, auto"),
    to_format: Optional[str] = typer.Option(None, "--to", help="Target format: agents-md, claude-md, llmstxt, all"),
    all_formats: bool = typer.Option(False, "--all", help="Equivalent to --to all"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print what would be written without writing"),
    diff: bool = typer.Option(False, "--diff", help="Show before/after diff of each file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write to specific file"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without prompting"),
) -> None:
    """Convert between AGENTS.md, CLAUDE.md, and llms.txt formats."""
    migrate_command(
        path=path,
        from_format=from_format,
        to_format=to_format,
        all_formats=all_formats,
        dry_run=dry_run,
        diff=diff,
        output=output,
        force=force,
    )


@app.command("sync")
def sync(
    path: Optional[str] = typer.Argument(None, help="Project directory (default: .)"),
    check: bool = typer.Option(False, "--check", help="Report sync status; exit 1 if stale"),
    fix: bool = typer.Option(False, "--fix", help="Re-run migrate to bring derived files in sync"),
) -> None:
    """Check or fix sync status between AGENTS.md, CLAUDE.md, and llms.txt."""
    sync_command(path=path, check=check, fix=fix)


@app.command("llmstxt")
def llmstxt(
    target: str = typer.Argument(".", help="Local path or github:owner/repo"),
    full: bool = typer.Option(False, "--full", help="Also generate llms-full.txt with inline file content"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Write files to directory (default: cwd)"),
    json_output: bool = typer.Option(False, "--json", help="Structured JSON output"),
    share: bool = typer.Option(False, "--share", help="Publish to here.now and return URL"),
    validate: bool = typer.Option(False, "--validate", help="Validate existing llms.txt against spec"),
    score: bool = typer.Option(False, "--score", help="Include quality score (0-100)"),
    sync_from: Optional[str] = typer.Option(None, "--sync-from", help="Generate llms.txt from agents-md or claude-md"),
) -> None:
    """Generate llms.txt (and optionally llms-full.txt) for a repository."""
    llmstxt_command(
        target=target,
        full=full,
        output_dir=output_dir,
        json_output=json_output,
        share=share,
        validate=validate,
        score=score,
        sync_from=sync_from,
    )


@app.command("search")
def search(
    query: str = typer.Argument("", help="Free-text search query (e.g. 'ai agents')"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Filter by language (e.g. python)"),
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by GitHub topic"),
    min_stars: Optional[int] = typer.Option(None, "--min-stars", help="Minimum star count"),
    max_stars: Optional[int] = typer.Option(None, "--max-stars", help="Maximum star count"),
    missing_only: bool = typer.Option(False, "--missing-only", help="Only repos without context files"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum repos to return (default: 20)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write HTML report to file"),
    github_token: Optional[str] = typer.Option(None, "--github-token", help="GitHub API token (or set GITHUB_TOKEN)"),
    no_check: bool = typer.Option(False, "--no-check", help="Skip Contents API checks (faster, no context status)"),
) -> None:
    """🔍 Discover GitHub repos missing CLAUDE.md / AGENTS.md."""
    search_command(
        query=query,
        language=language,
        topic=topic,
        min_stars=min_stars,
        max_stars=max_stars,
        missing_only=missing_only,
        limit=limit,
        json_output=json_output,
        share=share,
        output=output,
        github_token=github_token,
        no_check=no_check,
    )


@app.command("digest")
def digest(
    period: int = typer.Option(7, "--period", help="Number of days to include in the digest"),
    projects: Optional[str] = typer.Option(None, "--projects", help="Comma-separated project names to include"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    quiet: bool = typer.Option(False, "--quiet", help="Print summary line only"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write HTML report to file"),
    share: bool = typer.Option(False, "--share", help="Publish digest to here.now"),
    notify_slack: Optional[str] = typer.Option(None, "--notify-slack", help="Slack webhook URL for digest"),
    notify_discord: Optional[str] = typer.Option(None, "--notify-discord", help="Discord webhook URL for digest"),
    db_path: Optional[Path] = typer.Option(None, "--db-path", help="Custom history DB path (default: ~/.config/agentkit/history.db)", hidden=True),
) -> None:
    """Generate a quality digest across all tracked projects."""
    from agentkit_cli.digest import DigestEngine
    from agentkit_cli.digest_report import DigestReportRenderer

    project_list = [p.strip() for p in projects.split(",")] if projects else None

    engine = DigestEngine(db_path=db_path, period_days=period)
    report = engine.generate(projects=project_list)

    if json_output:
        import json as _json
        typer.echo(_json.dumps(report.to_dict(), indent=2))
        raise typer.Exit(0)

    if quiet:
        typer.echo(
            f"digest: {report.period_start.strftime('%Y-%m-%d')} → {report.period_end.strftime('%Y-%m-%d')} | "
            f"{report.projects_tracked} projects | {report.runs_in_period} runs | trend: {report.overall_trend}"
        )
        raise typer.Exit(0)

    # Rich console output
    typer.echo("")
    typer.echo(f"  agentkit quality digest")
    typer.echo(f"  Period : {report.period_start.strftime('%Y-%m-%d')} → {report.period_end.strftime('%Y-%m-%d')}")
    typer.echo(f"  Trend  : {report.overall_trend.upper()}")
    typer.echo(f"  Projects tracked : {report.projects_tracked}")
    typer.echo(f"  Runs in period   : {report.runs_in_period}")
    typer.echo(f"  Coverage         : {report.coverage_pct:.1f}%")
    typer.echo(f"  Regressions      : {len(report.regressions)}")
    typer.echo(f"  Improvements     : {len(report.improvements)}")
    typer.echo("")

    if report.per_project:
        typer.echo("  Per-project:")
        typer.echo(f"  {'Project':<30} {'Start':>6} {'End':>6} {'Delta':>7} {'Runs':>5} {'Status'}")
        typer.echo("  " + "-" * 65)
        for p in report.per_project:
            start = f"{p.score_start:.1f}" if p.score_start is not None else "  —  "
            end = f"{p.score_end:.1f}" if p.score_end is not None else "  —  "
            delta_str = (f"+{p.delta:.1f}" if p.delta and p.delta > 0 else f"{p.delta:.1f}") if p.delta is not None else "  —  "
            typer.echo(f"  {p.name:<30} {start:>6} {end:>6} {delta_str:>7} {p.runs:>5}   {p.status}")
        typer.echo("")

    if report.top_actions:
        typer.echo("  Top action items:")
        for action in report.top_actions[:5]:
            typer.echo(f"    → {action}")
        typer.echo("")

    renderer = DigestReportRenderer()
    html = renderer.render(report)

    if output:
        output.write_text(html, encoding="utf-8")
        typer.echo(f"  Digest report written to: {output}")

    if share:
        from agentkit_cli.share import upload_scorecard
        url = upload_scorecard(html)
        if url:
            typer.echo(f"  Shared at: {url}")
        else:
            typer.echo("  Share failed (check HERENOW_API_KEY)", err=True)

    if notify_slack or notify_discord:
        from agentkit_cli.notifier import resolve_notify_configs, fire_notifications
        summary = (
            f"agentkit digest | {report.period_start.strftime('%Y-%m-%d')} → {report.period_end.strftime('%Y-%m-%d')} | "
            f"trend: {report.overall_trend} | {report.projects_tracked} projects | {report.runs_in_period} runs"
        )
        configs = resolve_notify_configs(
            notify_slack=notify_slack,
            notify_discord=notify_discord,
            notify_on="always",
            project_name="agentkit-digest",
        )
        for cfg in configs:
            from agentkit_cli.notifier import NotifyConfig, build_payload, _send_with_retry
            payload = build_payload(cfg, 0.0, "DIGEST", [summary[:200]], None)
            _send_with_retry(cfg.url, payload)

    raise typer.Exit(0)


@app.command("benchmark")
def benchmark(
    path: Path = typer.Argument(Path("."), help="Project path (default: current dir)"),
    agents: Optional[str] = typer.Option(None, "--agents", help="Comma-separated agents (default: claude,codex,gemini)"),
    tasks: Optional[str] = typer.Option(None, "--tasks", help="Comma-separated tasks (default: all 5)"),
    rounds: int = typer.Option(1, "--rounds", help="Rounds per task (3+ for statistical confidence)"),
    timeout: int = typer.Option(300, "--timeout", help="Timeout per task in seconds"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON to stdout"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save HTML report to file"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Minimal output"),
) -> None:
    """🏆 Benchmark Claude vs Codex vs Gemini on your own codebase."""
    benchmark_command(
        path=path,
        agents=agents,
        tasks=tasks,
        rounds=rounds,
        timeout=timeout,
        json_output=json_output,
        output=output,
        share=share,
        quiet=quiet,
    )


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
