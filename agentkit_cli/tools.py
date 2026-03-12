"""Tool detection and subprocess execution utilities."""
from __future__ import annotations

import shutil
import subprocess
from typing import Optional


QUARTET_TOOLS = ["agentmd", "coderace", "agentlint", "agentreflect"]

INSTALL_HINTS = {
    "agentmd": "pip install agentmd",
    "coderace": "pip install coderace",
    "agentlint": "pip install agentlint",
    "agentreflect": "pip install agentreflect",
}


def which(tool: str) -> Optional[str]:
    """Return path to tool if installed, else None."""
    return shutil.which(tool)


def is_installed(tool: str) -> bool:
    return which(tool) is not None


def get_version(tool: str) -> Optional[str]:
    """Try to get the version string for a tool."""
    path = which(tool)
    if not path:
        return None
    for flag in ["--version", "version"]:
        try:
            result = subprocess.run(
                [path, flag],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = (result.stdout + result.stderr).strip()
            if output:
                # Return first line
                return output.splitlines()[0]
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    return "installed"


def run_tool(tool: str, args: list[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run a quartet tool via subprocess."""
    path = which(tool)
    if not path:
        raise FileNotFoundError(f"Tool not found: {tool}. Install with: {INSTALL_HINTS.get(tool, f'pip install {tool}')}")
    return subprocess.run(
        [path] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def tool_status() -> dict[str, dict]:
    """Return status dict for all quartet tools."""
    result = {}
    for tool in QUARTET_TOOLS:
        installed = is_installed(tool)
        result[tool] = {
            "installed": installed,
            "path": which(tool) if installed else None,
            "version": get_version(tool) if installed else None,
        }
    return result
