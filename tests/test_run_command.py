from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.exceptions import Exit as ClickExit

from agentkit_cli.commands.run_cmd import run_command
from agentkit_cli.release_check import CheckResult, ReleaseCheckResult


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    (tmp_path / "CLAUDE.md").write_text("# context\n")
    return tmp_path


def _fake_config():
    class Notify:
        slack_url = None
        discord_url = None
        webhook_url = None
        on = "fail"

    class Run:
        label = None

    class Config:
        notify = Notify()
        run = Run()

    return Config()


def _step_side_effect(name, tool, args, cwd):
    return {"step": name, "tool": tool, "status": "pass", "duration": 0.0, "output": "ok"}


def test_run_command_fails_when_release_check_fails(fake_root):
    with patch("agentkit_cli.commands.run_cmd.load_config", return_value=_fake_config()), \
         patch("agentkit_cli.commands.run_cmd._run_step", side_effect=_step_side_effect), \
         patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=fake_root), \
         patch("agentkit_cli.release_check.run_release_check") as mock_release, \
         patch("agentkit_cli.commands.release_check_cmd._render_table"):
        mock_release.return_value = ReleaseCheckResult(
            verdict="RELEASE-READY",
            package="agentkit-cli",
            version="0.96.0",
            registry="pypi",
            path=str(fake_root),
            checks=[CheckResult("git_push", "pass", "ok")],
        )
        with pytest.raises(ClickExit) as exc:
            run_command(path=fake_root, skip=["lint", "benchmark", "reflect"], release_check=True, json_output=True)
    assert exc.value.exit_code == 1


def test_run_command_json_summary_includes_release_check(fake_root, capsys):
    with patch("agentkit_cli.commands.run_cmd.load_config", return_value=_fake_config()), \
         patch("agentkit_cli.commands.run_cmd._run_step", side_effect=_step_side_effect), \
         patch("agentkit_cli.commands.run_cmd.find_project_root", return_value=fake_root), \
         patch("agentkit_cli.release_check.run_release_check") as mock_release, \
         patch("agentkit_cli.commands.release_check_cmd._render_table"):
        mock_release.return_value = ReleaseCheckResult(
            verdict="SHIPPED",
            package="agentkit-cli",
            version="0.96.0",
            registry="pypi",
            path=str(fake_root),
            checks=[CheckResult("git_push", "pass", "ok")],
        )
        run_command(path=fake_root, skip=["lint", "benchmark", "reflect"], release_check=True, json_output=True)
    out = capsys.readouterr().out
    assert '"release_check"' in out
    assert '"verdict": "SHIPPED"' in out
