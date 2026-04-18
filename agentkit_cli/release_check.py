"""release_check.py, Python-oriented release-surface verification engine for agentkit-cli."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

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
            "markdown": self.to_markdown(),
        }

    def to_markdown(self) -> str:
        lines = [
            "# agentkit release-check",
            "",
            f"- Verdict: **{self.verdict}**",
            f"- Path: `{self.path}`",
        ]
        if self.package:
            lines.append(f"- Package: `{self.package}`")
        if self.version:
            lines.append(f"- Version: `{self.version}`")
        if self.registry:
            lines.append(f"- Registry: `{self.registry}`")
        lines.extend([
            "",
            "| Surface | Status | Detail | Hint |",
            "|---|---|---|---|",
        ])
        for check in self.checks:
            lines.append(
                f"| {check.name} | {check.status} | {_escape_markdown_cell(check.detail)} | {_escape_markdown_cell(check.hint)} |"
            )
        return "\n".join(lines)

    @property
    def passed(self) -> bool:
        return self.verdict == "SHIPPED"


def _run_git(path: Path, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(path),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _shorten(text: str, limit: int = 200) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>") if value else ""


def _extract_summary(output: str) -> str:
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if stripped and ("passed" in stripped or "failed" in stripped or "error" in stripped):
            return stripped
    return _shorten(output)


def _python_test_support_result(name: str, registry: Registry) -> Optional[CheckResult]:
    if registry != "pypi":
        return CheckResult(
            name=name,
            status="fail",
            detail="Automated test execution is currently implemented only for Python/pytest projects.",
            hint="Run release-check on a Python project, use --skip-tests for a partial check, or add project-specific validation outside release-check.",
        )
    return None


def check_tests(path: Path) -> CheckResult:
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "-q", "--tb=no"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=600,
        )
        passed = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        return CheckResult(
            name="tests",
            status="pass" if passed else "fail",
            detail=_extract_summary(output),
            hint="" if passed else "Run `pytest` and fix failing tests before releasing.",
        )
    except FileNotFoundError:
        return CheckResult("tests", "error", "pytest not found", "Install pytest: pip install pytest")
    except subprocess.TimeoutExpired:
        return CheckResult("tests", "error", "pytest timed out after 600s", "Tests are taking too long. Run manually to diagnose.")
    except Exception as exc:
        return CheckResult("tests", "error", str(exc), "Could not run tests. Check Python environment.")


def check_smoke_tests(path: Path) -> CheckResult:
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
        summary = _extract_summary(output)
        if "no tests ran" in output.lower():
            return CheckResult(
                name="smoke_tests",
                status="skip",
                detail="No smoke tests found (pytest -m smoke matched 0 tests).",
                hint="Add smoke tests with @pytest.mark.smoke marker.",
            )
        return CheckResult(
            name="smoke_tests",
            status="pass" if passed else "fail",
            detail=f"Smoke tests: {summary}" if summary else _shorten(output),
            hint="" if passed else "Run `pytest -m smoke` to see failures.",
        )
    except FileNotFoundError:
        return CheckResult("smoke_tests", "error", "pytest not found", "Install pytest: pip install pytest")
    except subprocess.TimeoutExpired:
        return CheckResult("smoke_tests", "error", "Smoke tests timed out after 120s", "Check for hanging tests.")
    except Exception as exc:
        return CheckResult("smoke_tests", "error", str(exc))


def _git_current_branch(path: Path) -> tuple[Optional[str], Optional[CheckResult]]:
    try:
        branch = _run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"])
    except subprocess.TimeoutExpired:
        return None, CheckResult("git_push", "error", "git branch lookup timed out", "Retry when git is responsive.")
    except Exception as exc:
        return None, CheckResult("git_push", "error", str(exc), "Check git availability.")

    if branch.returncode != 0:
        return None, CheckResult("git_push", "error", "git rev-parse failed, is this a git repo?", "Run inside a git repository.")

    name = branch.stdout.strip()
    if name == "HEAD":
        return None, CheckResult(
            "git_push",
            "fail",
            "Detached HEAD, release-check needs a tracked branch.",
            "Check out the release branch and set an upstream, then retry.",
        )
    return name, None


def _git_dirty(path: Path) -> tuple[bool, Optional[CheckResult]]:
    try:
        dirty = _run_git(path, ["status", "--porcelain"])
    except subprocess.TimeoutExpired:
        return False, CheckResult("git_push", "error", "git status timed out", "Retry when git is responsive.")
    except Exception as exc:
        return False, CheckResult("git_push", "error", str(exc), "Check git availability.")

    if dirty.returncode != 0:
        return False, CheckResult("git_push", "error", "git status failed", "Run inside a git repository.")
    lines = [line for line in dirty.stdout.splitlines() if line.strip()]
    return bool(lines), None


def check_git_push(path: Path) -> CheckResult:
    try:
        head = _run_git(path, ["rev-parse", "HEAD"])
        if head.returncode != 0:
            return CheckResult("git_push", "error", "git rev-parse HEAD failed, is this a git repo?", "Run inside a git repository.")
        head_sha = head.stdout.strip()

        branch, branch_error = _git_current_branch(path)
        if branch_error:
            return branch_error

        is_dirty, dirty_error = _git_dirty(path)
        if dirty_error:
            return dirty_error
        if is_dirty:
            return CheckResult(
                "git_push",
                "fail",
                f"Working tree is dirty on branch {branch}.",
                "Commit or stash changes before releasing.",
            )

        upstream = _run_git(path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"])
        if upstream.returncode != 0:
            return CheckResult(
                "git_push",
                "fail",
                f"Branch {branch} has no upstream tracking branch.",
                f"Run `git push --set-upstream origin {branch}` before releasing.",
            )
        upstream_ref = upstream.stdout.strip()

        upstream_sha = _run_git(path, ["rev-parse", upstream_ref])
        if upstream_sha.returncode != 0:
            return CheckResult(
                "git_push",
                "fail",
                f"Tracked upstream {upstream_ref} is not available locally.",
                "Run `git fetch --prune` and retry the release check.",
            )
        upstream_head = upstream_sha.stdout.strip()

        delta = _run_git(path, ["rev-list", "--left-right", "--count", f"{upstream_ref}...HEAD"])
        if delta.returncode != 0:
            return CheckResult(
                "git_push",
                "error",
                f"Could not compare HEAD against {upstream_ref}.",
                "Run `git fetch --prune` and retry.",
            )
        behind_str, ahead_str = (delta.stdout.strip() or "0\t0").split()[:2]
        behind, ahead = int(behind_str), int(ahead_str)

        if ahead == 0 and behind == 0:
            return CheckResult(
                "git_push",
                "pass",
                detail=f"Branch {branch} is clean and synced with {upstream_ref} at {head_sha[:8]}.",
            )
        if ahead > 0 and behind == 0:
            return CheckResult(
                "git_push",
                "fail",
                detail=f"Branch {branch} is ahead of {upstream_ref} by {ahead} commit(s) ({head_sha[:8]} vs {upstream_head[:8]}).",
                hint=f"Run `git push origin {branch}` before releasing.",
            )
        if behind > 0 and ahead == 0:
            return CheckResult(
                "git_push",
                "fail",
                detail=f"Branch {branch} is behind {upstream_ref} by {behind} commit(s).",
                hint=f"Pull or rebase from {upstream_ref} before releasing.",
            )
        return CheckResult(
            "git_push",
            "fail",
            detail=f"Branch {branch} has diverged from {upstream_ref} (ahead {ahead}, behind {behind}).",
            hint=f"Reconcile local {branch} with {upstream_ref}, then rerun release-check.",
        )
    except subprocess.TimeoutExpired:
        return CheckResult("git_push", "error", "git comparison timed out", "Check git responsiveness and retry.")
    except Exception as exc:
        return CheckResult("git_push", "error", str(exc))


def _parse_remote_tag_sha(output: str, tag: str) -> Optional[str]:
    target_ref = f"refs/tags/{tag}"
    peeled_ref = f"{target_ref}^{{}}"
    fallback_sha: Optional[str] = None

    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        sha, ref = parts[0], parts[1]
        if ref == peeled_ref:
            return sha
        if ref == target_ref:
            fallback_sha = sha

    return fallback_sha


def check_git_tag(path: Path, version: str) -> CheckResult:
    tag = f"v{version}"
    try:
        head = _run_git(path, ["rev-parse", "HEAD"])
        if head.returncode != 0:
            return CheckResult("git_tag", "error", "git rev-parse HEAD failed", "Run inside a git repository.")
        head_sha = head.stdout.strip()

        local_tag = _run_git(path, ["rev-parse", f"{tag}^{{}}"])
        if local_tag.returncode != 0:
            return CheckResult(
                "git_tag",
                "fail",
                f"Local tag {tag} does not exist.",
                f"Create it with `git tag {tag}` after confirming version {version} is release-ready.",
            )
        local_sha = local_tag.stdout.strip()
        if local_sha != head_sha:
            return CheckResult(
                "git_tag",
                "fail",
                f"Local tag {tag} points to {local_sha[:8]}, but HEAD is {head_sha[:8]}.",
                f"Move or recreate {tag} so it points at HEAD before releasing.",
            )

        remote_tag = _run_git(path, ["ls-remote", "--tags", "origin", tag])
        if remote_tag.returncode != 0:
            return CheckResult(
                "git_tag",
                "error",
                "git ls-remote --tags failed",
                "Check remote origin configuration and connectivity.",
            )
        if not remote_tag.stdout.strip():
            return CheckResult(
                "git_tag",
                "fail",
                f"Local tag {tag} points at HEAD, but remote origin is missing the tag.",
                f"Run `git push origin {tag}` before releasing.",
            )

        remote_sha = _parse_remote_tag_sha(remote_tag.stdout, tag)
        if not remote_sha:
            return CheckResult(
                "git_tag",
                "fail",
                f"Remote origin returned no usable ref for tag {tag}.",
                f"Run `git ls-remote --tags origin {tag}` and verify the remote tag before releasing.",
            )
        if remote_sha != head_sha:
            return CheckResult(
                "git_tag",
                "fail",
                f"Remote tag {tag} points to {remote_sha[:8]}, but HEAD is {head_sha[:8]}.",
                f"Update the remote tag {tag} so it matches HEAD before releasing.",
            )

        return CheckResult("git_tag", "pass", f"Tag {tag} exists locally and on origin, both pointing at {head_sha[:8]}.")
    except subprocess.TimeoutExpired:
        return CheckResult("git_tag", "error", "git tag lookup timed out", "Check git responsiveness and retry.")
    except Exception as exc:
        return CheckResult("git_tag", "error", str(exc))


def check_registry_pypi(package: str, version: str) -> CheckResult:
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agentkit-release-check/0.96.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read())
                released = data.get("info", {}).get("version", "")
                if released != version:
                    return CheckResult(
                        "registry",
                        "fail",
                        f"PyPI returned version {released} for {package}, expected {version}.",
                        "Publish the expected version or fix local version metadata.",
                    )
                return CheckResult("registry", "pass", f"PyPI: {package}=={released} is live.")
            return CheckResult("registry", "fail", f"PyPI returned HTTP {resp.status}", "Publish with: python -m build && twine upload dist/*")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return CheckResult("registry", "fail", f"PyPI: {package}=={version} not found (404).", "Publish with: python -m build && twine upload dist/*")
        return CheckResult("registry", "error", f"PyPI HTTP error: {exc.code}")
    except Exception as exc:
        return CheckResult("registry", "error", f"PyPI check failed: {exc}", "Check network connectivity.")


def check_registry_npm(package: str, version: str) -> CheckResult:
    url = f"https://registry.npmjs.org/{package}/{version}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "agentkit-release-check/0.96.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                body = json.loads(resp.read() or b"{}")
                returned_version = body.get("version", version)
                if returned_version != version:
                    return CheckResult(
                        "registry",
                        "fail",
                        f"npm returned version {returned_version} for {package}, expected {version}.",
                        "Publish the expected version or fix local version metadata.",
                    )
                return CheckResult("registry", "pass", f"npm: {package}@{version} is live.")
            return CheckResult("registry", "fail", f"npm returned HTTP {resp.status}", "Publish with: npm publish")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return CheckResult("registry", "fail", f"npm: {package}@{version} not found (404).", "Publish with: npm publish")
        return CheckResult("registry", "error", f"npm HTTP error: {exc.code}")
    except Exception as exc:
        return CheckResult("registry", "error", f"npm check failed: {exc}", "Check network connectivity.")


def _detect_registry(path: Path) -> Registry:
    if (path / "pyproject.toml").exists() or (path / "setup.py").exists() or (path / "setup.cfg").exists():
        return "pypi"
    if (path / "package.json").exists():
        return "npm"
    return "pypi"


def _read_pyproject(path: Path) -> tuple[str, str]:
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return _parse_pyproject_manual(path)

    pyproject = path / "pyproject.toml"
    if not pyproject.exists():
        return "", ""
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    return project.get("name", ""), project.get("version", "")


def _parse_pyproject_manual(path: Path) -> tuple[str, str]:
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
    pkg = path / "package.json"
    if not pkg.exists():
        return "", ""
    try:
        data = json.loads(pkg.read_text())
        return data.get("name", ""), data.get("version", "")
    except Exception:
        return "", ""


def resolve_metadata(path: Path, package: Optional[str], version: Optional[str], registry: Registry) -> tuple[str, str, Registry]:
    if registry == "auto":
        registry = _detect_registry(path)
    if not package or not version:
        detected_name, detected_version = _read_package_json(path) if registry == "npm" else _read_pyproject(path)
        package = package or detected_name
        version = version or detected_version
    return package or "", version or "", registry


def write_step_summary(result: ReleaseCheckResult, summary_path: Optional[Path] = None) -> Optional[Path]:
    destination = summary_path or (Path(os.environ["GITHUB_STEP_SUMMARY"]) if os.environ.get("GITHUB_STEP_SUMMARY") else None)
    if destination is None:
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(result.to_markdown() + "\n", encoding="utf-8")
    return destination


def run_release_check(
    path: Optional[Path] = None,
    package: Optional[str] = None,
    version: Optional[str] = None,
    registry: Registry = "auto",
    skip_tests: bool = False,
) -> ReleaseCheckResult:
    root = path or Path.cwd()
    pkg, ver, reg = resolve_metadata(root, package, version, registry)
    result = ReleaseCheckResult(package=pkg, version=ver, registry=reg, path=str(root))

    if skip_tests:
        result.checks.append(CheckResult("smoke_tests", "skip", "Skipped via --skip-tests."))
        result.checks.append(CheckResult("tests", "skip", "Skipped via --skip-tests."))
    else:
        smoke_support = _python_test_support_result("smoke_tests", reg)
        tests_support = _python_test_support_result("tests", reg)
        result.checks.append(smoke_support or check_smoke_tests(root))
        result.checks.append(tests_support or check_tests(root))

    result.checks.append(check_git_push(root))

    if ver:
        result.checks.append(check_git_tag(root, ver))
    else:
        result.checks.append(CheckResult(
            "git_tag",
            "fail",
            "Version metadata is missing, cannot verify release tag.",
            "Provide --version or add version metadata to pyproject.toml/package.json.",
        ))

    if pkg and ver:
        result.checks.append(check_registry_npm(pkg, ver) if reg == "npm" else check_registry_pypi(pkg, ver))
    else:
        result.checks.append(CheckResult(
            "registry",
            "fail",
            "Package name or version metadata is missing, cannot verify registry state.",
            "Provide --package/--version or add package metadata to project files.",
        ))

    statuses = {c.name: c.status for c in result.checks}
    tests_ok = statuses.get("tests") in ("pass", "skip")
    smoke_ok = statuses.get("smoke_tests") in ("pass", "skip")
    push_ok = statuses.get("git_push") == "pass"
    tag_ok = statuses.get("git_tag") == "pass"
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
