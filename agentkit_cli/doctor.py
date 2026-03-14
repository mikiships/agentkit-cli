"""Core doctor checks and rendering helpers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Literal

from rich.console import Console
from rich.table import Table

from agentkit_cli import __version__

DoctorStatus = Literal["pass", "warn", "fail"]


@dataclass(frozen=True)
class DoctorCheckResult:
    """Structured result for a single doctor check."""

    id: str
    name: str
    status: DoctorStatus
    summary: str
    details: str
    fix_hint: str
    category: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorReport:
    """Structured doctor report."""

    root: str
    checks: list[DoctorCheckResult]

    @property
    def pass_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "pass")

    @property
    def warn_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for check in self.checks if check.status == "fail")

    def as_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "checks": [check.as_dict() for check in self.checks],
            "summary": {
                "pass": self.pass_count,
                "warn": self.warn_count,
                "fail": self.fail_count,
            },
        }

    def exit_code(self) -> int:
        return 1 if self.fail_count else 0


@dataclass(frozen=True)
class GitRepoState:
    """Cached repo-state helper used by multiple checks."""

    git_available: bool
    is_repo: bool
    message: str


def detect_git_repo(root: Path) -> GitRepoState:
    """Return whether *root* is inside a git work tree."""
    if shutil.which("git") is None:
        return GitRepoState(
            git_available=False,
            is_repo=False,
            message="git is not installed on PATH.",
        )

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return GitRepoState(
            git_available=True,
            is_repo=False,
            message=f"git probe failed: {exc}",
        )

    if result.returncode == 0 and result.stdout.strip() == "true":
        return GitRepoState(
            git_available=True,
            is_repo=True,
            message="Current directory is inside a git work tree.",
        )

    details = (result.stderr or result.stdout).strip() or "Current directory is not a git repository."
    return GitRepoState(git_available=True, is_repo=False, message=details)


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a git command and return the result, or None if git execution failed."""
    try:
        return subprocess.run(
            ["git"] + args,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def check_git_repo(root: Path) -> DoctorCheckResult:
    """Check whether the current directory is a git repository."""
    repo_state = detect_git_repo(root)
    if repo_state.is_repo:
        return DoctorCheckResult(
            id="repo.git",
            name="Git repository",
            status="pass",
            summary="Git repository detected.",
            details=repo_state.message,
            fix_hint="",
            category="repo",
        )

    return DoctorCheckResult(
        id="repo.git",
        name="Git repository",
        status="fail",
        summary="Current directory is not a git repository.",
        details=repo_state.message,
        fix_hint="Run 'git init' to create a repository here.",
        category="repo",
    )


def check_git_has_commit(root: Path, repo_state: GitRepoState | None = None) -> DoctorCheckResult:
    """Check whether the repository has at least one commit."""
    repo_state = repo_state or detect_git_repo(root)
    if not repo_state.is_repo:
        return DoctorCheckResult(
            id="repo.commit",
            name="Initial commit",
            status="warn",
            summary="Commit check skipped because this is not a git repository.",
            details=repo_state.message,
            fix_hint="Initialize git first, then create an initial commit.",
            category="repo",
        )

    result = _run_git(root, ["rev-parse", "--verify", "HEAD"])
    if result is None:
        return DoctorCheckResult(
            id="repo.commit",
            name="Initial commit",
            status="warn",
            summary="Could not verify repository history.",
            details="git exited unexpectedly while checking HEAD.",
            fix_hint="Run 'git status' manually and create an initial commit if needed.",
            category="repo",
        )

    if result.returncode == 0:
        return DoctorCheckResult(
            id="repo.commit",
            name="Initial commit",
            status="pass",
            summary="Repository has at least one commit.",
            details=result.stdout.strip(),
            fix_hint="",
            category="repo",
        )

    details = (result.stderr or result.stdout).strip() or "Repository does not have a valid HEAD yet."
    return DoctorCheckResult(
        id="repo.commit",
        name="Initial commit",
        status="warn",
        summary="Repository has no commits yet.",
        details=details,
        fix_hint="Create an initial commit with 'git add . && git commit -m \"Initial commit\"'.",
        category="repo",
    )


def check_working_tree_clean(root: Path, repo_state: GitRepoState | None = None) -> DoctorCheckResult:
    """Check whether the git working tree is clean."""
    repo_state = repo_state or detect_git_repo(root)
    if not repo_state.is_repo:
        return DoctorCheckResult(
            id="repo.working_tree",
            name="Working tree",
            status="warn",
            summary="Working tree check skipped because this is not a git repository.",
            details=repo_state.message,
            fix_hint="Initialize git first if you want clean/dirty repo diagnostics.",
            category="repo",
        )

    result = _run_git(root, ["status", "--porcelain"])
    if result is None:
        return DoctorCheckResult(
            id="repo.working_tree",
            name="Working tree",
            status="warn",
            summary="Could not inspect working tree state.",
            details="git exited unexpectedly while checking status.",
            fix_hint="Run 'git status' manually to inspect local changes.",
            category="repo",
        )

    dirty_entries = [line for line in result.stdout.splitlines() if line.strip()]
    if not dirty_entries:
        return DoctorCheckResult(
            id="repo.working_tree",
            name="Working tree",
            status="pass",
            summary="Working tree is clean.",
            details="No tracked or untracked file changes detected.",
            fix_hint="",
            category="repo",
        )

    details = "; ".join(dirty_entries[:5])
    return DoctorCheckResult(
        id="repo.working_tree",
        name="Working tree",
        status="warn",
        summary="Working tree has local changes.",
        details=details,
        fix_hint="Commit or stash local changes before running the full stack.",
        category="repo",
    )


def check_readme_present(root: Path) -> DoctorCheckResult:
    """Check whether README.md exists."""
    readme = root / "README.md"
    if readme.exists():
        return DoctorCheckResult(
            id="repo.readme",
            name="README.md",
            status="pass",
            summary="README.md is present.",
            details=str(readme),
            fix_hint="",
            category="repo",
        )

    return DoctorCheckResult(
        id="repo.readme",
        name="README.md",
        status="warn",
        summary="README.md is missing.",
        details="Expected project overview file was not found.",
        fix_hint="Add a README.md so the repo has a clear project entry point.",
        category="repo",
    )


def check_pyproject_present(root: Path) -> DoctorCheckResult:
    """Check whether pyproject.toml exists."""
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        return DoctorCheckResult(
            id="repo.pyproject",
            name="pyproject.toml",
            status="pass",
            summary="pyproject.toml is present.",
            details=str(pyproject),
            fix_hint="",
            category="repo",
        )

    return DoctorCheckResult(
        id="repo.pyproject",
        name="pyproject.toml",
        status="warn",
        summary="pyproject.toml is missing.",
        details="Expected Python project metadata file was not found.",
        fix_hint="Add a pyproject.toml file to declare project metadata and tool settings.",
        category="repo",
    )


def check_context_files(root: Path) -> DoctorCheckResult:
    """Check whether the repo contains a context file or directory."""
    context_paths = [
        root / "CLAUDE.md",
        root / "AGENTS.md",
        root / ".agents",
    ]
    existing = [path for path in context_paths if path.exists()]
    if existing:
        return DoctorCheckResult(
            id="context.presence",
            name="Context files",
            status="pass",
            summary="Context files are present.",
            details=", ".join(path.name for path in existing),
            fix_hint="",
            category="context",
        )

    return DoctorCheckResult(
        id="context.presence",
        name="Context files",
        status="warn",
        summary="No context files were found.",
        details="Looked for CLAUDE.md, AGENTS.md, or a .agents/ directory.",
        fix_hint="Run 'agentmd generate .' to create a baseline CLAUDE.md.",
        category="context",
    )


def run_doctor(root: Path | None = None) -> DoctorReport:
    """Run the core doctor checks for the given path."""
    project_root = (root or Path.cwd()).resolve()
    repo_state = detect_git_repo(project_root)
    checks = [
        check_git_repo(project_root),
        check_git_has_commit(project_root, repo_state=repo_state),
        check_working_tree_clean(project_root, repo_state=repo_state),
        check_readme_present(project_root),
        check_pyproject_present(project_root),
        check_context_files(project_root),
    ]
    return DoctorReport(root=str(project_root), checks=checks)


def render_human_report(report: DoctorReport, console: Console | None = None) -> None:
    """Render a human-readable Rich table for a doctor report."""
    console = console or Console()
    table = Table(title=f"agentkit doctor — agentkit-cli v{__version__}", show_header=True)
    table.add_column("Category", style="bold")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Summary")
    table.add_column("Fix hint")

    status_labels = {
        "pass": "[green]PASS[/green]",
        "warn": "[yellow]WARN[/yellow]",
        "fail": "[red]FAIL[/red]",
    }
    for check in report.checks:
        summary_text = check.summary
        if check.details:
            summary_text = f"{summary_text}\n{check.details}"
        table.add_row(
            check.category,
            check.name,
            status_labels[check.status],
            summary_text,
            check.fix_hint or "—",
        )

    console.print(table)
    console.print(
        f"Doctor: {report.pass_count} pass, {report.warn_count} warn, {report.fail_count} fail"
    )
