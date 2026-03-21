"""Tests for agentkit site CLI command (D3) — v0.83.0."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(tmp_path, records=None):
    from agentkit_cli.history import HistoryDB
    db = HistoryDB(db_path=tmp_path / "test.db")
    for rec in (records or []):
        db.record_run(*rec)
    return db


def _make_engine(db):
    from agentkit_cli.site_engine import SiteEngine, SiteConfig
    cfg = SiteConfig(topics=["python", "typescript"])
    return SiteEngine(config=cfg, db=db)


# ---------------------------------------------------------------------------
# site_command unit tests
# ---------------------------------------------------------------------------

def test_site_command_creates_output_dir(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "mysite"
    site_command(output_dir=str(out), quiet=True, db_path=tmp_path / "e.db")
    assert out.exists()
    assert (out / "index.html").exists()


def test_site_command_creates_sitemap(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    site_command(output_dir=str(out), quiet=True, db_path=tmp_path / "e.db")
    assert (out / "sitemap.xml").exists()


def test_site_command_creates_topic_pages(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    site_command(output_dir=str(out), topics="python,rust", quiet=True, db_path=tmp_path / "e.db")
    assert (out / "topic" / "python.html").exists()
    assert (out / "topic" / "rust.html").exists()


def test_site_command_json_output(tmp_path, capsys):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    result = site_command(output_dir=str(out), topics="python", quiet=True, json_output=True, db_path=tmp_path / "e.db")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "pages_generated" in data
    assert "sitemap_count" in data


def test_site_command_returns_summary(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    summary = site_command(output_dir=str(out), quiet=True, db_path=tmp_path / "e.db")
    assert summary is not None
    assert summary["pages_generated"] >= 1


def test_site_command_limit_respected(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    db = _make_db(tmp_path, [
        ("owner/repo1", "agentlint", 80.0),
        ("owner/repo2", "agentlint", 70.0),
    ])
    out = tmp_path / "s"
    summary = site_command(output_dir=str(out), topics="python", limit=1, quiet=True, db_path=tmp_path / "test.db")
    assert summary["pages_generated"] >= 1


def test_site_command_custom_base_url(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    site_command(output_dir=str(out), base_url="https://mysite.example.com/", topics="python", quiet=True, db_path=tmp_path / "e.db")
    html = (out / "index.html").read_text()
    assert "mysite.example.com" in html


def test_site_command_deploy_copies_to_docs(tmp_path, monkeypatch):
    from agentkit_cli.commands.site_cmd import site_command
    # Change to tmp_path so docs/ lands there
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "s"
    site_command(output_dir=str(out), topics="python", quiet=True, deploy=True, db_path=tmp_path / "e.db")
    assert (tmp_path / "docs" / "index.html").exists()


def test_site_command_share_called(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    upload_calls = []
    def fake_upload(html):
        upload_calls.append(html)
        return "https://test.here.now/abc"
    summary = site_command(output_dir=str(out), topics="python", quiet=True, share=True, db_path=tmp_path / "e.db", _upload_fn=fake_upload)
    assert len(upload_calls) == 1
    assert summary["share_url"] == "https://test.here.now/abc"


def test_site_command_share_failure_does_not_crash(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    def bad_upload(html):
        raise RuntimeError("network error")
    summary = site_command(output_dir=str(out), topics="python", quiet=True, share=True, db_path=tmp_path / "e.db", _upload_fn=bad_upload)
    # Should not raise, share_url should be None
    assert summary["share_url"] is None


def test_site_command_rich_output(tmp_path, capsys):
    from agentkit_cli.commands.site_cmd import site_command
    out = tmp_path / "s"
    # No exception, output goes through rich but doesn't crash
    site_command(output_dir=str(out), topics="python", quiet=False, db_path=tmp_path / "e.db")
    assert (out / "index.html").exists()


def test_site_command_engine_injection(tmp_path):
    from agentkit_cli.commands.site_cmd import site_command
    from agentkit_cli.site_engine import SiteEngine, SiteConfig
    db = _make_db(tmp_path)
    engine = _make_engine(db)
    out = tmp_path / "injected"
    summary = site_command(output_dir=str(out), topics="python", quiet=True, _engine=engine)
    assert summary["pages_generated"] >= 1


def test_site_help(tmp_path):
    """agentkit site --help should not error."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app
    runner = CliRunner()
    result = runner.invoke(app, ["site", "--help"])
    assert result.exit_code == 0
    assert "output-dir" in result.output or "site" in result.output.lower()
