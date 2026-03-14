"""Tests for agentkit doctor."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from agentkit_cli.doctor import (
    check_context_files,
    check_git_has_commit,
    check_git_repo,
    check_pyproject_present,
    check_readme_present,
    check_working_tree_clean,
    run_doctor,
)
from agentkit_cli.main import app

runner = CliRunner()


def init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "doctor@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Doctor Test"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def write_file(path: Path, text: str = "content\n") -> None:
    path.write_text(text, encoding="utf-8")


def commit_all(path: Path, message: str = "Initial commit") -> None:
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_check_git_repo_pass(tmp_path: Path) -> None:
    init_repo(tmp_path)

    result = check_git_repo(tmp_path)

    assert result.status == "pass"
    assert result.id == "repo.git"


def test_check_git_repo_fail_outside_repo(tmp_path: Path) -> None:
    result = check_git_repo(tmp_path)

    assert result.status == "fail"
    assert "git init" in result.fix_hint


def test_check_git_has_commit_warn_for_new_repo(tmp_path: Path) -> None:
    init_repo(tmp_path)

    result = check_git_has_commit(tmp_path)

    assert result.status == "warn"
    assert "initial commit" in result.fix_hint.lower()


def test_check_git_has_commit_pass_after_commit(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    commit_all(tmp_path)

    result = check_git_has_commit(tmp_path)

    assert result.status == "pass"
    assert result.details


def test_check_working_tree_clean_pass_when_clean(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    commit_all(tmp_path)

    result = check_working_tree_clean(tmp_path)

    assert result.status == "pass"


def test_check_working_tree_clean_warn_when_dirty(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md", "hello\n")
    commit_all(tmp_path)
    write_file(tmp_path / "README.md", "changed\n")

    result = check_working_tree_clean(tmp_path)

    assert result.status == "warn"
    assert "stash" in result.fix_hint.lower()


def test_check_readme_present_pass(tmp_path: Path) -> None:
    write_file(tmp_path / "README.md")

    result = check_readme_present(tmp_path)

    assert result.status == "pass"


def test_check_readme_present_warn_when_missing(tmp_path: Path) -> None:
    result = check_readme_present(tmp_path)

    assert result.status == "warn"
    assert "README.md" in result.summary


def test_check_pyproject_present_pass(tmp_path: Path) -> None:
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")

    result = check_pyproject_present(tmp_path)

    assert result.status == "pass"


def test_check_pyproject_present_warn_when_missing(tmp_path: Path) -> None:
    result = check_pyproject_present(tmp_path)

    assert result.status == "warn"
    assert "pyproject.toml" in result.summary


def test_check_context_files_pass_with_agents_md(tmp_path: Path) -> None:
    write_file(tmp_path / "AGENTS.md")

    result = check_context_files(tmp_path)

    assert result.status == "pass"
    assert "AGENTS.md" in result.details


def test_check_context_files_pass_with_dot_agents_dir(tmp_path: Path) -> None:
    (tmp_path / ".agents").mkdir()

    result = check_context_files(tmp_path)

    assert result.status == "pass"
    assert ".agents" in result.details


def test_check_context_files_warn_when_missing(tmp_path: Path) -> None:
    result = check_context_files(tmp_path)

    assert result.status == "warn"
    assert "agentmd generate" in result.fix_hint


def test_run_doctor_has_fixed_check_order(tmp_path: Path) -> None:
    report = run_doctor(tmp_path)

    assert [check.id for check in report.checks] == [
        "repo.git",
        "repo.commit",
        "repo.working_tree",
        "repo.readme",
        "repo.pyproject",
        "context.presence",
    ]


def test_run_doctor_summary_counts(tmp_path: Path) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    write_file(tmp_path / "CLAUDE.md")
    commit_all(tmp_path)

    report = run_doctor(tmp_path)

    assert report.pass_count == 6
    assert report.warn_count == 0
    assert report.fail_count == 0


def test_doctor_cli_exit_zero_for_warn_only(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Doctor:" in result.output


def test_doctor_cli_exit_one_for_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "FAIL" in result.output


def test_doctor_cli_human_output_contains_core_checks(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    write_file(tmp_path / "AGENTS.md")
    commit_all(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor"])

    assert "Git repository" in result.output
    assert "README.md" in result.output
    assert "Context files" in result.output
    assert "Doctor: 6 pass, 0 warn, 0 fail" in result.output


def test_doctor_cli_json_payload_uses_same_model(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    write_file(tmp_path / "AGENTS.md")
    commit_all(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"] == {"pass": 6, "warn": 0, "fail": 0}
    assert payload["checks"][0]["id"] == "repo.git"


def test_doctor_cli_json_exit_code_tracks_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["summary"]["fail"] == 1


def test_doctor_resolves_root_path(tmp_path: Path) -> None:
    report = run_doctor(tmp_path)

    assert report.root == str(tmp_path.resolve())
