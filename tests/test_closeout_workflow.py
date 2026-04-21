from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result

runner = CliRunner()


def test_launch_to_relaunch_to_closeout_workflow(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")

    observe_dir = project / "observe"
    observe = runner.invoke(app, ["observe", str(project), "--target", "codex", "--output-dir", str(observe_dir)])
    assert observe.exit_code == 0, observe.output

    supervise_dir = project / "supervise"
    supervise = runner.invoke(app, ["supervise", str(project), "--output-dir", str(supervise_dir)])
    assert supervise.exit_code == 0, supervise.output

    reconcile_dir = project / "reconcile"
    reconcile = runner.invoke(app, ["reconcile", str(project), "--output-dir", str(reconcile_dir)])
    assert reconcile.exit_code == 0, reconcile.output
    (project / "reconcile.json").write_text((reconcile_dir / "reconcile.json").read_text(encoding="utf-8"), encoding="utf-8")

    resume_dir = project / "resume"
    resume = runner.invoke(app, ["resume", str(project), "--output-dir", str(resume_dir)])
    assert resume.exit_code == 0, resume.output
    (project / "resume.json").write_text((resume_dir / "resume.json").read_text(encoding="utf-8"), encoding="utf-8")

    relaunch_dir = project / "relaunch"
    relaunch = runner.invoke(app, ["relaunch", str(project), "--output-dir", str(relaunch_dir)])
    assert relaunch.exit_code == 0, relaunch.output
    (project / "relaunch.json").write_text((relaunch_dir / "relaunch.json").read_text(encoding="utf-8"), encoding="utf-8")

    closeout_dir = tmp_path / "closeout"
    closeout = runner.invoke(app, ["closeout", str(project), "--output-dir", str(closeout_dir), "--json"])
    assert closeout.exit_code == 0, closeout.output
    payload = json.loads("\n".join(closeout.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.closeout.v1"
    assert payload["merge_ready_lane_ids"] == ["lane-01"]
    assert payload["review_required_lane_ids"] == ["lane-02"]
    assert (closeout_dir / "lanes" / "lane-01" / "packet.md").exists()
    assert (closeout_dir / "lanes" / "lane-02" / "closeout.md").exists()
