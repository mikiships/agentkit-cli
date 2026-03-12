"""Config file management for .agentkit.yaml."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    import yaml  # type: ignore
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


CONFIG_FILENAME = ".agentkit.yaml"
LAST_RUN_FILENAME = ".agentkit-last-run.json"

DEFAULT_CONFIG = {
    "tools": {
        "coderace": True,
        "agentmd": True,
        "agentlint": True,
        "agentreflect": True,
    },
    "defaults": {
        "min_score": 80,
        "context_file": "CLAUDE.md",
    },
}

DEFAULT_CONFIG_YAML = """\
tools:
  coderace: true
  agentmd: true
  agentlint: true
  agentreflect: true
defaults:
  min_score: 80
  context_file: CLAUDE.md
"""


def find_project_root(start: Optional[Path] = None) -> Path:
    """Walk up to find git root; fall back to cwd."""
    cwd = start or Path.cwd()
    current = cwd
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return cwd


def config_path(root: Optional[Path] = None) -> Path:
    root = root or find_project_root()
    return root / CONFIG_FILENAME


def last_run_path(root: Optional[Path] = None) -> Path:
    root = root or find_project_root()
    return root / LAST_RUN_FILENAME


def config_exists(root: Optional[Path] = None) -> bool:
    return config_path(root).exists()


def write_default_config(root: Optional[Path] = None) -> Path:
    path = config_path(root)
    path.write_text(DEFAULT_CONFIG_YAML)
    return path


def load_last_run(root: Optional[Path] = None) -> Optional[dict]:
    import json
    p = last_run_path(root)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def save_last_run(data: dict, root: Optional[Path] = None) -> None:
    import json
    p = last_run_path(root)
    p.write_text(json.dumps(data, indent=2))
