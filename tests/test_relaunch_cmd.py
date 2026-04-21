from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result
from tests.test_relaunch_engine import _save_resume_chain

runner = CliRunner()


def test_relaunch_command_writes_packet_directory_and_json(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_resume_chain(project)

    output_dir = tmp_path / "relaunch-report"
    result = runner.invoke(app, ["relaunch", str(project), "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.relaunch.v1"
    assert payload["relaunch_now_lane_ids"] == ["lane-02"]
    assert (output_dir / "relaunch.md").exists()
    assert (output_dir / "relaunch.json").exists()
    assert (output_dir / "lanes" / "lane-02" / "handoff.md").exists()
    assert (output_dir / "lanes" / "lane-02" / "launch.sh").exists()


def test_relaunch_command_supports_explicit_resume_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry this lane.")
    _save_resume_chain(project)

    result = runner.invoke(app, ["relaunch", str(project), "--resume-path", str(project / "resume"), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["resume_path"].endswith("resume/resume.json")


def test_relaunch_help():
    result = runner.invoke(app, ["relaunch", "--help"])
    assert result.exit_code == 0
    assert "--resume-path" in result.output
    assert "--packet-dir" in result.output
