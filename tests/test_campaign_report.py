"""Tests for campaign HTML report generation (D4)."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from agentkit_cli.campaign import CampaignResult, PRResult, RepoSpec
from agentkit_cli.campaign_report import generate_campaign_html, upload_campaign_report


def _make_result():
    result = CampaignResult(campaign_id="rep001", target_spec="github:pallets", file="CLAUDE.md")
    result.submitted.append(
        PRResult(
            repo=RepoSpec("pallets", "flask", stars=68000),
            pr_url="https://github.com/pallets/flask/pull/1",
            score_after=82.5,
        )
    )
    result.skipped.append(RepoSpec("pallets", "click", stars=15000))
    result.failed.append((RepoSpec("pallets", "jinja"), "Fork creation failed"))
    return result


# ---------------------------------------------------------------------------
# HTML structure tests
# ---------------------------------------------------------------------------

def test_generate_returns_string():
    result = _make_result()
    html = generate_campaign_html(result)
    assert isinstance(html, str)
    assert len(html) > 100


def test_html_contains_campaign_id():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "rep001" in html


def test_html_contains_target_spec():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "github:pallets" in html


def test_html_dark_theme():
    result = _make_result()
    html = generate_campaign_html(result)
    # Dark background color should be present
    assert "#0d1117" in html


def test_html_contains_pr_url():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "https://github.com/pallets/flask/pull/1" in html


def test_html_contains_totals():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "PRs Opened" in html
    assert "Skipped" in html
    assert "Failed" in html


def test_html_contains_pypi_cta():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "pypi.org/project/agentkit-cli" in html


def test_html_contains_repo_names():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "flask" in html
    assert "click" in html
    assert "jinja" in html


def test_html_contains_score():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "82.5" in html


def test_html_status_indicators():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "PR opened" in html
    assert "Skipped" in html
    assert "Failed" in html


def test_html_empty_result():
    result = CampaignResult(campaign_id="empty", target_spec="github:nobody")
    html = generate_campaign_html(result)
    assert "empty" in html
    assert "PRs Opened" in html


def test_html_stars_formatted():
    result = _make_result()
    html = generate_campaign_html(result)
    # 68000 stars should be formatted with commas or k notation
    assert "68" in html


# ---------------------------------------------------------------------------
# upload_campaign_report tests
# ---------------------------------------------------------------------------

def test_upload_no_api_key(monkeypatch):
    monkeypatch.delenv("HERENOW_API_KEY", raising=False)
    result = _make_result()
    url = upload_campaign_report(result)
    assert url is None


def test_upload_with_api_key_calls_publish(monkeypatch):
    monkeypatch.setenv("HERENOW_API_KEY", "fake-key")
    result = _make_result()

    with patch("agentkit_cli.campaign_report.publish_html", return_value="https://here.now/abc") as mock_pub:
        url = upload_campaign_report(result)

    assert url == "https://here.now/abc"
    mock_pub.assert_called_once()


def test_upload_publish_error_returns_none(monkeypatch):
    monkeypatch.setenv("HERENOW_API_KEY", "fake-key")
    result = _make_result()

    with patch("agentkit_cli.campaign_report.publish_html", side_effect=Exception("network error")):
        url = upload_campaign_report(result)

    assert url is None


def test_html_file_keyword():
    result = _make_result()
    html = generate_campaign_html(result)
    assert "CLAUDE.md" in html
