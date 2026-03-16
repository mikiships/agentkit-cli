"""release_check.py — 4-surface release verification engine for agentkit-cli."""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

Status = Literal["pass", "fail", "skip", "error"]
Verdict = Literal["SHIPPED", "RELEASE-READY", "BUILT", "UNKNOWN"]
Registry = Literal["pypi", "npm", "auto"]


@dataclass
class CheckResult:
    name: str
    status: Status
    detail: str = ""
    hint: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "hint": self.hint,
        }


@dataclass
class ReleaseCheckResult:
    checks: list[CheckResult] = field(default_factory=list)
    verdict: Verdict = "UNKNOWN"
    package: str = ""
    version: str = ""
    registry: str = ""
    path: str = ""

    def as_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "package": self.package,
            "version": self.version,
            "registry": self.registry,
            "path": self.path,
            "checks": [c.as_dict() for c in self.checks],
        }

    @property
    def passed(self) -> bool:
        return self.verdict == "SHIPPED"


# ---------------------------------------------------------------------------
# Individual check implementations
# ---------------------------------------------------------------------------

def check_tests(path: Path) -> CheckResult:
    """Run pytest -q --tb=no and return pass/fail."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "-q", "--tb=no"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=300,
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        # Extract summary line (e.g. "42 passed in 1.23s")
        summary = ""
        for line in reversed(output.splitlines()):
            line = line.strip()
            if line and ("passed" in line or "failed" in line or "error" in line):
                summary = line
                break
        return CheckResult(
            name="tests",
            status="pass" if passed else "fail",
            detail=summary or output[:200],
            hint="" if passed else "Run `pytest` and fix failing tests before releasing.",
        )
    except FileNotFoundError:
        return CheckResult(
            name="tests",
            status="error",
            detail="pytest not found",
            hint="Install pytest: pip install pytest",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="tests",
            status="error",
            detail="pytest timed out after 300s",
            hint="Tests are taking too long. Run manually to diagnose.",
        )
    except Exception as exc:
        return CheckResult(
            name="tests",
            status="error",
            detail=str(exc),
            hint="Could not run tests. Check Python environment.",
        )


def check_git_push(path: Path) -> CheckResult:
    """Compare local HEAD with remote origin HEAD."""
    try:
        # Get local HEAD
        local = subprocess.run(
            ["git", "log", "--oneline", "-1", "--format=%H"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if local.returncode != 0:
            return CheckResult(
                name="git_push",
                status="error",
                detail="git log failed — is this a git repo?",
                hint="Run `git init` and commit your changes.",
            )
        local_hash = local.stdout.strip()

        # Get remote HEAD
        remote = subprocess.run(
            ["git", "ls-remote", "origin", "HEAD"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if remote.returncode != 0 or not remote.stdout.strip():
            return CheckResult(
                name="git_push",
                status="fail",
                detail="Could not reach remote origin or no remote configured.",
                hint="Add a remote: `git remote add origin <url>` then push.",
            )
        remote_hash = remote.stdout.strip().split()[0]

        if local_hash == remote_hash:
            return CheckResult(
                name="git_push",
                status="pass",
                detail=f"Local HEAD {local_hash[:8]} matches remote.",
            )
        else:
            return CheckResult(
                name="git_push",
                status="fail",
                detail=f"Local HEAD {local_hash[:8]} != remote HEAD {remote_hash[:8]}.",
                hint="Run `git push origin <branch>` to sync.",
            )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="git_push",
            status="error",
            detail="git ls-remote timed out",
            hint="Check network connectivity to the git remote.",
        )
    except Exception as exc:
        return CheckResult(
            name="git_push",
            status="error",
            detail=str(exc),
        )


def check_git_tag(path: Path, version: str) -> CheckResult:
    """Check if vX.Y.Z tag exists on the remote."""
    tag = f"v{version}"
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--tags", "origin", tag],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return CheckResult(
                name="git_tag",
                status="error",
                detail="git ls-remote --tags failed",
                hint="Check git remote configuration.",
            )
        if tag in result.stdout:
            return CheckResult(
                name="git_tag",
                status="pass",
                detail=f"Tag {tag} found on remote.",
            )
        else:
            return CheckResult(
                name="git_tag",
                status="fail",
                detail=f"Tag {tag} not found on remote.",
                hint=f"Run: git tag {tag} && git push --tags",
            )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="git_tag",
            status="error",
            detail="git ls-remote timed out",
            hint="Check network connectivity.",
        )
    except Exception as exc:
        return CheckResult(
            name="git_tag",
            status="error",
            detail=str(exc),
        )


def check_smoke_tests(path: Path) -> CheckResult:
    """Run smoke test suite (pytest -m smoke) and return pass/fail."""
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "-m", "smoke", "-q", "--tb=no"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        # Extract summary line
        summary = ""
        for line in reversed(output.splitlines()):
            line = line.strip()
            if line and ("passed" in line or "failed" in line or "error" in line):
                summary = line
                break
        if not summary and "no tests ran" in output.lower():
            return CheckResult(
                name="smoke_tests",
                status="skip",
                detail="No smoke tests found (pytest -m smoke matched 0 tests).",
                hint="Add smoke tests with @pytest.mark.smoke marker.",
            )
        return CheckResult(
            name="smoke_tests",
            status="pass" if passed else "fail",
            detail=f"Smoke tests: {summary}" if summary else output[:200],
            hint="" if passed else "Run `pytest -m smoke` to see failures.",
        )
    except FileNotFoundError:
        return CheckResult(
            name="smoke_tests",
            status="error",
            detail="pytest not found",
            hint="Install pytest: pip install pytest",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name="smoke_tests",
            status="error",
            detail="Smoke tests timed out after 120s",
            hint="Check for hanging tests.",
        )
    except Exception as exc:
        return CheckResult(
            name="smoke_tests",
            status="error",
            detail=str(exc),
        )


def check_registry_pypi(package: str, version: str) -> CheckResult:
    """Check if package@version is live on PyPI."""
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agentkit-release-check/0.27.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read())
                released = data.get("info", {}).get("version", "")
                return CheckResult(
                    name="registry",
                    status="pass",
                    detail=f"PyPI: {package}=={released} is live.",
                )
            else:
                return CheckResult(
                    name="registry",
                    status="fail",
                    detail=f"PyPI returned HTTP {resp.status}",
                    hint=f"Publish with: python -m build && twine upload dist/*",
                )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return CheckResult(
                name="registry",
                status="fail",
                detail=f"PyPI: {package}=={version} not found (404).",
                hint="Publish with: python -m build && twine upload dist/*",
            )
        return CheckResult(
            name="registry",
            status="error",
            detail=f"PyPI HTTP error: {exc.code}",
        )
    except Exception as exc:
        return CheckResult(
            name="registry",
            status="error",
            detail=f"PyPI check failed: {exc}",
            hint="Check network connectivity.",
        )


def check_registry_npm(package: str, version: str) -> CheckResult:
    """Check if package@version is live on npm registry."""
    url = f"https://registry.npmjs.org/{package}/{version}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agentkit-release-check/0.27.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return CheckResult(
                    name="registry",
                    status="pass",
                    detail=f"npm: {package}@{version} is live.",
                )
            else:
                return CheckResult(
                    name="registry",
                    status="fail",
                    detail=f"npm returned HTTP {resp.status}",
                    hint=f"Publish with: npm publish",
                )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return CheckResult(
                name="registry",
                status="fail",
                detail=f"npm: {package}@{version} not found (404).",
                hint="Publish with: npm publish",
            )
        return CheckResult(
            name="registry",
            status="error",
            detail=f"npm HTTP error: {exc.code}",
        )
    except Exception as exc:
        return CheckResult(
            name="registry",
            status="error",
            detail=f"npm check failed: {exc}",
            hint="Check network connectivity.",
        )


# ---------------------------------------------------------------------------
# Project metadata detection
# ---------------------------------------------------------------------------

def _detect_registry(path: Path) -> Registry:
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists() or (path / "setup.cfg").exists():
        return "pypi"
    if (path / "package.json").exists():
        return "npm"
    return "pypi"  # default


def _read_pyproject(path: Path) -> tuple[str, str]:
    """Return (name, version) from pyproject.toml."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            # Manual parse fallback
            return _parse_pyproject_manual(path)

    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return "", ""
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    return project.get("name", ""), project.get("version", "")


def _parse_pyproject_manual(path: Path) -> tuple[str, str]:
    """Minimal fallback parser for pyproject.toml."""
    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return "", ""
    name, version = "", ""
    in_project = False
    for line in pyproject.read_text().splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project = True
            continue
        if in_project and stripped.startswith("[") and stripped != "[project]":
            in_project = False
        if in_project:
            if stripped.startswith("name"):
                name = stripped.split("=", 1)[1].strip().strip('"').strip("'")
            elif stripped.startswith("version"):
                version = stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return name, version


def _read_package_json(path: Path) -> tuple[str, str]:
    """Return (name, version) from package.json."""
    pkg = path / "package.json"
    if not pkg.exists():
        return "", ""
    try:
        data = json.loads(pkg.read_text())
        return data.get("name", ""), data.get("version", "")
    except Exception:
        return "", ""


def resolve_metadata(
    path: Path,
    package: Optional[str],
    version: Optional[str],
    registry: Registry,
) -> tuple[str, str, Registry]:
    """Resolve package name, version, and registry from project files if not provided."""
    if registry == "auto":
        registry = _detect_registry(path)

    if not package or not version:
        if registry == "npm":
            detected_name, detected_version = _read_package_json(path)
        else:
            detected_name, detected_version = _read_pyproject(path)
        package = package or detected_name
        version = version or detected_version

    return package or "", version or "", registry


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

def run_release_check(
    path: Optional[Path] = None,
    package: Optional[str] = None,
    version: Optional[str] = None,
    registry: Registry = "auto",
    skip_tests: bool = False,
) -> ReleaseCheckResult:
    """Run all 4 release surface checks and return a structured result."""
    root = path or Path.cwd()
    pkg, ver, reg = resolve_metadata(root, package, version, registry)

    result = ReleaseCheckResult(
        package=pkg,
        version=ver,
        registry=reg,
        path=str(root),
    )

    # Check 0: Smoke tests (lightweight, run first)
    result.checks.append(check_smoke_tests(root))

    # Check 1: Tests
    if skip_tests:
        result.checks.append(CheckResult(
            name="tests",
            status="skip",
            detail="Skipped via --skip-tests.",
        ))
    else:
        result.checks.append(check_tests(root))

    # Check 2: Git push
    result.checks.append(check_git_push(root))

    # Check 3: Git tag
    if ver:
        result.checks.append(check_git_tag(root, ver))
    else:
        result.checks.append(CheckResult(
            name="git_tag",
            status="skip",
            detail="Version unknown — cannot check tag.",
            hint="Provide --version or ensure pyproject.toml/package.json has version set.",
        ))

    # Check 4: Registry
    if pkg and ver:
        if reg == "npm":
            result.checks.append(check_registry_npm(pkg, ver))
        else:
            result.checks.append(check_registry_pypi(pkg, ver))
    else:
        result.checks.append(CheckResult(
            name="registry",
            status="skip",
            detail="Package name or version unknown — cannot check registry.",
            hint="Provide --package and --version, or ensure pyproject.toml/package.json is present.",
        ))

    # Compute verdict
    statuses = {c.name: c.status for c in result.checks}
    tests_ok = statuses.get("tests") in ("pass", "skip")
    smoke_ok = statuses.get("smoke_tests") in ("pass", "skip")
    push_ok = statuses.get("git_push") == "pass"
    tag_ok = statuses.get("git_tag") in ("pass", "skip")
    registry_ok = statuses.get("registry") == "pass"

    if tests_ok and smoke_ok and push_ok and tag_ok and registry_ok:
        result.verdict = "SHIPPED"
    elif tests_ok and smoke_ok and push_ok and tag_ok:
        result.verdict = "RELEASE-READY"
    elif tests_ok and smoke_ok:
        result.verdict = "BUILT"
    else:
        result.verdict = "UNKNOWN"

    return result
