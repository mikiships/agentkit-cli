"""agentkit gate command."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.gate import GateError, GateResult, run_gate
from agentkit_cli.notifier import fire_notifications, resolve_notify_configs

console = Console()


def _score_color(score: float) -> str:
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _write_payload(payload: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _build_job_summary(result: GateResult) -> str:
    lines = [
        "## agentkit gate",
        "",
        f"- Verdict: **{result.verdict}**",
        f"- Score: **{result.score:.1f}/100 ({result.grade})**",
    ]

    min_score = result.thresholds.get("min_score")
    if min_score is not None:
        lines.append(f"- Min score: {min_score:.1f}")

    baseline_score = result.thresholds.get("baseline_score")
    max_drop = result.thresholds.get("max_drop")
    if baseline_score is not None:
        lines.append(f"- Baseline score: {baseline_score:.1f}")
    if result.baseline_delta is not None:
        lines.append(f"- Baseline delta: {result.baseline_delta:+.1f}")
    if max_drop is not None:
        lines.append(f"- Max drop: {max_drop:.1f}")

    if result.failure_reasons:
        lines.extend(["", "### Failure reasons"])
        lines.extend(f"- {reason}" for reason in result.failure_reasons)

    return "\n".join(lines) + "\n"


def _write_job_summary(result: GateResult) -> None:
    summary_target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_target:
        print(_build_job_summary(result))
        return

    summary_path = Path(summary_target)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(_build_job_summary(result), encoding="utf-8")


def gate_command(
    path: Optional[Path] = None,
    min_score: Optional[float] = None,
    baseline_report: Optional[Path] = None,
    max_drop: Optional[float] = None,
    json_output: bool = False,
    output: Optional[Path] = None,
    job_summary: bool = False,
    notify_slack: Optional[str] = None,
    notify_discord: Optional[str] = None,
    notify_webhook: Optional[str] = None,
    notify_on: str = "fail",
    profile: Optional[str] = None,
) -> None:
    """Evaluate the current project against gate thresholds."""
    # Apply config defaults when CLI flags were not provided
    from agentkit_cli.config import load_config
    from agentkit_cli.profiles import ProfileRegistry, apply_profile
    cfg = load_config(path)

    # Apply profile (fills gaps not covered by explicit CLI flags)
    if profile is not None:
        try:
            apply_profile(
                profile,
                cfg,
                cli_min_score=min_score,
                cli_max_drop=max_drop,
            )
        except ValueError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=2)

    if min_score is None and cfg.gate.min_score is not None:
        min_score = cfg.gate.min_score
    if max_drop is None and cfg.gate.max_drop is not None:
        max_drop = cfg.gate.max_drop
    if not notify_slack and cfg.notify.slack_url:
        notify_slack = cfg.notify.slack_url
    if not notify_discord and cfg.notify.discord_url:
        notify_discord = cfg.notify.discord_url
    if not notify_webhook and cfg.notify.webhook_url:
        notify_webhook = cfg.notify.webhook_url
    if notify_on == "fail" and cfg.notify.on != "fail":
        notify_on = cfg.notify.on

    try:
        result = run_gate(
            path=path,
            min_score=min_score,
            baseline_report=baseline_report,
            max_drop=max_drop,
        )
        payload = result.to_json_payload()

        if output is not None:
            _write_payload(payload, output)
        if job_summary:
            _write_job_summary(result)

        # Fire notifications (never affect exit code)
        try:
            notify_configs = resolve_notify_configs(
                notify_slack=notify_slack,
                notify_discord=notify_discord,
                notify_webhook=notify_webhook,
                notify_on=notify_on,
                project_name=str((path or Path.cwd()).resolve().name),
            )
            fire_notifications(
                notify_configs,
                verdict=result.verdict,
                score=result.score,
                top_findings=list(result.failure_reasons),
                delta=result.baseline_delta,
            )
        except Exception:
            pass

        if json_output:
            print(json.dumps(payload, indent=2))
            raise typer.Exit(code=0 if result.passed else 1)

        color = "green" if result.passed else "red"
        score_color = _score_color(result.score)
        console.print()
        console.print(f"[bold]agentkit gate[/bold] — project: {(path or Path.cwd()).resolve()}")
        if profile is not None:
            console.print(f"[bold]Profile:[/bold] {profile}")
        console.print(f"[bold]Verdict:[/bold] [{color}]{result.verdict}[/{color}]")
        console.print(
            f"[bold]Score:[/bold] [{score_color}]{result.score:.1f}/100 ({result.grade})[/{score_color}]"
        )

        min_score_value = result.thresholds.get("min_score")
        if min_score_value is not None:
            console.print(f"[bold]Min score:[/bold] {min_score_value:.1f}")

        baseline_score = result.thresholds.get("baseline_score")
        if baseline_score is not None:
            console.print(f"[bold]Baseline score:[/bold] {baseline_score:.1f}")
        if result.baseline_delta is not None:
            console.print(f"[bold]Baseline delta:[/bold] {result.baseline_delta:+.1f}")
        max_drop_value = result.thresholds.get("max_drop")
        if max_drop_value is not None:
            console.print(f"[bold]Max drop:[/bold] {max_drop_value:.1f}")

        if result.failure_reasons:
            console.print("[bold]Failure reasons:[/bold]")
            for reason in result.failure_reasons:
                console.print(f"- {reason}")
        else:
            console.print("[bold]Failure reasons:[/bold] none")

        if output is not None:
            console.print(f"[dim]JSON payload saved to {output}[/dim]")
        if job_summary:
            console.print("[dim]Job summary written to GITHUB_STEP_SUMMARY[/dim]")

        raise typer.Exit(code=0 if result.passed else 1)
    except GateError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=2) from exc
