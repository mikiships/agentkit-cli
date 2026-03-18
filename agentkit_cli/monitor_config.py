"""Monitor configuration for agentkit — persistent target registry.

Stores monitor targets in .agentkit.toml under [monitor.targets].
Each target is a monitored repo/path with schedule, notification, and threshold config.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

VALID_SCHEDULES = ("hourly", "daily", "weekly")
MONITOR_TOML_FILENAME = ".agentkit.toml"
MONITOR_STATE_DIR = Path.home() / ".agentkit"


@dataclass
class MonitorTarget:
    """A single monitored target (repo path or GitHub URL)."""
    target: str
    schedule: str = "daily"  # hourly | daily | weekly
    notify_slack: Optional[str] = None
    notify_discord: Optional[str] = None
    notify_webhook: Optional[str] = None
    min_score: Optional[float] = None
    alert_threshold: float = 10.0
    last_checked: Optional[str] = None
    last_score: Optional[float] = None

    def __post_init__(self) -> None:
        if self.schedule not in VALID_SCHEDULES:
            raise ValueError(f"schedule must be one of {VALID_SCHEDULES}, got {self.schedule!r}")
        if self.alert_threshold < 0:
            raise ValueError("alert_threshold must be non-negative")

    def has_notify(self) -> bool:
        """Return True if any notification channel is configured."""
        return bool(self.notify_slack or self.notify_discord or self.notify_webhook)

    def schedule_seconds(self) -> int:
        """Return schedule period in seconds."""
        return {"hourly": 3600, "daily": 86400, "weekly": 604800}[self.schedule]

    def is_due(self) -> bool:
        """Return True if this target's next check is overdue."""
        if self.last_checked is None:
            return True
        try:
            last = datetime.fromisoformat(self.last_checked)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            elapsed = (now - last).total_seconds()
            return elapsed >= self.schedule_seconds()
        except (ValueError, TypeError):
            return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dict suitable for TOML storage."""
        d: Dict[str, Any] = {
            "schedule": self.schedule,
            "alert_threshold": self.alert_threshold,
        }
        if self.notify_slack:
            d["notify_slack"] = self.notify_slack
        if self.notify_discord:
            d["notify_discord"] = self.notify_discord
        if self.notify_webhook:
            d["notify_webhook"] = self.notify_webhook
        if self.min_score is not None:
            d["min_score"] = self.min_score
        if self.last_checked is not None:
            d["last_checked"] = self.last_checked
        if self.last_score is not None:
            d["last_score"] = self.last_score
        return d

    @classmethod
    def from_dict(cls, target: str, data: Dict[str, Any]) -> "MonitorTarget":
        """Deserialize from a TOML dict."""
        return cls(
            target=target,
            schedule=data.get("schedule", "daily"),
            notify_slack=data.get("notify_slack") or None,
            notify_discord=data.get("notify_discord") or None,
            notify_webhook=data.get("notify_webhook") or None,
            min_score=data.get("min_score"),
            alert_threshold=float(data.get("alert_threshold", 10.0)),
            last_checked=data.get("last_checked") or None,
            last_score=data.get("last_score"),
        )


class MonitorConfig:
    """Loads and persists monitor targets to/from .agentkit.toml.

    Uses the existing [monitor.targets] section without clobbering other sections.
    """

    def __init__(self, toml_path: Optional[Path] = None) -> None:
        self._path = toml_path or self._find_toml()
        self._targets: Dict[str, MonitorTarget] = {}
        self._raw: Dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_toml(start: Optional[Path] = None) -> Path:
        """Walk up from start to find .agentkit.toml; fall back to cwd."""
        cwd = start or Path.cwd()
        current = cwd
        while True:
            candidate = current / MONITOR_TOML_FILENAME
            if candidate.exists():
                return candidate
            parent = current.parent
            if parent == current:
                break
            current = parent
        return cwd / MONITOR_TOML_FILENAME

    def _parse_toml(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        if tomllib is None:
            return {}
        try:
            with open(self._path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}

    def _write_toml(self, data: Dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(_dict_to_toml(data))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Reload targets from disk."""
        self._raw = self._parse_toml()
        monitor_section = self._raw.get("monitor", {})
        targets_section = monitor_section.get("targets", {})
        self._targets = {}
        for name, data in targets_section.items():
            if isinstance(data, dict):
                try:
                    self._targets[name] = MonitorTarget.from_dict(name, data)
                except (ValueError, TypeError):
                    pass

    def save(self) -> None:
        """Persist current targets back to disk, preserving other TOML sections."""
        raw = dict(self._raw)
        # Rebuild the [monitor] section
        monitor_section = {k: v for k, v in raw.get("monitor", {}).items() if k != "targets"}
        targets_dict: Dict[str, Any] = {}
        for name, mt in self._targets.items():
            targets_dict[name] = mt.to_dict()
        monitor_section["targets"] = targets_dict
        raw["monitor"] = monitor_section
        self._write_toml(raw)
        # Re-parse to keep _raw in sync
        self._raw = self._parse_toml()

    def add_target(
        self,
        target: str,
        schedule: str = "daily",
        notify_slack: Optional[str] = None,
        notify_discord: Optional[str] = None,
        notify_webhook: Optional[str] = None,
        min_score: Optional[float] = None,
        alert_threshold: float = 10.0,
    ) -> MonitorTarget:
        """Add or replace a target. Raises ValueError on invalid args."""
        mt = MonitorTarget(
            target=target,
            schedule=schedule,
            notify_slack=notify_slack,
            notify_discord=notify_discord,
            notify_webhook=notify_webhook,
            min_score=min_score,
            alert_threshold=alert_threshold,
        )
        self._targets[target] = mt
        self.save()
        return mt

    def remove_target(self, target: str) -> bool:
        """Remove a target. Returns True if it existed."""
        if target in self._targets:
            del self._targets[target]
            self.save()
            return True
        return False

    def list_targets(self) -> List[MonitorTarget]:
        """Return all registered targets."""
        return list(self._targets.values())

    def get_target(self, target: str) -> Optional[MonitorTarget]:
        """Return a single target by name, or None."""
        return self._targets.get(target)

    def update_last_run(
        self, target: str, score: float, ts: Optional[str] = None
    ) -> None:
        """Update last_checked and last_score for a target."""
        mt = self._targets.get(target)
        if mt is None:
            return
        mt.last_checked = ts or datetime.now(timezone.utc).isoformat()
        mt.last_score = score
        self.save()


# ---------------------------------------------------------------------------
# Minimal TOML serializer (no external deps)
# ---------------------------------------------------------------------------

def _toml_key(k: str) -> str:
    """Return a bare TOML key or quoted key if necessary."""
    import re
    if re.match(r'^[A-Za-z0-9_\-]+$', k):
        return k
    escaped = k.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _dict_to_toml(data: Dict[str, Any], prefix: str = "") -> str:
    """Serialize a nested dict to TOML text."""
    lines: List[str] = []
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables = {k: v for k, v in data.items() if isinstance(v, dict)}

    for k, v in scalars.items():
        key = _toml_key(k)
        if isinstance(v, bool):
            lines.append(f"{key} = {str(v).lower()}")
        elif isinstance(v, str):
            escaped = v.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key} = "{escaped}"')
        elif isinstance(v, list):
            items = ", ".join(f'"{x}"' if isinstance(x, str) else str(x) for x in v)
            lines.append(f"{key} = [{items}]")
        elif v is None:
            pass  # skip None values
        else:
            lines.append(f"{key} = {v}")

    for k, v in tables.items():
        qk = _toml_key(k)
        section = f"{prefix}.{qk}" if prefix else qk
        lines.append("")
        lines.append(f"[{section}]")
        inner = _dict_to_toml(v, section)
        if inner.strip():
            lines.append(inner.rstrip())

    return "\n".join(lines) + "\n" if lines else ""
