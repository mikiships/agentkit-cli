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
from agentkit_cli.history import record_run
from agentkit_cli.composite import CompositeScoreEngine
from agentkit_cli.notifier import fire_notifications, resolve_notify_configs

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
    publish: bool = typer.Option(False, "--publish", help="Publish HTML report to here.now after run"),
    inject_readme: bool = False,
    no_history: bool = typer.Option(False, "--no-history", help="Skip recording scores to history DB"),
    label: Optional[str] = typer.Option(None, "--label", help="Tag this run with a label for leaderboard"),
    notify_slack: Optional[str] = None,
    notify_discord: Optional[str] = None,
    notify_webhook: Optional[str] = None,
    notify_on: str = "fail",
    profile: Optional[str] = None,
    share: bool = False,
    record_findings: bool = False,
    serve: bool = False,
    harden: bool = False,
    timeline: bool = False,
    explain: bool = False,
    no_llm: bool = False,
    improve: bool = False,
    improve_no_generate: bool = False,
    improve_no_harden: bool = False,
    improve_threshold: float = 80.0,
    webhook_notify: bool = False,
    checks: Optional[bool] = None,
    llmstxt: bool = False,
    migrate: bool = False,
    agent_benchmark: bool = False,
    user_duel: Optional[str] = None,
    user_tournament: Optional[str] = None,
    user_improve: Optional[str] = None,
    user_card: Optional[str] = None,
    user_rank_topic: Optional[str] = None,
    ecosystem: Optional[str] = None,
) -> None:
    """Run the full Agent Quality pipeline."""
    # Apply config defaults
    from agentkit_cli.config import load_config
    from agentkit_cli.profiles import apply_profile
    cfg = load_config(path)
    if profile is not None:
        try:
            apply_profile(profile, cfg)
        except ValueError as exc:
            from rich.console import Console as _Console
            _Console().print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=2)
    if not notify_slack and cfg.notify.slack_url:
        notify_slack = cfg.notify.slack_url
    if not notify_discord and cfg.notify.discord_url:
        notify_discord = cfg.notify.discord_url
    if not notify_webhook and cfg.notify.webhook_url:
        notify_webhook = cfg.notify.webhook_url
    if notify_on == "fail" and cfg.notify.on != "fail":
        notify_on = cfg.notify.on
    if label is None and cfg.run.label:
        label = cfg.run.label

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

    # GitHub Checks API integration
    _checks_client = None
    _check_run_id: Optional[int] = None
    _should_post_checks = checks if checks is not None else None  # None = auto-detect
    try:
        from agentkit_cli.checks_client import GitHubChecksClient, detect_github_env
        if _should_post_checks is True or (_should_post_checks is None):
            env = detect_github_env()
            if env is not None:
                _checks_client = GitHubChecksClient(env=env)
                _check_run_id = _checks_client.create_check_run(name="agentkit run", status="in_progress")
            elif _should_post_checks is True:
                import logging as _logging
                _logging.getLogger(__name__).warning("--checks requested but not in GitHub Actions environment")
    except Exception as _exc:
        import logging as _logging
        _logging.getLogger(__name__).warning("Checks API: %s", _exc)

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

    # Record scores to history DB (silently, never aborts the run)
    if not no_history:
        try:
            project_name = root.name
            # Map step results to per-tool scores (pass=100, fail=0, skipped=None)
            tool_scores: list[float] = []
            step_to_tool = {
                "generate": "agentmd",
                "lint-context": "agentlint",
                "lint-diff": "agentlint",
                "benchmark": "coderace",
                "reflect": "agentreflect",
            }
            recorded_tools: set[str] = set()
            for r in results:
                tool_name = step_to_tool.get(r["step"])
                if not tool_name:
                    continue
                status = r.get("status", "unknown")
                if status == "pass":
                    score = 100.0
                elif status == "fail":
                    score = 0.0
                else:
                    continue  # skipped/error → don't record
                tool_scores.append(score)
                if tool_name not in recorded_tools:
                    record_run(project_name, tool_name, score, label=label)
                    recorded_tools.add(tool_name)
            if tool_scores:
                overall = round(sum(tool_scores) / len(tool_scores), 1)
                # Collect findings from agentlint results when --record-findings is set
                findings_to_store: Optional[list] = None
                if record_findings:
                    findings_to_store = []
                    for r in results:
                        if r.get("step") in ("lint-context", "lint-diff"):
                            raw = r.get("output", "") or ""
                            for line in raw.splitlines():
                                line = line.strip()
                                if line and not line.startswith("#"):
                                    findings_to_store.append(line)
                record_run(project_name, "overall", overall, label=label, findings=findings_to_store)
        except Exception as exc:
            import sys
            print(f"[agentkit history] DEBUG: history recording failed: {exc}", file=sys.stderr)

    # json_output deferred to after optional steps (llmstxt, etc.) can add fields

    # Optional publish step
    if publish:
        from agentkit_cli.publish import publish_html, resolve_html_path, PublishError
        import os
        try:
            html_path = resolve_html_path(None)
            api_key = os.environ.get("HERENOW_API_KEY") or None
            result = publish_html(html_path, api_key=api_key)
            url = result["url"]
            if ci:
                active_console.print(f"\nReport published: {url}")
            else:
                console.print(f"\n[bold]Report published:[/bold] {url}")
            if result.get("anonymous"):
                msg = "Note: anonymous publish — link expires in 24h."
                if ci:
                    active_console.print(msg)
                else:
                    console.print(f"[dim]{msg}[/dim]")
        except (FileNotFoundError, PublishError, Exception) as e:
            warn = f"Warning: publish failed — {e}"
            if ci:
                active_console.print(warn)
            else:
                console.print(f"[yellow]{warn}[/yellow]")

    # Optional README badge injection
    if inject_readme:
        from agentkit_cli.commands.readme_cmd import readme_command
        readme_command(
            readme=None,
            dry_run=False,
            remove=False,
            section_header="## Agent Quality",
            path=root,
            score_override=None,
        )

    # Optional share step
    if share:
        from agentkit_cli.share import generate_scorecard_html, upload_scorecard
        import os as _os
        try:
            _share_score_result: dict = {}
            # Composite score comes later, so do a quick inline score
            try:
                import agentkit_cli.composite as _composite_mod
                _cse = _composite_mod.CompositeScoreEngine()
                _csr = _cse.compute({})
                _share_score_result = {"composite": _csr.composite, "breakdown": _csr.breakdown}
            except Exception:
                pass
            _share_html = generate_scorecard_html(
                score_result=_share_score_result,
                project_name=(root.resolve().name if root else Path.cwd().name),
                ref="unknown",
            )
            _share_api_key = _os.environ.get("HERENOW_API_KEY") or None
            _share_url = upload_scorecard(_share_html, api_key=_share_api_key)
            if _share_url:
                if ci:
                    active_console.print(f"\nScore card: {_share_url}")
                else:
                    console.print(f"\n[bold]Score card:[/bold] {_share_url}")
        except Exception as _e:
            _warn = f"Warning: share failed — {_e}"
            if ci:
                active_console.print(_warn)
            else:
                console.print(f"[yellow]{_warn}[/yellow]")

    # Composite score display
    _composite_score: float | None = None
    try:
        tool_score_map: dict[str, float | None] = {}
        step_tool_score: dict[str, float | None] = {
            "generate": None,
            "lint-context": None,
            "benchmark": None,
            "reflect": None,
        }
        _tool_key = {
            "generate": "agentmd",
            "lint-context": "agentlint",
            "benchmark": "coderace",
            "reflect": "agentreflect",
        }
        for r in results:
            sname = r["step"]
            if sname in _tool_key:
                status = r.get("status", "unknown")
                if status == "pass":
                    step_tool_score[sname] = 100.0
                elif status == "fail":
                    step_tool_score[sname] = 0.0
                # skipped/error → None
        for step, tname in _tool_key.items():
            score_val = step_tool_score.get(step)
            # Only record if not already set by a previous step for same tool
            if tname not in tool_score_map:
                tool_score_map[tname] = score_val
            elif score_val is not None:
                # Average if both present (e.g., lint has lint-context and lint-diff)
                existing = tool_score_map[tname]
                if existing is not None:
                    tool_score_map[tname] = (existing + score_val) / 2
                else:
                    tool_score_map[tname] = score_val

        engine = CompositeScoreEngine()
        comp_result = engine.compute(tool_score_map)
        _composite_score = comp_result.score
        grade = comp_result.grade
        comp_parts = ", ".join(
            f"{t} {d['raw_score']:.0f}" for t, d in sorted(comp_result.components.items())
        )
        score_color = "green" if _composite_score >= 80 else ("yellow" if _composite_score >= 60 else "red")
        sep = "─" * 60
        if ci:
            active_console.print(f"\n{sep}")
            active_console.print(
                f"Agent Quality Score: {_composite_score:.0f}/100 ({grade})  [components: {comp_parts}]"
            )
            active_console.print(sep)
        else:
            console.print(f"\n[dim]{sep}[/dim]")
            console.print(
                f"[bold]Agent Quality Score:[/bold] [{score_color}]{_composite_score:.0f}/100 ({grade})[/{score_color}]"
                f"  [dim][components: {comp_parts}][/dim]"
            )
            console.print(f"[dim]{sep}[/dim]")

        # Record composite score to history
        if not no_history:
            try:
                record_run(root.name, "composite", _composite_score, label=label)
            except Exception:
                pass
    except Exception:
        pass  # Never let composite scoring abort the run

    # Fire notifications (never affect exit code)
    try:
        _notify_verdict = "FAIL" if failed_count > 0 else "PASS"
        _notify_score = _composite_score if "_composite_score" in dir() else 0.0
        _notify_findings = [r["step"] for r in results if r.get("status") in ("fail", "error")]
        _notify_configs = resolve_notify_configs(
            notify_slack=notify_slack,
            notify_discord=notify_discord,
            notify_webhook=notify_webhook,
            notify_on=notify_on,
            project_name=str(root.name),
        )
        fire_notifications(_notify_configs, verdict=_notify_verdict, score=_notify_score, top_findings=_notify_findings)
    except Exception:
        pass

    # Print dashboard URL if --serve was requested
    if serve:
        from agentkit_cli.serve import DEFAULT_PORT
        active_console.print(f"Dashboard: http://localhost:{DEFAULT_PORT}")

    # --harden: run harden on detected context file after pipeline
    if harden:
        try:
            from agentkit_cli.commands.harden_cmd import harden_command
            harden_command(
                path=path or root,
                output=None,
                dry_run=False,
                report=False,
                share=False,
                json_output=json_output,
            )
        except SystemExit:
            pass
        except Exception:
            pass

    # --explain: generate coaching report after pipeline
    if explain:
        try:
            from agentkit_cli.explain import ExplainEngine
            from rich.markdown import Markdown as _Markdown
            _engine = ExplainEngine()
            _coaching = (
                _engine.template_explain(summary)
                if no_llm
                else _engine.explain_run_result(summary)
            )
            if ci:
                active_console.print("\n## Coaching Report")
                active_console.print(_coaching)
            else:
                console.print("\n[bold cyan]## Coaching Report[/bold cyan]")
                console.print(_Markdown(_coaching))
            # Append to summary if json_output
            if json_output:
                summary["coaching_report"] = _coaching
        except Exception as _exc:
            pass

    # --improve: run improvement workflow if score < threshold
    if improve:
        _improve_result: dict | None = None
        try:
            from agentkit_cli.improve_engine import ImproveEngine as _ImproveEngine
            _ie = _ImproveEngine()
            _improve_plan = _ie.run(
                str(root),
                no_generate=improve_no_generate,
                no_harden=improve_no_harden,
            )
            _improve_result = {
                "baseline": _improve_plan.baseline_score,
                "final": _improve_plan.final_score,
                "delta": _improve_plan.delta,
                "actions_taken": _improve_plan.actions_taken,
            }
            delta_sign = "+" if _improve_plan.delta >= 0 else ""
            if ci:
                active_console.print(
                    f"\nImprovement: {_improve_plan.baseline_score:.0f} → {_improve_plan.final_score:.0f}"
                    f" ({delta_sign}{_improve_plan.delta:.1f} pts)"
                )
            else:
                score_col = "green" if _improve_plan.delta > 0 else "yellow"
                console.print(
                    f"\n[bold]Improvement:[/bold] {_improve_plan.baseline_score:.0f} → {_improve_plan.final_score:.0f}"
                    f"  [{score_col}]{delta_sign}{_improve_plan.delta:.1f} pts[/{score_col}]"
                )
        except SystemExit:
            pass
        except Exception as _exc:
            _warn = f"Warning: improve failed — {_exc}"
            if ci:
                active_console.print(_warn)
            else:
                console.print(f"[yellow]{_warn}[/yellow]")
        if json_output and _improve_result is not None:
            summary["improvement"] = _improve_result

    # --timeline: generate timeline HTML after run
    if timeline:
        try:
            from agentkit_cli.commands.timeline_cmd import timeline_command
            from pathlib import Path as _Path
            timeline_command(output=_Path("timeline.html"), share=share)
        except SystemExit:
            pass
        except Exception:
            pass

    # --webhook-notify: POST result to configured webhook URL after run
    if webhook_notify:
        try:
            from agentkit_cli.config import load_config as _load_cfg
            _wh_cfg = _load_cfg(path)
            _wh_url = _wh_cfg.notify.webhook_url
            if _wh_url:
                import json as _json
                import urllib.request as _urllib_req
                _payload = _json.dumps({
                    "event": "run_complete",
                    "project": cwd_str,
                    "passed": passed_count,
                    "failed": failed_count,
                    "score": _composite_score if "_composite_score" in dir() else None,
                }).encode("utf-8")
                _req = _urllib_req.Request(
                    _wh_url,
                    data=_payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with _urllib_req.urlopen(_req, timeout=5) as _resp:
                    pass
                if ci:
                    active_console.print(f"webhook-notify: posted to {_wh_url}")
                else:
                    console.print(f"[dim]webhook-notify: posted to {_wh_url}[/dim]")
            else:
                warn = "webhook-notify: no webhook URL configured. Set notify.webhook_url in .agentkit.toml"
                if ci:
                    active_console.print(warn)
                else:
                    console.print(f"[yellow]{warn}[/yellow]")
        except Exception as _exc:
            warn = f"webhook-notify failed: {_exc}"
            if ci:
                active_console.print(warn)
            else:
                console.print(f"[yellow]{warn}[/yellow]")

    # Update GitHub Check Run with final results
    if _checks_client is not None and _check_run_id is not None:
        try:
            from agentkit_cli.checks_formatter import format_check_output
            _checks_score = _composite_score if _composite_score is not None else 0.0
            from agentkit_cli.composite import _compute_grade as _cg
            _checks_grade = _cg(_checks_score) if _composite_score is not None else "F"
            _checks_result = {
                "score": _checks_score,
                "grade": _checks_grade,
                "components": {},
            }
            # Try to get components from the composite result
            try:
                _checks_result["components"] = {
                    t: d for t, d in sorted(comp_result.components.items())
                } if "comp_result" in dir() else {}
            except Exception:
                pass
            _checks_output = format_check_output(_checks_result)
            _checks_conclusion = "success" if failed_count == 0 else "failure"
            _checks_client.update_check_run(
                _check_run_id,
                status="completed",
                conclusion=_checks_conclusion,
                output=_checks_output,
            )
        except Exception as _exc:
            import logging as _logging
            _logging.getLogger(__name__).warning("Checks API update failed: %s", _exc)

    # --migrate: auto-generate missing format files before analysis
    if migrate:
        try:
            from agentkit_cli.migrate import MigrateEngine as _MigrateEngine, FORMAT_FILENAMES as _FMT_FILENAMES
            _mig_engine = _MigrateEngine()
            _mig_source = _mig_engine.detect_source(root)
            if _mig_source is not None:
                _mig_fmt, _mig_path = _mig_source
                _mig_content = _mig_path.read_text(encoding="utf-8", errors="replace")
                _mig_results = _mig_engine.convert_all(_mig_content, _mig_fmt, directory=root)
                for _mr in _mig_results:
                    _out = root / _FMT_FILENAMES[_mr.target_format]
                    if not _out.exists():
                        _out.write_text(_mr.content, encoding="utf-8")
                        if not ci:
                            console.print(f"[dim]migrate: generated {_out.name}[/dim]")
        except Exception as _mig_exc:
            if not ci:
                console.print(f"[yellow]Warning: migrate failed — {_mig_exc}[/yellow]")

    # --llmstxt: generate llms.txt after pipeline
    llmstxt_generated: bool = False
    llmstxt_path: Optional[str] = None
    llmstxt_section_count: int = 0
    llmstxt_size: int = 0
    if llmstxt:
        try:
            from agentkit_cli.llmstxt import LlmsTxtGenerator
            _llms_gen = LlmsTxtGenerator()
            _llms_info = _llms_gen.scan_repo(cwd_str)
            _llms_content = _llms_gen.generate_llms_txt(_llms_info)
            _llms_out = root / "llms.txt"
            _llms_out.write_text(_llms_content, encoding="utf-8")
            llmstxt_generated = True
            llmstxt_path = str(_llms_out)
            llmstxt_section_count = sum(1 for l in _llms_content.splitlines() if l.startswith("## "))
            llmstxt_size = len(_llms_content.encode("utf-8"))
            if ci:
                active_console.print(f"\nllms.txt: generated ({llmstxt_size} bytes, {llmstxt_section_count} sections) → {_llms_out}")
            else:
                console.print(f"\n[bold]llms.txt:[/bold] generated ({llmstxt_size} bytes, {llmstxt_section_count} sections) → [dim]{_llms_out}[/dim]")
        except Exception as _exc:
            _warn = f"Warning: llmstxt generation failed — {_exc}"
            if ci:
                active_console.print(_warn)
            else:
                console.print(f"[yellow]{_warn}[/yellow]")
    if llmstxt:
        summary["llmstxt_generated"] = llmstxt_generated
        summary["llmstxt_path"] = llmstxt_path
        summary["llmstxt_section_count"] = llmstxt_section_count
        summary["llmstxt_size"] = llmstxt_size

    # Optional agent benchmark step (cross-agent comparison)
    if agent_benchmark:
        try:
            from agentkit_cli.benchmark import BenchmarkEngine, BenchmarkConfig
            _bm_engine = BenchmarkEngine()
            _bm_report = _bm_engine.run(cwd_str, config=BenchmarkConfig())
            summary["benchmark_result"] = _bm_report.to_dict()
            if not ci and not json_output:
                console.print(f"\n[bold]Agent Benchmark:[/bold] winner=[green]{_bm_report.winner}[/green]")
        except Exception as _bm_exc:
            summary["benchmark_result"] = {"error": str(_bm_exc)}
            if not ci:
                console.print(f"[yellow]Warning: agent benchmark failed — {_bm_exc}[/yellow]")

    if user_duel:
        try:
            from agentkit_cli.user_duel import UserDuelEngine
            _duel_parts = user_duel.split(":")
            if len(_duel_parts) == 2:
                _u1, _u2 = _duel_parts[0].strip(), _duel_parts[1].strip()
                _duel_engine = UserDuelEngine()
                _duel_result = _duel_engine.run(_u1, _u2)
                summary["user_duel"] = _duel_result.to_dict()
                if not ci and not json_output:
                    _winner = _duel_result.user1 if _duel_result.overall_winner == "user1" else (
                        _duel_result.user2 if _duel_result.overall_winner == "user2" else "tie"
                    )
                    console.print(f"\n[bold]User Duel:[/bold] winner=[green]{_winner}[/green]")
            else:
                summary["user_duel"] = {"error": "Invalid --user-duel format. Use user1:user2"}
        except Exception as _duel_exc:
            summary["user_duel"] = {"error": str(_duel_exc)}

    if user_tournament:
        try:
            from agentkit_cli.engines.user_tournament import UserTournamentEngine
            _t_parts = [p.strip() for p in user_tournament.split(":") if p.strip()]
            if len(_t_parts) >= 2:
                _t_engine = UserTournamentEngine()
                _t_result = _t_engine.run(_t_parts)
                summary["user_tournament"] = _t_result.to_dict()
                if not ci and not json_output:
                    console.print(f"\n[bold]User Tournament:[/bold] champion=[green]{_t_result.champion}[/green]")
            else:
                summary["user_tournament"] = {"error": "Invalid --user-tournament format. Use user1:user2:..."}
        except Exception as _t_exc:
            summary["user_tournament"] = {"error": str(_t_exc)}

    if user_improve:
        try:
            from agentkit_cli.user_improve import UserImproveEngine
            _ui_target = user_improve.strip()
            if _ui_target.startswith("github:"):
                _ui_user = _ui_target[len("github:"):]
            else:
                _ui_user = _ui_target
            _ui_engine = UserImproveEngine()
            _ui_report = _ui_engine.run(_ui_user, limit=5, below=80)
            summary["user_improve"] = _ui_report.to_dict()
            if not ci and not json_output:
                console.print(f"\n[bold]User Improve:[/bold] @{_ui_user} — {_ui_report.improved} repos improved, avg lift {_ui_report.summary_stats.get('avg_lift', 0.0):+.1f} pts")
        except Exception as _ui_exc:
            summary["user_improve"] = {"error": str(_ui_exc)}

    if user_card:
        try:
            from agentkit_cli.user_card import UserCardEngine
            _uc_target = user_card.strip()
            if _uc_target.startswith("github:"):
                _uc_user = _uc_target[len("github:"):]
            else:
                _uc_user = _uc_target
            _uc_engine = UserCardEngine()
            _uc_result = _uc_engine.run(_uc_user)
            summary["user_card"] = _uc_result.to_dict()
            if not ci and not json_output:
                console.print(f"\n[bold]User Card:[/bold] @{_uc_user} — Grade {_uc_result.grade}, avg {_uc_result.avg_score:.1f}")
        except Exception as _uc_exc:
            summary["user_card"] = {"error": str(_uc_exc)}

    if user_rank_topic:
        try:
            from agentkit_cli.user_rank import UserRankEngine
            _ur_engine = UserRankEngine(topic=user_rank_topic.strip())
            _ur_result = _ur_engine.run()
            summary["user_rank"] = _ur_result.to_dict()
            if not ci and not json_output:
                console.print(f"\n[bold]User Rank:[/bold] topic={user_rank_topic} — Top: @{_ur_result.top_scorer}, Mean {_ur_result.mean_score:.1f}")
        except Exception as _ur_exc:
            summary["user_rank"] = {"error": str(_ur_exc)}

    if ecosystem:
        try:
            from agentkit_cli.engines.ecosystem import EcosystemEngine
            _eco_preset = ecosystem.strip() or "default"
            _eco_engine = EcosystemEngine(preset=_eco_preset)
            _eco_result = _eco_engine.run()
            summary["ecosystem"] = _eco_result.to_dict()
            if not ci and not json_output:
                _winner = _eco_result.winner
                _w_str = f"{_winner.topic} ({_winner.score:.1f})" if _winner else "n/a"
                console.print(f"\n[bold]Ecosystem:[/bold] preset={_eco_preset} — Winner: {_w_str}")
        except Exception as _eco_exc:
            summary["ecosystem"] = {"error": str(_eco_exc)}

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
