#!/usr/bin/env python3
"""
run-agentkit-action.py — Run agentlint, agentmd drift, and coderace review.
Aggregates results into /tmp/agentkit-quality-summary.json and sets GitHub
Actions output variables (lint-score, drift-status, review-summary).
Exits 1 if lint score < MIN_LINT_SCORE.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SUMMARY_FILE = Path(os.environ.get("QUALITY_SUMMARY_FILE", "/tmp/agentkit-quality-summary.json"))
MIN_LINT_SCORE = int(os.environ.get("MIN_LINT_SCORE", "70"))
IS_PR = bool(os.environ.get("PR_NUMBER", ""))


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def find_context_file(base: Path = Path(".")) -> Path | None:
    candidates = [
        base / "AGENTS.md",
        base / "CLAUDE.md",
        base / "copilot-instructions.md",
        base / ".github" / "copilot-instructions.md",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def run_agentlint(context_file: Path | None) -> dict:
    if context_file is None:
        return {"score": 0, "status": "skipped", "reason": "no context file found"}

    result = run(["agentlint", "check-context", str(context_file)])
    score = 0
    lines = (result.stdout + result.stderr).splitlines()
    for line in lines:
        # Look for a score line like "Score: 85/100" or "score: 85"
        lower = line.lower()
        if "score:" in lower or "score " in lower:
            import re
            m = re.search(r"(\d{1,3})\s*/\s*100", line)
            if m:
                score = int(m.group(1))
                break
            m = re.search(r"score[:\s]+(\d{1,3})", line, re.IGNORECASE)
            if m:
                score = int(m.group(1))
                break

    return {
        "score": score,
        "status": "ok" if result.returncode == 0 else "error",
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def run_agentmd_drift(context_file: Path | None) -> dict:
    if context_file is None:
        return {"drift_status": "skipped", "reason": "no context file found"}

    result = run(["agentmd", "drift", str(context_file.parent)])
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        return {"drift_status": "error", "stdout": stdout, "stderr": stderr}

    combined = (stdout + " " + stderr).lower()
    # Check "fresh" / "no drift" first to avoid "drift" substring matching
    if "fresh" in combined or "no drift" in combined or "up to date" in combined:
        status = "fresh"
    elif "drifted" in combined or "drift detected" in combined or "stale" in combined:
        status = "drifted"
    else:
        status = "unknown"

    return {"drift_status": status, "stdout": stdout, "stderr": stderr}


def run_coderace() -> dict:
    if not IS_PR:
        return {"status": "skipped", "reason": "not a PR context"}

    result = run(["coderace", "review", "--diff", "HEAD~1..HEAD", "--lanes", "2"])
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if result.returncode != 0:
        # coderace might not be installed or configured — treat as skipped
        if "not found" in stderr.lower() or "no such" in stderr.lower():
            return {"status": "skipped", "reason": "coderace not available"}
        return {"status": "error", "stdout": stdout, "stderr": stderr}

    # Extract a summary line
    summary = "Review complete"
    lines = stdout.splitlines()
    for line in lines:
        if "issue" in line.lower() or "finding" in line.lower() or "problem" in line.lower():
            summary = line.strip()
            break

    return {"status": "ok", "summary": summary, "stdout": stdout, "stderr": stderr}


def set_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback for local testing
        print(f"::set-output name={name}::{value}")


def drift_emoji(status: str) -> str:
    return {"fresh": "✅ Fresh", "drifted": "⚠️ Drifted", "skipped": "⏭️ Skipped",
            "unknown": "❓ Unknown", "error": "❌ Error"}.get(status, status)


def main() -> int:
    context_file = find_context_file()

    lint_result = run_agentlint(context_file)
    drift_result = run_agentmd_drift(context_file)
    coderace_result = run_coderace()

    lint_score = lint_result.get("score", 0)
    drift_status = drift_result.get("drift_status", "skipped")
    review_summary = coderace_result.get("summary", coderace_result.get("status", "skipped"))

    summary = {
        "lint": lint_result,
        "drift": drift_result,
        "coderace": coderace_result,
        "aggregated": {
            "lint_score": lint_score,
            "drift_status": drift_status,
            "review_summary": review_summary,
        },
        "comment_markdown": _build_comment(lint_score, drift_status, coderace_result),
    }

    SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2))
    print(f"Quality summary written to {SUMMARY_FILE}")

    set_output("lint-score", str(lint_score))
    set_output("drift-status", drift_status)
    set_output("review-summary", review_summary)

    if lint_score < MIN_LINT_SCORE:
        print(
            f"❌ Lint score {lint_score} is below minimum {MIN_LINT_SCORE}",
            file=sys.stderr,
        )
        return 1

    print(f"✅ Lint score {lint_score} meets minimum {MIN_LINT_SCORE}")
    return 0


def _build_comment(lint_score: int, drift_status: str, coderace_result: dict) -> str:
    coderace_display = coderace_result.get("summary", coderace_result.get("status", "Skipped"))
    return f"""## 🔬 Agent Quality Report

| Check | Result |
|-------|--------|
| Context Lint Score | {lint_score}/100 |
| Context Drift | {drift_emoji(drift_status)} |
| Code Review | {coderace_display} |

[Details in workflow logs]"""


if __name__ == "__main__":
    sys.exit(main())
