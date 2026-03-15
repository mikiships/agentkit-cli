"""agentkit notify command — test and configure webhook notifications."""
from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console

from agentkit_cli.notifier import (
    NotifyConfig,
    _send_with_retry,
    build_payload,
)

console = Console()

notify_app = typer.Typer(
    name="notify",
    help="Manage and test webhook notifications (Slack / Discord / generic).",
    add_completion=False,
)


@notify_app.command("test")
def notify_test(
    slack: Optional[str] = typer.Option(None, "--slack", help="Slack webhook URL to test"),
    discord: Optional[str] = typer.Option(None, "--discord", help="Discord webhook URL to test"),
    webhook: Optional[str] = typer.Option(None, "--webhook", help="Generic webhook URL to test"),
) -> None:
    """Send a test notification to verify connectivity."""
    targets: list[tuple[str, str]] = []
    if slack:
        targets.append((slack, "slack"))
    if discord:
        targets.append((discord, "discord"))
    if webhook:
        targets.append((webhook, "webhook"))

    if not targets:
        console.print("[yellow]No webhook URL provided. Use --slack, --discord, or --webhook.[/yellow]")
        raise typer.Exit(code=1)

    any_failed = False
    for url, service in targets:
        cfg = NotifyConfig(
            url=url,
            service=service,
            notify_on="always",
            project_name="test-project",
        )
        payload = build_payload(
            config=cfg,
            score=85.0,
            verdict="PASS",
            top_findings=["This is a test notification from agentkit-cli."],
            delta=None,
        )
        ok, msg = _send_with_retry(url, payload)
        if ok:
            console.print(f"[green]✓ Notification delivered[/green] ({service}: {msg})")
        else:
            console.print(f"[red]✗ Failed[/red] ({service}): {msg}")
            any_failed = True

    if any_failed:
        raise typer.Exit(code=1)


@notify_app.command("config")
def notify_config() -> None:
    """Show current notification configuration (env vars)."""
    mapping = [
        ("AGENTKIT_NOTIFY_SLACK", "Slack webhook"),
        ("AGENTKIT_NOTIFY_DISCORD", "Discord webhook"),
        ("AGENTKIT_NOTIFY_WEBHOOK", "Generic webhook"),
        ("AGENTKIT_NOTIFY_ON", "Notify on (fail|always)"),
    ]
    console.print("\n[bold]agentkit notify config[/bold]")
    console.print()
    any_set = False
    for var, label in mapping:
        val = os.environ.get(var, "")
        if val:
            display = val if var == "AGENTKIT_NOTIFY_ON" else f"{val[:30]}..." if len(val) > 30 else val
            console.print(f"  [green]✓[/green] {label}: {display}  [dim]({var})[/dim]")
            any_set = True
        else:
            console.print(f"  [dim]–[/dim] {label}: [dim]not set[/dim]  [dim]({var})[/dim]")

    console.print()
    if not any_set:
        console.print("[dim]No notification env vars configured.[/dim]")
        console.print("[dim]Set AGENTKIT_NOTIFY_SLACK, AGENTKIT_NOTIFY_DISCORD, or AGENTKIT_NOTIFY_WEBHOOK.[/dim]")
    console.print()
