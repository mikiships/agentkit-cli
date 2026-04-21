from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result

runner = CliRunner()


def test_land_to_merge_workflow_and_apply(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")

    observe_dir = project / "observe"
    assert runner.invoke(app, ["observe", str(project), "--target", "codex", "--output-dir", str(observe_dir)]).exit_code == 0
    supervise_dir = project / "supervise"
    assert runner.invoke(app, ["supervise", str(project), "--output-dir", str(supervise_dir)]).exit_code == 0
    reconcile_dir = project / "reconcile"
    assert runner.invoke(app, ["reconcile", str(project), "--output-dir", str(reconcile_dir)]).exit_code == 0
    (project / "reconcile.json").write_text((reconcile_dir / "reconcile.json").read_text(encoding="utf-8"), encoding="utf-8")
    resume_dir = project / "resume"
    assert runner.invoke(app, ["resume", str(project), "--output-dir", str(resume_dir)]).exit_code == 0
    (project / "resume.json").write_text((resume_dir / "resume.json").read_text(encoding="utf-8"), encoding="utf-8")
    relaunch_dir = project / "relaunch"
    assert runner.invoke(app, ["relaunch", str(project), "--output-dir", str(relaunch_dir)]).exit_code == 0
    (project / "relaunch.json").write_text((relaunch_dir / "relaunch.json").read_text(encoding="utf-8"), encoding="utf-8")
    closeout_dir = project / "closeout"
    assert runner.invoke(app, ["closeout", str(project), "--output-dir", str(closeout_dir)]).exit_code == 0
    (project / "closeout.json").write_text((closeout_dir / "closeout.json").read_text(encoding="utf-8"), encoding="utf-8")

    merge_dir = tmp_path / "merge"
    result = runner.invoke(app, ["merge", str(project), "--output-dir", str(merge_dir), "--json", "--apply"])
    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["applied_lane_ids"] == ["lane-01"]
    assert payload["blocked_lane_ids"] == []
    assert "done" in (project / "src" / "api" / "handlers.py").read_text(encoding="utf-8")


def test_merge_apply_stops_on_conflict(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'lane'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")

    (project / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'root'\n", encoding="utf-8")
    _git(project, "add", "src/api/handlers.py")
    _git(project, "commit", "-m", "root change")

    for cmd in [
        ["observe", str(project), "--target", "codex", "--output-dir", str(project / "observe")],
        ["supervise", str(project), "--output-dir", str(project / "supervise")],
        ["reconcile", str(project), "--output-dir", str(project / "reconcile")],
        ["resume", str(project), "--output-dir", str(project / "resume")],
        ["relaunch", str(project), "--output-dir", str(project / "relaunch")],
        ["closeout", str(project), "--output-dir", str(project / "closeout")],
    ]:
        res = runner.invoke(app, cmd)
        assert res.exit_code == 0, res.output
    for name in ["reconcile", "resume", "relaunch", "closeout"]:
        src = project / name / f"{name}.json"
        (project / f"{name}.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    result = runner.invoke(app, ["merge", str(project), "--json", "--apply"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["stopped_on_lane_id"] == "lane-01"
    assert payload["blocked_lane_ids"] == ["lane-01"]
    assert payload["applied_lane_ids"] == []
