"""agentkit webhook CLI commands.

Subcommands:
  agentkit webhook serve   — start webhook HTTP server
  agentkit webhook config  — manage webhook configuration in .agentkit.toml
  agentkit webhook test    — simulate an event locally (no HTTP required)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

console = Console()

webhook_app = typer.Typer(
    name="webhook",
    help="GitHub webhook server: receive push/pull_request events and run agentkit analysis.",
    add_completion=False,
)


# ---------------------------------------------------------------------------
# D2a: serve
# ---------------------------------------------------------------------------

@webhook_app.command("serve")
def serve_cmd(
    port: int = typer.Option(8080, "--port", "-p", help="Port to listen on (default: 8080)"),
    secret: Optional[str] = typer.Option(None, "--secret", "-s", help="HMAC secret from GitHub webhook settings"),
    no_verify_sig: bool = typer.Option(False, "--no-verify-sig", help="Disable signature verification (dev only)"),
) -> None:
    """Start the webhook HTTP server.

    GitHub should POST events to http://<your-host>:<port>/
    """
    from agentkit_cli.config import load_config, find_project_root
    from agentkit_cli.webhook.server import WebhookServer

    cfg = load_config()
    webhook_cfg = _load_webhook_config()

    effective_port = port
    effective_secret = secret or webhook_cfg.get("secret", "")
    verify_sig = not no_verify_sig
    notify_channels: List[str] = webhook_cfg.get("notify_channels", [])

    srv = WebhookServer(
        port=effective_port,
        secret=effective_secret,
        verify_sig=verify_sig,
        notify_channels=notify_channels,
    )

    console.print(f"\n[bold]agentkit webhook serve[/bold]")
    console.print(f"Listening on [green]{srv.local_url}[/green]")
    if not effective_secret and verify_sig:
        console.print("[yellow]Warning: no HMAC secret configured. All requests accepted.[/yellow]")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    srv.serve_forever()


# ---------------------------------------------------------------------------
# D2b: config
# ---------------------------------------------------------------------------

@webhook_app.command("config")
def config_cmd(
    show: bool = typer.Option(False, "--show", help="Display current webhook configuration"),
    set_secret: Optional[str] = typer.Option(None, "--set-secret", help="Set the HMAC webhook secret"),
    set_port: Optional[int] = typer.Option(None, "--set-port", help="Set the default webhook listen port"),
    set_channel: Optional[str] = typer.Option(None, "--set-channel", help="Add a notification channel URL"),
) -> None:
    """Manage webhook configuration in .agentkit.toml."""
    from agentkit_cli.config import find_project_root, set_config_value, TOML_FILENAME

    root = find_project_root()
    toml_path = root / TOML_FILENAME

    changed = False

    if set_secret is not None:
        set_config_value("webhook.secret", set_secret, toml_path)
        console.print(f"[green]webhook.secret[/green] saved to {toml_path}")
        changed = True

    if set_port is not None:
        set_config_value("webhook.port", str(set_port), toml_path)
        console.print(f"[green]webhook.port[/green] set to {set_port}")
        changed = True

    if set_channel is not None:
        # Append channel to notify_channels list
        _append_notify_channel(toml_path, set_channel)
        console.print(f"[green]webhook.notify_channels[/green] += {set_channel}")
        changed = True

    if show or not changed:
        _show_config()


def _show_config() -> None:
    """Print current webhook configuration."""
    cfg = _load_webhook_config()
    console.print("\n[bold]Webhook Configuration[/bold]")
    console.print(f"  port             : {cfg.get('port', 8080)}")
    secret = cfg.get("secret", "")
    masked = ("*" * min(len(secret), 8) + "...") if secret else "(not set)"
    console.print(f"  secret           : {masked}")
    channels = cfg.get("notify_channels", [])
    if channels:
        for ch in channels:
            console.print(f"  notify_channel   : {ch}")
    else:
        console.print("  notify_channels  : (none)")
    console.print()


def _load_webhook_config() -> dict:
    """Load [webhook] section from .agentkit.toml, returning defaults if absent."""
    from agentkit_cli.config import find_project_root, _parse_toml, TOML_FILENAME
    root = find_project_root()
    toml_path = root / TOML_FILENAME
    data = _parse_toml(toml_path) if toml_path.exists() else {}
    defaults = {"port": 8080, "secret": "", "notify_channels": []}
    webhook_section = data.get("webhook", {})
    return {**defaults, **webhook_section}


def _append_notify_channel(toml_path: Path, channel: str) -> None:
    """Add a URL to webhook.notify_channels list in .agentkit.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            tomllib = None  # type: ignore

    from agentkit_cli.config import _parse_toml, _dict_to_toml
    existing = _parse_toml(toml_path) if toml_path.exists() else {}
    webhook = existing.setdefault("webhook", {})
    channels = webhook.get("notify_channels", [])
    if channel not in channels:
        channels.append(channel)
    webhook["notify_channels"] = channels
    toml_path.parent.mkdir(parents=True, exist_ok=True)
    toml_path.write_text(_dict_to_toml(existing))


# ---------------------------------------------------------------------------
# D2c: test
# ---------------------------------------------------------------------------

@webhook_app.command("test")
def test_cmd(
    event: str = typer.Option("push", "--event", "-e", help="Event type to simulate: push|pull_request"),
    repo: str = typer.Option(".", "--repo", "-r", help="Repo full name or local path (default: .)"),
) -> None:
    """Simulate a webhook event locally (no HTTP, no server required).

    Runs the event through EventProcessor end-to-end with analysis mocked if
    the repo path isn't a real agentkit project.
    """
    from agentkit_cli.webhook.event_processor import EventProcessor
    from pathlib import Path as _Path

    if event not in ("push", "pull_request"):
        console.print(f"[red]Error:[/red] --event must be push or pull_request, got {event!r}")
        raise typer.Exit(code=2)

    # Build a synthetic event
    synthetic = _build_synthetic_event(event, repo)

    console.print(f"\n[bold]agentkit webhook test[/bold]")
    console.print(f"  event : {event}")
    console.print(f"  repo  : {repo}")
    console.print()

    ep = EventProcessor()
    result = ep.process(synthetic)

    console.print(f"[green]Score:[/green] {result['score']:.0f}/100")
    if result.get("comment_body"):
        console.print("\n[bold]PR Comment Body:[/bold]")
        console.print(result["comment_body"])

    console.print(f"\n[dim]recorded={result['recorded']}, notified={result['notified']}[/dim]")


def _build_synthetic_event(event_type: str, repo: str) -> dict:
    """Build a minimal synthetic GitHub event dict."""
    # If repo looks like a path (starts with . or /), derive full_name from cwd
    if repo.startswith(".") or repo.startswith("/"):
        from pathlib import Path as _Path
        resolved = _Path(repo).resolve()
        full_name = f"local/{resolved.name}"
    else:
        full_name = repo

    base = {
        "event_type": event_type,
        "repository": {
            "full_name": full_name,
            "clone_url": "",
        },
        "ref": "refs/heads/main",
    }
    if event_type == "pull_request":
        base["pull_request"] = {"number": 1, "title": "test PR"}
        base["action"] = "opened"
    else:
        base["commits"] = []

    return base
