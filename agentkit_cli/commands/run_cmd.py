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
                record_run(project_name, "overall", overall, label=label)
        except Exception as exc:
            import sys
            print(f"[agentkit history] DEBUG: history recording failed: {exc}", file=sys.stderr)

    if json_output:
        print(json.dumps(summary, indent=2))

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
