"""Tests for CertEngine core (D1)."""
from __future__ import annotations

import json
import hashlib
import pytest
from unittest.mock import patch

from agentkit_cli.certify import (
    CertEngine,
    CertResult,
    compute_verdict,
    compute_sha256,
    _extract_composite_score,
    _extract_redteam_score,
    _extract_freshness_score,
    _extract_test_count,
    PASS_THRESHOLDS,
    WARN_THRESHOLDS,
)


# ---------------------------------------------------------------------------
# compute_verdict tests
# ---------------------------------------------------------------------------

def test_verdict_pass_all_above_thresholds():
    assert compute_verdict(80, 70, 70) == "PASS"


def test_verdict_pass_high_scores():
    assert compute_verdict(100, 100, 100) == "PASS"


def test_verdict_pass_boundary():
    assert compute_verdict(80, 70, 70) == "PASS"


def test_verdict_warn_one_below_pass():
    # score below pass but above warn
    assert compute_verdict(65, 70, 70) == "WARN"


def test_verdict_warn_redteam_below_pass():
    assert compute_verdict(80, 55, 70) == "WARN"


def test_verdict_warn_freshness_below_pass():
    assert compute_verdict(80, 70, 55) == "WARN"


def test_verdict_fail_all_below_warn():
    assert compute_verdict(40, 30, 20) == "FAIL"


def test_verdict_fail_score_zero():
    assert compute_verdict(0, 0, 0) == "FAIL"


def test_verdict_fail_boundary():
    # Below all warn thresholds
    assert compute_verdict(59, 49, 49) == "FAIL"


# ---------------------------------------------------------------------------
# compute_sha256 tests
# ---------------------------------------------------------------------------

def test_sha256_is_hex_string():
    data = {"score": 80, "verdict": "PASS"}
    result = compute_sha256(data)
    assert isinstance(result, str)
    assert len(result) == 64
    int(result, 16)  # must be valid hex


def test_sha256_excludes_sha256_field():
    data = {"score": 80, "sha256": "shouldbeignored"}
    result = compute_sha256(data)
    # Same result without the sha256 key
    data2 = {"score": 80}
    result2 = compute_sha256(data2)
    assert result == result2


def test_sha256_excludes_cert_id_field():
    data = {"score": 80, "cert_id": "abc"}
    data2 = {"score": 80}
    assert compute_sha256(data) == compute_sha256(data2)


def test_sha256_deterministic():
    data = {"score": 80, "verdict": "PASS", "timestamp": "2026-01-01T00:00:00+00:00"}
    assert compute_sha256(data) == compute_sha256(data)


# ---------------------------------------------------------------------------
# _extract_* helpers
# ---------------------------------------------------------------------------

def test_extract_composite_score_json():
    out = json.dumps({"score": 85})
    assert _extract_composite_score(out) == 85


def test_extract_composite_score_fallback():
    assert _extract_composite_score("Score: 73") == 73


def test_extract_composite_score_clamps():
    out = json.dumps({"score": 200})
    assert _extract_composite_score(out) == 100


def test_extract_redteam_score_resistance_key():
    out = json.dumps({"resistance_score": 72})
    assert _extract_redteam_score(out) == 72


def test_extract_freshness_score_json():
    out = json.dumps({"freshness_score": 68})
    assert _extract_freshness_score(out) == 68


def test_extract_test_count_json():
    out = json.dumps({"tests_found": 42})
    assert _extract_test_count(out) == 42


def test_extract_test_count_text_pattern():
    assert _extract_test_count("1725 tests found") == 1725


# ---------------------------------------------------------------------------
# CertEngine.certify (mocked)
# ---------------------------------------------------------------------------

def make_runner(score_out, redteam_out, freshness_out, doctor_out):
    """Build a mock runner that returns appropriate output based on cmd."""
    def runner(cmd, cwd):
        cmd_str = " ".join(cmd)
        if "score" in cmd_str:
            return 0, score_out, ""
        if "redteam" in cmd_str:
            return 0, redteam_out, ""
        if "check-context" in cmd_str or "agentlint" in cmd_str:
            return 0, freshness_out, ""
        if "doctor" in cmd_str:
            return 0, doctor_out, ""
        return 1, "", "unknown cmd"
    return runner


def test_certify_pass():
    runner = make_runner(
        json.dumps({"score": 85}),
        json.dumps({"resistance_score": 75}),
        json.dumps({"freshness_score": 80}),
        json.dumps({"tests_found": 100}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    assert isinstance(result, CertResult)
    assert result.verdict == "PASS"
    assert result.score == 85
    assert result.redteam_score == 75
    assert result.freshness_score == 80
    assert result.tests_found == 100


def test_certify_fail():
    runner = make_runner(
        json.dumps({"score": 30}),
        json.dumps({"resistance_score": 20}),
        json.dumps({"freshness_score": 10}),
        json.dumps({"tests_found": 5}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    assert result.verdict == "FAIL"


def test_certify_warn():
    runner = make_runner(
        json.dumps({"score": 65}),
        json.dumps({"resistance_score": 45}),
        json.dumps({"freshness_score": 80}),
        json.dumps({"tests_found": 50}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    assert result.verdict == "WARN"


def test_certify_cert_id_is_8_hex_chars():
    runner = make_runner(
        json.dumps({"score": 85}),
        json.dumps({"resistance_score": 75}),
        json.dumps({"freshness_score": 80}),
        json.dumps({"tests_found": 100}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    assert len(result.cert_id) == 8
    int(result.cert_id, 16)  # valid hex


def test_certify_sha256_matches_cert_id():
    runner = make_runner(
        json.dumps({"score": 85}),
        json.dumps({"resistance_score": 75}),
        json.dumps({"freshness_score": 80}),
        json.dumps({"tests_found": 100}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    assert result.sha256.startswith(result.cert_id)


def test_certify_to_json_round_trips():
    runner = make_runner(
        json.dumps({"score": 85}),
        json.dumps({"resistance_score": 75}),
        json.dumps({"freshness_score": 80}),
        json.dumps({"tests_found": 100}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    data = json.loads(result.to_json())
    assert data["verdict"] == result.verdict
    assert data["cert_id"] == result.cert_id


def test_certify_timestamp_is_utc_iso():
    runner = make_runner(
        json.dumps({"score": 85}),
        json.dumps({"resistance_score": 75}),
        json.dumps({"freshness_score": 80}),
        json.dumps({"tests_found": 100}),
    )
    engine = CertEngine(runner=runner)
    result = engine.certify("/fake/path")
    # Must parse as valid ISO timestamp
    from datetime import datetime
    dt = datetime.fromisoformat(result.timestamp)
    assert dt.tzinfo is not None
