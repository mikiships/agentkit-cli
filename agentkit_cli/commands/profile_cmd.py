"""agentkit profile command — list, show, create, use, export profiles."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

import agentkit_cli.profiles as _profiles_mod
from agentkit_cli.profiles import ProfileDefinition, ProfileRegistry, _load_profile_toml
from agentkit_cli.config import TOML_FILENAME, _find_toml_config, _parse_toml, set_config_value

console = Console()
profile_app = typer.Typer(help="Manage agentkit quality profiles (presets for gate thresholds).")


@profile_app.command("list")
def profile_list() -> None:
    """List all profiles (built-in + user-defined)."""
    registry = ProfileRegistry()
    profiles = registry.list_all()

    table = Table(title="agentkit profiles", show_header=True, header_style="bold")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Source", style="dim")
    table.add_column("Min Score", justify="right")
    table.add_column("Max Drop", justify="right")
    table.add_column("Notify On")
    table.add_column("Description")

    for p in profiles:
        source = "built-in" if registry.is_built_in(p.name) else "user"
        min_score = str(p.min_score) if p.min_score is not None else "-"
        max_drop = str(p.max_drop) if p.max_drop is not None else "-"
        table.add_row(p.name, source, min_score, max_drop, p.notify_on, p.description)

    console.print(table)


@profile_app.command("show")
def profile_show(
    name: str = typer.Argument(..., help="Profile name to show"),
) -> None:
    """Show profile configuration details."""
    registry = ProfileRegistry()
    profile = registry.get(name)
    if profile is None:
        console.print(f"[red]Error:[/red] Profile '{name}' not found.")
        raise typer.Exit(code=1)

    source = "built-in" if registry.is_built_in(name) else "user"
    table = Table(title=f"Profile: {profile.name}", show_header=True, header_style="bold")
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    table.add_row("name", profile.name)
    table.add_row("description", profile.description)
    table.add_row("source", source)
    table.add_row("gate.min_score", str(profile.min_score) if profile.min_score is not None else "-")
    table.add_row("gate.max_drop", str(profile.max_drop) if profile.max_drop is not None else "-")
    table.add_row("gate.fail_on_regression", str(profile.fail_on_regression).lower())
    table.add_row("gate.enabled", str(profile.gate_enabled).lower())
    table.add_row("notify.on", profile.notify_on)
    table.add_row("run.record_history", str(profile.record_history).lower())

    console.print(table)


@profile_app.command("create")
def profile_create(
    name: str = typer.Argument(..., help="Name for the new profile"),
    from_base: Optional[str] = typer.Option(None, "--from", help="Base profile to inherit from"),
    min_score: Optional[float] = typer.Option(None, "--min-score", help="Minimum score threshold"),
    max_drop: Optional[float] = typer.Option(None, "--max-drop", help="Maximum score drop allowed"),
    notify_on: Optional[str] = typer.Option(None, "--notify-on", help="When to notify: fail|always|never"),
    description: str = typer.Option("", "--description", "-d", help="Profile description"),
) -> None:
    """Create a new user-defined profile (optionally inheriting from a base)."""
    registry = ProfileRegistry()

    # Start from base if provided
    base: Optional[ProfileDefinition] = None
    if from_base:
        base = registry.get(from_base)
        if base is None:
            console.print(f"[red]Error:[/red] Base profile '{from_base}' not found.")
            raise typer.Exit(code=1)

    new_profile = ProfileDefinition(
        name=name,
        description=description or (f"Based on {from_base}" if from_base else "User-defined profile"),
        min_score=min_score if min_score is not None else (base.min_score if base else None),
        max_drop=max_drop if max_drop is not None else (base.max_drop if base else None),
        fail_on_regression=base.fail_on_regression if base else False,
        notify_on=notify_on if notify_on is not None else (base.notify_on if base else "fail"),
        gate_enabled=base.gate_enabled if base else True,
        record_history=base.record_history if base else True,
        _source="user",
    )

    # Write to ~/.agentkit/profiles/<name>.toml
    profiles_dir = _profiles_mod.USER_PROFILES_DIR
    profiles_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profiles_dir / f"{name}.toml"

    lines = [
        f'name = "{new_profile.name}"',
        f'description = "{new_profile.description}"',
        "",
        "[gate]",
    ]
    if new_profile.min_score is not None:
        lines.append(f"min_score = {new_profile.min_score}")
    if new_profile.max_drop is not None:
        lines.append(f"max_drop = {new_profile.max_drop}")
    lines.append(f"fail_on_regression = {str(new_profile.fail_on_regression).lower()}")
    lines.append(f"enabled = {str(new_profile.gate_enabled).lower()}")
    lines.extend([
        "",
        "[notify]",
        f'on = "{new_profile.notify_on}"',
        "",
        "[run]",
        f"record_history = {str(new_profile.record_history).lower()}",
    ])

    profile_path.write_text("\n".join(lines) + "\n")
    console.print(f"[green]Created[/green] profile '{name}' at {profile_path}")


@profile_app.command("use")
def profile_use(
    name: str = typer.Argument(..., help="Profile name to activate"),
) -> None:
    """Set the active profile in .agentkit.toml."""
    registry = ProfileRegistry()
    if registry.get(name) is None:
        console.print(f"[red]Error:[/red] Profile '{name}' not found.")
        raise typer.Exit(code=1)

    # Find or create .agentkit.toml in cwd / project root
    project_toml = _find_toml_config()
    if project_toml is None:
        project_toml = Path.cwd() / TOML_FILENAME

    set_config_value("profile.active", name, project_toml)
    console.print(f"[green]Active profile set to[/green] '{name}' in {project_toml}")


@profile_app.command("export")
def profile_export(
    name: str = typer.Argument(..., help="Profile name to export"),
    format: str = typer.Option("toml", "--format", "-f", help="Output format: toml or json"),
) -> None:
    """Print a profile as TOML or JSON."""
    registry = ProfileRegistry()
    profile = registry.get(name)
    if profile is None:
        console.print(f"[red]Error:[/red] Profile '{name}' not found.")
        raise typer.Exit(code=1)

    if format.lower() == "json":
        print(json.dumps(profile.to_dict(), indent=2))
    else:
        # TOML output
        d = profile.to_dict()
        lines = [
            f'name = "{d["name"]}"',
            f'description = "{d["description"]}"',
            "",
            "[gate]",
        ]
        gate = d["gate"]
        if gate["min_score"] is not None:
            lines.append(f'min_score = {gate["min_score"]}')
        if gate["max_drop"] is not None:
            lines.append(f'max_drop = {gate["max_drop"]}')
        lines.append(f'fail_on_regression = {str(gate["fail_on_regression"]).lower()}')
        lines.append(f'enabled = {str(gate["enabled"]).lower()}')
        lines.extend([
            "",
            "[notify]",
            f'on = "{d["notify"]["on"]}"',
            "",
            "[run]",
            f'record_history = {str(d["run"]["record_history"]).lower()}',
        ])
        if d["sweep"]["targets"]:
            lines.extend([
                "",
                "[sweep]",
                f'targets = {json.dumps(d["sweep"]["targets"])}',
            ])
        print("\n".join(lines))
