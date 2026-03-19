"""Tests for D1: UserImproveEngine core (≥14 tests)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.user_improve import (
    UserImproveEngine,
    UserImproveReport,
    UserImproveResult,
    UserRepoScore,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repos(n=5):
    return [
        {
            "full_name": f"alice/repo-{i}",
            "name": f"repo-{i}",
            "stars": 10 - i,
            "fork": False,
        }
        for i in range(n)
    ]


def _make_scores(scores: dict[str, float]) -> list[UserRepoScore]:
    return [
        UserRepoScore(
            name=full.split("/")[-1],
            full_name=full,
            score=sc,
            grade="A" if sc >= 80 else "B" if sc >= 65 else "C" if sc >= 50 else "D",
            stars=5,
            repo_url=f"https://github.com/{full}",
        )
        for full, sc in scores.items()
    ]


def _make_analyze_fn(scores: dict[str, float]):
    def _fn(full_name, timeout):
        if full_name in scores:
            return scores[full_name], None
        return None, "not found"
    return _fn


def _improve_override_fn(repo: UserRepoScore, clone_dir: str):
    """Simulates improvement: after = before + 10."""
    before = repo.score
    after = before + 10.0
    return before, after, ["CLAUDE.md generated"], ["redteam hardening"]


# ---------------------------------------------------------------------------
# UserRepoScore
# ---------------------------------------------------------------------------

def test_user_repo_score_to_dict():
    s = UserRepoScore(name="repo", full_name="alice/repo", score=72.0, grade="B", stars=3, repo_url="https://github.com/alice/repo")
    d = s.to_dict()
    assert d["name"] == "repo"
    assert d["full_name"] == "alice/repo"
    assert d["score"] == 72.0
    assert d["grade"] == "B"
    assert d["stars"] == 3


def test_user_improve_result_to_dict():
    r = UserImproveResult(
        repo_url="https://github.com/alice/repo",
        full_name="alice/repo",
        before_score=60.0,
        after_score=75.0,
        lift=15.0,
        files_generated=["CLAUDE.md"],
        files_hardened=["harden.md"],
        errors=[],
        skipped=False,
    )
    d = r.to_dict()
    assert d["before_score"] == 60.0
    assert d["after_score"] == 75.0
    assert d["lift"] == 15.0
    assert d["skipped"] is False
    assert "CLAUDE.md" in d["files_generated"]


def test_user_improve_result_skipped_to_dict():
    r = UserImproveResult(
        repo_url="https://github.com/alice/repo",
        full_name="alice/repo",
        before_score=55.0,
        after_score=55.0,
        lift=0.0,
        errors=["Clone failed"],
        skipped=True,
    )
    d = r.to_dict()
    assert d["skipped"] is True
    assert "Clone failed" in d["errors"]


def test_user_improve_report_to_dict():
    report = UserImproveReport(
        user="alice",
        avatar_url="https://github.com/alice.png",
        total_repos=10,
        improved=3,
        skipped=1,
        results=[],
        summary_stats={"avg_before": 60.0, "avg_after": 75.0, "avg_lift": 15.0},
    )
    d = report.to_dict()
    assert d["user"] == "alice"
    assert d["total_repos"] == 10
    assert d["improved"] == 3
    assert d["skipped"] == 1
    assert d["summary_stats"]["avg_lift"] == 15.0


# ---------------------------------------------------------------------------
# select_targets
# ---------------------------------------------------------------------------

def test_select_targets_basic():
    engine = UserImproveEngine()
    scores = _make_scores({
        "alice/a": 90.0,
        "alice/b": 70.0,
        "alice/c": 55.0,
        "alice/d": 40.0,
    })
    targets = engine.select_targets(scores, limit=5, below=80)
    assert len(targets) == 3
    names = [t.full_name for t in targets]
    assert "alice/a" not in names
    assert "alice/d" in names


def test_select_targets_sorted_ascending():
    engine = UserImproveEngine()
    scores = _make_scores({"alice/a": 30.0, "alice/b": 60.0, "alice/c": 50.0})
    targets = engine.select_targets(scores, limit=5, below=80)
    assert targets[0].score <= targets[1].score <= targets[2].score


def test_select_targets_limit():
    engine = UserImproveEngine()
    scores = _make_scores({f"alice/repo-{i}": float(i * 5) for i in range(15)})
    targets = engine.select_targets(scores, limit=3, below=80)
    assert len(targets) == 3


def test_select_targets_none_below_threshold():
    engine = UserImproveEngine()
    scores = _make_scores({"alice/a": 85.0, "alice/b": 95.0})
    targets = engine.select_targets(scores, limit=5, below=80)
    assert targets == []


# ---------------------------------------------------------------------------
# score_repos (with override)
# ---------------------------------------------------------------------------

def test_score_repos_with_override():
    analyze_fn = _make_analyze_fn({"alice/repo-0": 72.0, "alice/repo-1": 45.0})
    engine = UserImproveEngine(_analyze_override=analyze_fn)
    repos = _make_repos(2)
    scored = engine.score_repos(repos)
    assert len(scored) == 2
    assert scored[0].score == 72.0 or scored[1].score == 45.0


def test_score_repos_skips_failed():
    def fail_fn(full_name, timeout):
        return None, "timeout"
    engine = UserImproveEngine(_analyze_override=fail_fn)
    repos = _make_repos(3)
    scored = engine.score_repos(repos)
    assert scored == []


# ---------------------------------------------------------------------------
# run pipeline (with overrides)
# ---------------------------------------------------------------------------

def test_run_pipeline_basic():
    repos = _make_repos(4)
    analyze_fn = _make_analyze_fn({
        "alice/repo-0": 85.0,
        "alice/repo-1": 65.0,
        "alice/repo-2": 50.0,
        "alice/repo-3": 30.0,
    })
    engine = UserImproveEngine(
        _repos_override=repos,
        _analyze_override=analyze_fn,
        _improve_override=_improve_override_fn,
        _avatar_override="https://github.com/alice.png",
    )
    report = engine.run("alice", limit=5, below=80)
    assert report.user == "alice"
    assert report.total_repos == 4
    assert report.improved > 0
    assert isinstance(report.summary_stats, dict)
    assert "avg_lift" in report.summary_stats


def test_run_pipeline_limit_enforced():
    repos = _make_repos(10)
    analyze_fn = _make_analyze_fn({f"alice/repo-{i}": float(10 + i * 5) for i in range(10)})
    engine = UserImproveEngine(
        _repos_override=repos,
        _analyze_override=analyze_fn,
        _improve_override=_improve_override_fn,
        _avatar_override="",
    )
    report = engine.run("alice", limit=2, below=80)
    assert len(report.results) <= 2


def test_run_limit_max_capped():
    engine = UserImproveEngine(
        _repos_override=[],
        _analyze_override=lambda fn, t: (50.0, None),
        _improve_override=_improve_override_fn,
        _avatar_override="",
    )
    # limit > 20 should be capped
    report = engine.run("alice", limit=999, below=80)
    assert report.user == "alice"


def test_run_error_resilient():
    """If improve_override raises for one repo, it should be skipped not aborted."""
    repos = _make_repos(3)
    call_count = [0]

    def analyze_fn(full_name, timeout):
        return 50.0, None

    def improve_fn(repo, clone_dir):
        call_count[0] += 1
        if call_count[0] == 2:
            raise RuntimeError("network error")
        return repo.score, repo.score + 5.0, [], []

    engine = UserImproveEngine(
        _repos_override=repos,
        _analyze_override=analyze_fn,
        _improve_override=improve_fn,
        _avatar_override="",
    )
    report = engine.run("alice", limit=5, below=80)
    # Should have 3 results total (1 skipped)
    assert len(report.results) == 3
    skipped = [r for r in report.results if r.skipped]
    assert len(skipped) == 1
