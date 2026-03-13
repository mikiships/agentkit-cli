"""Git helpers for agentkit compare — worktree-based checkout."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class GitError(Exception):
    pass


def resolve_ref(ref: str, cwd: Optional[str] = None) -> str:
    """Return the full SHA for a git ref."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise GitError(f"Cannot resolve ref '{ref}': {result.stderr.strip()}")
    return result.stdout.strip()


def git_root(cwd: Optional[str] = None) -> Path:
    """Return the git repo root."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise GitError("Not inside a git repository.")
    return Path(result.stdout.strip())


def changed_files(ref1: str, ref2: str, cwd: Optional[str] = None) -> list[str]:
    """Return list of files changed between ref1 and ref2."""
    result = subprocess.run(
        ["git", "diff", "--name-only", ref1, ref2],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.strip().splitlines() if line]


class Worktree:
    """Context manager that adds/removes a git worktree for a specific ref."""

    def __init__(self, ref: str, repo_root: Path) -> None:
        self.ref = ref
        self.repo_root = repo_root
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None  # type: ignore[type-arg]
        self.path: Optional[Path] = None

    def __enter__(self) -> Path:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="agentkit-compare-")
        wt_path = Path(self._tmpdir.name) / "worktree"
        sha = resolve_ref(self.ref, cwd=str(self.repo_root))
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(wt_path), sha],
            capture_output=True,
            text=True,
            cwd=str(self.repo_root),
        )
        if result.returncode != 0:
            self._tmpdir.cleanup()
            raise GitError(f"Failed to create worktree for '{self.ref}': {result.stderr.strip()}")
        self.path = wt_path
        return wt_path

    def __exit__(self, *_: object) -> None:
        if self.path is not None:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(self.path)],
                capture_output=True,
                cwd=str(self.repo_root),
            )
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
