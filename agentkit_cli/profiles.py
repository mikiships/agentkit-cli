"""Profile system for agentkit-cli v0.23.0.

Profiles are named presets for gate thresholds, notify config, and sweep targets.
Three built-in presets: strict, balanced, minimal.
User-defined profiles can be stored in ~/.agentkit/profiles/*.toml.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


USER_PROFILES_DIR = Path.home() / ".agentkit" / "profiles"


@dataclass
class ProfileDefinition:
    """A named preset for agentkit configuration."""
    name: str
    description: str
    # gate settings
    min_score: Optional[float] = None
    max_drop: Optional[float] = None
    fail_on_regression: bool = False
    # notify settings
    notify_on: str = "fail"
    # run settings
    record_history: bool = True
    # sweep settings
    sweep_targets: List[str] = field(default_factory=list)
    # gate enabled/disabled
    gate_enabled: bool = True
    # source tracking
    _source: str = "built-in"

    def to_dict(self) -> Dict[str, Any]:
        """Return profile as a plain dict for export."""
        return {
            "name": self.name,
            "description": self.description,
            "gate": {
                "min_score": self.min_score,
                "max_drop": self.max_drop,
                "fail_on_regression": self.fail_on_regression,
                "enabled": self.gate_enabled,
            },
            "notify": {
                "on": self.notify_on,
            },
            "run": {
                "record_history": self.record_history,
            },
            "sweep": {
                "targets": self.sweep_targets,
            },
        }


# Built-in presets
_BUILT_IN_PROFILES: List[ProfileDefinition] = [
    ProfileDefinition(
        name="strict",
        description="High standards: min-score 85, max-drop 3, notify on failure",
        min_score=85.0,
        max_drop=3.0,
        fail_on_regression=True,
        notify_on="fail",
        gate_enabled=True,
    ),
    ProfileDefinition(
        name="balanced",
        description="Sensible defaults: min-score 70, max-drop 10, notify off",
        min_score=70.0,
        max_drop=10.0,
        fail_on_regression=False,
        notify_on="never",
        gate_enabled=True,
    ),
    ProfileDefinition(
        name="minimal",
        description="Permissive: min-score 50, max-drop 20, gate disabled",
        min_score=50.0,
        max_drop=20.0,
        fail_on_regression=False,
        notify_on="never",
        gate_enabled=False,
    ),
]


class ProfileRegistry:
    """Registry of built-in and user-defined profiles."""

    def __init__(self, profiles_dir: Optional[Path] = None) -> None:
        self._profiles: Dict[str, ProfileDefinition] = {}
        # Load built-ins first
        for p in _BUILT_IN_PROFILES:
            self._profiles[p.name.lower()] = p
        # Load user-defined profiles
        self._profiles_dir = profiles_dir or USER_PROFILES_DIR
        self._load_user_profiles()

    def _load_user_profiles(self) -> None:
        if not self._profiles_dir.exists():
            return
        for toml_file in sorted(self._profiles_dir.glob("*.toml")):
            try:
                profile = _load_profile_toml(toml_file)
                if profile:
                    self._profiles[profile.name.lower()] = profile
            except Exception:
                pass

    def get(self, name: str) -> Optional[ProfileDefinition]:
        """Look up profile by name (case-insensitive)."""
        return self._profiles.get(name.lower())

    def list_all(self) -> List[ProfileDefinition]:
        """Return all profiles, built-ins first, then user-defined."""
        built_in_names = {p.name.lower() for p in _BUILT_IN_PROFILES}
        built_ins = [self._profiles[n] for n in built_in_names if n in self._profiles]
        user = [p for n, p in self._profiles.items() if n not in built_in_names]
        return built_ins + user

    def register(self, profile: ProfileDefinition) -> None:
        """Register a profile (replaces existing with same name)."""
        self._profiles[profile.name.lower()] = profile

    def is_built_in(self, name: str) -> bool:
        built_in_names = {p.name.lower() for p in _BUILT_IN_PROFILES}
        return name.lower() in built_in_names


def _load_profile_toml(path: Path) -> Optional[ProfileDefinition]:
    """Load a ProfileDefinition from a TOML file."""
    if tomllib is None:
        return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except Exception:
        return None

    name = data.get("name") or path.stem
    description = data.get("description", "")
    gate = data.get("gate", {})
    notify = data.get("notify", {})
    run_cfg = data.get("run", {})
    sweep = data.get("sweep", {})

    return ProfileDefinition(
        name=name,
        description=description,
        min_score=float(gate["min_score"]) if "min_score" in gate else None,
        max_drop=float(gate["max_drop"]) if "max_drop" in gate else None,
        fail_on_regression=bool(gate.get("fail_on_regression", False)),
        gate_enabled=bool(gate.get("enabled", True)),
        notify_on=notify.get("on", "fail"),
        record_history=bool(run_cfg.get("record_history", True)),
        sweep_targets=list(sweep.get("targets", [])),
        _source=str(path),
    )


def apply_profile(
    name: str,
    config: Any,
    registry: Optional[ProfileRegistry] = None,
    *,
    # explicit CLI flag values (None means "not provided by user")
    cli_min_score: Optional[float] = None,
    cli_max_drop: Optional[float] = None,
) -> Any:
    """Merge profile values into an AgentKitConfig.

    Precedence: explicit CLI flags > profile > existing config values.
    Returns the mutated config object.
    """
    if registry is None:
        registry = ProfileRegistry()

    profile = registry.get(name)
    if profile is None:
        raise ValueError(f"Profile '{name}' not found. Available: {[p.name for p in registry.list_all()]}")

    # Apply gate settings only if not overridden by explicit CLI flags
    if cli_min_score is None and profile.min_score is not None:
        config.gate.min_score = profile.min_score
    if cli_max_drop is None and profile.max_drop is not None:
        config.gate.max_drop = profile.max_drop

    # fail_on_regression: profile wins over default (False) but not over toml
    # We always apply profile's fail_on_regression if not explicitly set
    config.gate.fail_on_regression = profile.fail_on_regression

    # notify: profile fills gaps
    if not config.notify.on or config.notify.on == "fail":
        config.notify.on = profile.notify_on

    return config


# Convenience: get a single registry instance
_registry: Optional[ProfileRegistry] = None


def get_registry() -> ProfileRegistry:
    global _registry
    if _registry is None:
        _registry = ProfileRegistry()
    return _registry
