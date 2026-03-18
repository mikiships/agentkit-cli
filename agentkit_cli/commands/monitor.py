"""agentkit monitor command — continuous quality monitoring daemon.

Subcommands:
  add      — add/configure a monitored target
  remove   — remove a monitored target
  list     — show all monitored targets (rich table)
  run      — force an immediate check (all or specific target)
  start    — start background daemon
  stop     — stop background daemon
  status   — show daemon state + next run times
  logs     — tail daemon log / recent check history
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.monitor_config import MonitorConfig, MonitorTarget, VALID_SCHEDULES

console = Console()

# Daemon state files
MONITOR_DIR = Path.home() / ".agentkit"
PID_FILE = MONITOR_DIR / "monitor.pid"
LOG_FILE = MONITOR_DIR / "monitor.log"

monitor_app = typer.Typer(
    name="monitor",
    help="Continuous quality monitoring daemon for agentkit.",
    add_completion=False,
)


def _load_config(toml_path: Optional[Path] = None) -> MonitorConfig:
    return MonitorConfig(toml_path=toml_path) if toml_path else MonitorConfig()


def _format_ts(ts: Optional[str]) -> str:
    if not ts:
        return "never"
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return ts


def _next_due(mt: MonitorTarget) -> str:
    if mt.last_checked is None:
        return "now"
    try:
        last = datetime.fromisoformat(mt.last_checked)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        from datetime import timedelta
        next_dt = last + timedelta(seconds=mt.schedule_seconds())
        now = datetime.now(timezone.utc)
        if next_dt <= now:
            return "overdue"
        delta = next_dt - now
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        if hours > 0:
            return f"in {hours}h {minutes}m"
        return f"in {minutes}m"
    except (ValueError, TypeError):
        return "unknown"


@monitor_app.command("add")
def add(
    target: str = typer.Argument(..., help="Target: github:owner/repo, https://github.com/..., or local path"),
    schedule: str = typer.Option("daily", "--schedule", "-s", help="Check schedule: hourly|daily|weekly"),
    notify_slack: Optional[str] = typer.Option(None, "--notify-slack", help="Slack incoming webhook URL"),
    notify_discord: Optional[str] = typer.Option(None, "--notify-discord", help="Discord webhook URL"),
    notify_webhook: Optional[str] = typer.Option(None, "--notify-webhook", help="Generic JSON webhook URL"),
    min_score: Optional[float] = typer.Option(None, "--min-score", help="Alert when score drops below this"),
    alert_threshold: float = typer.Option(10.0, "--alert-threshold", help="Score change that triggers alert (default: 10)"),
    toml_path: Optional[Path] = typer.Option(None, "--config", hidden=True, help="Override .agentkit.toml path"),
) -> None:
    """Add a target to continuous monitoring."""
    if schedule not in VALID_SCHEDULES:
        console.print(f"[red]Error:[/red] --schedule must be one of {VALID_SCHEDULES}")
        raise typer.Exit(code=1)
    cfg = _load_config(toml_path)
    try:
        mt = cfg.add_target(
            target=target,
            schedule=schedule,
            notify_slack=notify_slack,
            notify_discord=notify_discord,
            notify_webhook=notify_webhook,
            min_score=min_score,
            alert_threshold=alert_threshold,
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    console.print(f"[green]✓[/green] Added monitor target: [bold]{target}[/bold]")
    console.print(f"  Schedule: {mt.schedule}")
    console.print(f"  Alert threshold: {mt.alert_threshold:+.0f} points")
    if mt.notify_slack:
        console.print("  Slack: configured")
    if mt.notify_discord:
        console.print("  Discord: configured")
    if mt.notify_webhook:
        console.print("  Webhook: configured")


@monitor_app.command("remove")
def remove(
    target: str = typer.Argument(..., help="Target to remove from monitoring"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    toml_path: Optional[Path] = typer.Option(None, "--config", hidden=True, help="Override .agentkit.toml path"),
) -> None:
    """Remove a target from monitoring."""
    cfg = _load_config(toml_path)
    if not yes:
        confirm = typer.confirm(f"Remove monitor target '{target}'?")
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit()
    removed = cfg.remove_target(target)
    if removed:
        console.print(f"[green]✓[/green] Removed: {target}")
    else:
        console.print(f"[yellow]Not found:[/yellow] {target}")
        raise typer.Exit(code=1)


@monitor_app.command("list")
def list_targets(
    toml_path: Optional[Path] = typer.Option(None, "--config", hidden=True, help="Override .agentkit.toml path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show all monitored targets."""
    cfg = _load_config(toml_path)
    targets = cfg.list_targets()

    if json_output:
        data = [
            {
                "target": mt.target,
                "schedule": mt.schedule,
                "last_score": mt.last_score,
                "last_checked": mt.last_checked,
                "next_due": _next_due(mt),
                "notify": mt.has_notify(),
                "alert_threshold": mt.alert_threshold,
                "min_score": mt.min_score,
            }
            for mt in targets
        ]
        console.print_json(json.dumps(data))
        return

    if not targets:
        console.print("[dim]No monitored targets configured. Use:[/dim] agentkit monitor add <target>")
        return

    table = Table(title="Monitored Targets", show_lines=True)
    table.add_column("Target", style="bold")
    table.add_column("Schedule")
    table.add_column("Last Score", justify="right")
    table.add_column("Last Checked")
    table.add_column("Next Due")
    table.add_column("Notify", justify="center")

    for mt in targets:
        score_str = f"{mt.last_score:.1f}" if mt.last_score is not None else "—"
        score_color = "green" if mt.last_score and mt.last_score >= 80 else "yellow" if mt.last_score else "dim"
        notify_str = "✓" if mt.has_notify() else "✗"
        notify_color = "green" if mt.has_notify() else "dim"

        table.add_row(
            mt.target,
            mt.schedule,
            f"[{score_color}]{score_str}[/{score_color}]",
            _format_ts(mt.last_checked),
            _next_due(mt),
            f"[{notify_color}]{notify_str}[/{notify_color}]",
        )

    console.print(table)


@monitor_app.command("run")
def run(
    target: Optional[str] = typer.Option(None, "--target", "-t", help="Run only this target (default: all due)"),
    all_targets: bool = typer.Option(False, "--all", help="Force-run all targets regardless of schedule"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
    toml_path: Optional[Path] = typer.Option(None, "--config", hidden=True, help="Override .agentkit.toml path"),
) -> None:
    """Force an immediate check (all due targets or a specific one)."""
    from agentkit_cli.monitor_engine import MonitorEngine

    cfg = _load_config(toml_path)
    engine = MonitorEngine(config=cfg)

    results = []
    if target:
        result = engine.run_target(target)
        if result is None:
            console.print(f"[red]Error:[/red] Target not found: {target}")
            raise typer.Exit(code=1)
        results = [result]
    elif all_targets:
        for mt in cfg.list_targets():
            result = engine.run_check(mt)
            results.append(result)
    else:
        results = engine.run_all_due()

    if not results:
        console.print("[dim]No targets due for check. Use --all to force-run all targets.[/dim]")
        return

    if json_output:
        data = [
            {
                "target": r.target,
                "score": r.score,
                "prev_score": r.prev_score,
                "delta": r.delta,
                "timestamp": r.timestamp,
                "notify_fired": r.notify_fired,
                "error": r.error,
            }
            for r in results
        ]
        console.print_json(json.dumps(data))
        return

    table = Table(title="Monitor Run Results", show_lines=True)
    table.add_column("Target", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Prev Score", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Notified", justify="center")
    table.add_column("Status")

    for r in results:
        score_color = "green" if r.score >= 80 else "yellow" if r.score >= 60 else "red"
        delta_color = "green" if r.delta >= 0 else "red"
        delta_str = f"{r.delta:+.1f}" if r.prev_score is not None else "—"
        status = "[red]ERROR[/red]" if r.error else "[green]OK[/green]"
        prev_str = f"{r.prev_score:.1f}" if r.prev_score is not None else "—"

        table.add_row(
            r.target,
            f"[{score_color}]{r.score:.1f}[/{score_color}]",
            prev_str,
            f"[{delta_color}]{delta_str}[/{delta_color}]",
            "✓" if r.notify_fired else "—",
            status,
        )

    console.print(table)


@monitor_app.command("start")
def start(
    toml_path: Optional[Path] = typer.Option(None, "--config", hidden=True, help="Override .agentkit.toml path"),
) -> None:
    """Start the background monitoring daemon."""
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)

    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            console.print(f"[yellow]Daemon already running[/yellow] (PID {pid})")
            return
        except (ProcessLookupError, ValueError):
            PID_FILE.unlink(missing_ok=True)

    log_fh = open(LOG_FILE, "a")
    env = os.environ.copy()
    if toml_path:
        env["AGENTKIT_MONITOR_TOML"] = str(toml_path)

    proc = subprocess.Popen(
        [sys.executable, "-m", "agentkit_cli.monitor_daemon"],
        stdout=log_fh,
        stderr=log_fh,
        start_new_session=True,
        env=env,
    )
    PID_FILE.write_text(str(proc.pid))
    console.print(f"[green]✓[/green] Monitor daemon started (PID {proc.pid})")
    console.print(f"  Log: {LOG_FILE}")


@monitor_app.command("stop")
def stop() -> None:
    """Stop the background monitoring daemon."""
    if not PID_FILE.exists():
        console.print("[yellow]No daemon PID file found.[/yellow] Daemon may not be running.")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        console.print(f"[green]✓[/green] Daemon stopped (PID {pid})")
    except (ProcessLookupError, ValueError):
        PID_FILE.unlink(missing_ok=True)
        console.print("[dim]Daemon was not running.[/dim]")
    except PermissionError:
        console.print("[red]Error:[/red] Permission denied sending SIGTERM.")
        raise typer.Exit(code=1)


@monitor_app.command("status")
def status(
    toml_path: Optional[Path] = typer.Option(None, "--config", hidden=True, help="Override .agentkit.toml path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show daemon state and next scheduled run times."""
    daemon_running = False
    daemon_pid: Optional[int] = None

    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            daemon_running = True
            daemon_pid = pid
        except (ProcessLookupError, ValueError):
            daemon_running = False

    cfg = _load_config(toml_path)
    targets = cfg.list_targets()

    if json_output:
        data = {
            "daemon_running": daemon_running,
            "daemon_pid": daemon_pid,
            "pid_file": str(PID_FILE),
            "log_file": str(LOG_FILE),
            "targets": [
                {
                    "target": mt.target,
                    "schedule": mt.schedule,
                    "next_due": _next_due(mt),
                    "last_score": mt.last_score,
                    "last_checked": mt.last_checked,
                }
                for mt in targets
            ],
        }
        console.print_json(json.dumps(data))
        return

    status_str = f"[green]running[/green] (PID {daemon_pid})" if daemon_running else "[red]stopped[/red]"
    console.print(f"Daemon: {status_str}")
    console.print(f"PID file: {PID_FILE}")
    console.print(f"Log file: {LOG_FILE}")

    if targets:
        console.print()
        table = Table(title="Scheduled Targets")
        table.add_column("Target")
        table.add_column("Schedule")
        table.add_column("Next Due")
        table.add_column("Last Score", justify="right")
        for mt in targets:
            score_str = f"{mt.last_score:.1f}" if mt.last_score is not None else "—"
            table.add_row(mt.target, mt.schedule, _next_due(mt), score_str)
        console.print(table)
    else:
        console.print("[dim]No targets configured.[/dim]")


@monitor_app.command("logs")
def logs(
    limit: int = typer.Option(20, "--limit", "-n", help="Max log entries to show (default: 20)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON lines"),
) -> None:
    """Show recent monitor check history from daemon log."""
    if not LOG_FILE.exists():
        console.print("[dim]No log file found. Has the daemon been started?[/dim]")
        return

    entries = []
    try:
        lines = LOG_FILE.read_text().strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    except OSError as e:
        console.print(f"[red]Error reading log:[/red] {e}")
        raise typer.Exit(code=1)

    entries = entries[-limit:]

    if json_output:
        console.print_json(json.dumps(entries))
        return

    if not entries:
        console.print("[dim]No structured log entries found.[/dim]")
        return

    table = Table(title="Monitor Log", show_lines=True)
    table.add_column("Timestamp")
    table.add_column("Target", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Notified", justify="center")

    for entry in entries:
        ts = _format_ts(entry.get("ts") or entry.get("timestamp"))
        target = entry.get("target", "?")
        score = entry.get("score")
        delta = entry.get("delta")
        notified = entry.get("notify_fired", False)

        score_str = f"{score:.1f}" if score is not None else "—"
        delta_str = f"{delta:+.1f}" if delta is not None else "—"
        delta_color = "green" if (delta or 0) >= 0 else "red"
        score_color = "green" if score and score >= 80 else "yellow" if score else "dim"

        table.add_row(
            ts,
            target,
            f"[{score_color}]{score_str}[/{score_color}]",
            f"[{delta_color}]{delta_str}[/{delta_color}]",
            "✓" if notified else "—",
        )

    console.print(table)
