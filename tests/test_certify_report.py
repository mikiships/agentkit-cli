"""Tests for dark-theme HTML cert report (D3)."""
from __future__ import annotations

from agentkit_cli.certify import CertResult, compute_sha256
from agentkit_cli.certify_report import render_html_cert, _score_bar, VERDICT_COLOR


def _make_result(verdict="PASS", score=85, redteam=75, freshness=80, tests=100):
    ts = "2026-01-01T00:00:00+00:00"
    payload = dict(timestamp=ts, score=score, redteam_score=redteam,
                   freshness_score=freshness, tests_found=tests, verdict=verdict)
    sha = compute_sha256(payload)
    return CertResult(timestamp=ts, score=score, redteam_score=redteam,
                      freshness_score=freshness, tests_found=tests, verdict=verdict,
                      sha256=sha, cert_id=sha[:8])


def test_html_contains_doctype():
    result = _make_result()
    html = render_html_cert(result)
    assert "<!DOCTYPE html>" in html


def test_html_contains_cert_id():
    result = _make_result()
    html = render_html_cert(result)
    assert result.cert_id in html


def test_html_contains_verdict():
    result = _make_result("WARN")
    html = render_html_cert(result, project_name="myrepo")
    assert "WARN" in html


def test_html_contains_project_name():
    result = _make_result()
    html = render_html_cert(result, project_name="agentkit-cli")
    assert "agentkit-cli" in html


def test_html_contains_sha256():
    result = _make_result()
    html = render_html_cert(result)
    assert result.sha256 in html


def test_html_dark_background():
    result = _make_result()
    html = render_html_cert(result)
    assert "#0d1117" in html


def test_html_pass_accent_color():
    result = _make_result("PASS")
    html = render_html_cert(result)
    assert VERDICT_COLOR["PASS"] in html


def test_html_fail_accent_color():
    result = _make_result("FAIL", score=20, redteam=10, freshness=10)
    html = render_html_cert(result)
    assert VERDICT_COLOR["FAIL"] in html


def test_html_score_bar_zero():
    bar = _score_bar(0)
    assert 'width:0%' in bar


def test_html_score_bar_hundred():
    bar = _score_bar(100)
    assert 'width:100%' in bar


def test_html_contains_timestamp():
    result = _make_result()
    html = render_html_cert(result)
    assert result.timestamp in html


def test_html_contains_all_sub_scores():
    result = _make_result(score=85, redteam=75, freshness=80, tests=100)
    html = render_html_cert(result)
    assert "85" in html
    assert "75" in html
    assert "80" in html
    assert "100" in html
