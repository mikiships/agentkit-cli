"""Tests for agentkit site --deploy functionality — v0.84.0."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _init_git_repo(path: Path) -> None:
    """Initialize a git repo with one empty commit."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(path), capture_output=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=str(path), capture_output=True)


def _make_site_dir(path: Path) -> Path:
    """Create a minimal site output directory."""
    site = path / "site_out"
    site.mkdir()
    (site / "index.html").write_text("<html><body>Test</body></html>")
    (site / "sitemap.xml").write_text("<urlset></urlset>")
    return site


class TestRunDeploy:
    def test_copies_index_html(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        site = _make_site_dir(tmp_path)
        result = _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="docs",
            commit_message="deploy test",
            no_push=True,
            quiet=True,
        )
        assert (repo / "docs" / "index.html").exists()

    def test_copies_multiple_files(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        site = _make_site_dir(tmp_path)
        (site / "topic-python.html").write_text("<html></html>")
        _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="docs",
            commit_message="deploy test",
            no_push=True,
            quiet=True,
        )
        assert (repo / "docs" / "sitemap.xml").exists()
        assert (repo / "docs" / "topic-python.html").exists()

    def test_commits_when_changes_exist(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        site = _make_site_dir(tmp_path)
        result = _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="docs",
            commit_message="chore: update site",
            no_push=True,
            quiet=True,
        )
        assert result["committed"] is True

    def test_no_push_flag_skips_push(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        site = _make_site_dir(tmp_path)
        result = _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="docs",
            commit_message="deploy",
            no_push=True,
            quiet=True,
        )
        assert result["pushed"] is False

    def test_success_flag_true_on_success(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        site = _make_site_dir(tmp_path)
        result = _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="docs",
            commit_message="deploy",
            no_push=True,
            quiet=True,
        )
        assert result["success"] is True

    def test_creates_deploy_dir_if_missing(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        site = _make_site_dir(tmp_path)
        result = _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="public",
            commit_message="deploy",
            no_push=True,
            quiet=True,
        )
        assert (repo / "public").exists()

    def test_handles_git_failure_gracefully(self, tmp_path):
        from agentkit_cli.commands.site_cmd import _run_deploy
        # Use a non-git directory
        repo = tmp_path / "not_a_repo"
        repo.mkdir()
        site = _make_site_dir(tmp_path)
        result = _run_deploy(
            output_path=site,
            repo_path=repo,
            deploy_dir="docs",
            commit_message="deploy",
            no_push=True,
            quiet=True,
        )
        assert result["success"] is False
        assert "error" in result

    def test_site_command_deploy_integration(self, tmp_path):
        """site_command with --deploy copies files into docs/."""
        from agentkit_cli.commands.site_cmd import site_command
        from agentkit_cli.history import HistoryDB
        from agentkit_cli.site_engine import SiteEngine, SiteConfig
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_git_repo(repo)
        db = HistoryDB(db_path=tmp_path / "test.db")
        cfg = SiteConfig(topics=["python"])
        engine = SiteEngine(config=cfg, db=db)
        out = tmp_path / "site"
        summary = site_command(
            output_dir=str(out),
            topics="python",
            quiet=True,
            deploy=True,
            repo_path=repo,
            deploy_dir="docs",
            no_push=True,
            _engine=engine,
        )
        assert summary["deploy"]["success"] is True
        assert (repo / "docs" / "index.html").exists()
