"""Tests for agentkit spotlight-queue command (D1-D4)."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.commands.spotlight_queue_cmd import (
    DEFAULT_REPOS,
    _do_seed,
    _ensure_seeded,
    _load,
    _parse_repo,
    _save,
    app,
)
from agentkit_cli.doctor import check_spotlight_queue
from agentkit_cli.main import app as main_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_queue_path(tmp_path: Path) -> Path:
    return tmp_path / "spotlight-queue.json"


def invoke_sq(*args, queue_path: Path):
    """Invoke spotlight-queue subcommand with --queue-path override."""
    return runner.invoke(app, list(args) + ["--queue-path", str(queue_path)])


# ---------------------------------------------------------------------------
# D1: _parse_repo
# ---------------------------------------------------------------------------

def test_parse_repo_strips_prefix():
    assert _parse_repo("github:pallets/flask") == "pallets/flask"


def test_parse_repo_no_prefix():
    assert _parse_repo("pallets/flask") == "pallets/flask"


# ---------------------------------------------------------------------------
# D1: _load / _save
# ---------------------------------------------------------------------------

def test_load_returns_empty_on_missing(tmp_path):
    p = make_queue_path(tmp_path)
    data = _load(p)
    assert data == {"repos": [], "lastSpotlighted": {}}


def test_save_and_load_roundtrip(tmp_path):
    p = make_queue_path(tmp_path)
    original = {"repos": ["django/django"], "lastSpotlighted": {"django/django": "2026-01-01"}}
    _save(original, p)
    loaded = _load(p)
    assert loaded == original


def test_load_corrupt_returns_empty(tmp_path):
    p = make_queue_path(tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json at all!!!")
    data = _load(p)
    assert data == {"repos": [], "lastSpotlighted": {}}


# ---------------------------------------------------------------------------
# D1: seed
# ---------------------------------------------------------------------------

def test_seed_adds_default_repos(tmp_path):
    p = make_queue_path(tmp_path)
    data = _do_seed(p)
    assert set(DEFAULT_REPOS).issubset(set(data["repos"]))
    assert len(data["repos"]) == len(DEFAULT_REPOS)


def test_seed_idempotent(tmp_path):
    p = make_queue_path(tmp_path)
    _do_seed(p)
    _do_seed(p)
    data = _load(p)
    # No duplicates
    assert len(data["repos"]) == len(set(data["repos"]))


def test_seed_preserves_existing_repos(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["custom/repo"], "lastSpotlighted": {}}, p)
    data = _do_seed(p)
    assert "custom/repo" in data["repos"]
    assert all(r in data["repos"] for r in DEFAULT_REPOS)


def test_seed_command(tmp_path):
    p = make_queue_path(tmp_path)
    result = invoke_sq("seed", queue_path=p)
    assert result.exit_code == 0
    assert "Seeded" in result.output


# ---------------------------------------------------------------------------
# D1: ensure_seeded (auto-seed)
# ---------------------------------------------------------------------------

def test_ensure_seeded_creates_file_if_missing(tmp_path):
    p = make_queue_path(tmp_path)
    assert not p.exists()
    data = _ensure_seeded(p)
    assert p.exists()
    assert len(data["repos"]) == len(DEFAULT_REPOS)


def test_ensure_seeded_noop_if_exists(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["only/one"], "lastSpotlighted": {}}, p)
    data = _ensure_seeded(p)
    assert data["repos"] == ["only/one"]


# ---------------------------------------------------------------------------
# D1: add
# ---------------------------------------------------------------------------

def test_add_repo(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    result = invoke_sq("add", "github:pallets/flask", queue_path=p)
    assert result.exit_code == 0
    data = _load(p)
    assert "pallets/flask" in data["repos"]


def test_add_repo_no_prefix(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    result = invoke_sq("add", "pallets/flask", queue_path=p)
    assert result.exit_code == 0
    data = _load(p)
    assert "pallets/flask" in data["repos"]


def test_add_duplicate_skips(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask"], "lastSpotlighted": {}}, p)
    result = invoke_sq("add", "pallets/flask", queue_path=p)
    assert result.exit_code == 0
    assert "Already in queue" in result.output
    data = _load(p)
    assert data["repos"].count("pallets/flask") == 1


def test_add_multiple_repos(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    invoke_sq("add", "pallets/flask", queue_path=p)
    invoke_sq("add", "django/django", queue_path=p)
    data = _load(p)
    assert data["repos"] == ["pallets/flask", "django/django"]


# ---------------------------------------------------------------------------
# D1: remove
# ---------------------------------------------------------------------------

def test_remove_repo(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask", "django/django"], "lastSpotlighted": {}}, p)
    result = invoke_sq("remove", "github:pallets/flask", queue_path=p)
    assert result.exit_code == 0
    data = _load(p)
    assert "pallets/flask" not in data["repos"]
    assert "django/django" in data["repos"]


def test_remove_not_in_queue(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    result = invoke_sq("remove", "not/here", queue_path=p)
    assert result.exit_code == 1


def test_remove_clears_last_spotlighted(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask"], "lastSpotlighted": {"pallets/flask": "2026-01-01"}}, p)
    invoke_sq("remove", "pallets/flask", queue_path=p)
    data = _load(p)
    assert "pallets/flask" not in data.get("lastSpotlighted", {})


# ---------------------------------------------------------------------------
# D1: clear
# ---------------------------------------------------------------------------

def test_clear_queue(tmp_path):
    p = make_queue_path(tmp_path)
    _do_seed(p)
    result = invoke_sq("clear", queue_path=p)
    assert result.exit_code == 0
    data = _load(p)
    assert data["repos"] == []
    assert data["lastSpotlighted"] == {}


# ---------------------------------------------------------------------------
# D1: list
# ---------------------------------------------------------------------------

def test_list_shows_repos(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask", "django/django"], "lastSpotlighted": {"pallets/flask": "2026-01-01"}}, p)
    result = invoke_sq("list", queue_path=p)
    assert result.exit_code == 0
    assert "pallets/flask" in result.output
    assert "django/django" in result.output
    assert "2026-01-01" in result.output
    assert "never" in result.output


def test_list_empty_queue_message(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    result = invoke_sq("list", queue_path=p)
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


# ---------------------------------------------------------------------------
# D1: next — rotation logic
# ---------------------------------------------------------------------------

def test_next_returns_never_spotlighted_first(tmp_path):
    p = make_queue_path(tmp_path)
    _save({
        "repos": ["pallets/flask", "django/django", "encode/httpx"],
        "lastSpotlighted": {"pallets/flask": "2026-01-01"},
    }, p)
    result = invoke_sq("next", queue_path=p)
    assert result.exit_code == 0
    assert result.output.strip() == "django/django"


def test_next_returns_oldest_spotlighted_when_all_done(tmp_path):
    p = make_queue_path(tmp_path)
    _save({
        "repos": ["a/a", "b/b", "c/c"],
        "lastSpotlighted": {
            "a/a": "2026-01-03",
            "b/b": "2026-01-01",   # oldest
            "c/c": "2026-01-02",
        },
    }, p)
    result = invoke_sq("next", queue_path=p)
    assert result.exit_code == 0
    assert result.output.strip() == "b/b"


def test_next_empty_queue_exits_1(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    result = invoke_sq("next", queue_path=p)
    assert result.exit_code == 1


def test_next_output_is_plain_text(tmp_path):
    """next must output plain owner/repo with no Rich markup."""
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask"], "lastSpotlighted": {}}, p)
    result = invoke_sq("next", queue_path=p)
    assert result.exit_code == 0
    output = result.output.strip()
    assert output == "pallets/flask"
    assert "[" not in output  # no Rich markup


def test_next_order_insertion_for_never_spotlighted(tmp_path):
    """When multiple repos are never spotlighted, return in insertion order."""
    p = make_queue_path(tmp_path)
    _save({
        "repos": ["first/repo", "second/repo", "third/repo"],
        "lastSpotlighted": {},
    }, p)
    result = invoke_sq("next", queue_path=p)
    assert result.output.strip() == "first/repo"


# ---------------------------------------------------------------------------
# D1: mark-done
# ---------------------------------------------------------------------------

def test_mark_done_updates_last_spotlighted(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask"], "lastSpotlighted": {}}, p)
    result = invoke_sq("mark-done", "github:pallets/flask", queue_path=p)
    assert result.exit_code == 0
    data = _load(p)
    today = str(date.today())
    assert data["lastSpotlighted"]["pallets/flask"] == today


def test_mark_done_overwrites_existing_date(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": ["pallets/flask"], "lastSpotlighted": {"pallets/flask": "2026-01-01"}}, p)
    invoke_sq("mark-done", "pallets/flask", queue_path=p)
    data = _load(p)
    assert data["lastSpotlighted"]["pallets/flask"] == str(date.today())


def test_mark_done_not_in_queue_fails(tmp_path):
    p = make_queue_path(tmp_path)
    _save({"repos": [], "lastSpotlighted": {}}, p)
    result = invoke_sq("mark-done", "not/here", queue_path=p)
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# D4: doctor check_spotlight_queue
# ---------------------------------------------------------------------------

def test_doctor_check_missing_file(tmp_path, monkeypatch):
    p = tmp_path / "spotlight-queue.json"
    monkeypatch.setattr(
        "agentkit_cli.doctor.Path.home",
        lambda: tmp_path / "nonexistent",
    )
    # directly test with a path that doesn't exist
    from agentkit_cli import doctor as doc_mod
    import agentkit_cli.doctor as dm
    original = dm.Path.home
    # patch check_spotlight_queue to use our tmp path
    from unittest.mock import patch
    with patch("agentkit_cli.doctor.Path") as mock_path_cls:
        # Simplest: call the function directly but monkeypatch the queue path lookup
        pass

    # Test via direct patching of the function internals
    import agentkit_cli.doctor as dm2
    from unittest.mock import patch as up
    with up("agentkit_cli.doctor.Path") as MockPath:
        MockPath.home.return_value = tmp_path / "no_home"
        result = dm2.check_spotlight_queue()
    assert result.status == "warn"
    assert "not found" in result.summary.lower()


def test_doctor_check_empty_queue(tmp_path):
    from unittest.mock import patch
    import agentkit_cli.doctor as dm
    p = tmp_path / ".local" / "share" / "agentkit" / "spotlight-queue.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"repos": [], "lastSpotlighted": {}}))
    with patch("agentkit_cli.doctor.Path") as MockPath:
        MockPath.home.return_value = tmp_path
        result = dm.check_spotlight_queue()
    assert result.status == "warn"
    assert "empty" in result.summary.lower()


def test_doctor_check_few_repos(tmp_path):
    from unittest.mock import patch
    import agentkit_cli.doctor as dm
    p = tmp_path / ".local" / "share" / "agentkit" / "spotlight-queue.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"repos": ["a/a", "b/b"], "lastSpotlighted": {}}))
    with patch("agentkit_cli.doctor.Path") as MockPath:
        MockPath.home.return_value = tmp_path
        result = dm.check_spotlight_queue()
    assert result.status == "warn"
    assert "2" in result.summary


def test_doctor_check_healthy_queue(tmp_path):
    from unittest.mock import patch
    import agentkit_cli.doctor as dm
    p = tmp_path / ".local" / "share" / "agentkit" / "spotlight-queue.json"
    p.parent.mkdir(parents=True)
    repos = ["a/a", "b/b", "c/c", "d/d"]
    p.write_text(json.dumps({"repos": repos, "lastSpotlighted": {}}))
    with patch("agentkit_cli.doctor.Path") as MockPath:
        MockPath.home.return_value = tmp_path
        result = dm.check_spotlight_queue()
    assert result.status == "pass"
    assert "4" in result.summary
    assert "a/a" in result.summary  # next is first never-spotlighted


def test_doctor_check_corrupt_file(tmp_path):
    from unittest.mock import patch
    import agentkit_cli.doctor as dm
    p = tmp_path / ".local" / "share" / "agentkit" / "spotlight-queue.json"
    p.parent.mkdir(parents=True)
    p.write_text("not valid json }{")
    with patch("agentkit_cli.doctor.Path") as MockPath:
        MockPath.home.return_value = tmp_path
        result = dm.check_spotlight_queue()
    assert result.status == "fail"
    assert "corrupt" in result.summary.lower()


# ---------------------------------------------------------------------------
# Integration: main app registers spotlight-queue
# ---------------------------------------------------------------------------

def test_main_app_has_spotlight_queue_command():
    result = runner.invoke(main_app, ["spotlight-queue", "--help"])
    assert result.exit_code == 0
    assert "spotlight-queue" in result.output.lower() or "queue" in result.output.lower()


def test_main_app_spotlight_queue_seed(tmp_path):
    p = make_queue_path(tmp_path)
    result = runner.invoke(main_app, ["spotlight-queue", "seed", "--queue-path", str(p)])
    assert result.exit_code == 0
    assert "Seeded" in result.output


def test_main_app_spotlight_queue_next_returns_first_default(tmp_path):
    p = make_queue_path(tmp_path)
    _do_seed(p)
    result = runner.invoke(main_app, ["spotlight-queue", "next", "--queue-path", str(p)])
    assert result.exit_code == 0
    assert result.output.strip() == DEFAULT_REPOS[0]
