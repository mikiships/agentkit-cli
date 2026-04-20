from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class SuperviseError(Exception):
    pass


@dataclass(frozen=True)
class LaneDependencyStatus:
    lane_id: str
    reason: str
    satisfied: bool
    dependency_state: str

    def to_dict(self) -> dict[str, object]:
        return {
            "dependency_state": self.dependency_state,
            "lane_id": self.lane_id,
            "reason": self.reason,
            "satisfied": self.satisfied,
        }


@dataclass(frozen=True)
class GitSummary:
    branch: str | None
    head: str | None
    base_commit: str | None
    dirty: bool
    detached_head: bool
    branch_mismatch: bool
    worktree_missing: bool
    uncommitted_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "base_commit": self.base_commit,
            "branch": self.branch,
            "branch_mismatch": self.branch_mismatch,
            "detached_head": self.detached_head,
            "dirty": self.dirty,
            "head": self.head,
            "uncommitted_files": list(self.uncommitted_files),
            "worktree_missing": self.worktree_missing,
        }


@dataclass(frozen=True)
class SuperviseLane:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    serialization_group: str
    branch_name: str
    worktree_path: str
    packet_path: str
    state: str
    reason: str
    next_action: str
    newly_unblocked: bool
    owned_paths: list[str] = field(default_factory=list)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    dependency_status: list[LaneDependencyStatus] = field(default_factory=list)
    launch_state: str = ""
    launch_state_reason: str = ""
    git_summary: GitSummary | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "branch_name": self.branch_name,
            "dependencies": list(self.dependencies),
            "dependency_status": [item.to_dict() for item in self.dependency_status],
            "git_summary": self.git_summary.to_dict() if self.git_summary else None,
            "lane_id": self.lane_id,
            "launch_state": self.launch_state,
            "launch_state_reason": self.launch_state_reason,
            "newly_unblocked": self.newly_unblocked,
            "next_action": self.next_action,
            "owned_paths": list(self.owned_paths),
            "packet_path": self.packet_path,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "reason": self.reason,
            "serialization_group": self.serialization_group,
            "state": self.state,
            "title": self.title,
            "worktree_path": self.worktree_path,
        }


@dataclass(frozen=True)
class SupervisePlan:
    schema_version: str
    project_path: str
    launch_path: str
    target: str
    summary_path: str
    output_dir: str | None
    ready_lane_ids: list[str] = field(default_factory=list)
    running_lane_ids: list[str] = field(default_factory=list)
    waiting_lane_ids: list[str] = field(default_factory=list)
    blocked_lane_ids: list[str] = field(default_factory=list)
    completed_lane_ids: list[str] = field(default_factory=list)
    drifted_lane_ids: list[str] = field(default_factory=list)
    newly_unblocked_lane_ids: list[str] = field(default_factory=list)
    instructions: list[str] = field(default_factory=list)
    lanes: list[SuperviseLane] = field(default_factory=list)
    source_launch: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "blocked_lane_ids": list(self.blocked_lane_ids),
            "completed_lane_ids": list(self.completed_lane_ids),
            "drifted_lane_ids": list(self.drifted_lane_ids),
            "instructions": list(self.instructions),
            "lanes": [item.to_dict() for item in self.lanes],
            "launch_path": self.launch_path,
            "newly_unblocked_lane_ids": list(self.newly_unblocked_lane_ids),
            "output_dir": self.output_dir,
            "project_path": self.project_path,
            "ready_lane_ids": list(self.ready_lane_ids),
            "running_lane_ids": list(self.running_lane_ids),
            "schema_version": self.schema_version,
            "source_launch": self.source_launch,
            "summary_path": self.summary_path,
            "target": self.target,
            "waiting_lane_ids": list(self.waiting_lane_ids),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class SuperviseEngine:
    def __init__(self) -> None:
        self._loader = LaunchArtifactLoader()

    def build(self, project_dir: str | Path, *, launch_path: str | Path | None = None) -> SupervisePlan:
        root = Path(project_dir).expanduser().resolve()
        resolved_launch_path, launch = self._loader.load(root, launch_path=launch_path)
        if resolved_launch_path is None or launch is None:
            raise FileNotFoundError(
                "No launch.json artifact found. Save a launch packet first, then run agentkit supervise."
            )
        if str(launch.get("schema_version") or "") != "agentkit.launch.v1":
            raise SuperviseError("Saved launch artifact is not a supported agentkit.launch.v1 packet.")

        project_path = Path(launch.get("project_path") or root).expanduser().resolve()
        summary_path = resolved_launch_path.parent / "supervise.md"
        output_dir = str(resolved_launch_path.parent) if resolved_launch_path.parent != root else None

        provisional: list[dict[str, Any]] = []
        for lane in sorted(launch.get("actions") or [], key=lambda item: (int(item.get("phase_index") or 0), str(item.get("lane_id") or ""))):
            packet_path = self._packet_path_from_launch(resolved_launch_path, lane)
            worktree_path = Path(str(lane.get("worktree_path") or "")).expanduser().resolve()
            git_summary = self._git_summary(worktree_path, expected_branch=str(lane.get("branch_name") or ""))
            provisional.append({
                "lane": lane,
                "packet_path": packet_path,
                "git_summary": git_summary,
            })

        states_by_lane: dict[str, str] = {}
        lanes: list[SuperviseLane] = []
        for item in provisional:
            lane = item["lane"]
            lane_id = str(lane.get("lane_id") or "")
            dep_status = self._dependency_status(lane.get("dependencies") or [], states_by_lane)
            state, reason, next_action, newly_unblocked = self._classify_lane(
                lane=lane,
                packet_path=item["packet_path"],
                git_summary=item["git_summary"],
                dependency_status=dep_status,
            )
            states_by_lane[lane_id] = state
            lanes.append(
                SuperviseLane(
                    lane_id=lane_id,
                    title=str(lane.get("title") or lane_id),
                    phase_id=str(lane.get("phase_id") or "phase-00"),
                    phase_index=int(lane.get("phase_index") or 0),
                    serialization_group=str(lane.get("serialization_group") or ""),
                    branch_name=str(lane.get("branch_name") or ""),
                    worktree_path=str(Path(str(lane.get("worktree_path") or "")).expanduser().resolve()),
                    packet_path=str(item["packet_path"]),
                    state=state,
                    reason=reason,
                    next_action=next_action,
                    newly_unblocked=newly_unblocked,
                    owned_paths=list(lane.get("owned_paths") or []),
                    dependencies=list(lane.get("dependencies") or []),
                    dependency_status=dep_status,
                    launch_state=str(lane.get("state") or ""),
                    launch_state_reason=str(lane.get("state_reason") or ""),
                    git_summary=item["git_summary"],
                )
            )

        ready = [item.lane_id for item in lanes if item.state == "ready"]
        running = [item.lane_id for item in lanes if item.state == "running"]
        waiting = [item.lane_id for item in lanes if item.state == "waiting"]
        blocked = [item.lane_id for item in lanes if item.state == "blocked"]
        completed = [item.lane_id for item in lanes if item.state == "completed"]
        drifted = [item.lane_id for item in lanes if item.state == "drifted"]
        newly_unblocked = [item.lane_id for item in lanes if item.newly_unblocked]

        instructions = [
            "Supervision is local-only and observational: it reads saved launch artifacts plus local git/worktree state.",
            "This command never launches, kills, pushes, tags, or mutates remote state.",
        ]
        if newly_unblocked:
            instructions.append(
                f"Serialized waiting lanes are now unblocked and can be launched next: {', '.join(newly_unblocked)}."
            )
        if blocked:
            instructions.append(f"Blocked lanes need local artifact or worktree repair: {', '.join(blocked)}.")
        if drifted:
            instructions.append(f"Drifted lanes need branch/HEAD repair before trusting handoff status: {', '.join(drifted)}.")

        return SupervisePlan(
            schema_version="agentkit.supervise.v1",
            project_path=str(project_path),
            launch_path=str(resolved_launch_path),
            target=str(launch.get("target") or "generic"),
            summary_path=str(summary_path),
            output_dir=output_dir,
            ready_lane_ids=ready,
            running_lane_ids=running,
            waiting_lane_ids=waiting,
            blocked_lane_ids=blocked,
            completed_lane_ids=completed,
            drifted_lane_ids=drifted,
            newly_unblocked_lane_ids=newly_unblocked,
            instructions=instructions,
            lanes=lanes,
            source_launch=launch,
        )

    def render_markdown(self, plan: SupervisePlan) -> str:
        lines = [
            f"# Supervision summary: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Launch packet: `{plan.launch_path}`",
            "",
            "## Summary",
            "",
            f"- Ready lanes: {', '.join(plan.ready_lane_ids) if plan.ready_lane_ids else 'none'}",
            f"- Running lanes: {', '.join(plan.running_lane_ids) if plan.running_lane_ids else 'none'}",
            f"- Waiting lanes: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Completed lanes: {', '.join(plan.completed_lane_ids) if plan.completed_lane_ids else 'none'}",
            f"- Blocked lanes: {', '.join(plan.blocked_lane_ids) if plan.blocked_lane_ids else 'none'}",
            f"- Drifted lanes: {', '.join(plan.drifted_lane_ids) if plan.drifted_lane_ids else 'none'}",
            f"- Newly unblocked lanes: {', '.join(plan.newly_unblocked_lane_ids) if plan.newly_unblocked_lane_ids else 'none'}",
            "",
            "## Instructions",
            "",
        ]
        for item in plan.instructions:
            lines.append(f"- {item}")
        lines.extend(["", "## Lanes", ""])
        for lane in plan.lanes:
            lines.append(f"### {lane.lane_id}: {lane.title}")
            lines.append("")
            lines.append(f"- State: `{lane.state}`")
            lines.append(f"- Reason: {lane.reason}")
            lines.append(f"- Next action: {lane.next_action}")
            lines.append(f"- Worktree path: `{lane.worktree_path}`")
            lines.append(f"- Branch: `{lane.branch_name}`")
            lines.append(f"- Launch packet: `{lane.packet_path}`")
            if lane.newly_unblocked:
                lines.append("- Newly unblocked: yes")
            if lane.dependency_status:
                lines.append(
                    "- Dependency status: "
                    + ", ".join(
                        f"{item.lane_id}={item.dependency_state} ({'satisfied' if item.satisfied else 'pending'})"
                        for item in lane.dependency_status
                    )
                )
            else:
                lines.append("- Dependency status: none")
            if lane.git_summary is not None:
                lines.append(
                    f"- Git summary: branch={lane.git_summary.branch or '(detached)'}; head={lane.git_summary.head or '(missing)'}; dirty={'yes' if lane.git_summary.dirty else 'no'}"
                )
                if lane.git_summary.uncommitted_files:
                    lines.append(f"- Uncommitted files: {', '.join(lane.git_summary.uncommitted_files)}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: SupervisePlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "supervise.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "supervise.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "supervise.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "supervise.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: SuperviseLane) -> str:
        lines = [
            f"# Supervision lane: {lane.lane_id}",
            "",
            f"- State: `{lane.state}`",
            f"- Reason: {lane.reason}",
            f"- Next action: {lane.next_action}",
            f"- Worktree path: `{lane.worktree_path}`",
            f"- Branch: `{lane.branch_name}`",
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _dependency_status(self, dependencies: list[dict[str, Any]], states_by_lane: dict[str, str]) -> list[LaneDependencyStatus]:
        result: list[LaneDependencyStatus] = []
        for item in sorted(dependencies, key=lambda value: (str(value.get("lane_id") or ""), str(value.get("reason") or ""))):
            lane_id = str(item.get("lane_id") or "")
            state = states_by_lane.get(lane_id, "unknown")
            satisfied = state == "completed"
            result.append(
                LaneDependencyStatus(
                    lane_id=lane_id,
                    reason=str(item.get("reason") or ""),
                    satisfied=satisfied,
                    dependency_state=state,
                )
            )
        return result

    def _classify_lane(
        self,
        *,
        lane: dict[str, Any],
        packet_path: Path,
        git_summary: GitSummary,
        dependency_status: list[LaneDependencyStatus],
    ) -> tuple[str, str, str, bool]:
        lane_id = str(lane.get("lane_id") or "")
        if not packet_path.exists():
            return "blocked", f"Expected launch lane packet is missing: {packet_path}", "Rebuild launch artifacts, then rerun supervise.", False
        if dependency_status and not all(item.satisfied for item in dependency_status):
            return "waiting", "Serialized dependencies are still incomplete.", "Wait for dependency lanes to complete, then rerun supervise.", False
        if git_summary.worktree_missing:
            if dependency_status and all(item.satisfied for item in dependency_status):
                return "ready", f"Dependencies for {lane_id} are complete, so this serialized lane is now launchable.", "Re-run materialize to create the newly unblocked worktree, then launch the lane.", True
            if str(lane.get("state") or "") == "waiting":
                return "waiting", str(lane.get("state_reason") or "Serialized lane is still waiting for its turn to materialize."), "Finish earlier serialized lanes, then rerun supervise.", False
            return "blocked", f"Expected materialized worktree is missing: {Path(str(lane.get('worktree_path') or '')).expanduser().resolve()}", "Re-run materialize or restore the missing worktree.", False
        newly_unblocked = bool(dependency_status) and all(item.satisfied for item in dependency_status)
        if git_summary.detached_head:
            return "drifted", "Lane worktree is on a detached HEAD.", "Reattach the expected branch before trusting or relaunching this lane.", False
        if git_summary.branch_mismatch:
            return "drifted", f"Lane branch drifted from expected branch {lane.get('branch_name')!r}.", "Switch back to the expected branch or rebuild the lane worktree.", False
        if git_summary.dirty:
            return "running", "Local uncommitted changes indicate active in-progress work.", "Keep working or commit the lane changes when finished.", newly_unblocked
        if git_summary.base_commit and git_summary.head and git_summary.head != git_summary.base_commit:
            return "completed", "HEAD advanced beyond the materialized base commit and the worktree is clean.", "Review, merge, or use this completed lane to unblock the next serialized lane.", newly_unblocked
        if str(lane.get("launch_state") or lane.get("state") or "") == "blocked":
            return "blocked", str(lane.get("state_reason") or "Launch marked this lane blocked."), "Repair the saved launch prerequisites before continuing.", False
        if newly_unblocked:
            return "ready", f"Dependencies for {lane_id} are complete, so this serialized lane is now launchable.", "Launch this newly unblocked lane when you are ready.", True
        return "ready", "Lane is materialized locally and has not started yet.", "Launch the saved command or handoff packet from this worktree.", False

    def _packet_path_from_launch(self, launch_path: Path, lane: dict[str, Any]) -> Path:
        explicit = lane.get("packet_paths") or {}
        handoff = explicit.get("handoff_markdown_path")
        lane_id = str(lane.get("lane_id") or "")
        candidate = launch_path.parent / "lanes" / lane_id / "launch.json"
        if candidate.exists():
            return candidate.resolve()
        if handoff:
            return Path(str(handoff)).expanduser().resolve()
        return candidate.resolve()

    def _git_summary(self, worktree_path: Path, *, expected_branch: str) -> GitSummary:
        if not worktree_path.exists():
            return GitSummary(None, None, None, False, False, False, True, [])
        metadata_path = worktree_path / ".agentkit" / "materialize" / "materialize.json"
        base_commit = None
        if metadata_path.exists():
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            base_commit = str(payload.get("base_commit") or "") or None
        head = self._git_stdout(worktree_path, ["rev-parse", "--verify", "HEAD"])
        branch = self._git_stdout(worktree_path, ["symbolic-ref", "--short", "-q", "HEAD"], allow_failure=True)
        status = self._git_stdout(worktree_path, ["status", "--short"], allow_failure=True) or ""
        files = [line[3:] if len(line) > 3 else line for line in status.splitlines() if line.strip()]
        files = [
            item
            for item in files
            if not item.startswith('.agentkit/materialize')
            and not item.startswith('.agentkit/observe')
            and not item.startswith('.agentkit/supervise')
        ]
        detached = branch in {None, ""}
        branch_mismatch = bool(branch and expected_branch and branch != expected_branch)
        return GitSummary(
            branch=branch or None,
            head=head or None,
            base_commit=base_commit,
            dirty=bool(files),
            detached_head=detached,
            branch_mismatch=branch_mismatch,
            worktree_missing=False,
            uncommitted_files=files,
        )

    def _git_stdout(self, cwd: Path, args: list[str], allow_failure: bool = False) -> str | None:
        result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
        if result.returncode != 0:
            if allow_failure:
                return None
            message = result.stderr.strip() or result.stdout.strip() or "git command failed"
            raise SuperviseError(message)
        return result.stdout.strip()


class LaunchArtifactLoader:
    def load(self, project_dir: Path, launch_path: str | Path | None = None) -> tuple[Path | None, dict[str, Any] | None]:
        if launch_path is not None:
            path = Path(launch_path).expanduser().resolve()
            if path.exists() and path.is_file():
                return path, json.loads(path.read_text(encoding="utf-8"))
            return None, None
        for candidate in self._candidates(project_dir):
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), json.loads(candidate.read_text(encoding="utf-8"))
        return None, None

    def _candidates(self, root: Path) -> list[Path]:
        direct = [
            root / "launch.json",
            root / ".agentkit" / "launch.json",
            root / "artifacts" / "launch.json",
            root / "launch" / "launch.json",
        ]
        packet_dirs = (
            sorted(
                [path for path in root.iterdir() if path.is_dir() and path.name.startswith(("launch", "packet", "handoff"))],
                key=lambda path: path.name,
            )
            if root.exists()
            else []
        )
        nested = [path / "launch.json" for path in packet_dirs]
        return direct + nested
