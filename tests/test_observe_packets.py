from __future__ import annotations

import json

from agentkit_cli.launch import LaunchEngine
from agentkit_cli.observe import ObserveEngine
from tests.test_launch_engine import _make_repo, _write_materialize
from tests.test_observe_engine import _write_observe_result


def test_observe_packet_directory_writes_top_level_and_lane_packets_with_evidence(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="codex", single_lane=True)
    launch_dir = project / "launch"
    launch_plan = LaunchEngine().build(project, target="codex")
    LaunchEngine().write_directory(launch_plan, launch_dir)
    (project / "launch.json").write_text((launch_dir / "launch.json").read_text(encoding="utf-8"), encoding="utf-8")
    _write_observe_result(project, "lane-01", "success", "Lane completed with saved evidence.")

    plan = ObserveEngine().build(project, target="codex")
    output_dir = tmp_path / "observe-packets"
    ObserveEngine().write_directory(plan, output_dir)

    top = json.loads((output_dir / "observe.json").read_text(encoding="utf-8"))
    lane = json.loads((output_dir / "lanes" / "lane-01" / "observe.json").read_text(encoding="utf-8"))
    assert top["success_lane_ids"] == ["lane-01"]
    assert lane["status"] == "success"
    assert lane["recommended_next_action"]
    assert lane["evidence"]
    assert "Recommended next action" in (output_dir / "lanes" / "lane-01" / "observe.md").read_text(encoding="utf-8")
