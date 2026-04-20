from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result

runner = CliRunner()


def test_launch_to_observe_to_supervise_to_reconcile_workflow(tmp_path):
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

    reconcile_dir = tmp_path / "reconcile"
    reconcile = runner.invoke(app, ["reconcile", str(project), "--output-dir", str(reconcile_dir), "--json"])
    assert reconcile.exit_code == 0, reconcile.output
    payload = json.loads("\n".join(reconcile.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.reconcile.v1"
    assert payload["complete_lane_ids"] == ["lane-01"]
    assert payload["ready_lane_ids"] == ["lane-02"]
    assert payload["newly_unblocked_lane_ids"] == ["lane-02"]
    assert payload["next_execution_order"] == ["lane-02"]
    assert (reconcile_dir / "lanes" / "lane-02" / "reconcile.md").exists()
