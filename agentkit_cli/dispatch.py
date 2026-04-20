from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentkit_cli.bundle import BundleEngine
from agentkit_cli.clarify import ClarifyEngine
from agentkit_cli.resolve import ResolveEngine
from agentkit_cli.taskpack import TaskpackEngine


_TARGET_RUNNERS = {
    "generic": {
        "runner": "generic coding agent",
        "note": "Use the lane packet as the primary handoff and keep execution inside the declared owned paths.",
    },
    "codex": {
        "runner": "codex exec --full-auto",
        "note": "Keep prompts short, enumerate owned paths explicitly, and stop when another lane owns the next file surface.",
    },
    "claude-code": {
        "runner": "claude --print --permission-mode bypassPermissions",
        "note": "Paste the lane packet directly, keep stop conditions concrete, and avoid guessing outside the owned paths.",
    },
}


@dataclass(frozen=True)
class DispatchDependency:
    lane_id: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"lane_id": self.lane_id, "reason": self.reason}


@dataclass(frozen=True)
class DispatchLanePacket:
    objective: str
    runner: str
    execution_notes: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "objective": self.objective,
            "runner": self.runner,
            "execution_notes": list(self.execution_notes),
            "stop_conditions": list(self.stop_conditions),
        }


@dataclass(frozen=True)
class DispatchLane:
    lane_id: str
    title: str
    phase_id: str
    phase_index: int
    ownership_mode: str
    owned_paths: list[str] = field(default_factory=list)
    subsystem_hints: list[str] = field(default_factory=list)
    dependencies: list[DispatchDependency] = field(default_factory=list)
    packet: DispatchLanePacket | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "lane_id": self.lane_id,
            "title": self.title,
            "phase_id": self.phase_id,
            "phase_index": self.phase_index,
            "ownership_mode": self.ownership_mode,
            "owned_paths": list(self.owned_paths),
            "subsystem_hints": list(self.subsystem_hints),
            "dependencies": [item.to_dict() for item in self.dependencies],
            "packet": self.packet.to_dict() if self.packet else None,
        }


@dataclass(frozen=True)
class DispatchPhase:
    phase_id: str
    index: int
    execution_mode: str
    lane_ids: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "phase_id": self.phase_id,
            "index": self.index,
            "execution_mode": self.execution_mode,
            "lane_ids": list(self.lane_ids),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class DispatchPlan:
    schema_version: str
    project_path: str
    target: str
    execution_recommendation: str
    recommendation_reason: str
    worktree_guidance: list[str] = field(default_factory=list)
    phases: list[DispatchPhase] = field(default_factory=list)
    lanes: list[DispatchLane] = field(default_factory=list)
    ownership_conflicts: list[dict[str, object]] = field(default_factory=list)
    source_resolve: dict[str, Any] = field(default_factory=dict)
    source_taskpack: dict[str, Any] = field(default_factory=dict)
    source_bundle: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_path": self.project_path,
            "target": self.target,
            "execution_recommendation": self.execution_recommendation,
            "recommendation_reason": self.recommendation_reason,
            "worktree_guidance": list(self.worktree_guidance),
            "phases": [item.to_dict() for item in self.phases],
            "lanes": [item.to_dict() for item in self.lanes],
            "ownership_conflicts": list(self.ownership_conflicts),
            "source_resolve": self.source_resolve,
            "source_taskpack": self.source_taskpack,
            "source_bundle": self.source_bundle,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class DispatchEngine:
    def __init__(self) -> None:
        self._bundle = BundleEngine()
        self._taskpack = TaskpackEngine()
        self._clarify = ClarifyEngine()
        self._resolve = ResolveArtifactLoader()

    def build(self, project_dir: str | Path, *, target: str = "generic") -> DispatchPlan:
        root = Path(project_dir).expanduser().resolve()
        normalized_target = self._normalize_target(target)
        bundle = self._bundle.build(root)
        taskpack = self._taskpack.build(root, target=normalized_target)
        clarify = self._clarify.build(root, target=normalized_target)
        resolve = self._resolve.load(root)
        if resolve is None:
            raise FileNotFoundError(
                "No resolve.json artifact found. Save a resolved packet first, then run agentkit dispatch."
            )

        recommendation = str(resolve.get("execution_recommendation") or "pause")
        reason = str(resolve.get("recommendation_reason") or "Dispatch requires a saved resolve packet.")
        remaining_blockers = resolve.get("remaining_blockers") or []
        if remaining_blockers:
            recommendation = "pause"
            reason = "Resolve still contains remaining blockers, so dispatch must pause."

        candidates = self._candidate_lanes(bundle.to_dict(), taskpack.to_dict(), clarify.to_dict(), resolve)
        phases, lanes, conflicts = self._schedule(candidates, normalized_target, recommendation)
        guidance = self._worktree_guidance(lanes)

        return DispatchPlan(
            schema_version="agentkit.dispatch.v1",
            project_path=str(root),
            target=normalized_target,
            execution_recommendation=recommendation,
            recommendation_reason=reason,
            worktree_guidance=guidance,
            phases=phases,
            lanes=lanes,
            ownership_conflicts=conflicts,
            source_resolve=resolve,
            source_taskpack=taskpack.to_dict(),
            source_bundle=bundle.to_dict(),
        )

    def render_markdown(self, plan: DispatchPlan) -> str:
        lines = [
            f"# Dispatch plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Recommendation: `{plan.execution_recommendation}`",
            f"- Reason: {plan.recommendation_reason}",
            "",
            "## Worktree guidance",
            "",
        ]
        if plan.worktree_guidance:
            for item in plan.worktree_guidance:
                lines.append(f"- {item}")
        else:
            lines.append("- Keep all work inside this repo.")
        lines.extend(["", "## Phases", ""])
        for phase in plan.phases:
            lines.append(f"### {phase.phase_id} ({phase.execution_mode})")
            lines.append("")
            lines.append(f"- Lanes: {', '.join(phase.lane_ids)}")
            if phase.rationale:
                lines.append(f"- Rationale: {phase.rationale}")
            lines.append("")
        lines.extend(["## Lanes", ""])
        for lane in plan.lanes:
            lines.append(f"### {lane.lane_id}: {lane.title}")
            lines.append("")
            lines.append(f"- Phase: {lane.phase_id}")
            lines.append(f"- Ownership mode: {lane.ownership_mode}")
            lines.append(f"- Owned paths: {', '.join(lane.owned_paths) if lane.owned_paths else '(fallback: whole repo context)'}")
            if lane.dependencies:
                lines.append(f"- Dependencies: {', '.join(f'{item.lane_id} ({item.reason})' for item in lane.dependencies)}")
            else:
                lines.append("- Dependencies: none")
            if lane.subsystem_hints:
                lines.append(f"- Hints: {'; '.join(lane.subsystem_hints)}")
            packet = lane.packet
            if packet:
                lines.extend(["", "#### Runner packet", "", f"- Objective: {packet.objective}", f"- Runner: {packet.runner}"])
                if packet.execution_notes:
                    for note in packet.execution_notes:
                        lines.append(f"- Note: {note}")
                if packet.stop_conditions:
                    for stop in packet.stop_conditions:
                        lines.append(f"- Stop: {stop}")
            lines.append("")
        if plan.ownership_conflicts:
            lines.extend(["## Ownership conflicts", ""])
            for item in plan.ownership_conflicts:
                lines.append(f"- {item['left_lane_id']} vs {item['right_lane_id']}: {item['overlap']}")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: DispatchPlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "dispatch.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "dispatch.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        lanes_dir.mkdir(exist_ok=True)
        for lane in plan.lanes:
            (lanes_dir / f"{lane.lane_id}.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
            (lanes_dir / f"{lane.lane_id}.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: DispatchLane) -> str:
        packet = lane.packet or DispatchLanePacket(objective=lane.title, runner="generic coding agent")
        lines = [
            f"# {lane.lane_id}: {lane.title}",
            "",
            f"- Phase: {lane.phase_id}",
            f"- Ownership mode: {lane.ownership_mode}",
            f"- Owned paths: {', '.join(lane.owned_paths) if lane.owned_paths else '(fallback scope)'}",
            "",
            "## Objective",
            "",
            packet.objective,
            "",
            "## Execution notes",
            "",
        ]
        for note in packet.execution_notes:
            lines.append(f"- {note}")
        lines.extend(["", "## Stop conditions", ""])
        for stop in packet.stop_conditions:
            lines.append(f"- {stop}")
        return "\n".join(lines).rstrip() + "\n"

    def _candidate_lanes(self, bundle: dict[str, Any], taskpack: dict[str, Any], clarify: dict[str, Any], resolve: dict[str, Any]) -> list[dict[str, object]]:
        architecture_map = (
            ((resolve.get("source_clarify") or {}).get("source_bundle") or {}).get("architecture_map")
            or ((clarify.get("source_bundle") or {}).get("architecture_map") if clarify else None)
            or bundle.get("architecture_map")
            or {}
        )
        subsystems = architecture_map.get("subsystems") or []
        tests = architecture_map.get("tests") or []
        hints = architecture_map.get("hints") or []
        candidates: list[dict[str, object]] = []
        for item in sorted(subsystems, key=lambda row: (str(row.get("path", "")), str(row.get("name", "")))):
            path = str(item.get("path") or "").strip()
            if not path:
                continue
            owned_paths = {path}
            for test in tests:
                related = str(test.get("related_area") or "").strip()
                test_path = str(test.get("path") or "").strip()
                if related and (related == path or related.startswith(path + "/") or path.startswith(related + "/")):
                    owned_paths.add(test_path)
            lane_hints = [
                str(hint.get("detail") or "").strip()
                for hint in hints
                if str(hint.get("detail") or "").strip() and path in str(hint.get("detail") or "")
            ]
            candidates.append(
                {
                    "title": str(item.get("name") or path),
                    "owned_paths": sorted(owned_paths),
                    "subsystem_hints": sorted(set(lane_hints))[:4],
                    "objective": f"Implement the planned work for {item.get('name') or path} while staying inside the owned paths.",
                }
            )
        if not candidates:
            important = architecture_map.get("important_paths") or []
            fallback_paths = [str(item.get("path") or "").strip() for item in important[:4] if str(item.get("path") or "").strip()]
            if not fallback_paths:
                fallback_paths = ["."]
            candidates.append(
                {
                    "title": "repo-wide fallback lane",
                    "owned_paths": sorted(set(fallback_paths)),
                    "subsystem_hints": ["No subsystem map artifact was saved, so dispatch fell back to a single deterministic lane."],
                    "objective": "Execute the resolved packet in one lane because no saved subsystem planning surfaces were available.",
                }
            )
        return candidates

    def _schedule(self, candidates: list[dict[str, object]], target: str, recommendation: str) -> tuple[list[DispatchPhase], list[DispatchLane], list[dict[str, object]]]:
        phase_rows: dict[str, dict[str, object]] = {}
        lanes: list[DispatchLane] = []
        conflicts: list[dict[str, object]] = []
        if recommendation == "pause":
            candidates = candidates[:1]
        for index, candidate in enumerate(candidates, start=1):
            lane_id = f"lane-{index:02d}"
            owned_paths = list(candidate["owned_paths"])
            phase_index = 1
            execution_mode = "parallel"
            ownership_mode = "exclusive"
            phase_rationale = "No overlapping ownership detected."
            dependency_items: list[DispatchDependency] = []
            for other in lanes:
                overlap = self._overlap(other.owned_paths, owned_paths)
                if overlap:
                    conflicts.append({
                        "left_lane_id": other.lane_id,
                        "right_lane_id": lane_id,
                        "overlap": overlap,
                    })
                    phase_index = max(phase_index, other.phase_index + 1)
                    execution_mode = "serial"
                    ownership_mode = "serialized-overlap"
                    phase_rationale = "Overlapping owned paths were moved into serialized execution phases."
                    dependency_items.append(DispatchDependency(lane_id=other.lane_id, reason=f"overlapping ownership: {overlap}"))
            phase_id = f"phase-{phase_index:02d}"
            packet = self._packet(
                target=target,
                title=str(candidate["title"]),
                owned_paths=owned_paths,
                dependency_items=dependency_items,
                recommendation=recommendation,
            )
            lane = DispatchLane(
                lane_id=lane_id,
                title=str(candidate["title"]),
                phase_id=phase_id,
                phase_index=phase_index,
                ownership_mode=ownership_mode,
                owned_paths=owned_paths,
                subsystem_hints=list(candidate["subsystem_hints"]),
                dependencies=dependency_items,
                packet=packet,
            )
            lanes.append(lane)
            row = phase_rows.setdefault(
                phase_id,
                {"phase_id": phase_id, "index": phase_index, "execution_mode": execution_mode, "lane_ids": [], "rationale": phase_rationale},
            )
            row["lane_ids"].append(lane_id)
            if execution_mode == "serial":
                row["execution_mode"] = "serial"
                row["rationale"] = phase_rationale
        normalized_phases = [
            DispatchPhase(
                phase_id=str(row["phase_id"]),
                index=int(row["index"]),
                execution_mode="parallel" if len(row["lane_ids"]) > 1 and int(row["index"]) == 1 and not conflicts else str(row["execution_mode"]),
                lane_ids=list(row["lane_ids"]),
                rationale=str(row["rationale"]),
            )
            for row in sorted(phase_rows.values(), key=lambda item: (int(item["index"]), str(item["phase_id"])))
        ]
        return normalized_phases, sorted(lanes, key=lambda item: item.lane_id), sorted(conflicts, key=lambda item: (item["left_lane_id"], item["right_lane_id"], item["overlap"]))

    def _packet(self, *, target: str, title: str, owned_paths: list[str], dependency_items: list[DispatchDependency], recommendation: str) -> DispatchLanePacket:
        target_spec = _TARGET_RUNNERS[target]
        execution_notes = [
            target_spec["note"],
            f"Owned paths: {', '.join(owned_paths) if owned_paths else '.'}",
        ]
        if dependency_items:
            execution_notes.append("Wait for dependency lanes to finish before touching overlapping files.")
        if len(owned_paths) > 1:
            execution_notes.append("Keep edits worktree-safe by staying within the listed paths and refusing opportunistic cross-lane cleanup.")
        stop_conditions = [
            "Stop if the work requires files outside the owned paths.",
            "Stop if the contract or resolve packet would need to change.",
        ]
        if recommendation == "proceed-with-assumptions":
            stop_conditions.append("Stop if the lane cannot continue without validating the saved assumptions.")
        return DispatchLanePacket(
            objective=f"Complete {title} for this dispatch phase without broadening scope.",
            runner=str(target_spec["runner"]),
            execution_notes=execution_notes,
            stop_conditions=stop_conditions,
        )

    def _worktree_guidance(self, lanes: list[DispatchLane]) -> list[str]:
        if len(lanes) <= 1:
            return ["Single-lane plan, so no fake parallelism is claimed."]
        return [
            "Use separate worktrees or isolated branches per lane when phases contain more than one lane.",
            "Do not let one lane edit another lane's owned paths without first re-planning dispatch.",
            "If two lanes discover overlapping files, serialize them instead of improvising parallel execution.",
        ]

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in _TARGET_RUNNERS:
            raise ValueError("target must be one of: generic, codex, claude-code")
        return value

    def _overlap(self, left_paths: list[str], right_paths: list[str]) -> str:
        for left in sorted(left_paths):
            for right in sorted(right_paths):
                if left == right:
                    return left
                if left != "." and right.startswith(left + "/"):
                    return left
                if right != "." and left.startswith(right + "/"):
                    return right
                if left == "." or right == ".":
                    return "."
        return ""


class ResolveArtifactLoader:
    def load(self, project_dir: str | Path) -> dict[str, Any] | None:
        root = Path(project_dir).expanduser().resolve()
        for candidate in self._candidates(root):
            if candidate.exists() and candidate.is_file():
                return json.loads(candidate.read_text(encoding="utf-8"))
        return None

    def _candidates(self, root: Path) -> list[Path]:
        direct = [
            root / "resolve.json",
            root / ".agentkit" / "resolve.json",
            root / "artifacts" / "resolve.json",
        ]
        packet_dirs = sorted(
            [path for path in root.iterdir() if path.is_dir() and path.name.startswith(("resolve", "packet", "handoff"))],
            key=lambda path: path.name,
        ) if root.exists() else []
        nested = [path / "resolve.json" for path in packet_dirs]
        return direct + nested
