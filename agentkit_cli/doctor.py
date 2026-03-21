"""Core doctor checks and rendering helpers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Literal

from rich.console import Console
from rich.table import Table

from agentkit_cli import __version__
from agentkit_cli.history import get_history

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


# ---------------------------------------------------------------------------
# D2: Toolchain probes
# ---------------------------------------------------------------------------

_CORE_TOOLS = ("agentmd", "agentlint", "coderace", "agentreflect")
_OPTIONAL_TOOLS = ("git", "python3")


def _probe_binary_version(binary: str) -> tuple[bool, str]:
    """Return (found, version_text).  version_text is '' when unavailable."""
    if shutil.which(binary) is None:
        return False, ""
    try:
        result = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        raw = (result.stdout or result.stderr).strip()
        # Take the first non-empty line and cap to 80 chars for readability.
        version_line = next((line for line in raw.splitlines() if line.strip()), "")
        return True, version_line[:80]
    except (OSError, subprocess.SubprocessError):
        return True, ""  # binary exists but --version probe failed; still found


def check_tool_binary(binary: str, *, is_core: bool) -> DoctorCheckResult:
    """Check whether a toolkit binary is available on PATH."""
    found, version = _probe_binary_version(binary)
    category = "toolchain"
    tool_id = f"toolchain.{binary.replace('-', '_')}"

    if found:
        summary = f"{binary} is available."
        details = version if version else f"{binary} found on PATH; version probe returned no output."
        return DoctorCheckResult(
            id=tool_id,
            name=binary,
            status="pass",
            summary=summary,
            details=details,
            fix_hint="",
            category=category,
        )

    if is_core:
        return DoctorCheckResult(
            id=tool_id,
            name=binary,
            status="fail",
            summary=f"{binary} is not installed.",
            details=f"Required core tool '{binary}' was not found on PATH.",
            fix_hint=f"Install {binary} and make sure it is on your PATH.",
            category=category,
        )

    return DoctorCheckResult(
        id=tool_id,
        name=binary,
        status="warn",
        summary=f"{binary} is not installed (optional).",
        details=f"Optional tool '{binary}' was not found on PATH.",
        fix_hint=f"Install {binary} for the full toolkit experience.",
        category=category,
    )


def check_toolchain() -> list[DoctorCheckResult]:
    """Return a check result for each core and optional tool."""
    results: list[DoctorCheckResult] = []
    for binary in _CORE_TOOLS:
        results.append(check_tool_binary(binary, is_core=True))
    for binary in _OPTIONAL_TOOLS:
        results.append(check_tool_binary(binary, is_core=False))
    results.append(check_ecosystem_available())
    return results


# ---------------------------------------------------------------------------
# D3: Actionability checks with fix hints
# ---------------------------------------------------------------------------

_SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".tsx", ".jsx"}


def check_source_files(root: Path) -> DoctorCheckResult:
    """Check whether *root* contains at least one recognised source file."""
    found = next(
        (
            f
            for f in root.rglob("*")
            if f.suffix in _SOURCE_EXTENSIONS and f.is_file()
        ),
        None,
    )
    if found:
        return DoctorCheckResult(
            id="context.source_files",
            name="Source files",
            status="pass",
            summary="Source files found in project.",
            details=f"e.g. {found.relative_to(root)}",
            fix_hint="",
            category="context",
        )

    return DoctorCheckResult(
        id="context.source_files",
        name="Source files",
        status="warn",
        summary="No source files found.",
        details=f"Looked for {', '.join(sorted(_SOURCE_EXTENSIONS))} files recursively.",
        fix_hint="Add at least one source file (.py, .ts, .js, .tsx, or .jsx) to the project.",
        category="context",
    )


def check_context_freshness(root: Path) -> DoctorCheckResult:
    """Run agentlint check-context via ToolAdapter; degrade gracefully."""
    from agentkit_cli.tools import is_installed, get_adapter

    if not is_installed("agentlint"):
        return DoctorCheckResult(
            id="context.freshness",
            name="Context freshness",
            status="warn",
            summary="agentlint not found; context freshness check skipped.",
            details="Install agentlint to enable context freshness diagnostics.",
            fix_hint="Install agentlint and re-run 'agentkit doctor'.",
            category="context",
        )

    payload = get_adapter().agentlint_check_context(str(root))

    if payload is None:
        return DoctorCheckResult(
            id="context.freshness",
            name="Context freshness",
            status="warn",
            summary="agentlint check-context failed or returned unparseable output.",
            details="ToolAdapter returned None (non-zero exit, timeout, or bad JSON).",
            fix_hint="Run 'agentlint check-context' manually to diagnose.",
            category="context",
        )

    fresh = payload.get("fresh", True)
    age_days = payload.get("age_days")
    detail = json.dumps(payload)[:200]
    if fresh:
        return DoctorCheckResult(
            id="context.freshness",
            name="Context freshness",
            status="pass",
            summary="Context files are up to date.",
            details=detail,
            fix_hint="",
            category="context",
        )
    age_label = f" ({age_days}d old)" if age_days is not None else ""
    return DoctorCheckResult(
        id="context.freshness",
        name="Context freshness",
        status="warn",
        summary=f"Context files may be stale{age_label}.",
        details=detail,
        fix_hint="Run 'agentmd generate .' to refresh context files.",
        category="context",
    )


def check_output_dir(root: Path) -> DoctorCheckResult:
    """Check whether the default report output directory is accessible."""
    report_dir = root / "agentkit-report"
    if report_dir.exists():
        if os.access(report_dir, os.W_OK):
            return DoctorCheckResult(
                id="context.output_dir",
                name="Report output dir",
                status="pass",
                summary="agentkit-report/ is present and writable.",
                details=str(report_dir),
                fix_hint="",
                category="context",
            )
        return DoctorCheckResult(
            id="context.output_dir",
            name="Report output dir",
            status="fail",
            summary="agentkit-report/ exists but is not writable.",
            details=str(report_dir),
            fix_hint="Fix permissions: 'chmod u+w agentkit-report/'.",
            category="context",
        )

    # Dir doesn't exist yet — check parent is writable.
    if os.access(root, os.W_OK):
        return DoctorCheckResult(
            id="context.output_dir",
            name="Report output dir",
            status="pass",
            summary="agentkit-report/ does not exist yet; parent dir is writable.",
            details=f"Will be created at {report_dir} when needed.",
            fix_hint="",
            category="context",
        )

    return DoctorCheckResult(
        id="context.output_dir",
        name="Report output dir",
        status="fail",
        summary="Cannot create agentkit-report/ — parent directory is not writable.",
        details=str(root),
        fix_hint=f"Fix permissions on '{root}' or use --output to specify a writable path.",
        category="context",
    )


def check_herenow_api_key() -> DoctorCheckResult:
    """Warn if HERENOW_API_KEY is unset (publish will fail without it)."""
    key = os.environ.get("HERENOW_API_KEY", "").strip()
    if key:
        return DoctorCheckResult(
            id="publish.herenow_key",
            name="HERENOW_API_KEY",
            status="pass",
            summary="HERENOW_API_KEY is set.",
            details="Publish via 'agentkit publish' will be authenticated.",
            fix_hint="",
            category="publish",
        )

    return DoctorCheckResult(
        id="publish.herenow_key",
        name="HERENOW_API_KEY",
        status="warn",
        summary="HERENOW_API_KEY is not set.",
        details="Publishing reports via 'agentkit publish' will use anonymous mode (24h expiry).",
        fix_hint="Set HERENOW_API_KEY in your shell profile for persistent publish URLs.",
        category="publish",
    )


# ---------------------------------------------------------------------------
# D5: Serve availability check
# ---------------------------------------------------------------------------


def check_redteam_recency(root: Path) -> DoctorCheckResult:
    """Warn if redteam has not been run in the last 7 days."""
    try:
        from datetime import datetime, timezone, timedelta
        rows = get_history(project=root.name, tool="redteam", limit=1)
        if not rows:
            return DoctorCheckResult(
                id="context.redteam_recency",
                name="redteam recency",
                status="warn",
                summary="No redteam run found for this project.",
                details="Run 'agentkit redteam' to assess adversarial resistance.",
                fix_hint="agentkit redteam",
                category="context",
            )
        last_ts = rows[0].get("created_at") or rows[0].get("timestamp", "")
        try:
            if isinstance(last_ts, str):
                last_dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            else:
                last_dt = datetime.fromtimestamp(float(last_ts), tz=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            if last_dt < cutoff:
                days_ago = (datetime.now(timezone.utc) - last_dt).days
                return DoctorCheckResult(
                    id="context.redteam_recency",
                    name="redteam recency",
                    status="warn",
                    summary=f"Last redteam run was {days_ago} days ago (>7 days).",
                    details="Re-run to detect new vulnerabilities after context file changes.",
                    fix_hint="agentkit redteam",
                    category="context",
                )
        except (ValueError, TypeError):
            pass
        return DoctorCheckResult(
            id="context.redteam_recency",
            name="redteam recency",
            status="pass",
            summary="redteam run is recent (within 7 days).",
            details="",
            fix_hint="",
            category="context",
        )
    except Exception as e:
        return DoctorCheckResult(
            id="context.redteam_recency",
            name="redteam recency",
            status="warn",
            summary="Could not check redteam history.",
            details=str(e),
            fix_hint="agentkit redteam",
            category="context",
        )


def check_ecosystem_available() -> DoctorCheckResult:
    """Verify that agentkit ecosystem command is importable and functional."""
    try:
        from agentkit_cli.commands import ecosystem_cmd as _eco_cmd  # noqa: F401
        from agentkit_cli.engines import ecosystem as _eco_eng  # noqa: F401
        return DoctorCheckResult(
            id="toolchain.ecosystem",
            name="agentkit ecosystem",
            status="pass",
            summary="agentkit ecosystem is available.",
            details="Run 'agentkit ecosystem' for macro AI-agent-readiness scan.",
            fix_hint="",
            category="toolchain",
        )
    except ImportError as exc:
        return DoctorCheckResult(
            id="toolchain.ecosystem",
            name="agentkit ecosystem",
            status="fail",
            summary="agentkit ecosystem is not importable.",
            details=str(exc),
            fix_hint="Reinstall agentkit-cli: pip install -U agentkit-cli",
            category="toolchain",
        )


def check_serve_available() -> DoctorCheckResult:
    """Verify that agentkit serve command is importable and functional."""
    try:
        from agentkit_cli import serve as _serve_mod  # noqa: F401
        from agentkit_cli.commands import serve_cmd as _serve_cmd  # noqa: F401
        return DoctorCheckResult(
            id="publish.serve",
            name="agentkit serve",
            status="pass",
            summary="agentkit serve is available.",
            details="Run 'agentkit serve' to start the local dashboard.",
            fix_hint="",
            category="publish",
        )
    except ImportError as exc:
        return DoctorCheckResult(
            id="publish.serve",
            name="agentkit serve",
            status="fail",
            summary="agentkit serve is not importable.",
            details=str(exc),
            fix_hint="Reinstall agentkit-cli: pip install -U agentkit-cli",
            category="publish",
        )


def check_webhook_config(root: Path) -> DoctorCheckResult:
    """Check whether a webhook is configured and, if so, whether the secret is set."""
    try:
        from agentkit_cli.config import TOML_FILENAME, _parse_toml
        toml_path = root / TOML_FILENAME
        data = _parse_toml(toml_path) if toml_path.exists() else {}
        webhook = data.get("webhook", {})

        if not webhook:
            return DoctorCheckResult(
                id="integrations.webhook",
                name="webhook config",
                status="pass",
                summary="No webhook configured (optional).",
                details="Run 'agentkit webhook config --set-secret <secret>' to enable.",
                fix_hint="agentkit webhook config --set-secret <SECRET>",
                category="integrations",
            )

        secret = webhook.get("secret", "")
        if not secret:
            return DoctorCheckResult(
                id="integrations.webhook",
                name="webhook config",
                status="warn",
                summary="Webhook configured but HMAC secret is empty.",
                details="Without a secret, any HTTP client can trigger analysis.",
                fix_hint="agentkit webhook config --set-secret <SECRET>",
                category="integrations",
            )

        port = webhook.get("port", 8080)
        return DoctorCheckResult(
            id="integrations.webhook",
            name="webhook config",
            status="pass",
            summary=f"Webhook configured on port {port} with HMAC secret.",
            details="Run 'agentkit webhook serve' to start listening.",
            fix_hint="",
            category="integrations",
        )
    except Exception as exc:
        return DoctorCheckResult(
            id="integrations.webhook",
            name="webhook config",
            status="warn",
            summary="Could not read webhook config.",
            details=str(exc),
            fix_hint="agentkit webhook config --show",
            category="integrations",
        )


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def check_llmstxt_readiness(root: Path) -> DoctorCheckResult:
    """Check whether the repo is ready to generate llms.txt."""
    has_readme = any((root / p).exists() for p in ("README.md", "README.rst", "README.txt", "README"))
    has_docs = any((root / d).is_dir() for d in ("docs", "doc", "documentation"))
    has_llmstxt = (root / "llms.txt").exists()

    if has_llmstxt:
        return DoctorCheckResult(
            id="context.llmstxt",
            name="llms.txt",
            status="pass",
            summary="llms.txt found — repo is AI-accessible.",
            details=str(root / "llms.txt"),
            fix_hint="",
            category="context",
        )
    if has_readme:
        return DoctorCheckResult(
            id="context.llmstxt",
            name="llms.txt",
            status="pass",
            summary="README found — ready to generate llms.txt. Run 'agentkit llmstxt'.",
            details=f"docs/: {'found' if has_docs else 'not found'}",
            fix_hint="Run: agentkit llmstxt",
            category="context",
        )
    return DoctorCheckResult(
        id="context.llmstxt",
        name="llms.txt",
        status="warn",
        summary="No README or llms.txt found. Add a README.md first, then run 'agentkit llmstxt'.",
        details="",
        fix_hint="Add README.md, then run: agentkit llmstxt",
        category="context",
    )


def check_context_sync(root: Path) -> DoctorCheckResult:
    """Check whether managed context format files are in sync."""
    try:
        from agentkit_cli.migrate import MigrateEngine
        eng = MigrateEngine()
        status = eng.get_sync_status(root)
    except Exception:
        return DoctorCheckResult(
            id="context.sync",
            name="context-sync",
            status="warn",
            summary="Could not check context format sync.",
            details="",
            fix_hint="Run: agentkit migrate --all",
            category="context",
        )

    if not status:
        return DoctorCheckResult(
            id="context.sync",
            name="context-sync",
            status="pass",
            summary="No managed context files found — nothing to sync.",
            details="",
            fix_hint="",
            category="context",
        )

    stale = [fmt for fmt, s in status.items() if s == "stale"]
    missing = [fmt for fmt, s in status.items() if s == "missing"]

    if stale:
        return DoctorCheckResult(
            id="context.sync",
            name="context-sync",
            status="warn",
            summary=f"Context format files out of sync: {', '.join(stale)}",
            details="Run 'agentkit sync --fix' to update derived files.",
            fix_hint="Run: agentkit sync --fix",
            category="context",
        )
    if missing:
        return DoctorCheckResult(
            id="context.sync",
            name="context-sync",
            status="pass",
            summary=f"Context files present; {len(missing)} format(s) not yet generated.",
            details="Run 'agentkit migrate --all' to generate missing formats.",
            fix_hint="Run: agentkit migrate --all",
            category="context",
        )
    return DoctorCheckResult(
        id="context.sync",
        name="context-sync",
        status="pass",
        summary="All managed context format files are in sync.",
        details="",
        fix_hint="",
        category="context",
    )


def check_spotlight_github_access() -> DoctorCheckResult:
    """Check that GitHub API is reachable for spotlight candidate selection."""
    import json as _json
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://api.github.com/rate_limit",
            headers={"Accept": "application/vnd.github+json"},
        )
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
        remaining = data.get("rate", {}).get("remaining", 0)
        if remaining < 10:
            return DoctorCheckResult(
                id="spotlight.github_api",
                name="github_api_access",
                status="warn",
                summary=f"GitHub API reachable but rate limit low ({remaining} remaining).",
                details="",
                fix_hint="Set GITHUB_TOKEN for higher rate limits.",
                category="spotlight",
            )
        return DoctorCheckResult(
            id="spotlight.github_api",
            name="github_api_access",
            status="pass",
            summary="GitHub API reachable.",
            details=f"{remaining} requests remaining.",
            fix_hint="",
            category="spotlight",
        )
    except Exception as exc:
        return DoctorCheckResult(
            id="spotlight.github_api",
            name="github_api_access",
            status="fail",
            summary=f"GitHub API unreachable: {exc}",
            details="",
            fix_hint="Check network connectivity or set GITHUB_TOKEN.",
            category="spotlight",
        )


def check_spotlight_queue() -> DoctorCheckResult:
    """Check spotlight queue health."""
    import json as _json
    queue_path = Path.home() / ".local" / "share" / "agentkit" / "spotlight-queue.json"
    if not queue_path.exists():
        return DoctorCheckResult(
            id="spotlight.queue",
            name="spotlight_queue",
            status="warn",
            summary="Spotlight queue file not found.",
            details="Run `agentkit spotlight-queue seed` to populate.",
            fix_hint="agentkit spotlight-queue seed",
            category="spotlight",
        )
    try:
        data = _json.loads(queue_path.read_text())
    except Exception:
        return DoctorCheckResult(
            id="spotlight.queue",
            name="spotlight_queue",
            status="fail",
            summary="Spotlight queue file is corrupt.",
            details="",
            fix_hint="agentkit spotlight-queue clear && agentkit spotlight-queue seed",
            category="spotlight",
        )
    repos = data.get("repos", [])
    count = len(repos)
    if count == 0:
        return DoctorCheckResult(
            id="spotlight.queue",
            name="spotlight_queue",
            status="warn",
            summary="Spotlight queue is empty.",
            details="Run `agentkit spotlight-queue seed` to add default repos.",
            fix_hint="agentkit spotlight-queue seed",
            category="spotlight",
        )
    if count < 3:
        next_repo = repos[0] if repos else "—"
        return DoctorCheckResult(
            id="spotlight.queue",
            name="spotlight_queue",
            status="warn",
            summary=f"Spotlight queue has only {count} repo(s). Consider adding more.",
            details=f"Next: {next_repo}",
            fix_hint="agentkit spotlight-queue add github:owner/repo",
            category="spotlight",
        )
    # Find next (never spotlighted first)
    last = data.get("lastSpotlighted", {})
    next_repo = next((r for r in repos if r not in last), None)
    if next_repo is None:
        next_repo = min(repos, key=lambda r: last.get(r, "0000-00-00"))
    return DoctorCheckResult(
        id="spotlight.queue",
        name="spotlight_queue",
        status="pass",
        summary=f"Spotlight queue has {count} repos. Next: {next_repo}",
        details="",
        fix_hint="",
        category="spotlight",
    )


def run_doctor(root: Path | None = None) -> DoctorReport:
    """Run the core doctor checks for the given path."""
    project_root = (root or Path.cwd()).resolve()
    repo_state = detect_git_repo(project_root)
    checks: list[DoctorCheckResult] = [
        # D1: repo checks
        check_git_repo(project_root),
        check_git_has_commit(project_root, repo_state=repo_state),
        check_working_tree_clean(project_root, repo_state=repo_state),
        check_readme_present(project_root),
        check_pyproject_present(project_root),
        check_context_files(project_root),
        # D2: toolchain probes
        *check_toolchain(),
        # D3: actionability checks
        check_source_files(project_root),
        check_context_freshness(project_root),
        check_output_dir(project_root),
        check_herenow_api_key(),
    ]
    checks.append(check_serve_available())
    checks.append(check_redteam_recency(project_root))
    checks.append(check_webhook_config(project_root))
    checks.append(check_llmstxt_readiness(project_root))
    checks.append(check_context_sync(project_root))
    checks.append(check_spotlight_github_access())
    checks.append(check_spotlight_queue())
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
