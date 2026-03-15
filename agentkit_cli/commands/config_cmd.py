"""agentkit config subcommand — init/show/set/get."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.config import (
    DEFAULT_TOML_TEMPLATE,
    TOML_FILENAME,
    USER_CONFIG_DIR,
    USER_CONFIG_FILE,
    _find_toml_config,
    _parse_toml,
    get_config_value,
    load_config,
    set_config_value,
)

console = Console()

config_app = typer.Typer(
    name="config",
    help="Manage agentkit project and user configuration.",
    add_completion=False,
)


def _project_config_path(start: Optional[Path] = None) -> Path:
    """Return the project .agentkit.toml path (in cwd or git root)."""
    from agentkit_cli.config import find_project_root
    root = find_project_root(start)
    return root / TOML_FILENAME


@config_app.command("init")
def config_init(
    global_flag: bool = typer.Option(False, "--global", help="Write to user-level ~/.config/agentkit/config.toml"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config file"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory (default: git root or cwd)"),
) -> None:
    """Write a .agentkit.toml with all defaults and inline comments."""
    if global_flag:
        target = USER_CONFIG_FILE
    else:
        target = _project_config_path(path)

    if target.exists() and not force:
        console.print(f"[yellow]Config already exists:[/yellow] {target}")
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(DEFAULT_TOML_TEMPLATE)
    console.print(f"[green]Created:[/green] {target}")


@config_app.command("show")
def config_show(
    global_flag: bool = typer.Option(False, "--global", help="Show only user-level config"),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
) -> None:
    """Display effective config merged from all sources with source annotations."""
    from agentkit_cli.config import find_project_root
    start = path or find_project_root()
    config = load_config(start)

    if json_output:
        import json
        out: dict = {
            "gate": {
                "min_score": config.gate.min_score,
                "max_drop": config.gate.max_drop,
                "fail_on_regression": config.gate.fail_on_regression,
            },
            "notify": {
                "slack_url": config.notify.slack_url,
                "discord_url": config.notify.discord_url,
                "webhook_url": config.notify.webhook_url,
                "on": config.notify.on,
            },
            "run": {
                "output_dir": config.run.output_dir,
                "label": config.run.label,
                "record_history": config.run.record_history,
            },
            "sweep": {
                "targets": config.sweep.targets,
                "sort_by": config.sweep.sort_by,
                "limit": config.sweep.limit,
            },
            "score": {
                "weights": {
                    "coderace": config.score.weights.coderace,
                    "agentlint": config.score.weights.agentlint,
                    "agentmd": config.score.weights.agentmd,
                    "agentreflect": config.score.weights.agentreflect,
                }
            },
            "_sources": config._sources,
        }
        typer.echo(json.dumps(out, indent=2))
        return

    # Show project config location
    project_toml = _find_toml_config(start)
    if not global_flag:
        if project_toml:
            console.print(f"[dim]Project config:[/dim] {project_toml}")
        else:
            console.print("[dim]Project config:[/dim] (none found)")
    if USER_CONFIG_FILE.exists():
        console.print(f"[dim]User config:[/dim] {USER_CONFIG_FILE}")

    console.print()

    table = Table(title="Effective Configuration", show_header=True)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Source", style="dim")

    rows = [
        ("gate.min_score", str(config.gate.min_score) if config.gate.min_score is not None else "(none)"),
        ("gate.max_drop", str(config.gate.max_drop) if config.gate.max_drop is not None else "(none)"),
        ("gate.fail_on_regression", str(config.gate.fail_on_regression)),
        ("notify.slack_url", config.notify.slack_url or "(empty)"),
        ("notify.discord_url", config.notify.discord_url or "(empty)"),
        ("notify.webhook_url", config.notify.webhook_url or "(empty)"),
        ("notify.on", config.notify.on),
        ("run.output_dir", config.run.output_dir),
        ("run.label", config.run.label or "(empty)"),
        ("run.record_history", str(config.run.record_history)),
        ("sweep.sort_by", config.sweep.sort_by),
        ("sweep.limit", str(config.sweep.limit)),
        ("sweep.targets", str(config.sweep.targets) if config.sweep.targets else "[]"),
        ("score.weights.coderace", str(config.score.weights.coderace)),
        ("score.weights.agentlint", str(config.score.weights.agentlint)),
        ("score.weights.agentmd", str(config.score.weights.agentmd)),
        ("score.weights.agentreflect", str(config.score.weights.agentreflect)),
    ]
    for key, val in rows:
        source = config._sources.get(key, "[default]")
        table.add_row(key, val, source)

    console.print(table)


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key (e.g. gate.min_score)"),
    global_flag: bool = typer.Option(False, "--global", help="Read from user-level config only"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
) -> None:
    """Print a single config value by dotted key."""
    from agentkit_cli.config import find_project_root
    start = path or find_project_root()
    val = get_config_value(key, start)
    if val is None:
        console.print(f"[red]Unknown key:[/red] {key}")
        raise typer.Exit(1)
    typer.echo(str(val))


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g. gate.min_score)"),
    value: str = typer.Argument(..., help="Value to set"),
    global_flag: bool = typer.Option(False, "--global", help="Write to user-level ~/.config/agentkit/config.toml"),
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Project directory"),
) -> None:
    """Set a key in the project (or user) config file."""
    if global_flag:
        target = USER_CONFIG_FILE
    else:
        target = _project_config_path(path)

    set_config_value(key, value, target)
    console.print(f"[green]Set[/green] {key} = {value} in {target}")
