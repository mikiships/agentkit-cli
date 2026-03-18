"""agentkit certify — CertEngine core + cert schema."""
from __future__ import annotations

import hashlib
import json
import subprocess
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Verdict thresholds
# ---------------------------------------------------------------------------

PASS_THRESHOLDS = {"score": 80, "redteam": 70, "freshness": 70}
WARN_THRESHOLDS = {"score": 60, "redteam": 50, "freshness": 50}


def compute_verdict(score: int, redteam_score: int, freshness_score: int) -> str:
    """Compute PASS/WARN/FAIL verdict from sub-scores."""
    if (
        score >= PASS_THRESHOLDS["score"]
        and redteam_score >= PASS_THRESHOLDS["redteam"]
        and freshness_score >= PASS_THRESHOLDS["freshness"]
    ):
        return "PASS"
    if (
        score >= WARN_THRESHOLDS["score"]
        or redteam_score >= WARN_THRESHOLDS["redteam"]
        or freshness_score >= WARN_THRESHOLDS["freshness"]
    ):
        return "WARN"
    return "FAIL"


# ---------------------------------------------------------------------------
# CertResult dataclass
# ---------------------------------------------------------------------------

@dataclass
class CertResult:
    timestamp: str       # UTC ISO 8601
    score: int           # composite score (agentkit score)
    redteam_score: int   # redteam resistance score
    freshness_score: int # context freshness score
    tests_found: int     # test count from agentkit doctor
    verdict: str         # PASS / WARN / FAIL
    sha256: str          # SHA256 of canonical JSON content
    cert_id: str         # 8-char hex prefix of sha256

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# SHA256 helpers
# ---------------------------------------------------------------------------

def _canonical_json(data: dict) -> str:
    """Produce deterministic JSON (sorted keys, no extra whitespace)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_sha256(data: dict) -> str:
    """Compute SHA256 of the canonical JSON representation of data (excluding sha256/cert_id fields)."""
    payload = {k: v for k, v in data.items() if k not in ("sha256", "cert_id")}
    canonical = _canonical_json(payload)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Subprocess runners (overridable for testing)
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: str) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode, result.stdout, result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return 1, "", str(exc)


def _extract_composite_score(stdout: str) -> int:
    """Extract composite score from `agentkit score` JSON output."""
    try:
        data = json.loads(stdout)
        if isinstance(data, dict):
            for key in ("score", "composite_score", "total_score"):
                v = data.get(key)
                if v is not None:
                    return max(0, min(100, int(round(float(v)))))
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    # Fallback: look for a number in text
    m = re.search(r"\b(\d{1,3})\b", stdout)
    if m:
        return max(0, min(100, int(m.group(1))))
    return 0


def _extract_redteam_score(stdout: str) -> int:
    """Extract redteam resistance score from `agentkit redteam` JSON output."""
    try:
        data = json.loads(stdout)
        if isinstance(data, dict):
            for key in ("resistance_score", "score", "redteam_score", "total_score"):
                v = data.get(key)
                if v is not None:
                    return max(0, min(100, int(round(float(v)))))
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    m = re.search(r"\b(\d{1,3})\b", stdout)
    if m:
        return max(0, min(100, int(m.group(1))))
    return 0


def _extract_freshness_score(stdout: str) -> int:
    """Extract freshness score from `agentlint check-context` JSON output."""
    try:
        data = json.loads(stdout)
        if isinstance(data, dict):
            for key in ("score", "freshness_score", "total_score"):
                v = data.get(key)
                if v is not None:
                    return max(0, min(100, int(round(float(v)))))
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    m = re.search(r"\b(\d{1,3})\b", stdout)
    if m:
        return max(0, min(100, int(m.group(1))))
    return 0


def _extract_test_count(stdout: str) -> int:
    """Extract test count from `agentkit doctor` output."""
    try:
        data = json.loads(stdout)
        if isinstance(data, dict):
            for key in ("tests_found", "test_count", "tests"):
                v = data.get(key)
                if v is not None:
                    return max(0, int(v))
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    # Look for "N tests" or "tests: N" patterns
    for pattern in (
        r"(\d+)\s+tests?\s+found",
        r"tests?\s*[:\s]+(\d+)",
        r"(\d+)\s+passed",
    ):
        m = re.search(pattern, stdout, re.IGNORECASE)
        if m:
            return max(0, int(m.group(1)))
    return 0


# ---------------------------------------------------------------------------
# CertEngine
# ---------------------------------------------------------------------------

class CertEngine:
    """Runs 4 checks and produces a CertResult."""

    def __init__(self, runner=None):
        """
        Parameters
        ----------
        runner : callable, optional
            Signature: (cmd: list[str], cwd: str) -> (returncode, stdout, stderr)
            Defaults to the real subprocess runner.
        """
        self._run = runner or _run

    def run_composite_score(self, path: str) -> int:
        """Run `agentkit score --json` and return integer score 0-100."""
        _, stdout, _ = self._run(["agentkit", "score", "--json"], path)
        return _extract_composite_score(stdout)

    def run_redteam_score(self, path: str) -> int:
        """Run `agentkit redteam --json` and return integer score 0-100."""
        _, stdout, _ = self._run(["agentkit", "redteam", "--json"], path)
        return _extract_redteam_score(stdout)

    def run_freshness_score(self, path: str) -> int:
        """Run `agentlint check-context --json` and return integer score 0-100."""
        _, stdout, _ = self._run(["agentlint", "check-context", "--json", path], path)
        return _extract_freshness_score(stdout)

    def run_test_count(self, path: str) -> int:
        """Run `agentkit doctor --json` and extract test count."""
        _, stdout, _ = self._run(["agentkit", "doctor", "--json"], path)
        return _extract_test_count(stdout)

    def certify(self, path: str) -> CertResult:
        """Run all 4 checks and produce a signed CertResult."""
        score = self.run_composite_score(path)
        redteam_score = self.run_redteam_score(path)
        freshness_score = self.run_freshness_score(path)
        tests_found = self.run_test_count(path)
        verdict = compute_verdict(score, redteam_score, freshness_score)
        timestamp = datetime.now(tz=timezone.utc).isoformat()

        # Build payload for hashing (without sha256/cert_id)
        payload = {
            "timestamp": timestamp,
            "score": score,
            "redteam_score": redteam_score,
            "freshness_score": freshness_score,
            "tests_found": tests_found,
            "verdict": verdict,
        }
        sha256 = compute_sha256(payload)
        cert_id = sha256[:8]

        return CertResult(
            timestamp=timestamp,
            score=score,
            redteam_score=redteam_score,
            freshness_score=freshness_score,
            tests_found=tests_found,
            verdict=verdict,
            sha256=sha256,
            cert_id=cert_id,
        )
