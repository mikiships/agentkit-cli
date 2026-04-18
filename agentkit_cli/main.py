"""agentkit CLI entry point."""
from __future__ import annotations

import typer
from typing import List, Optional
from pathlib import Path

from agentkit_cli.commands.api_cmd import api_command
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
from agentkit_cli.commands.gist_cmd import gist_command
from agentkit_cli.commands.analyze_cmd import analyze_command
from agentkit_cli.commands.frameworks_cmd import frameworks_command
from agentkit_cli.commands.sweep_cmd import sweep_command
from agentkit_cli.commands.gate_cmd import gate_command
from agentkit_cli.commands.setup_ci_cmd import setup_ci_command
from agentkit_cli.commands.release_check_cmd import release_check_command
from agentkit_cli.commands.changelog_cmd import changelog_command
from agentkit_cli.commands.notify_cmd import notify_app
from agentkit_cli.commands.config_cmd import config_app
from agentkit_cli.commands.profile_cmd import profile_app
from agentkit_cli.commands.insights_cmd import insights_command
from agentkit_cli.commands.trending_cmd import trending_command
from agentkit_cli.commands.duel_cmd import duel_command
from agentkit_cli.commands.tournament_cmd import tournament_command
from agentkit_cli.commands.org_cmd import org_command
from agentkit_cli.commands.pages_org_cmd import pages_org_command
from agentkit_cli.commands.pages_trending_cmd import pages_trending_command
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
from agentkit_cli.commands.optimize_cmd import optimize_command
from agentkit_cli.commands.monitor import monitor_app
from agentkit_cli.commands.webhook import webhook_app
from agentkit_cli.commands.checks_cmd import checks_app
from agentkit_cli.commands.llmstxt_cmd import llmstxt_command
from agentkit_cli.commands.migrate_cmd import migrate_command
from agentkit_cli.commands.sync_cmd import sync_command
from agentkit_cli.commands.search_cmd import search_command
from agentkit_cli.commands.benchmark_cmd import benchmark_command
from agentkit_cli.commands.daily_cmd import daily_command
from agentkit_cli.commands.weekly_cmd import weekly_command
from agentkit_cli.commands.user_scorecard_cmd import user_scorecard_command
from agentkit_cli.commands.user_badge_cmd import user_badge_command
from agentkit_cli.commands.user_duel_cmd import user_duel_command
from agentkit_cli.commands.user_tournament_cmd import user_tournament_command
from agentkit_cli.commands.user_improve_cmd import user_improve_command
from agentkit_cli.commands.user_card_cmd import user_card_command
from agentkit_cli.commands.user_team_cmd import user_team_command
from agentkit_cli.commands.user_rank_cmd import user_rank_command
from agentkit_cli.commands.topic_rank_cmd import topic_rank_command
from agentkit_cli.commands.topic_duel_cmd import topic_duel_command
from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
from agentkit_cli.commands.topic_league_cmd import topic_league_command
from agentkit_cli.commands.ecosystem_cmd import ecosystem_command
from agentkit_cli.commands.spotlight_cmd import spotlight_command
from agentkit_cli.commands.spotlight_queue_cmd import app as spotlight_queue_app
from agentkit_cli.commands.hooks_cmd import hooks_app
from agentkit_cli.commands.weekly_digest_cmd import app as weekly_digest_app
from agentkit_cli.commands.daily_duel_cmd import daily_duel_command
from agentkit_cli.commands.hot_cmd import hot_command
from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command
from agentkit_cli.commands.pages_refresh import pages_refresh_command
from agentkit_cli.commands.site_cmd import site_command
from agentkit_cli.commands.populate_cmd import populate_command
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
app.add_typer(spotlight_queue_app, name="spotlight-queue")
app.add_typer(hooks_app, name="hooks")
app.add_typer(weekly_digest_app, name="weekly-digest")


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
    improve_optimize_context: bool = typer.Option(False, "--improve-optimize-context", help="Also run context optimization inside --improve"),
    improve_threshold: float = typer.Option(80.0, "--improve-threshold", help="Score threshold below which --improve runs (default 80)"),
    webhook_notify: bool = typer.Option(False, "--webhook-notify", help="POST result to configured webhook URL after run"),
    checks: Optional[bool] = typer.Option(None, "--checks/--no-checks", help="Post a GitHub Check Run (default: auto-detect GitHub Actions env)"),
    run_llmstxt: bool = typer.Option(False, "--llmstxt", help="Generate llms.txt after pipeline completes"),
    run_migrate: bool = typer.Option(False, "--migrate", help="Auto-generate missing context format files before analysis"),
    run_digest: bool = typer.Option(False, "--digest", help="Print a quality digest for this project after the run"),
    agent_benchmark: bool = typer.Option(False, "--agent-benchmark", help="Run cross-agent benchmark after pipeline and include result in output"),
    run_user_duel: Optional[str] = typer.Option(None, "--user-duel", help="Run user duel after pipeline (format: user1:user2)"),
    run_user_tournament: Optional[str] = typer.Option(None, "--user-tournament", help="Run user tournament after pipeline (format: user1:user2:...)"),
    run_user_improve: Optional[str] = typer.Option(None, "--user-improve", help="Run user-improve after pipeline (format: github:<user>)"),
    run_user_card: Optional[str] = typer.Option(None, "--user-card", help="Run user-card after pipeline (format: github:<user>)"),
    run_user_rank_topic: Optional[str] = typer.Option(None, "--topic", help="Run user-rank for topic after pipeline (e.g. python)"),
    run_topic_repos: Optional[str] = typer.Option(None, "--topic-repos", help="Run topic repo-rank after pipeline (e.g. python)"),
    run_topic_league: Optional[str] = typer.Option(None, "--topic-league", help="Run topic-league after pipeline (e.g. python rust go)"),
    run_ecosystem: Optional[str] = typer.Option(None, "--ecosystem", help="Run ecosystem scan after pipeline (preset: default, extended, or custom)"),
    run_gist: bool = typer.Option(False, "--gist", help="Publish run report as a GitHub Gist after completion"),
    run_site: Optional[str] = typer.Option(None, "--site", help="Regenerate site index.html in this directory after run"),
    run_populate: bool = typer.Option(False, "--populate", help="After scoring, populate history DB with top repos for detected topics"),
    run_populate_topics: Optional[str] = typer.Option(None, "--populate-topics", help="Topics for --populate (default: python,typescript,rust,go)"),
    run_populate_limit: int = typer.Option(10, "--populate-limit", help="Max repos per topic for --populate"),
    run_frameworks: bool = typer.Option(False, "--frameworks", help="Run frameworks check after pipeline and include result in output"),
    api_cache: bool = typer.Option(False, "--api-cache", help="Warm API cache after run (best-effort)"),
    run_pages: bool = typer.Option(False, "--pages", help="Add result to leaderboard (docs/data.json) after run"),
) -> None:
    """Run the full Agent Quality pipeline sequentially."""
    run_command(path=path, skip=skip, benchmark=benchmark, json_output=json_output, notes=notes, ci=ci, publish=publish, inject_readme=inject_readme, no_history=no_history, label=label, notify_slack=notify_slack, notify_discord=notify_discord, notify_webhook=notify_webhook, notify_on=notify_on, profile=profile, share=share, release_check=release_check, record_findings=record_findings, harden=run_harden, timeline=run_timeline, explain=run_explain, no_llm=no_llm, improve=run_improve, improve_no_generate=improve_no_generate, improve_no_harden=improve_no_harden, improve_optimize_context=improve_optimize_context, improve_threshold=improve_threshold, webhook_notify=webhook_notify, checks=checks, llmstxt=run_llmstxt, migrate=run_migrate, agent_benchmark=agent_benchmark, user_duel=run_user_duel, user_tournament=run_user_tournament, user_improve=run_user_improve, user_card=run_user_card, user_rank_topic=run_user_rank_topic, ecosystem=run_ecosystem, gist=run_gist, site_dir=run_site, populate=run_populate, populate_topics=run_populate_topics, populate_limit=run_populate_limit, frameworks=run_frameworks, api_cache=api_cache)
    if run_pages:
        try:
            from agentkit_cli.pages_sync_engine import SyncEngine
            SyncEngine().sync(push=False)
            typer.echo("✓ Added to leaderboard: https://mikiships.github.io/agentkit-cli/")
        except Exception as _pe:
            typer.echo(f"Warning: pages sync failed — {_pe}")
    if run_topic_repos:
        from agentkit_cli.commands.topic_rank_cmd import topic_rank_command
        topic_rank_command(topic=run_topic_repos.strip())
    if run_topic_league:
        from agentkit_cli.commands.topic_league_cmd import topic_league_command as _tlc
        _tlc(topics=[t.strip() for t in run_topic_league.split() if t.strip()])
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
    report_user_duel: Optional[str] = typer.Option(None, "--user-duel", help="Include user duel section (format: user1:user2)"),
    report_user_tournament: Optional[str] = typer.Option(None, "--user-tournament", help="Include user tournament section (format: user1:user2:...)"),
    report_user_improve: Optional[str] = typer.Option(None, "--user-improve", help="Include user-improve section (format: github:<user>)"),
    report_user_card: Optional[str] = typer.Option(None, "--user-card", help="Include user-card section (format: github:<user>)"),
    spotlight_feed: bool = typer.Option(False, "--spotlight-feed", help="Show spotlight run feed instead of project report"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
    report_gist: bool = typer.Option(False, "--gist", help="Publish HTML report as a GitHub Gist after generation"),
) -> None:
    """Run all toolkit checks and generate a self-contained HTML quality report."""
    if spotlight_feed:
        _show_spotlight_feed(json_output=json_output, db_path=db_path)
        return
    report_command(path=path, json_output=json_output, output=output, open_browser=open_browser, publish=publish, inject_readme=inject_readme, share=share, llmstxt=report_llmstxt, user_duel=report_user_duel, user_tournament=report_user_tournament, user_improve=report_user_improve, user_card=report_user_card, gist=report_gist)
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


@app.command("gist")
def gist(
    from_file: Optional[Path] = typer.Option(None, "--from", help="Path to a file to publish as a gist"),
    public: bool = typer.Option(False, "--public", help="Create a public gist (default: private/secret)"),
    description: str = typer.Option("agentkit analysis report", "--description", help="Gist description"),
    fmt: str = typer.Option("markdown", "--format", help="Output format: markdown or html"),
) -> None:
    """Publish a report or analysis output as a permanent GitHub Gist."""
    gist_command(from_file=from_file, public=public, description=description, fmt=fmt)


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
    spotlights: bool = typer.Option(False, "--spotlights", help="Show only spotlight runs"),
    duels: bool = typer.Option(False, "--duels", help="Show only repo-duel runs"),
) -> None:
    """Show agent quality score history and trends."""
    if spotlights:
        _show_spotlight_history(limit=limit, json_output=json_output, db_path=db_path)
        return
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
        duels=duels,
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


@app.command("frameworks")
def frameworks(
    path: Path = typer.Argument(Path("."), help="Project directory to analyze (default: .)"),
    context_file: Optional[Path] = typer.Option(None, "--context-file", help="Explicit path to CLAUDE.md/AGENTS.md"),
    min_score: int = typer.Option(60, "--min-score", help="Highlight frameworks scoring below N (default: 60)"),
    json_output: bool = typer.Option(False, "--json", help="Structured JSON output"),
    quiet: bool = typer.Option(False, "--quiet", help="Summary line only"),
    share: bool = typer.Option(False, "--share", help="Upload report to here.now and print URL"),
    generate: bool = typer.Option(False, "--generate", help="Auto-add missing framework sections to context file"),
) -> None:
    """Detect frameworks and check if agent context file covers them."""
    frameworks_command(
        path=path,
        context_file=context_file,
        min_score=min_score,
        json_output=json_output,
        quiet=quiet,
        share=share,
        generate=generate,
    )


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
    analyze_gist: bool = typer.Option(False, "--gist", help="Publish analyze output as a GitHub Gist"),
    analyze_pages: bool = typer.Option(False, "--pages", help="Add result to leaderboard (docs/data.json) after analysis"),
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
        gist=analyze_gist,
        pages=analyze_pages,
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


@app.command("changelog")
def changelog(
    since: Optional[str] = typer.Option(None, "--since", help="Git ref or tag baseline (default: last tag)"),
    version: Optional[str] = typer.Option(None, "--version", help="Version string for header (e.g. v0.93.0)"),
    fmt: str = typer.Option("markdown", "--format", help="Output format: markdown|release|json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write to file instead of stdout"),
    score_delta: bool = typer.Option(True, "--score-delta/--no-score-delta", help="Include quality score delta from history DB"),
    no_chore: bool = typer.Option(False, "--no-chore", help="Exclude chore/test/ci commits"),
    project: Optional[str] = typer.Option(None, "--project", help="Project path for score delta lookup"),
    github_release: bool = typer.Option(False, "--github-release", help="Alias for --format release"),
    create_release: bool = typer.Option(False, "--create-release", help="Create a GitHub release using gh CLI (requires --version)"),
) -> None:
    """Generate an AI-friendly changelog from git commits + quality score deltas."""
    changelog_command(
        since=since,
        version=version,
        fmt=fmt,
        output=output,
        score_delta=score_delta,
        no_chore=no_chore,
        project=project,
        github_release=github_release,
        create_release=create_release,
    )


@app.command("release-check")
def release_check(
    path: Optional[Path] = typer.Argument(None, help="Project directory (default: cwd)"),
    version: Optional[str] = typer.Option(None, "--version", help="Version to check (default: from pyproject.toml/package.json)"),
    package: Optional[str] = typer.Option(None, "--package", help="Package name (default: from pyproject.toml/package.json)"),
    registry: str = typer.Option("auto", "--registry", help="Registry to check: pypi|npm|auto"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip the pytest/npm test step"),
    json_output: bool = typer.Option(False, "--json", help="Output structured JSON for CI integration"),
    changelog: bool = typer.Option(False, "--changelog", help="Generate and append a changelog preview to the output"),
) -> None:
    """Verify the release surface: smoke tests, tests, git push, tag, and registry."""
    release_check_command(
        path=path,
        version=version,
        package=package,
        registry=registry,
        skip_tests=skip_tests,
        json_output=json_output,
        changelog=changelog,
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


@app.command("daily")
def daily(
    date_str: Optional[str] = typer.Option(None, "--date", help="Date to fetch leaderboard for (YYYY-MM-DD, default: today)"),
    limit: int = typer.Option(20, "--limit", help="Max repos to fetch (default: 20)"),
    min_score: float = typer.Option(0.0, "--min-score", help="Filter repos below this composite score"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now and print URL"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON instead of table"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save HTML report to file"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential output (cron-friendly)"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub API token (or GITHUB_TOKEN env var)", envvar="GITHUB_TOKEN"),
    pages: bool = typer.Option(False, "--pages", help="Publish HTML to GitHub Pages (permanent URL)"),
    pages_repo: Optional[str] = typer.Option(None, "--pages-repo", help="Target repo for Pages publish (format: github:owner/repo)"),
    pages_path: str = typer.Option("docs/leaderboard.html", "--pages-path", help="Output path within repo (default: docs/leaderboard.html)"),
) -> None:
    """Generate a daily leaderboard of the most agent-ready GitHub repos."""
    daily_command(
        date_str=date_str,
        limit=limit,
        min_score=min_score,
        share=share,
        json_output=json_output,
        output=output,
        quiet=quiet,
        token=token,
        pages=pages,
        pages_repo=pages_repo,
        pages_path=pages_path,
    )


@app.command("weekly")
def weekly(
    days: int = typer.Option(7, "--days", help="Number of days to look back (default: 7)"),
    project: Optional[list[str]] = typer.Option(None, "--project", "-p", help="Filter to specific projects (repeatable)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON instead of table"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save HTML report to file"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential output (cron-friendly)"),
    tweet_only: bool = typer.Option(False, "--tweet-only", help="Print only the tweet-ready summary and exit"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report and print URL"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override history DB path"),
) -> None:
    """Generate a 7-day agent quality digest across all tracked projects."""
    weekly_command(
        days=days,
        projects=project or None,
        json_output=json_output,
        output=output,
        quiet=quiet,
        tweet_only=tweet_only,
        share=share,
        db_path=db_path,
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
    pages: bool = typer.Option(False, "--pages", help="After scoring, publish org leaderboard to GitHub Pages"),
    pages_repo: Optional[str] = typer.Option(None, "--pages-repo", help="GitHub Pages repo (default: <owner>/agentkit-scores)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Score repos but skip git push when --pages is set"),
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
        pages=pages,
        pages_repo=pages_repo,
        dry_run=dry_run,
    )


@app.command("pages-org")
def pages_org(
    target: str = typer.Argument(..., help="GitHub org to score: 'github:vercel'"),
    pages_repo: Optional[str] = typer.Option(None, "--pages-repo", help="GitHub repo for Pages (default: <owner>/agentkit-scores)"),
    pages_path: str = typer.Option("docs/", "--pages-path", help="Subdirectory in repo for HTML (default: docs/)"),
    pages_branch: str = typer.Option("main", "--pages-branch", help="Branch (default: main)"),
    only_below: Optional[int] = typer.Option(None, "--only-below", help="Only include repos scoring below this threshold"),
    limit: int = typer.Option(50, "--limit", help="Max repos to score (default: 50)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON result instead of rich table"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress progress, print only final URL"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Score repos but skip git push"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub API token (or set GITHUB_TOKEN env var)"),
) -> None:
    """Score all public repos in a GitHub org and publish an org-wide leaderboard to GitHub Pages."""
    pages_org_command(
        target=target,
        pages_repo=pages_repo,
        pages_path=pages_path,
        pages_branch=pages_branch,
        only_below=only_below,
        limit=limit,
        json_output=json_output,
        quiet=quiet,
        dry_run=dry_run,
        token=token,
    )


@app.command("pages-trending")
def pages_trending(
    pages_repo: Optional[str] = typer.Option(None, "--pages-repo", help="GitHub repo for Pages (default: detect or <owner>/agentkit-trending)"),
    limit: int = typer.Option(20, "--limit", help="Max repos to score (1-50, default: 20)"),
    language: Optional[str] = typer.Option(None, "--language", help="Filter trending by language (e.g. python)"),
    period: str = typer.Option("today", "--period", help="Trending period: today, week, month (default: today)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Score and generate HTML but skip git push"),
    quiet: bool = typer.Option(False, "--quiet", help="Print only the final Pages URL"),
    share: bool = typer.Option(False, "--share", help="Also publish to here.now for 24h preview"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON result"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub API token (or set GITHUB_TOKEN)"),
) -> None:
    """Fetch trending GitHub repos, score them with agentkit, publish leaderboard to GitHub Pages."""
    pages_trending_command(
        pages_repo=pages_repo,
        limit=limit,
        language=language,
        period=period,
        dry_run=dry_run,
        quiet=quiet,
        share=share,
        json_output=json_output,
        token=token,
    )


@app.command("pages-sync")
def pages_sync(
    push: bool = typer.Option(True, "--push/--no-push", help="Commit and push docs/data.json to git (default: push)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be synced without writing"),
    json_output: bool = typer.Option(False, "--json", help="Output sync summary as JSON"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Only sync top N repos by score (default: all)"),
    docs_dir: Optional[Path] = typer.Option(None, "--docs-dir", help="Docs directory (default: docs/)"),
) -> None:
    """Sync local history DB results to docs/data.json and push to GitHub."""
    from agentkit_cli.commands.pages_sync import pages_sync_command
    from agentkit_cli.pages_sync_engine import SyncEngine
    engine = SyncEngine(docs_dir=docs_dir)
    pages_sync_command(push=push, dry_run=dry_run, json_output=json_output, limit=limit, _engine=engine)


@app.command("pages-add")
def pages_add(
    target: str = typer.Argument(..., help="GitHub repo to add: github:owner/repo"),
    push: bool = typer.Option(True, "--push/--no-push", help="Commit and push after adding (default: push)"),
    share: bool = typer.Option(False, "--share", help="Publish a scorecard and include URL in data.json"),
    docs_dir: Optional[Path] = typer.Option(None, "--docs-dir", help="Docs directory (default: docs/)"),
) -> None:
    """Analyze a single repo and add it to the leaderboard."""
    from agentkit_cli.commands.pages_add import pages_add_command
    pages_add_command(target=target, push=push, share=share, docs_dir=docs_dir)


@app.command("pages-refresh")
def pages_refresh(
    ecosystems: Optional[str] = typer.Option(None, "--ecosystems", help="Comma-separated ecosystems (default: python,typescript,rust,go)"),
    limit: int = typer.Option(5, "--limit", help="Repos per ecosystem (default: 5, max 25)"),
    docs_dir: Optional[Path] = typer.Option(None, "--docs-dir", help="Docs directory (default: docs/)"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub API token (or set GITHUB_TOKEN)"),
) -> None:
    """Refresh GitHub Pages leaderboard: score ecosystems, write docs/data.json + docs/leaderboard.html, update docs/index.html."""
    pages_refresh_command(
        ecosystems=ecosystems,
        limit=limit,
        docs_dir=docs_dir,
        token=token,
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
    optimize_context: bool = typer.Option(False, "--optimize-context", help="Also run agentkit optimize inside improve"),
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
        optimize_context=optimize_context,
        json_output=json_output,
        share=share,
        output=output,
    )


@app.command("optimize")
def optimize(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory (default: cwd)"),
    file: Optional[Path] = typer.Option(None, "--file", help="Explicit CLAUDE.md or AGENTS.md target"),
    all_files: bool = typer.Option(False, "--all", help="Discover and optimize all CLAUDE.md and AGENTS.md files under the repo"),
    check: bool = typer.Option(False, "--check", help="Exit non-zero when meaningful rewrites are available"),
    apply: bool = typer.Option(False, "--apply", help="Overwrite the targeted context file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Write review or optimized content to file"),
    json_output: bool = typer.Option(False, "--json", help="Output structured JSON"),
    fmt: str = typer.Option("text", "--format", help="Review format: text or markdown"),
) -> None:
    """Optimize one context file or sweep repo context files."""
    optimize_command(path=path, file=file, all_files=all_files, check=check, apply=apply, output=output, json_output=json_output, fmt=fmt)


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


@app.command("user-scorecard")
def user_scorecard(
    target: str = typer.Argument(..., help="GitHub username: github:<user> or bare <user>"),
    limit: int = typer.Option(20, "--limit", help="Max repos to analyze (default: 20)"),
    min_stars: int = typer.Option(0, "--min-stars", help="Skip repos below this star count"),
    skip_forks: bool = typer.Option(True, "--skip-forks/--no-skip-forks", help="Exclude forked repos (default: True)"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
    share: bool = typer.Option(False, "--share", help="Upload HTML report to here.now and print URL"),
    pages: Optional[str] = typer.Option(None, "--pages", help="Publish HTML to GitHub Pages repo (github:<owner>/<repo>)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Print only final URL (for cron/scripting)"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout in seconds (default: 60)"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token (overrides GITHUB_TOKEN env var)"),
    badge: bool = typer.Option(False, "--badge", help="Print agent-readiness badge markdown after scorecard"),
) -> None:
    """🧑‍💻 Generate an agent-readiness profile card for a GitHub user's public repos."""
    user_scorecard_command(
        target=target,
        limit=limit,
        min_stars=min_stars,
        skip_forks=skip_forks,
        json_output=json_output,
        share=share,
        pages=pages,
        quiet=quiet,
        timeout=timeout,
        token=token,
        badge=badge,
    )


@app.command("user-duel")
def user_duel(
    user1: str = typer.Argument(..., help="First GitHub user: github:<user> or bare <user>"),
    user2: str = typer.Argument(..., help="Second GitHub user: github:<user> or bare <user>"),
    limit: int = typer.Option(10, "--limit", help="Max repos per user to score (default: 10)"),
    json_output: bool = typer.Option(False, "--json", help="Emit UserDuelResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress, just print winner"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout in seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token (overrides GITHUB_TOKEN env var)", envvar="GITHUB_TOKEN"),
) -> None:
    """⚔️  Head-to-head agent-readiness comparison of two GitHub developers."""
    # Parse github:<user> prefix for both args
    def _parse_user(t: str) -> str:
        if t.startswith("github:"):
            return t[len("github:"):]
        return t.strip("/").strip()

    user_duel_command(
        user1=_parse_user(user1),
        user2=_parse_user(user2),
        limit=limit,
        json_output=json_output,
        share=share,
        quiet=quiet,
        timeout=timeout,
        token=token,
    )


@app.command("user-tournament")
def user_tournament(
    participants: list[str] = typer.Argument(..., help="GitHub users: github:<user> or bare <user> (≥2 required)"),
    limit: int = typer.Option(10, "--limit", help="Max repos per user to score"),
    json_output: bool = typer.Option(False, "--json", help="Emit TournamentResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress, print champion only"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-user scorecard timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🏆  Bracket-style agent-readiness tournament for N GitHub developers."""
    def _parse_user(t: str) -> str:
        if t.startswith("github:"):
            return t[len("github:"):]
        return t.strip("/").strip()

    parsed = [_parse_user(p) for p in participants]
    user_tournament_command(
        participants=parsed,
        share=share,
        json_output=json_output,
        quiet=quiet,
        output=output,
        limit=limit,
        timeout=timeout,
        token=token,
    )


@app.command("user-team")
def user_team(
    target: str = typer.Argument(..., help="GitHub org: github:<org> or bare <org>"),
    limit: int = typer.Option(10, "--limit", help="Max contributors to fetch and score"),
    json_output: bool = typer.Option(False, "--json", help="Emit TeamScorecardResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-user scorecard timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🏢  Analyze a GitHub org's top contributors for agent-readiness."""
    user_team_command(
        target=target,
        limit=limit,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("user-rank")
def user_rank(
    topic: str = typer.Argument(..., help="GitHub topic to search (e.g. python, rust, llm)"),
    limit: int = typer.Option(20, "--limit", help="Max contributors to rank (default 20)"),
    json_output: bool = typer.Option(False, "--json", help="Emit UserRankResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-user scorecard timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🏆  Rank top GitHub contributors for a topic by agent-readiness."""
    user_rank_command(
        topic=topic,
        limit=limit,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("topic")
def topic(
    topic_name: str = typer.Argument(..., metavar="TOPIC", help="GitHub topic to search (e.g. python, llm, agents)"),
    limit: int = typer.Option(10, "--limit", help="Max repos to rank (default 10, max 25)"),
    language: Optional[str] = typer.Option(None, "--language", help="Filter by programming language (e.g. python)"),
    json_output: bool = typer.Option(False, "--json", help="Emit TopicRankResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🔍  Rank top GitHub repos for a topic by agent-readiness score."""
    topic_rank_command(
        topic=topic_name,
        limit=limit,
        language=language,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("topic-duel")
def topic_duel(
    topic1: str = typer.Argument(..., metavar="TOPIC1", help="First GitHub topic (e.g. fastapi)"),
    topic2: str = typer.Argument(..., metavar="TOPIC2", help="Second GitHub topic (e.g. django)"),
    repos_per_topic: int = typer.Option(5, "--repos-per-topic", help="Max repos per topic to score (1-10, default 5)"),
    json_output: bool = typer.Option(False, "--json", help="Emit TopicDuelResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """⚔️  Head-to-head agent-readiness comparison of two GitHub topics."""
    topic_duel_command(
        topic1=topic1,
        topic2=topic2,
        repos_per_topic=repos_per_topic,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("repo-duel")
def repo_duel(
    repo1: str = typer.Argument(..., help="First repo: github:owner/repo or https://..."),
    repo2: str = typer.Argument(..., help="Second repo: github:owner/repo or https://..."),
    deep: bool = typer.Option(False, "--deep", help="Add redteam resistance dimension"),
    json_output: bool = typer.Option(False, "--json", help="Emit RepoDuelResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(120, "--timeout", help="Per-repo analysis timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """⚔️  Head-to-head agent-readiness comparison of two GitHub repos."""
    repo_duel_command(
        repo1=repo1,
        repo2=repo2,
        deep=deep,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("topic-league")
def topic_league(
    topics: List[str] = typer.Argument(..., metavar="TOPIC...", help="2–10 GitHub topics to compare"),
    repos_per_topic: int = typer.Option(5, "--repos-per-topic", help="Max repos per topic to score (1-10, default 5)"),
    parallel: bool = typer.Option(False, "--parallel", help="Fetch topics in parallel (ThreadPoolExecutor)"),
    json_output: bool = typer.Option(False, "--json", help="Emit TopicLeagueResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🏆  Multi-topic standings comparison — rank N GitHub topics by agent-readiness."""
    topic_league_command(
        topics=topics,
        repos_per_topic=repos_per_topic,
        parallel=parallel,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("ecosystem")
def ecosystem(
    preset: str = typer.Option("default", "--preset", help="Preset: default (5 ecosystems), extended (12), or custom"),
    topics: Optional[List[str]] = typer.Option(None, "--topics", help="Comma-separated topics for custom preset"),
    repos_per_topic: int = typer.Option(3, "--repos-per-topic", help="Max repos per ecosystem to score (1-10, default 3)"),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel", help="Fetch ecosystems in parallel (default True)"),
    json_output: bool = typer.Option(False, "--json", help="Emit EcosystemResult as JSON"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress output"),
    output: Optional[str] = typer.Option(None, "--output", help="Save HTML report to local path"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🌐  Macro State of AI Agent Readiness scan across language/tech ecosystems."""
    # topics can be passed as comma-separated in one value or multiple values
    flat_topics: Optional[List[str]] = None
    if topics:
        flat_topics = []
        for t in topics:
            flat_topics.extend([x.strip() for x in t.split(",") if x.strip()])
    ecosystem_command(
        preset=preset,
        topics=flat_topics,
        repos_per_topic=repos_per_topic,
        parallel=parallel,
        json_output=json_output,
        share=share,
        quiet=quiet,
        output=output,
        timeout=timeout,
        token=token,
    )


@app.command("user-improve")
def user_improve(
    target: str = typer.Argument(..., help="GitHub user: github:<user> or bare <user>"),
    limit: int = typer.Option(5, "--limit", help="Max repos to improve (default 5, max 20)"),
    below: int = typer.Option(80, "--below", help="Only target repos scoring below this threshold"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now, print URL"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON result"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be improved, no changes"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🔧  Find a GitHub user's lowest-scoring repos and auto-improve them."""
    user_improve_command(
        target=target,
        limit=limit,
        below=below,
        share=share,
        json_output=json_output,
        dry_run=dry_run,
        token=token,
    )


@app.command("user-card")
def user_card(
    target: str = typer.Argument(..., help="GitHub user: github:<user> or bare <user>"),
    limit: int = typer.Option(10, "--limit", help="Max repos to analyze (default 10, max 30)"),
    min_stars: int = typer.Option(0, "--min-stars", help="Skip repos below this star count"),
    skip_forks: bool = typer.Option(True, "--skip-forks/--no-skip-forks", help="Skip forked repos (default: True)"),
    share: bool = typer.Option(False, "--share", help="Publish HTML card to here.now, print URL"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON result"),
    quiet: bool = typer.Option(False, "--quiet", help="Print only the share URL (cron-friendly)"),
    timeout: int = typer.Option(60, "--timeout", help="Per-repo analysis timeout in seconds"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
    badge: bool = typer.Option(False, "--badge", help="Print agent-readiness badge markdown after card"),
) -> None:
    """🃏  Generate a compact embeddable agent-readiness card for a GitHub user."""
    user_card_command(
        target=target,
        limit=limit,
        min_stars=min_stars,
        skip_forks=skip_forks,
        share=share,
        json_output=json_output,
        quiet=quiet,
        timeout=timeout,
        token=token,
        badge=badge,
    )


@app.command("user-badge")
def user_badge(
    target: str = typer.Argument(..., help="GitHub user: github:<user> or bare <user>"),
    score: Optional[float] = typer.Option(None, "--score", help="Skip scan, generate badge for this score directly"),
    grade: Optional[str] = typer.Option(None, "--grade", help="Explicit grade (A/B/C/D/F), used with --score"),
    output: Optional[str] = typer.Option(None, "--output", help="Write badge markdown to this file"),
    share: bool = typer.Option(False, "--share", help="Publish scorecard HTML to here.now, print URL"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON result"),
    inject: bool = typer.Option(False, "--inject", help="Auto-inject badge into local README.md"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be injected, no file changes"),
    limit: int = typer.Option(20, "--limit", help="Max repos to analyze when running full scan"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub token", envvar="GITHUB_TOKEN"),
) -> None:
    """🏅  Generate an agent-readiness badge for a GitHub user's profile README."""
    user_badge_command(
        target=target,
        score=score,
        grade=grade,
        output=output,
        share=share,
        json_output=json_output,
        inject=inject,
        dry_run=dry_run,
        limit=limit,
        token=token,
    )


@app.command("spotlight")
def spotlight(
    target: Optional[str] = typer.Argument(None, help="Target repo: owner/repo or github:owner/repo (auto-selects from trending if omitted)"),
    topic: Optional[str] = typer.Option(None, "--topic", help="Topic filter for auto-selection (e.g. 'machine-learning')"),
    language: Optional[str] = typer.Option(None, "--language", help="Language filter for auto-selection (e.g. 'python')"),
    deep: bool = typer.Option(False, "--deep", help="Run redteam + certify in addition to analyze"),
    share: bool = typer.Option(False, "--share", help="Publish HTML report to here.now"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON instead of rich terminal display"),
    output: Optional[str] = typer.Option(None, "--output", help="Write HTML report to file"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress terminal output"),
    no_history: bool = typer.Option(False, "--no-history", help="Don't record this run to history DB"),
    tweet_only: bool = typer.Option(False, "--tweet-only", help="Output only tweet-ready text to stdout (≤280 chars). Combine with --share to include URL."),
) -> None:
    """🔦  Repo of the Day: pick a trending repo, deep-dive analyze, shareable report."""
    spotlight_command(
        target=target,
        topic=topic,
        language=language,
        deep=deep,
        share=share,
        json_output=json_output,
        output=output,
        quiet=quiet,
        no_history=no_history,
        tweet_only=tweet_only,
    )


def _show_spotlight_history(limit: int = 10, json_output: bool = False, db_path=None) -> None:
    """Show only spotlight runs from history DB."""
    from agentkit_cli.history import HistoryDB
    import json as _json
    from rich.console import Console
    from rich.table import Table

    db = HistoryDB(db_path) if db_path else HistoryDB()
    rows = db.get_history(tool="spotlight", limit=limit)

    if not rows:
        if json_output:
            print("[]")
        else:
            Console().print("[dim]No spotlight runs found.[/dim]")
        return

    if json_output:
        out = []
        for r in rows:
            out.append({
                "project": r.get("project", ""),
                "repo": r.get("project", "").removeprefix("spotlight:"),
                "score": r.get("score", 0),
                "label": r.get("label", ""),
                "timestamp": r.get("timestamp", ""),
                "details": r.get("details", {}),
            })
        print(_json.dumps(out, indent=2))
        return

    console = Console()
    table = Table(title="Spotlight Runs")
    table.add_column("Repo")
    table.add_column("Score", justify="right")
    table.add_column("Date")
    for r in rows:
        repo = r.get("project", "").removeprefix("spotlight:")
        score = r.get("score", 0)
        ts = r.get("timestamp", "")[:19]
        table.add_row(repo, f"{score:.1f}", ts)
    console.print(table)


def _show_spotlight_feed(json_output: bool = False, db_path=None) -> None:
    """Show spotlight feed from history DB."""
    from agentkit_cli.history import HistoryDB
    import json as _json
    from rich.console import Console
    from rich.table import Table

    db = HistoryDB(db_path) if db_path else HistoryDB()
    rows = db.get_history(tool="spotlight", limit=20)

    if not rows:
        if json_output:
            print("[]")
        else:
            Console().print("[dim]No spotlight runs found.[/dim]")
        return

    if json_output:
        out = []
        for r in rows:
            out.append({
                "repo": r.get("project", "").removeprefix("spotlight:"),
                "score": r.get("score", 0),
                "timestamp": r.get("timestamp", ""),
                "details": r.get("details", {}),
            })
        print(_json.dumps(out, indent=2))
        return

    console = Console()
    table = Table(title="Spotlight Feed")
    table.add_column("Repo")
    table.add_column("Score", justify="right")
    table.add_column("Date")
    for r in rows:
        repo = r.get("project", "").removeprefix("spotlight:")
        score = r.get("score", 0)
        ts = r.get("timestamp", "")[:19]
        table.add_row(repo, f"{score:.1f}", ts)
    console.print(table)


@app.command("daily-duel")
def daily_duel(
    seed: Optional[str] = typer.Option(None, "--seed", help="Custom seed string (default: today YYYY-MM-DD)"),
    deep: bool = typer.Option(False, "--deep", help="Include redteam dimension"),
    share: bool = typer.Option(False, "--share", help="Upload HTML report and include URL in tweet"),
    json_output: bool = typer.Option(False, "--json", help="Print DailyDuelResult as JSON"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write HTML report to file"),
    pair: Optional[List[str]] = typer.Option(None, "--pair", help="Override auto-pick with explicit REPO1 REPO2"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress rich output, only print tweet_text"),
    tweet_only: bool = typer.Option(False, "--tweet-only", help="Print only the tweet text and exit (for piping)"),
    calendar: bool = typer.Option(False, "--calendar", help="Show 7-day schedule preview (no analysis)"),
    timeout: int = typer.Option(120, "--timeout", hidden=True),
    token: Optional[str] = typer.Option(None, "--token", hidden=True),
    existing: bool = typer.Option(True, "--existing/--no-existing", help="Score existing repo state (no agentmd generation). Default: True."),
) -> None:
    """🗓️  Daily Duel: auto-selects contrasting repos, duels them, outputs tweet-ready text."""
    daily_duel_command(
        seed=seed,
        deep=deep,
        share=share,
        json_output=json_output,
        output=output,
        pair=pair,
        quiet=quiet,
        tweet_only=tweet_only,
        calendar=calendar,
        timeout=timeout,
        token=token,
        existing=existing,
    )


@app.command("hot")
def hot(
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Filter trending by language (e.g. python, javascript)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of trending repos to score (max 25)"),
    tweet_only: bool = typer.Option(False, "--tweet-only", help="Print only the tweet text and exit"),
    share: bool = typer.Option(False, "--share", help="Upload HTML report to here.now and include URL in tweet"),
    json_output: bool = typer.Option(False, "--json", help="Print structured JSON output"),
    timeout: int = typer.Option(60, "--timeout", hidden=True),
    token: Optional[str] = typer.Option(None, "--token", hidden=True),
) -> None:
    """🔥 Hot: score GitHub trending repos for agent-readiness, output tweet-ready insight."""
    hot_command(
        language=language,
        limit=limit,
        tweet_only=tweet_only,
        share=share,
        json_output=json_output,
        timeout=timeout,
        token=token,
    )


@app.command("leaderboard-page")
def leaderboard_page(
    output: str = typer.Option("leaderboard.html", "--output", "-o", help="Output HTML file path"),
    ecosystems: Optional[str] = typer.Option(None, "--ecosystems", help="CSV of ecosystems (default: all 5)"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of repos per ecosystem (max 25)"),
    share: bool = typer.Option(False, "--share", help="Upload HTML and print share URL"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON instead of HTML"),
    pages: bool = typer.Option(False, "--pages", help="Write to docs/leaderboard.html (GitHub Pages)"),
    embed: Optional[str] = typer.Option(None, "--embed", help="Embed badge for a repo (e.g. github:owner/repo)"),
    embed_only: bool = typer.Option(False, "--embed-only", help="Only output badge markdown, no HTML"),
    token: Optional[str] = typer.Option(None, "--token", hidden=True),
) -> None:
    """🏆 Generate a public HTML leaderboard of top agent-ready GitHub repos by ecosystem."""
    leaderboard_page_command(
        output=output,
        ecosystems=ecosystems,
        limit=limit,
        share=share,
        json_output=json_output,
        pages=pages,
        embed=embed,
        embed_only=embed_only,
        token=token,
    )


@app.command("populate")
def populate(
    topics: str = typer.Option("python,typescript,rust,go", "--topics", help="Comma-separated list of GitHub topics"),
    limit: int = typer.Option(10, "--limit", help="Max repos per topic to fetch and score"),
    force: bool = typer.Option(False, "--force", help="Re-score even if history is fresh"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be scored without scoring"),
    json_output: bool = typer.Option(False, "--json", help="Print structured JSON summary"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress progress output, errors only"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Fetch top GitHub repos for topics and score each with agentkit analyze."""
    populate_command(
        topics=topics,
        limit=limit,
        force=force,
        dry_run=dry_run,
        json_output=json_output,
        quiet=quiet,
        db_path=db_path,
    )


@app.command("site")
def site(
    output_dir: str = typer.Argument("site", help="Output directory for generated site"),
    topics: str = typer.Option("python,typescript,rust,go", "--topics", help="Comma-separated topic list"),
    limit: int = typer.Option(20, "--limit", help="Max repos per topic page"),
    live: bool = typer.Option(False, "--live", help="Fetch and score top repos for each topic before generating the site"),
    repo_path: Optional[Path] = typer.Option(None, "--repo-path", help="Git repo to deploy into (default: current directory)"),
    deploy_dir: str = typer.Option("docs", "--deploy-dir", help="Subdirectory within repo for site output (default: docs)"),
    commit_message: str = typer.Option("chore: update agentkit site [skip ci]", "--commit-message", help="Git commit message for deploy"),
    no_push: bool = typer.Option(False, "--no-push", help="Stage and commit but do not push"),
    share: bool = typer.Option(False, "--share", help="Upload index.html to here.now and print URL"),
    deploy: bool = typer.Option(False, "--deploy", help="Copy generated site into docs/ for GitHub Pages"),
    base_url: str = typer.Option("https://mikiships.github.io/agentkit-cli/", "--base-url", help="Canonical base URL for sitemap and meta tags"),
    json_output: bool = typer.Option(False, "--json", help="Print summary JSON"),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress Rich output, errors only"),
    db_path: Optional[Path] = typer.Option(None, "--db", hidden=True, help="Override DB path (for testing)"),
) -> None:
    """Generate a multi-page static site from agentkit history data."""
    site_command(
        output_dir=output_dir,
        topics=topics,
        limit=limit,
        live=live,
        share=share,
        deploy=deploy,
        base_url=base_url,
        json_output=json_output,
        quiet=quiet,
        db_path=db_path,
        repo_path=repo_path,
        deploy_dir=deploy_dir,
        commit_message=commit_message,
        no_push=no_push,
    )


@app.command("api")
def api(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8742, "--port", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
    share: bool = typer.Option(False, "--share", help="Start ngrok tunnel"),
    interactive: bool = typer.Option(False, "--interactive", help="Confirm the interactive /ui form is enabled (always on)"),
) -> None:
    """Start the local REST API server."""
    api_command(host=host, port=port, reload=reload, share=share, interactive=interactive)


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
