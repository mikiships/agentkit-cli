"""Tests for agentkit leaderboard-page D3 — SEO in generated HTML."""
from __future__ import annotations

import json
import re

import pytest

from agentkit_cli.leaderboard_page import (
    LeaderboardPageEngine,
    render_leaderboard_html,
)


def _fake_repos(n=3):
    return [
        {"full_name": f"owner/repo{i+1}", "description": f"Desc {i+1}", "stars": 1000 * (n - i), "stargazers_count": 1000 * (n - i)}
        for i in range(n)
    ]


def _mock_score(repo, token, timeout):
    return 75.0


def _make_html(ecosystems=None):
    engine = LeaderboardPageEngine(
        ecosystems=ecosystems or ["python"],
        limit=3,
        _repos_override={"python": _fake_repos(), "typescript": _fake_repos(), "rust": _fake_repos()},
        _score_fn=_mock_score,
    )
    result = engine.run()
    return render_leaderboard_html(result)


def test_html_has_title():
    html = _make_html()
    assert "<title>" in html


def test_html_title_contains_ecosystem():
    html = _make_html(["python"])
    assert "python" in html.lower() or "Python" in html


def test_html_has_meta_description():
    html = _make_html()
    assert 'name="description"' in html


def test_html_meta_description_has_content():
    html = _make_html()
    match = re.search(r'<meta name="description" content="([^"]+)"', html)
    assert match is not None
    assert len(match.group(1)) > 20


def test_html_has_og_title():
    html = _make_html()
    assert 'property="og:title"' in html


def test_html_has_og_description():
    html = _make_html()
    assert 'property="og:description"' in html


def test_html_has_og_type():
    html = _make_html()
    assert 'property="og:type"' in html


def test_html_has_og_url():
    html = _make_html()
    assert 'property="og:url"' in html


def test_html_has_jsonld_script():
    html = _make_html()
    assert 'application/ld+json' in html


def test_html_jsonld_is_valid_json():
    html = _make_html()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1))
    assert isinstance(data, dict)


def test_html_jsonld_is_itemlist():
    html = _make_html()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    data = json.loads(match.group(1))
    assert data.get("@type") == "ItemList"


def test_html_jsonld_has_items():
    html = _make_html()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    data = json.loads(match.group(1))
    items = data.get("itemListElement", [])
    assert len(items) > 0


def test_html_has_twitter_card():
    html = _make_html()
    assert 'twitter:card' in html


def test_html_has_canonical_or_og_url():
    html = _make_html()
    assert 'og:url' in html or 'canonical' in html
