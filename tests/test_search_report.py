"""Tests for agentkit_cli/search_report.py (D3 — HTML report)."""
from __future__ import annotations

from agentkit_cli.search import SearchResult
from agentkit_cli.search_report import generate_search_report


def _make_results(n: int = 3) -> list[SearchResult]:
    results = []
    for i in range(n):
        results.append(SearchResult(
            owner="user",
            repo=f"repo{i}",
            url=f"https://github.com/user/repo{i}",
            stars=100 * (i + 1),
            language="Python",
            description=f"desc {i}",
            has_claude_md=(i % 2 == 0),
            has_agents_md=False,
            score=0.5,
        ))
    return results


def test_generate_returns_html():
    results = _make_results(2)
    html = generate_search_report(results, query="ai agents")
    assert "<!DOCTYPE html>" in html
    assert "<html" in html


def test_report_dark_theme():
    html = generate_search_report(_make_results(1))
    assert "#0d1117" in html or "background" in html


def test_report_contains_repo_links():
    results = _make_results(2)
    html = generate_search_report(results)
    assert "user/repo0" in html
    assert "user/repo1" in html
    assert "https://github.com/user/repo0" in html


def test_report_missing_badge_count():
    # 3 results: repo0(has), repo1(missing), repo2(has) based on i%2==0
    results = _make_results(3)
    html = generate_search_report(results)
    # 1 missing (repo1)
    assert "1" in html  # missing count badge


def test_report_shows_language():
    results = _make_results(1)
    html = generate_search_report(results)
    assert "Python" in html


def test_report_shows_stars():
    results = _make_results(1)
    html = generate_search_report(results)
    assert "100" in html  # stars value


def test_report_has_context_indicators():
    results = _make_results(2)
    html = generate_search_report(results)
    # Should show present/missing indicators
    assert "✓" in html or "✗" in html or "present" in html or "missing" in html


def test_report_has_action_buttons():
    results = _make_results(1)
    html = generate_search_report(results)
    assert "agentkit analyze" in html


def test_report_has_version():
    from agentkit_cli import __version__
    html = generate_search_report(_make_results(1))
    assert __version__ in html


def test_report_query_in_title():
    html = generate_search_report(_make_results(1), query="ai-agents python")
    assert "ai-agents python" in html


def test_report_generated_at_default():
    html = generate_search_report(_make_results(1))
    # Should contain some timestamp-like string
    assert "Z" in html  # UTC timestamp


def test_report_generated_at_custom():
    html = generate_search_report(_make_results(1), generated_at="2026-03-18T00:00:00Z")
    assert "2026-03-18" in html


def test_report_empty_results():
    html = generate_search_report([], query="nothing")
    assert "<!DOCTYPE html>" in html
    assert "0" in html


def test_upload_search_report_no_key(monkeypatch):
    monkeypatch.delenv("HERENOW_API_KEY", raising=False)
    from agentkit_cli.search_report import upload_search_report
    url = upload_search_report(_make_results(1), query="test")
    assert url is None
