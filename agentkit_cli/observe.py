from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_SUPPORTED_TARGETS = {"generic", "codex", "claude-code"}
_OBSERVE_STATUSES = {"success", "failure", "running", "waiting", "blocked", "unknown"}


class ObserveError(Exception):
    pass


@dataclass(frozen=True)
class ObserveDependency:
    lane_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"lane_id": self.lane_id, "reason": self.reason}


@dataclass(frozen=True)
class ObserveEvidence:
    kind: str
    status: str
    detail: str
    path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"detail": self.detail, "kind": self.kind, "path": self.path, "status": self.status}


@dataclass(frozen=True)
class ObservePacketPaths:
    handoff_markdown_path: str
    materialize_metadata_path: str
    stage_json_path: str
    stage_markdown_path: str
    observe_result_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "handoff_markdown_path": self.handoff_markdown_path,
            "materialize_metadata_path": self.materialize_metadata_path,
            "observe_result_path": self.observe_result_path,
            "stage_json_path": self.stage_json_path,
            "stage_markdown_path": self.stage_markdown_path,
        }


@dataclass(frozen=True)
class ObserveAction:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_name: str
    worktree_path: str
    owned_paths: list[str] = field(default_factory=list)
    dependencies: list[ObserveDependency] = field(default_factory=list)
    packet_paths: ObservePacketPaths | None = None
    source_state: str = ""
    source_state_reason: str = ""
    execution_mode: str = ""
    runner: str = ""
    display_command: str = ""
    status: str = "unknown"
    status_reason: str = ""
    recommended_next_action: str = ""
    evidence: list[ObserveEvidence] = field(default_factory=list)
    phase_notes: list[str] = field(default_factory=list)
    stage_notes: list[str] = field(default_factory=list)
    materialize_notes: list[str] = field(default_factory=list)
    launch_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_name": self.branch_name,
            "dependencies": [item.to_dict() for item in self.dependencies],
            "display_command": self.display_command,
            "evidence": [item.to_dict() for item in self.evidence],
            "execution_mode": self.execution_mode,
            "lane_id": self.lane_id,
            "launch_notes": list(self.launch_notes),
            "materialize_notes": list(self.materialize_notes),
            "owned_paths": list(self.owned_paths),
            "packet_paths": self.packet_paths.to_dict() if self.packet_paths else None,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "phase_notes": list(self.phase_notes),
            "recommended_next_action": self.recommended_next_action,
            "runner": self.runner,
            "serialization_group": self.serialization_group,
            "source_state": self.source_state,
            "source_state_reason": self.source_state_reason,
            "stage_notes": list(self.stage_notes),
            "status": self.status,
            "status_reason": self.status_reason,
            "title": self.title,
            "worktree_name": self.worktree_name,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class ObservePlan:
    schema_version: str
    project_path: str
    target: str
    launch_path: str
    observed_lane_ids: list[str] = field(default_factory=list)
    success_lane_ids: list[str] = field(default_factory=list)
    failure_lane_ids: list[str] = field(default_factory=list)
    running_lane_ids: list[str] = field(default_factory=list)
    waiting_lane_ids: list[str] = field(default_factory=list)
    blocked_lane_ids: list[str] = field(default_factory=list)
    unknown_lane_ids: list[str] = field(default_factory=list)
    summary_counts: dict[str, int] = field(default_factory=dict)
    recommended_next_actions: list[str] = field(default_factory=list)
    actions: list[ObserveAction] = field(default_factory=list)
    source_launch: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "actions": [item.to_dict() for item in self.actions],
            "blocked_lane_ids": list(self.blocked_lane_ids),
            "failure_lane_ids": list(self.failure_lane_ids),
            "launch_path": self.launch_path,
            "observed_lane_ids": list(self.observed_lane_ids),
            "project_path": self.project_path,
            "recommended_next_actions": list(self.recommended_next_actions),
            "running_lane_ids": list(self.running_lane_ids),
            "schema_version": self.schema_version,
            "source_launch": self.source_launch,
            "success_lane_ids": list(self.success_lane_ids),
            "summary_counts": dict(self.summary_counts),
            "target": self.target,
            "unknown_lane_ids": list(self.unknown_lane_ids),
            "waiting_lane_ids": list(self.waiting_lane_ids),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class ObserveEngine:
    def __init__(self) -> None:
        self._launch = LaunchArtifactLoader()

    def build(self, project_dir: str | Path, *, target: str | None = None) -> ObservePlan:
        root = Path(project_dir).expanduser().resolve()
        launch_path, launch = self._launch.load(root)
        if launch_path is None or launch is None:
            raise FileNotFoundError("No launch.json artifact found. Save a launch packet first, then run agentkit observe.")
        if str(launch.get("schema_version") or "") != "agentkit.launch.v1":
            raise ObserveError("Saved launch artifact is not a supported agentkit.launch.v1 packet.")
        launch_target = self._normalize_target(str(launch.get("target") or "generic"))
        if target is not None and self._normalize_target(target) != launch_target:
            raise ObserveError(f"Observe target {target.strip().lower()!r} does not match saved launch target {launch_target!r}.")
        project_path = Path(launch.get("project_path") or root).expanduser().resolve()
        actions = [self._build_action(item, launch_target) for item in sorted(launch.get("actions") or [], key=lambda i: (int(i.get("phase_index") or 0), str(i.get("lane_id") or "")))]
        return self._plan_from_actions(launch=launch, launch_path=launch_path, project_path=project_path, target=launch_target, actions=actions)

    def render_markdown(self, plan: ObservePlan) -> str:
        lines = [
            f"# Observe plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Launch packet: `{plan.launch_path}`",
            "",
            "## Summary",
            "",
            f"- Success: {', '.join(plan.success_lane_ids) if plan.success_lane_ids else 'none'}",
            f"- Failure: {', '.join(plan.failure_lane_ids) if plan.failure_lane_ids else 'none'}",
            f"- Running: {', '.join(plan.running_lane_ids) if plan.running_lane_ids else 'none'}",
            f"- Waiting: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Blocked: {', '.join(plan.blocked_lane_ids) if plan.blocked_lane_ids else 'none'}",
            f"- Unknown: {', '.join(plan.unknown_lane_ids) if plan.unknown_lane_ids else 'none'}",
            "",
            "## Recommended next actions",
            "",
        ]
        for item in plan.recommended_next_actions:
            lines.append(f"- {item}")
        lines.extend(["", "## Lanes", ""])
        for action in plan.actions:
            lines.extend([
                f"### {action.lane_id}: {action.title}",
                "",
                f"- Status: `{action.status}`",
                f"- Reason: {action.status_reason}",
                f"- Next: {action.recommended_next_action}",
                f"- Launch state: `{action.source_state}`",
                f"- Worktree path: `{action.worktree_path}`",
                f"- Runner: `{action.runner}`",
                f"- Command: `{action.display_command}`",
            ])
            if action.dependencies:
                lines.append(f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in action.dependencies)}")
            else:
                lines.append("- Dependencies: none")
            lines.append("- Evidence:")
            for evidence in action.evidence:
                suffix = f" (`{evidence.path}`)" if evidence.path else ""
                lines.append(f"  - `{evidence.kind}` / `{evidence.status}`: {evidence.detail}{suffix}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: ObservePlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "observe.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "observe.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for action in plan.actions:
            lane_dir = lanes_dir / action.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "observe.json").write_text(json.dumps(action.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "observe.md").write_text(self._render_lane_markdown(action), encoding="utf-8")
        return out

    def _render_lane_markdown(self, action: ObserveAction) -> str:
        lines = [
            f"# Observe lane: {action.lane_id}",
            "",
            f"- Title: {action.title}",
            f"- Status: `{action.status}`",
            f"- Reason: {action.status_reason}",
            f"- Recommended next action: {action.recommended_next_action}",
            f"- Worktree path: `{action.worktree_path}`",
            "",
            "## Evidence",
            "",
        ]
        for item in action.evidence:
            suffix = f" (`{item.path}`)" if item.path else ""
            lines.append(f"- `{item.kind}` / `{item.status}`: {item.detail}{suffix}")
        return "\n".join(lines).rstrip() + "\n"

    def _build_action(self, lane: dict[str, Any], target: str) -> ObserveAction:
        worktree_path = Path(str(lane.get("worktree_path") or "")).expanduser().resolve()
        packet_paths = self._resolve_packet_paths(lane, worktree_path)
        dependencies = [ObserveDependency(lane_id=str(item.get("lane_id") or ""), reason=str(item.get("reason") or "")) for item in sorted(lane.get("dependencies") or [], key=lambda i: (str(i.get("lane_id") or ""), str(i.get("reason") or "")))]
        status, reason, next_action, evidence = self._observe_status(lane=lane, target=target, worktree_path=worktree_path, packet_paths=packet_paths, dependencies=dependencies)
        return ObserveAction(
            lane_id=str(lane.get("lane_id") or "lane-00"),
            title=str(lane.get("title") or lane.get("lane_id") or "lane-00"),
            phase_id=str(lane.get("phase_id") or "phase-00"),
            phase_index=int(lane.get("phase_index") or 0),
            serialization_group=str(lane.get("serialization_group") or ""),
            branch_name=str(lane.get("branch_name") or ""),
            worktree_name=str(lane.get("worktree_name") or worktree_path.name),
            worktree_path=str(worktree_path),
            owned_paths=list(lane.get("owned_paths") or []),
            dependencies=dependencies,
            packet_paths=packet_paths,
            source_state=str(lane.get("state") or ""),
            source_state_reason=str(lane.get("state_reason") or ""),
            execution_mode=str(lane.get("execution_mode") or ""),
            runner=str(lane.get("runner") or ""),
            display_command=str(lane.get("display_command") or ""),
            status=status,
            status_reason=reason,
            recommended_next_action=next_action,
            evidence=evidence,
            phase_notes=list(lane.get("phase_notes") or []),
            stage_notes=list(lane.get("stage_notes") or []),
            materialize_notes=list(lane.get("materialize_notes") or []),
            launch_notes=list(lane.get("launch_notes") or []),
        )

    def _observe_status(self, *, lane: dict[str, Any], target: str, worktree_path: Path, packet_paths: ObservePacketPaths, dependencies: list[ObserveDependency]) -> tuple[str, str, str, list[ObserveEvidence]]:
        evidence = self._base_evidence(lane=lane, packet_paths=packet_paths, worktree_path=worktree_path)
        source_state = str(lane.get("state") or "")
        if source_state == "waiting" or dependencies:
            return "waiting", str(lane.get("state_reason") or "Serialized lane is still waiting on earlier dependency lanes."), "Finish the prerequisite lanes, then rerun materialize, launch, and observe.", evidence
        if source_state == "blocked":
            return "blocked", str(lane.get("state_reason") or "Launch planning marked this lane blocked."), "Repair the blocked launch or materialize artifact before trying again.", evidence
        result_path = Path(packet_paths.observe_result_path)
        if result_path.exists():
            result = self._load_json(result_path)
            status, reason, next_action = self._status_from_result(result=result, lane_id=str(lane.get("lane_id") or ""), target=target)
            evidence.append(ObserveEvidence(kind="observe-result", status="present", detail=reason, path=str(result_path)))
            return status, reason, next_action, evidence
        if source_state == "launched":
            return "running", "Launch command completed but no explicit lane outcome packet is saved yet.", "Wait for the builder to save `.agentkit/observe/result.json`, then rerun observe.", evidence
        if source_state == "ready":
            return "unknown", "Lane is launchable but no observed outcome packet exists yet.", "Launch the lane or save an observe result packet before relying on status.", evidence
        return "unknown", "No deterministic observe result is available from the saved launch/worktree state.", "Inspect the lane manually and save an explicit observe result packet.", evidence

    def _base_evidence(self, *, lane: dict[str, Any], packet_paths: ObservePacketPaths, worktree_path: Path) -> list[ObserveEvidence]:
        return [
            ObserveEvidence(kind="launch-state", status=str(lane.get("state") or "unknown"), detail=str(lane.get("state_reason") or "Saved launch state.")),
            ObserveEvidence(kind="worktree", status="present" if worktree_path.exists() else "missing", detail="Materialized lane worktree path.", path=str(worktree_path)),
            ObserveEvidence(kind="handoff", status="present" if Path(packet_paths.handoff_markdown_path).exists() else "missing", detail="Saved launch handoff markdown.", path=packet_paths.handoff_markdown_path),
            ObserveEvidence(kind="materialize-metadata", status="present" if Path(packet_paths.materialize_metadata_path).exists() else "missing", detail="Saved materialize lane metadata.", path=packet_paths.materialize_metadata_path),
        ]

    def _status_from_result(self, *, result: dict[str, Any], lane_id: str, target: str) -> tuple[str, str, str]:
        if str(result.get("schema_version") or "") != "agentkit.observe.lane-result.v1":
            raise ObserveError("Saved observe result is not a supported agentkit.observe.lane-result.v1 packet.")
        if str(result.get("lane_id") or "") != lane_id:
            raise ObserveError(f"Saved observe result points at {result.get('lane_id')!r}, expected {lane_id!r}.")
        result_target = str(result.get("target") or "")
        if result_target and result_target != target:
            raise ObserveError(f"Saved observe result target {result_target!r} does not match observe target {target!r}.")
        status = str(result.get("status") or "").strip().lower()
        if status not in _OBSERVE_STATUSES - {"waiting", "blocked", "unknown"}:
            raise ObserveError("Saved observe result status must be one of: success, failure, running.")
        summary = str(result.get("summary") or "").strip() or "Saved observe result packet."
        if status == "success":
            return status, summary, "Review the delivered lane output and merge or continue orchestration."
        if status == "failure":
            return status, summary, "Inspect the saved failure evidence, fix the lane, then relaunch if needed."
        return status, summary, "Wait for the running lane to finish and rewrite the observe result packet."

    def _resolve_packet_paths(self, lane: dict[str, Any], worktree_path: Path) -> ObservePacketPaths:
        packet_paths = lane.get("packet_paths") or {}
        handoff = Path(str(packet_paths.get("handoff_markdown_path") or (worktree_path / ".agentkit" / "materialize" / "handoff.md"))).expanduser().resolve()
        materialize_metadata = Path(str(packet_paths.get("materialize_metadata_path") or packet_paths.get("metadata_json_path") or (worktree_path / ".agentkit" / "materialize" / "materialize.json"))).expanduser().resolve()
        stage_json = Path(str(packet_paths.get("stage_json_path") or packet_paths.get("copied_stage_json_path") or (worktree_path / ".agentkit" / "materialize" / "stage.json"))).expanduser().resolve()
        stage_markdown = Path(str(packet_paths.get("stage_markdown_path") or packet_paths.get("copied_stage_markdown_path") or (worktree_path / ".agentkit" / "materialize" / "stage.md"))).expanduser().resolve()
        observe_result = worktree_path / ".agentkit" / "observe" / "result.json"
        return ObservePacketPaths(
            handoff_markdown_path=str(handoff),
            materialize_metadata_path=str(materialize_metadata),
            observe_result_path=str(observe_result.resolve()),
            stage_json_path=str(stage_json),
            stage_markdown_path=str(stage_markdown),
        )

    def _plan_from_actions(self, *, launch: dict[str, Any], launch_path: Path, project_path: Path, target: str, actions: list[ObserveAction]) -> ObservePlan:
        buckets = {status: [item.lane_id for item in actions if item.status == status] for status in _OBSERVE_STATUSES}
        recommended: list[str] = []
        if buckets["failure"]:
            recommended.append(f"Investigate failed lanes first: {', '.join(buckets['failure'])}.")
        if buckets["blocked"]:
            recommended.append(f"Repair blocked artifacts before any relaunch: {', '.join(buckets['blocked'])}.")
        if buckets["running"]:
            recommended.append(f"Wait for running lanes to emit explicit observe results: {', '.join(buckets['running'])}.")
        if buckets["waiting"]:
            recommended.append(f"Keep waiting lanes paused behind dependencies: {', '.join(buckets['waiting'])}.")
        if buckets["unknown"]:
            recommended.append(f"Unknown lanes need an explicit result packet or manual review: {', '.join(buckets['unknown'])}.")
        if buckets["success"] and len(buckets["success"]) == len(actions):
            recommended.append("All observed lanes are successful. The orchestrator can advance to merge or closeout.")
        summary_counts = {status: len(buckets[status]) for status in sorted(_OBSERVE_STATUSES)}
        return ObservePlan(
            schema_version="agentkit.observe.v1",
            project_path=str(project_path),
            target=target,
            launch_path=str(launch_path),
            observed_lane_ids=[item.lane_id for item in actions],
            success_lane_ids=buckets["success"],
            failure_lane_ids=buckets["failure"],
            running_lane_ids=buckets["running"],
            waiting_lane_ids=buckets["waiting"],
            blocked_lane_ids=buckets["blocked"],
            unknown_lane_ids=buckets["unknown"],
            summary_counts=summary_counts,
            recommended_next_actions=recommended or ["No lanes were available to observe."],
            actions=actions,
            source_launch=launch,
        )

    def _load_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ObserveError(f"Saved observe evidence is malformed JSON: {path}") from exc

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in _SUPPORTED_TARGETS:
            raise ObserveError("target must be one of: generic, codex, claude-code")
        return value


class LaunchArtifactLoader:
    def load(self, project_dir: str | Path) -> tuple[Path | None, dict[str, Any] | None]:
        root = Path(project_dir).expanduser().resolve()
        for candidate in self._candidates(root):
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), json.loads(candidate.read_text(encoding="utf-8"))
        return None, None

    def _candidates(self, root: Path) -> list[Path]:
        direct = [
            root / "launch.json",
            root / ".agentkit" / "launch.json",
            root / "artifacts" / "launch.json",
            root / "launch" / "launch.json",
            root / "observe" / "launch.json",
        ]
        packet_dirs = sorted([path for path in root.iterdir() if path.is_dir() and path.name.startswith(("observe", "launch", "packet", "handoff"))], key=lambda path: path.name) if root.exists() else []
        return direct + [path / "launch.json" for path in packet_dirs]
