"""Tests for agentkit doctor."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from agentkit_cli.doctor import (
    DoctorCheckResult,
    DoctorReport,
    check_context_files,
    check_context_freshness,
    check_git_has_commit,
    check_git_repo,
    check_herenow_api_key,
    check_output_dir,
    check_pyproject_present,
    check_readme_present,
    check_source_files,
    check_tool_binary,
    check_toolchain,
    check_working_tree_clean,
    run_doctor,
)
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

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


def _pass_check(id: str = "test.check", category: str = "repo") -> DoctorCheckResult:
    return DoctorCheckResult(
        id=id, name="Test", status="pass",
        summary="ok", details="", fix_hint="", category=category,
    )


def _warn_check(id: str = "test.check", category: str = "repo") -> DoctorCheckResult:
    return DoctorCheckResult(
        id=id, name="Test", status="warn",
        summary="warn", details="", fix_hint="fix it", category=category,
    )


def _fail_check(id: str = "test.check", category: str = "repo") -> DoctorCheckResult:
    return DoctorCheckResult(
        id=id, name="Test", status="fail",
        summary="fail", details="", fix_hint="fix it", category=category,
    )


# ---------------------------------------------------------------------------
# D1: existing repo checks (preserve behaviour, update for expanded suite)
# ---------------------------------------------------------------------------

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
    with patch("agentkit_cli.doctor.check_toolchain") as mock_tc, \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_tc.return_value = []
        mock_cf.return_value = _pass_check("context.freshness", "context")
        report = run_doctor(tmp_path)

    ids = [check.id for check in report.checks]
    assert ids[:6] == [
        "repo.git",
        "repo.commit",
        "repo.working_tree",
        "repo.readme",
        "repo.pyproject",
        "context.presence",
    ]
    assert "context.source_files" in ids
    assert "context.output_dir" in ids
    assert "publish.herenow_key" in ids


def test_run_doctor_summary_counts(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    write_file(tmp_path / "CLAUDE.md")
    write_file(tmp_path / "main.py", "print('hi')\n")
    commit_all(tmp_path)
    monkeypatch.setenv("HERENOW_API_KEY", "test-key")

    all_pass_toolchain = [
        _pass_check(f"toolchain.{t}", "toolchain")
        for t in ("agentmd", "agentlint", "coderace", "agentreflect", "git", "python3")
    ]

    with patch("agentkit_cli.doctor.check_toolchain", return_value=all_pass_toolchain), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        report = run_doctor(tmp_path)

    assert report.warn_count == 0
    assert report.fail_count == 0
    assert report.pass_count == len(report.checks)


def test_doctor_cli_exit_zero_for_warn_only(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Doctor:" in result.output


def test_doctor_cli_exit_one_for_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 1
    assert "FAIL" in result.output


def test_doctor_cli_human_output_contains_core_checks(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    write_file(tmp_path / "AGENTS.md")
    write_file(tmp_path / "main.py", "pass\n")
    commit_all(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HERENOW_API_KEY", "test-key")

    all_pass_toolchain = [
        _pass_check(f"toolchain.{t}", "toolchain")
        for t in ("agentmd", "agentlint", "coderace", "agentreflect", "git", "python3")
    ]

    with patch("agentkit_cli.doctor.check_toolchain", return_value=all_pass_toolchain), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor"])

    assert "Git repository" in result.output
    assert "README.md" in result.output
    assert "Context files" in result.output
    assert "0 fail" in result.output


def test_doctor_cli_json_payload_uses_same_model(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='demo'\n")
    write_file(tmp_path / "AGENTS.md")
    write_file(tmp_path / "main.py", "pass\n")
    commit_all(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HERENOW_API_KEY", "test-key")

    all_pass_toolchain = [
        _pass_check(f"toolchain.{t}", "toolchain")
        for t in ("agentmd", "agentlint", "coderace", "agentreflect", "git", "python3")
    ]

    with patch("agentkit_cli.doctor.check_toolchain", return_value=all_pass_toolchain), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["fail"] == 0
    assert payload["summary"]["warn"] == 0
    assert payload["checks"][0]["id"] == "repo.git"


def test_doctor_cli_json_exit_code_tracks_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["summary"]["fail"] == 1


def test_doctor_resolves_root_path(tmp_path: Path) -> None:
    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        report = run_doctor(tmp_path)

    assert report.root == str(tmp_path.resolve())


# ---------------------------------------------------------------------------
# D2: toolchain probe tests
# ---------------------------------------------------------------------------

def test_check_tool_binary_pass_when_found_with_version() -> None:
    with patch("shutil.which", return_value="/usr/bin/git"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="git version 2.39.0\n", stderr=""
        )
        result = check_tool_binary("git", is_core=False)

    assert result.status == "pass"
    assert "git version" in result.details
    assert result.category == "toolchain"


def test_check_tool_binary_pass_when_found_version_probe_fails() -> None:
    """Binary exists but --version raises; should still be 'pass' (found)."""
    with patch("shutil.which", return_value="/usr/bin/agentmd"), \
         patch("subprocess.run", side_effect=OSError("boom")):
        result = check_tool_binary("agentmd", is_core=True)

    assert result.status == "pass"
    assert result.details  # some fallback text


def test_check_tool_binary_fail_when_core_missing() -> None:
    with patch("shutil.which", return_value=None):
        result = check_tool_binary("agentmd", is_core=True)

    assert result.status == "fail"
    assert result.id == "toolchain.agentmd"
    assert "agentmd" in result.fix_hint


def test_check_tool_binary_warn_when_optional_missing() -> None:
    with patch("shutil.which", return_value=None):
        result = check_tool_binary("python3", is_core=False)

    assert result.status == "warn"
    assert result.id == "toolchain.python3"


def test_check_tool_binary_version_truncated_to_80_chars() -> None:
    long_version = "x" * 200
    with patch("shutil.which", return_value="/usr/bin/tool"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=long_version + "\n", stderr=""
        )
        result = check_tool_binary("tool", is_core=False)

    assert len(result.details) <= 80


def test_check_tool_binary_noisy_version_takes_first_line() -> None:
    noisy = "INFO: loading...\nagentmd v1.2.3\nmore lines here"
    with patch("shutil.which", return_value="/usr/bin/agentmd"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=noisy, stderr=""
        )
        result = check_tool_binary("agentmd", is_core=True)

    assert result.status == "pass"
    assert "INFO" in result.details  # first line taken


def test_check_tool_binary_subprocess_timeout_still_found() -> None:
    with patch("shutil.which", return_value="/usr/bin/coderace"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired("coderace", 5)):
        result = check_tool_binary("coderace", is_core=True)

    assert result.status == "pass"  # binary found even if --version timed out


def test_check_toolchain_returns_six_results() -> None:
    with patch("agentkit_cli.doctor._probe_binary_version", return_value=(True, "v1")):
        results = check_toolchain()

    assert len(results) == 6  # 4 core + 2 optional
    categories = {r.category for r in results}
    assert categories == {"toolchain"}


def test_check_toolchain_core_missing_is_fail() -> None:
    def probe(binary: str) -> tuple[bool, str]:
        return binary not in ("agentmd", "agentlint", "coderace", "agentreflect"), ""

    with patch("agentkit_cli.doctor._probe_binary_version", side_effect=probe):
        results = check_toolchain()

    fails = [r for r in results if r.status == "fail"]
    assert len(fails) == 4
    fail_names = {r.id for r in fails}
    assert "toolchain.agentmd" in fail_names


def test_check_toolchain_optional_missing_is_warn() -> None:
    def probe(binary: str) -> tuple[bool, str]:
        return binary not in ("git", "python3"), "v1"

    with patch("agentkit_cli.doctor._probe_binary_version", side_effect=probe):
        results = check_toolchain()

    warns = [r for r in results if r.status == "warn"]
    assert len(warns) == 2
    warn_ids = {r.id for r in warns}
    assert "toolchain.git" in warn_ids
    assert "toolchain.python3" in warn_ids


def test_check_toolchain_all_present_no_failures() -> None:
    with patch("agentkit_cli.doctor._probe_binary_version", return_value=(True, "v1.0")):
        results = check_toolchain()

    assert all(r.status == "pass" for r in results)


# ---------------------------------------------------------------------------
# D3: actionability checks
# ---------------------------------------------------------------------------

def test_check_source_files_pass_py(tmp_path: Path) -> None:
    write_file(tmp_path / "main.py", "print('hi')\n")
    result = check_source_files(tmp_path)
    assert result.status == "pass"
    assert result.category == "context"


def test_check_source_files_pass_ts(tmp_path: Path) -> None:
    write_file(tmp_path / "index.ts", "export const x = 1;\n")
    result = check_source_files(tmp_path)
    assert result.status == "pass"


def test_check_source_files_pass_jsx(tmp_path: Path) -> None:
    sub = tmp_path / "src"
    sub.mkdir()
    write_file(sub / "App.jsx", "export default App;\n")
    result = check_source_files(tmp_path)
    assert result.status == "pass"


def test_check_source_files_warn_when_none(tmp_path: Path) -> None:
    write_file(tmp_path / "README.md", "# hi\n")
    result = check_source_files(tmp_path)
    assert result.status == "warn"
    assert result.fix_hint


def test_check_source_files_id_and_category(tmp_path: Path) -> None:
    result = check_source_files(tmp_path)
    assert result.id == "context.source_files"
    assert result.category == "context"


def test_check_context_freshness_warn_when_no_agentlint() -> None:
    with patch("agentkit_cli.tools.is_installed", return_value=False):
        result = check_context_freshness(Path("."))

    assert result.status == "warn"
    assert result.id == "context.freshness"
    assert "agentlint" in result.summary.lower()


def test_check_context_freshness_warn_when_agentlint_fails(tmp_path: Path) -> None:
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error!")
        result = check_context_freshness(tmp_path)

    assert result.status == "warn"
    assert "failed" in result.summary.lower()


def test_check_context_freshness_warn_when_subprocess_error(tmp_path: Path) -> None:
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run", side_effect=OSError("boom")):
        result = check_context_freshness(tmp_path)

    assert result.status == "warn"
    assert "failed" in result.summary.lower() or "None" in result.details


def test_check_context_freshness_warn_when_non_json(tmp_path: Path) -> None:
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="not json output", stderr=""
        )
        result = check_context_freshness(tmp_path)

    assert result.status == "warn"
    assert "failed" in result.summary.lower() or "unparseable" in result.summary.lower()


def test_check_context_freshness_uses_format_json_flag(tmp_path: Path) -> None:
    """Regression: doctor must call 'agentlint check-context --format json', not '--json'."""
    payload = json.dumps({"fresh": True, "age_days": 1})
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=payload, stderr="")
        check_context_freshness(tmp_path)

    call_args = mock_run.call_args[0][0]
    assert "--format" in call_args, "Must use --format flag"
    assert "json" in call_args, "Must pass json as format value"
    assert "--json" not in call_args, "Must not use deprecated --json flag"


def test_check_context_freshness_pass_when_fresh(tmp_path: Path) -> None:
    payload = json.dumps({"fresh": True, "age_days": 2})
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=payload, stderr="")
        result = check_context_freshness(tmp_path)

    assert result.status == "pass"


def test_check_context_freshness_warn_when_stale(tmp_path: Path) -> None:
    payload = json.dumps({"fresh": False, "age_days": 30})
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=payload, stderr="")
        result = check_context_freshness(tmp_path)

    assert result.status == "warn"
    assert "30d" in result.summary


def test_check_context_freshness_timeout_degrades_gracefully(tmp_path: Path) -> None:
    with patch("agentkit_cli.tools.is_installed", return_value=True), \
         patch("agentkit_cli.tools.subprocess.run", side_effect=subprocess.TimeoutExpired("agentlint", 15)):
        result = check_context_freshness(tmp_path)

    assert result.status == "warn"


def test_check_output_dir_pass_when_existing_writable(tmp_path: Path) -> None:
    report_dir = tmp_path / "agentkit-report"
    report_dir.mkdir()
    result = check_output_dir(tmp_path)
    assert result.status == "pass"


def test_check_output_dir_fail_when_existing_not_writable(tmp_path: Path) -> None:
    report_dir = tmp_path / "agentkit-report"
    report_dir.mkdir()
    report_dir.chmod(0o444)
    try:
        result = check_output_dir(tmp_path)
        assert result.status == "fail"
        assert "chmod" in result.fix_hint
    finally:
        report_dir.chmod(0o755)


def test_check_output_dir_pass_when_not_existing_parent_writable(tmp_path: Path) -> None:
    result = check_output_dir(tmp_path)
    assert result.status == "pass"
    assert "does not exist" in result.summary


def test_check_output_dir_id_and_category(tmp_path: Path) -> None:
    result = check_output_dir(tmp_path)
    assert result.id == "context.output_dir"
    assert result.category == "context"


def test_check_herenow_api_key_pass_when_set(monkeypatch) -> None:
    monkeypatch.setenv("HERENOW_API_KEY", "abc123")
    result = check_herenow_api_key()
    assert result.status == "pass"
    assert result.id == "publish.herenow_key"
    assert result.category == "publish"


def test_check_herenow_api_key_warn_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("HERENOW_API_KEY", raising=False)
    result = check_herenow_api_key()
    assert result.status == "warn"
    assert "HERENOW_API_KEY" in result.fix_hint


def test_check_herenow_api_key_warn_when_empty_string(monkeypatch) -> None:
    monkeypatch.setenv("HERENOW_API_KEY", "   ")
    result = check_herenow_api_key()
    assert result.status == "warn"


# ---------------------------------------------------------------------------
# D4: CLI flags — --category, --fail-on, --no-fail-exit
# ---------------------------------------------------------------------------

def test_doctor_category_repo_filters_checks(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json", "--category", "repo"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert all(c["category"] == "repo" for c in payload["checks"])


def test_doctor_category_toolchain_filters_checks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain") as mock_tc, \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_tc.return_value = [_pass_check("toolchain.agentmd", "toolchain")]
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json", "--category", "toolchain"])

    payload = json.loads(result.output)
    assert all(c["category"] == "toolchain" for c in payload["checks"])
    assert len(payload["checks"]) == 1


def test_doctor_category_publish_filters_checks(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HERENOW_API_KEY", "key")

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json", "--category", "publish"])

    payload = json.loads(result.output)
    assert all(c["category"] == "publish" for c in payload["checks"])


def test_doctor_category_invalid_exits_2(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor", "--category", "invalid-cat"])
    assert result.exit_code == 2


def test_doctor_fail_on_warn_exits_1_when_warns_present(tmp_path: Path, monkeypatch) -> None:
    """--fail-on warn: exit 1 when there are warns but no fails."""
    init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--fail-on", "warn"])

    assert result.exit_code == 1


def test_doctor_fail_on_warn_exits_0_when_all_pass(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    write_file(tmp_path / "README.md")
    write_file(tmp_path / "pyproject.toml", "[project]\nname='x'\n")
    write_file(tmp_path / "AGENTS.md")
    write_file(tmp_path / "main.py", "pass\n")
    commit_all(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HERENOW_API_KEY", "key")

    all_pass_tc = [_pass_check(f"toolchain.{t}", "toolchain")
                   for t in ("agentmd", "agentlint", "coderace", "agentreflect", "git", "python3")]

    with patch("agentkit_cli.doctor.check_toolchain", return_value=all_pass_tc), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--fail-on", "warn"])

    assert result.exit_code == 0


def test_doctor_fail_on_invalid_exits_2(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["doctor", "--fail-on", "bogus"])
    assert result.exit_code == 2


def test_doctor_no_fail_exit_returns_0_even_with_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # not a git repo -> fail

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--no-fail-exit"])

    assert result.exit_code == 0


def test_doctor_json_schema_has_required_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json"])

    payload = json.loads(result.output)
    assert "root" in payload
    assert "checks" in payload
    assert "summary" in payload
    assert set(payload["summary"].keys()) == {"pass", "warn", "fail"}


def test_doctor_json_check_schema_fields(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json"])

    payload = json.loads(result.output)
    for check in payload["checks"]:
        assert "id" in check
        assert "name" in check
        assert "status" in check
        assert "summary" in check
        assert "category" in check
        assert "fix_hint" in check
        assert check["status"] in ("pass", "warn", "fail")


def test_doctor_json_and_category_combined(tmp_path: Path, monkeypatch) -> None:
    init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--json", "--category", "repo"])

    payload = json.loads(result.output)
    assert len(payload["checks"]) > 0
    assert all(c["category"] == "repo" for c in payload["checks"])
    # Summary only covers filtered checks
    total = sum(payload["summary"].values())
    assert total == len(payload["checks"])


def test_doctor_report_model_exit_code_with_fails() -> None:
    report = DoctorReport(root="/tmp", checks=[_fail_check()])
    assert report.exit_code() == 1


def test_doctor_report_model_exit_code_zero_for_warn() -> None:
    report = DoctorReport(root="/tmp", checks=[_warn_check()])
    assert report.exit_code() == 0


def test_doctor_report_model_counts() -> None:
    checks = [_pass_check(), _warn_check(), _fail_check()]
    report = DoctorReport(root="/tmp", checks=checks)
    assert report.pass_count == 1
    assert report.warn_count == 1
    assert report.fail_count == 1


def test_doctor_human_output_no_fail_exit_shows_results(tmp_path: Path, monkeypatch) -> None:
    """--no-fail-exit must still print output."""
    monkeypatch.chdir(tmp_path)

    with patch("agentkit_cli.doctor.check_toolchain", return_value=[]), \
         patch("agentkit_cli.doctor.check_context_freshness") as mock_cf:
        mock_cf.return_value = _pass_check("context.freshness", "context")
        result = runner.invoke(app, ["doctor", "--no-fail-exit"])

    assert "Doctor:" in result.output
    assert result.exit_code == 0
