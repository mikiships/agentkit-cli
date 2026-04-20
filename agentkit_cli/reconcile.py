from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentkit_cli.observe import ObserveEngine, ObserveError
from agentkit_cli.supervise import SuperviseEngine, SuperviseError

_RECONCILE_BUCKETS = {
    "blocked",
    "complete",
    "drifted",
    "needs-human-review",
    "ready",
    "relaunch-ready",
    "still-running",
    "waiting",
}


class ReconcileError(Exception):
    pass


@dataclass(frozen=True)
class ReconcileDependency:
    lane_id: str
    reason: str
    satisfied: bool

    def to_dict(self) -> dict[str, object]:
        return {"lane_id": self.lane_id, "reason": self.reason, "satisfied": self.satisfied}


@dataclass(frozen=True)
class ReconcileLane:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_path: str
    bucket: str
    reason: str
    next_action: str
    dependencies: list[ReconcileDependency] = field(default_factory=list)
    observe_status: str | None = None
    observe_reason: str | None = None
    supervise_state: str | None = None
    supervise_reason: str | None = None
    newly_unblocked: bool = False
    launch_state: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_name": self.branch_name,
            "bucket": self.bucket,
            "dependencies": [item.to_dict() for item in self.dependencies],
            "lane_id": self.lane_id,
            "launch_state": self.launch_state,
            "newly_unblocked": self.newly_unblocked,
            "next_action": self.next_action,
            "observe_reason": self.observe_reason,
            "observe_status": self.observe_status,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "reason": self.reason,
            "serialization_group": self.serialization_group,
            "supervise_reason": self.supervise_reason,
            "supervise_state": self.supervise_state,
            "title": self.title,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class ReconcilePlan:
    schema_version: str
    project_path: str
    target: str
    launch_path: str
    observe_path: str | None
    supervise_path: str | None
    complete_lane_ids: list[str] = field(default_factory=list)
    relaunch_ready_lane_ids: list[str] = field(default_factory=list)
    ready_lane_ids: list[str] = field(default_factory=list)
    still_running_lane_ids: list[str] = field(default_factory=list)
    waiting_lane_ids: list[str] = field(default_factory=list)
    blocked_lane_ids: list[str] = field(default_factory=list)
    drifted_lane_ids: list[str] = field(default_factory=list)
    needs_human_review_lane_ids: list[str] = field(default_factory=list)
    newly_unblocked_lane_ids: list[str] = field(default_factory=list)
    next_execution_order: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    lanes: list[ReconcileLane] = field(default_factory=list)
    source_launch: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "blocked_lane_ids": list(self.blocked_lane_ids),
            "complete_lane_ids": list(self.complete_lane_ids),
            "drifted_lane_ids": list(self.drifted_lane_ids),
            "launch_path": self.launch_path,
            "lanes": [item.to_dict() for item in self.lanes],
            "needs_human_review_lane_ids": list(self.needs_human_review_lane_ids),
            "newly_unblocked_lane_ids": list(self.newly_unblocked_lane_ids),
            "next_actions": list(self.next_actions),
            "next_execution_order": list(self.next_execution_order),
            "observe_path": self.observe_path,
            "project_path": self.project_path,
            "ready_lane_ids": list(self.ready_lane_ids),
            "relaunch_ready_lane_ids": list(self.relaunch_ready_lane_ids),
            "schema_version": self.schema_version,
            "source_launch": self.source_launch,
            "still_running_lane_ids": list(self.still_running_lane_ids),
            "supervise_path": self.supervise_path,
            "target": self.target,
            "waiting_lane_ids": list(self.waiting_lane_ids),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class ReconcileEngine:
    def __init__(self) -> None:
        self._observe = ObserveEngine()
        self._supervise = SuperviseEngine()

    def build(self, project_dir: str | Path, *, launch_path: str | Path | None = None) -> ReconcilePlan:
        root = Path(project_dir).expanduser().resolve()
        try:
            supervise_plan = self._supervise.build(root, launch_path=launch_path)
        except (FileNotFoundError, SuperviseError) as exc:
            raise ReconcileError(str(exc)) from exc
        try:
            observe_plan = self._observe.build(root, target=supervise_plan.target)
        except (FileNotFoundError, ObserveError):
            observe_plan = None

        observe_by_lane = {item.lane_id: item for item in (observe_plan.actions if observe_plan else [])}
        supervise_by_lane = {item.lane_id: item for item in supervise_plan.lanes}
        launch = supervise_plan.source_launch
        lanes: list[ReconcileLane] = []
        completed_ids: set[str] = set()

        for action in sorted(launch.get("actions") or [], key=lambda item: (int(item.get("phase_index") or 0), str(item.get("lane_id") or ""))):
            lane_id = str(action.get("lane_id") or "")
            supervise_lane = supervise_by_lane.get(lane_id)
            observe_lane = observe_by_lane.get(lane_id)
            dependencies = [
                ReconcileDependency(
                    lane_id=str(dep.get("lane_id") or ""),
                    reason=str(dep.get("reason") or ""),
                    satisfied=str(dep.get("lane_id") or "") in completed_ids,
                )
                for dep in sorted(action.get("dependencies") or [], key=lambda item: (str(item.get("lane_id") or ""), str(item.get("reason") or "")))
            ]
            bucket, reason, next_action = self._classify(action, observe_lane, supervise_lane, dependencies)
            newly_unblocked = bool(getattr(supervise_lane, "newly_unblocked", False)) or (
                bucket == "ready" and str(action.get("state") or "") == "waiting" and bool(dependencies) and all(dep.satisfied for dep in dependencies)
            )
            lane = ReconcileLane(
                lane_id=lane_id,
                title=str(action.get("title") or lane_id),
                phase_id=str(action.get("phase_id") or "phase-00"),
                phase_index=int(action.get("phase_index") or 0),
                serialization_group=str(action.get("serialization_group") or ""),
                branch_name=str(action.get("branch_name") or ""),
                worktree_path=str(action.get("worktree_path") or ""),
                bucket=bucket,
                reason=reason,
                next_action=next_action,
                dependencies=dependencies,
                observe_status=getattr(observe_lane, "status", None),
                observe_reason=getattr(observe_lane, "status_reason", None),
                supervise_state=getattr(supervise_lane, "state", None),
                supervise_reason=getattr(supervise_lane, "reason", None),
                newly_unblocked=newly_unblocked,
                launch_state=str(action.get("state") or ""),
            )
            lanes.append(lane)
            if bucket == "complete":
                completed_ids.add(lane_id)

        buckets = {bucket: [lane.lane_id for lane in lanes if lane.bucket == bucket] for bucket in sorted(_RECONCILE_BUCKETS)}
        next_execution_order = [
            lane.lane_id
            for lane in lanes
            if lane.bucket in {"ready", "relaunch-ready"} and all(dep.satisfied for dep in lane.dependencies)
        ]
        next_actions: list[str] = []
        if buckets["blocked"]:
            next_actions.append(f"Repair blocked lanes first: {', '.join(buckets['blocked'])}.")
        if buckets["drifted"]:
            next_actions.append(f"Repair drifted worktrees before trusting progress: {', '.join(buckets['drifted'])}.")
        if buckets["still-running"]:
            next_actions.append(f"Wait for active lanes to finish or save explicit results: {', '.join(buckets['still-running'])}.")
        if buckets["needs-human-review"]:
            next_actions.append(f"Review ambiguous lanes manually before auto-advancing: {', '.join(buckets['needs-human-review'])}.")
        if next_execution_order:
            next_actions.append(f"Next safe execution order: {', '.join(next_execution_order)}.")
        elif not next_actions:
            next_actions.append("No further execution is safe yet from the current local evidence.")

        return ReconcilePlan(
            schema_version="agentkit.reconcile.v1",
            project_path=supervise_plan.project_path,
            target=supervise_plan.target,
            launch_path=supervise_plan.launch_path,
            observe_path=self._find_saved_artifact(root, "observe"),
            supervise_path=self._find_saved_artifact(root, "supervise"),
            complete_lane_ids=buckets["complete"],
            relaunch_ready_lane_ids=buckets["relaunch-ready"],
            ready_lane_ids=buckets["ready"],
            still_running_lane_ids=buckets["still-running"],
            waiting_lane_ids=buckets["waiting"],
            blocked_lane_ids=buckets["blocked"],
            drifted_lane_ids=buckets["drifted"],
            needs_human_review_lane_ids=buckets["needs-human-review"],
            newly_unblocked_lane_ids=[lane.lane_id for lane in lanes if lane.newly_unblocked],
            next_execution_order=next_execution_order,
            next_actions=next_actions,
            lanes=lanes,
            source_launch=launch,
        )

    def render_markdown(self, plan: ReconcilePlan) -> str:
        lines = [
            f"# Reconcile plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Launch packet: `{plan.launch_path}`",
            f"- Observe packet: `{plan.observe_path or 'not found'}`",
            f"- Supervise packet: `{plan.supervise_path or 'not found'}`",
            "",
            "## Summary",
            "",
            f"- Complete: {', '.join(plan.complete_lane_ids) if plan.complete_lane_ids else 'none'}",
            f"- Relaunch-ready: {', '.join(plan.relaunch_ready_lane_ids) if plan.relaunch_ready_lane_ids else 'none'}",
            f"- Ready: {', '.join(plan.ready_lane_ids) if plan.ready_lane_ids else 'none'}",
            f"- Still running: {', '.join(plan.still_running_lane_ids) if plan.still_running_lane_ids else 'none'}",
            f"- Waiting: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Blocked: {', '.join(plan.blocked_lane_ids) if plan.blocked_lane_ids else 'none'}",
            f"- Drifted: {', '.join(plan.drifted_lane_ids) if plan.drifted_lane_ids else 'none'}",
            f"- Needs human review: {', '.join(plan.needs_human_review_lane_ids) if plan.needs_human_review_lane_ids else 'none'}",
            f"- Newly unblocked: {', '.join(plan.newly_unblocked_lane_ids) if plan.newly_unblocked_lane_ids else 'none'}",
            f"- Next safe execution order: {', '.join(plan.next_execution_order) if plan.next_execution_order else 'none'}",
            "",
            "## Next actions",
            "",
        ]
        for item in plan.next_actions:
            lines.append(f"- {item}")
        lines.extend(["", "## Lanes", ""])
        for lane in plan.lanes:
            lines.extend([
                f"### {lane.lane_id}: {lane.title}",
                "",
                f"- Bucket: `{lane.bucket}`",
                f"- Reason: {lane.reason}",
                f"- Next action: {lane.next_action}",
                f"- Launch state: `{lane.launch_state}`",
                f"- Observe status: `{lane.observe_status or 'missing'}`",
                f"- Supervise state: `{lane.supervise_state or 'missing'}`",
                f"- Worktree path: `{lane.worktree_path}`",
                f"- Branch: `{lane.branch_name}`",
            ])
            if lane.dependencies:
                lines.append(
                    "- Dependencies: " + ", ".join(f"{dep.lane_id} ({'satisfied' if dep.satisfied else 'pending'})" for dep in lane.dependencies)
                )
            else:
                lines.append("- Dependencies: none")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: ReconcilePlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "reconcile.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "reconcile.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "reconcile.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "reconcile.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: ReconcileLane) -> str:
        lines = [
            f"# Reconcile lane: {lane.lane_id}",
            "",
            f"- Bucket: `{lane.bucket}`",
            f"- Reason: {lane.reason}",
            f"- Next action: {lane.next_action}",
            f"- Observe status: `{lane.observe_status or 'missing'}`",
            f"- Supervise state: `{lane.supervise_state or 'missing'}`",
            f"- Worktree path: `{lane.worktree_path}`",
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _classify(self, action: dict[str, Any], observe_lane: Any | None, supervise_lane: Any | None, dependencies: list[ReconcileDependency]) -> tuple[str, str, str]:
        launch_state = str(action.get("state") or "")
        observe_status = getattr(observe_lane, "status", None)
        supervise_state = getattr(supervise_lane, "state", None)
        if launch_state == "launched" and observe_status in {None, "running"} and supervise_state != "completed":
            return "needs-human-review", "Launch recorded this lane as started, but no stable completion evidence was saved.", "Inspect the lane manually or save fresh observe/supervise artifacts before continuing."
        if observe_status == "failure" and supervise_state == "running":
            return "needs-human-review", getattr(observe_lane, "status_reason", "Lane failed and still has uncommitted local work."), "Inspect the dirty worktree manually before deciding whether to relaunch or salvage it."
        if supervise_state == "blocked":
            if str(action.get("state") or "") == "waiting" and dependencies and all(dep.satisfied for dep in dependencies):
                return "ready", f"Dependencies for {str(action.get('lane_id') or '')} are complete, so this serialized lane is now launchable.", "Re-run materialize to create the newly unblocked worktree, then launch the lane.",
            return "blocked", getattr(supervise_lane, "reason", "Lane is blocked."), getattr(supervise_lane, "next_action", "Repair the lane before continuing.")
        if supervise_state == "drifted":
            return "drifted", getattr(supervise_lane, "reason", "Lane worktree drifted."), getattr(supervise_lane, "next_action", "Repair the lane worktree before continuing.")
        if supervise_state == "completed" or observe_status == "success":
            return "complete", getattr(supervise_lane, "reason", getattr(observe_lane, "status_reason", "Lane completed successfully.")), "Use the completed lane to continue merge or serialized follow-on work."
        if observe_status == "failure":
            if supervise_state in {"ready", None}:
                return "relaunch-ready", getattr(observe_lane, "status_reason", "Lane failed and is ready for another pass."), "Fix the failure and relaunch this lane when ready."
            return "needs-human-review", getattr(observe_lane, "status_reason", "Lane failed but local state is ambiguous."), "Inspect the lane manually before relaunching."
        if observe_status == "running" or supervise_state == "running":
            return "still-running", getattr(observe_lane, "status_reason", getattr(supervise_lane, "reason", "Lane is still in progress.")), "Wait for the lane to finish and save stable output before advancing."
        if supervise_state == "waiting":
            return "waiting", getattr(supervise_lane, "reason", "Lane is still waiting on dependencies."), getattr(supervise_lane, "next_action", "Finish earlier lanes first.")
        if supervise_state == "ready":
            if dependencies and not all(dep.satisfied for dep in dependencies):
                return "waiting", "Dependencies are not complete yet.", "Finish prerequisite lanes before launching this one."
            if getattr(supervise_lane, "newly_unblocked", False):
                return "ready", getattr(supervise_lane, "reason", "Lane is newly unblocked and safe to launch."), "Launch this newly unblocked lane in the next safe slot."
            return "ready", getattr(supervise_lane, "reason", "Lane is ready to launch."), getattr(supervise_lane, "next_action", "Launch this lane when ready.")
        if launch_state == "blocked":
            return "blocked", str(action.get("state_reason") or "Launch marked this lane blocked."), "Repair the launch prerequisites before continuing."
        if launch_state == "waiting":
            return "waiting", str(action.get("state_reason") or "Launch marked this lane waiting."), "Finish prerequisite lanes before launching this one."
        return "needs-human-review", "No saved observe or supervise evidence was strong enough to auto-advance this lane.", "Inspect the lane manually, then save observe/supervise artifacts or relaunch intentionally."

    def _find_saved_artifact(self, root: Path, stem: str) -> str | None:
        candidates = [
            root / f"{stem}.json",
            root / stem / f"{stem}.json",
            root / "artifacts" / f"{stem}.json",
            root / ".agentkit" / f"{stem}.json",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())
        return None
