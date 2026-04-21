from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

from agentkit_cli.land import LandEngine, LandError
from agentkit_cli.schemas import MergeDependency, MergeLane, MergePlan


class MergeError(Exception):
    pass


class MergeEngine:
    def __init__(self) -> None:
        self._land = LandEngine()

    def build(
        self,
        project_dir: str | Path,
        *,
        closeout_path: str | Path | None = None,
        output_dir: str | Path | None = None,
        apply: bool = False,
    ) -> MergePlan:
        root = Path(project_dir).expanduser().resolve()
        try:
            land_plan = self._land.build(root, closeout_path=closeout_path, packet_dir=output_dir)
        except (FileNotFoundError, LandError) as exc:
            raise MergeError(str(exc)) from exc

        current_branch = self._git(root, "rev-parse", "--abbrev-ref", "HEAD", check=False) or land_plan.likely_target_branch
        target_branch = self._target_branch(root, current_branch=current_branch, fallback=land_plan.likely_target_branch, source_branches=[lane.branch_name for lane in land_plan.lanes])
        dirty_root = self._dirty_paths(root)
        lanes: list[MergeLane] = []
        merge_now: list[str] = []
        blocked: list[str] = []
        waiting: list[str] = []
        already_landed: list[str] = []
        applied: list[str] = []
        stopped_on_lane_id: str | None = None
        stop_reason: str | None = None
        merge_started = False

        for land_lane in land_plan.lanes:
            source_exists = self._branch_exists(root, land_lane.branch_name)
            already_merged = bool(source_exists and self._is_ancestor(root, land_lane.branch_name, target_branch))
            dependencies = [
                MergeDependency(lane_id=item.lane_id, reason=item.reason, satisfied=item.satisfied)
                for item in land_lane.dependencies
            ]
            bucket, reason, next_action, readiness, preflight = self._classify_lane(
                root=root,
                land_lane=land_lane,
                target_branch=target_branch,
                dirty_root=dirty_root,
                source_exists=source_exists,
                already_merged=already_merged,
            )
            result = "planned"
            if bucket == "merge-now":
                merge_now.append(land_lane.lane_id)
            elif bucket == "blocked":
                blocked.append(land_lane.lane_id)
            elif bucket == "waiting":
                waiting.append(land_lane.lane_id)
            else:
                already_landed.append(land_lane.lane_id)

            lane = MergeLane(
                lane_id=land_lane.lane_id,
                title=land_lane.title,
                phase_id=land_lane.phase_id,
                phase_index=land_lane.phase_index,
                serialization_group=land_lane.serialization_group,
                source_branch=land_lane.branch_name,
                target_branch=target_branch,
                worktree_path=land_lane.worktree_path,
                merge_bucket=bucket,
                readiness_reason=reason,
                next_action=next_action,
                readiness=readiness,
                preflight_checks=preflight,
                dependencies=dependencies,
                upstream_evidence_paths=list(land_lane.upstream_evidence_paths),
                source_land_bucket=land_lane.land_bucket,
                worktree_exists=land_lane.worktree_exists,
                worktree_dirty=land_lane.worktree_dirty,
                branch_matches=land_lane.branch_matches,
                branch_conflict=land_lane.branch_conflict,
                head_oid=land_lane.head_oid,
                packet_path=str(Path(output_dir).expanduser().resolve() / "lanes" / land_lane.lane_id / "merge.json") if output_dir else None,
                merge_packet_path=str(Path(output_dir).expanduser().resolve() / "lanes" / land_lane.lane_id / "packet.md") if output_dir else None,
                result=result,
            )
            lanes.append(lane)

        if apply:
            if current_branch != target_branch:
                raise MergeError(
                    f"Apply mode requires the project root to be on target branch {target_branch!r}, found {current_branch!r}."
                )
            if dirty_root:
                raise MergeError(
                    "Apply mode requires a clean target worktree before merging: " + ", ".join(dirty_root)
                )
            applied = []
            for index, lane in enumerate(lanes):
                if lane.merge_bucket != "merge-now":
                    continue
                merge_started = True
                try:
                    self._apply_lane(root, lane)
                except MergeError as exc:
                    stopped_on_lane_id = lane.lane_id
                    stop_reason = str(exc)
                    lanes[index] = replace(
                        lane,
                        merge_bucket="blocked",
                        readiness_reason=str(exc),
                        next_action="Resolve the local blocker or conflict, then rebuild merge artifacts.",
                        result="blocked-during-apply",
                    )
                    if lane.lane_id not in blocked:
                        blocked.append(lane.lane_id)
                    if lane.lane_id in merge_now:
                        merge_now.remove(lane.lane_id)
                    break
                applied.append(lane.lane_id)
                lanes[index] = replace(
                    lane,
                    result="applied",
                    next_action="This lane merged locally. Rebuild closeout or archive the lane packet as needed.",
                )
            if stopped_on_lane_id is not None:
                for j in range(index + 1, len(lanes)):
                    if lanes[j].merge_bucket == "merge-now":
                        waiting.append(lanes[j].lane_id)
                        merge_now.remove(lanes[j].lane_id)
                        lanes[j] = replace(
                            lanes[j],
                            merge_bucket="waiting",
                            readiness_reason=f"Apply mode stopped before this lane after {stopped_on_lane_id}.",
                            next_action="Resolve the earlier blocker, then rerun merge planning.",
                            result="not-attempted",
                        )
            else:
                stop_reason = None

        next_actions = ["Merge planning is local-only. Dry-run remains the default unless --apply is set."]
        if merge_now:
            next_actions.append(f"Eligible now: {', '.join(merge_now)}.")
        if blocked:
            next_actions.append(f"Blocked lanes remain visible: {', '.join(blocked)}.")
        if waiting:
            next_actions.append(f"Waiting lanes remain visible: {', '.join(waiting)}.")
        if already_landed:
            next_actions.append(f"Already-landed lanes remain visible: {', '.join(already_landed)}.")
        if apply and applied:
            next_actions.append(f"Applied locally: {', '.join(applied)}.")
        if stop_reason:
            next_actions.append(f"Apply mode stopped on {stopped_on_lane_id}: {stop_reason}")

        return MergePlan(
            schema_version="agentkit.merge.v1",
            project_path=str(root),
            target=land_plan.target,
            closeout_path=land_plan.closeout_path,
            relaunch_path=land_plan.relaunch_path,
            resume_path=land_plan.resume_path,
            reconcile_path=land_plan.reconcile_path,
            launch_path=land_plan.launch_path,
            land_path=land_plan.packet_dir and str(Path(land_plan.packet_dir) / "land.json") or None,
            observe_path=land_plan.observe_path,
            supervise_path=land_plan.supervise_path,
            target_branch=target_branch,
            apply_requested=apply,
            merge_now_lane_ids=merge_now,
            blocked_lane_ids=blocked,
            waiting_lane_ids=waiting,
            already_landed_lane_ids=already_landed,
            applied_lane_ids=applied,
            packet_dir=str(Path(output_dir).expanduser().resolve()) if output_dir else None,
            next_actions=next_actions,
            stopped_on_lane_id=stopped_on_lane_id,
            stop_reason=stop_reason,
            merge_started=merge_started,
            lanes=lanes,
        )

    def render_markdown(self, plan: MergePlan) -> str:
        lines = [
            f"# Merge plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Target branch: `{plan.target_branch}`",
            f"- Apply requested: `{plan.apply_requested}`",
            "",
            "## Summary",
            "",
            f"- Merge now: {', '.join(plan.merge_now_lane_ids) if plan.merge_now_lane_ids else 'none'}",
            f"- Blocked: {', '.join(plan.blocked_lane_ids) if plan.blocked_lane_ids else 'none'}",
            f"- Waiting: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Already landed: {', '.join(plan.already_landed_lane_ids) if plan.already_landed_lane_ids else 'none'}",
            f"- Applied: {', '.join(plan.applied_lane_ids) if plan.applied_lane_ids else 'none'}",
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
                f"- Merge bucket: `{lane.merge_bucket}`",
                f"- Readiness: `{lane.readiness}`",
                f"- Result: `{lane.result}`",
                f"- Source branch: `{lane.source_branch}`",
                f"- Target branch: `{lane.target_branch}`",
                f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
                f"- Reason: {lane.readiness_reason}",
                f"- Next action: {lane.next_action}",
            ])
            for check in lane.preflight_checks:
                lines.append(f"- Preflight: {check}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: MergePlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "merge.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "merge.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "merge.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "merge.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
            (lane_dir / "packet.md").write_text(self._render_packet(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: MergeLane) -> str:
        return self._render_packet(lane)

    def _render_packet(self, lane: MergeLane) -> str:
        lines = [
            f"# Merge packet: {lane.lane_id}",
            "",
            f"- Merge bucket: `{lane.merge_bucket}`",
            f"- Readiness reason: {lane.readiness_reason}",
            f"- Next operator action: {lane.next_action}",
            f"- Source branch: `{lane.source_branch}`",
            f"- Target branch: `{lane.target_branch}`",
            f"- Current worktree path: `{lane.worktree_path or 'unknown'}`",
            f"- Merge readiness: `{lane.readiness}`",
            f"- Result: `{lane.result}`",
            "",
            "## Source artifact chain",
            "",
        ]
        for path in lane.upstream_evidence_paths:
            lines.append(f"- `{path}`")
        if lane.dependencies:
            lines.extend(["", "## Dependencies", ""])
            for dep in lane.dependencies:
                lines.append(f"- {dep.lane_id}: {dep.reason} ({'satisfied' if dep.satisfied else 'pending'})")
        if lane.preflight_checks:
            lines.extend(["", "## Preflight checks", ""])
            for item in lane.preflight_checks:
                lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def _classify_lane(self, *, root: Path, land_lane: Any, target_branch: str, dirty_root: list[str], source_exists: bool, already_merged: bool) -> tuple[str, str, str, str, list[str]]:
        preflight = [
            f"Project root target branch must be `{target_branch}` before apply mode.",
            "Project root worktree must be clean before apply mode.",
            f"Source branch `{land_lane.branch_name}` must still exist locally.",
        ]
        if land_lane.land_bucket == "already-closed" or already_merged:
            return "already-landed", f"Lane {land_lane.lane_id} is already reachable from {target_branch}.", "Keep this lane as archival merge context only.", "already-landed", preflight
        if land_lane.land_bucket == "waiting":
            return "waiting", land_lane.reason, "Wait for prerequisite lanes or serialized ownership to clear.", "waiting", preflight
        if land_lane.land_bucket != "land-now":
            return "blocked", land_lane.reason, "Resolve the saved blocker before any merge attempt.", "blocked", preflight
        if dirty_root:
            return "blocked", "Project root has uncommitted changes, so local merge execution is not safe.", "Clean the target worktree before apply mode.", "blocked", preflight
        if not source_exists:
            return "blocked", f"Source branch {land_lane.branch_name!r} is missing locally.", "Repair or recreate the local branch before merging.", "blocked", preflight
        merge_base = self._merge_base(root, target_branch, land_lane.branch_name)
        if not merge_base:
            return "blocked", f"Local branch state for {land_lane.branch_name!r} is contradictory.", "Inspect branch tips before merging.", "blocked", preflight
        return "merge-now", land_lane.reason, "Merge this lane locally when ready.", "merge-now", preflight

    def _apply_lane(self, root: Path, lane: MergeLane) -> None:
        if self._dirty_paths(root):
            raise MergeError("target worktree became dirty before merge execution")
        result = subprocess.run(
            ["git", "-C", str(root), "merge", "--no-ff", "--no-edit", lane.source_branch],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            subprocess.run(["git", "-C", str(root), "merge", "--abort"], capture_output=True, text=True)
            message = result.stderr.strip() or result.stdout.strip() or "merge failed"
            if "CONFLICT" in message or "Automatic merge failed" in message:
                raise MergeError(f"merge conflict while merging {lane.source_branch} into {lane.target_branch}: {message}")
            raise MergeError(message)

    def _branch_exists(self, repo: Path, branch: str) -> bool:
        if not branch:
            return False
        result = subprocess.run(["git", "-C", str(repo), "show-ref", "--verify", f"refs/heads/{branch}"], capture_output=True, text=True)
        return result.returncode == 0

    def _is_ancestor(self, repo: Path, older: str, newer: str) -> bool:
        result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", older, newer], capture_output=True, text=True)
        return result.returncode == 0

    def _merge_base(self, repo: Path, left: str, right: str) -> str:
        return self._git(repo, "merge-base", left, right, check=False)

    def _dirty_paths(self, repo: Path) -> list[str]:
        ignored = {
            "dispatch.json",
            "launch.json",
            "observe.json",
            "reconcile.json",
            "resume.json",
            "relaunch.json",
            "closeout.json",
            "land.json",
            "merge.json",
            "stage/",
            "materialize/",
            "launch/",
            "observe/",
            "supervise/",
            "reconcile/",
            "resume/",
            "relaunch/",
            "closeout/",
            "land/",
            "merge/",
        }
        output = self._git(repo, "status", "--porcelain", check=False)
        dirty: list[str] = []
        for line in output.splitlines():
            if not line.strip() or ".agentkit/" in line:
                continue
            path = line[3:] if len(line) > 3 else line
            normalized = path.strip()
            if normalized in ignored or any(normalized.startswith(prefix[:-1]) for prefix in ignored if prefix.endswith('/')):
                continue
            dirty.append(normalized)
        return dirty

    def _target_branch(self, repo: Path, *, current_branch: str, fallback: str, source_branches: list[str]) -> str:
        if fallback and fallback != current_branch:
            return fallback
        for candidate in ("main", "master"):
            if candidate != current_branch and candidate not in source_branches and self._branch_exists(repo, candidate):
                return candidate
        return fallback or current_branch or "main"

    def _git(self, repo: Path, *args: str, check: bool) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        if check and result.returncode != 0:
            raise MergeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
        return result.stdout.strip()
