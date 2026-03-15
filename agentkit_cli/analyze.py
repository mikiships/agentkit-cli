"""Core analysis engine for `agentkit analyze`."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from agentkit_cli.tools import is_installed, run_tool, which
from agentkit_cli.composite import CompositeScoreEngine, _compute_grade


@dataclass
class ToolResult:
    tool: str
    status: str          # "pass", "fail", "skipped", "error"
    score: Optional[float]
    finding: str


@dataclass
class AnalyzeResult:
    target: str
    repo_name: str
    composite_score: float
    grade: str
    tools: dict[str, dict]  # tool name -> {score, status, finding}
    generated_context: bool = False
    temp_dir: Optional[str] = None
    report_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        # Remove None fields by convention (keep temp_dir/report_url only if set)
        if d["temp_dir"] is None:
            del d["temp_dir"]
        if d["report_url"] is None:
            del d["report_url"]
        return d


def parse_target(target: str) -> tuple[str, str]:
    """Parse target string into (url_or_path, repo_name).

    Supports:
    - github:owner/repo
    - https://github.com/owner/repo[.git]
    - owner/repo  (bare shorthand, exactly one slash, no spaces)
    - ./local, /abs, ~/home  (local path)
    """
    # Local path indicators
    if target.startswith((".","/" ,"~")):
        p = Path(target).expanduser()
        return (str(p), p.name)

    # github: prefix
    if target.startswith("github:"):
        slug = target[len("github:"):]
        return (f"https://github.com/{slug}.git", slug.rstrip("/").split("/")[-1])

    # Full https URL
    if target.startswith("https://") or target.startswith("http://"):
        name = target.rstrip("/").split("/")[-1].removesuffix(".git")
        url = target if target.endswith(".git") else target + ".git"
        return (url, name)

    # Bare owner/repo shorthand: exactly one slash, no spaces
    if "/" in target and target.count("/") == 1 and " " not in target:
        parts = target.split("/")
        return (f"https://github.com/{target}.git", parts[1])

    raise ValueError(f"Cannot parse target: {target!r}. Use github:owner/repo, https://..., or a local path.")


def _clone(url: str, dest: str, timeout: int = 120) -> None:
    """Clone a git repository. Raises on failure."""
    git = shutil.which("git")
    if not git:
        raise RuntimeError("git is not installed. Install git to analyze remote repositories.")

    for attempt in range(2):
        try:
            result = subprocess.run(
                [git, "clone", "--depth=1", "--quiet", url, dest],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                return
            err = (result.stdout + result.stderr).strip()
            if attempt == 0:
                time.sleep(5)
                continue
            raise RuntimeError(f"git clone failed: {err}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"git clone timed out after {timeout}s")


def _run_pipeline_step(tool: str, args: list[str], cwd: str, timeout: int) -> tuple[str, str]:
    """Run one tool step. Returns (status, output_text)."""
    if not is_installed(tool):
        return ("skipped", f"{tool} not installed")
    try:
        path = which(tool)
        result = subprocess.run(
            [path] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()
        status = "pass" if result.returncode == 0 else "fail"
        return (status, output)
    except subprocess.TimeoutExpired:
        return ("error", "timed out")
    except Exception as e:
        return ("error", str(e))


def _extract_score_from_output(output: str) -> Optional[float]:
    """Try to parse a numeric score from tool output."""
    import re
    # Look for patterns like "score: 82", "Score: 82/100", "82.0"
    for pattern in [
        r"score[:\s]+(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*/\s*100",
        r"^(\d+(?:\.\d+)?)$",
    ]:
        m = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                val = float(m.group(1))
                if 0 <= val <= 100:
                    return val
            except ValueError:
                continue
    return None


def _status_to_score(status: str, output: str) -> Optional[float]:
    """Convert tool status to a numeric score."""
    extracted = _extract_score_from_output(output)
    if extracted is not None:
        return extracted
    if status == "pass":
        return 100.0
    if status == "fail":
        return 0.0
    return None  # skipped/error


def analyze_target(
    target: str,
    keep: bool = False,
    publish: bool = False,
    timeout: int = 120,
    no_generate: bool = False,
) -> AnalyzeResult:
    """Run the full analysis pipeline on a target and return AnalyzeResult."""
    url_or_path, repo_name = parse_target(target)

    is_local = target.startswith((".", "/", "~"))
    temp_dir: Optional[str] = None
    work_dir: str

    if is_local:
        work_dir = url_or_path
    else:
        temp_dir = tempfile.mkdtemp(prefix="agentkit-analyze-")
        work_dir = temp_dir
        try:
            _clone(url_or_path, work_dir, timeout=timeout)
        except RuntimeError as e:
            if temp_dir and not keep:
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    tool_results: dict[str, ToolResult] = {}
    generated_context = False

    try:
        # Check if context file exists
        context_exists = (
            (Path(work_dir) / "CLAUDE.md").exists() or
            (Path(work_dir) / "AGENTS.md").exists()
        )

        # agentmd generate (if no context and not --no-generate)
        if not no_generate and not context_exists:
            status, output = _run_pipeline_step(
                "agentmd", ["generate", work_dir], work_dir, timeout
            )
            if status == "pass":
                generated_context = True
            tool_results["agentmd_generate"] = ToolResult(
                tool="agentmd",
                status=status,
                score=None,
                finding=output[:120] if output else "Context generated",
            )

        # agentmd score
        # If --no-generate and no context file exists, score 0 (repo is not agent-ready)
        if no_generate and not context_exists:
            tool_results["agentmd"] = ToolResult(
                tool="agentmd", status="fail", score=0.0,
                finding="No CLAUDE.md / AGENTS.md found. Run `agentmd generate` to create one."
            )
        else:
            status, output = _run_pipeline_step(
                "agentmd", ["score", work_dir], work_dir, timeout
            )
            score = _status_to_score(status, output)
            finding = output.splitlines()[0][:100] if output else ""
            tool_results["agentmd"] = ToolResult(tool="agentmd", status=status, score=score, finding=finding)

        # agentlint check-context --format json
        status, output = _run_pipeline_step(
            "agentlint", ["check-context", "--format", "json"], work_dir, timeout
        )
        lint_score = _status_to_score(status, output)
        lint_finding = ""
        if output:
            try:
                lint_data = json.loads(output)
                # Try to get a meaningful finding from JSON
                if isinstance(lint_data, dict):
                    lint_finding = lint_data.get("summary", lint_data.get("finding", ""))[:100]
                    raw_score = lint_data.get("score")
                    if raw_score is not None:
                        try:
                            lint_score = float(raw_score)
                        except (TypeError, ValueError):
                            pass
            except json.JSONDecodeError:
                lint_finding = output.splitlines()[0][:100]
        tool_results["agentlint"] = ToolResult(tool="agentlint", status=status, score=lint_score, finding=lint_finding)

        # agentreflect generate
        status, output = _run_pipeline_step(
            "agentreflect", ["generate", "--from-git", "--format", "markdown"], work_dir, timeout
        )
        reflect_score = _status_to_score(status, output)
        reflect_finding = output.splitlines()[0][:100] if output else ""
        tool_results["agentreflect"] = ToolResult(tool="agentreflect", status=status, score=reflect_score, finding=reflect_finding)

    finally:
        if temp_dir and not keep:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir = None

    # Compute composite score (gracefully handle all-None case)
    tool_score_map: dict[str, Optional[float]] = {
        "agentmd": tool_results.get("agentmd", ToolResult("agentmd", "skipped", None, "")).score,
        "agentlint": tool_results.get("agentlint", ToolResult("agentlint", "skipped", None, "")).score,
        "agentreflect": tool_results.get("agentreflect", ToolResult("agentreflect", "skipped", None, "")).score,
    }
    engine = CompositeScoreEngine()
    try:
        comp = engine.compute(tool_score_map)
        composite_score = comp.score
        grade = comp.grade
    except ValueError:
        # No tool scores available (all skipped/error)
        composite_score = 0.0
        grade = _compute_grade(0.0)

    # Build output tools dict
    tools_out: dict[str, dict] = {}
    for key, tr in tool_results.items():
        tools_out[key] = {"tool": tr.tool, "status": tr.status, "score": tr.score, "finding": tr.finding}

    result = AnalyzeResult(
        target=target,
        repo_name=repo_name,
        composite_score=composite_score,
        grade=grade,
        tools=tools_out,
        generated_context=generated_context,
        temp_dir=temp_dir if keep else None,
    )

    # Optional publish
    if publish:
        try:
            from agentkit_cli.publish import publish_html, resolve_html_path, PublishError
            import os
            html_path = resolve_html_path(None)
            api_key = os.environ.get("HERENOW_API_KEY") or None
            pub_result = publish_html(html_path, api_key=api_key)
            result.report_url = pub_result.get("url")
        except Exception:
            pass

    return result
