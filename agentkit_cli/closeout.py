from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from agentkit_cli.schemas import CloseoutDependency, CloseoutLane, CloseoutPlan


class CloseoutError(Exception):
    pass


class CloseoutEngine:
    def build(
        self,
        project_dir: str | Path,
        *,
        relaunch_path: str | Path | None = None,
        packet_dir: str | Path | None = None,
    ) -> CloseoutPlan:
        root = Path(project_dir).expanduser().resolve()
        resolved_relaunch_path, relaunch = self._load_relaunch(root, relaunch_path=relaunch_path)
        resolved_resume_path, resume = self._load_required_json(Path(str(relaunch.get("resume_path") or "")), label="resume packet from relaunch plan")
        resolved_reconcile_path, reconcile = self._load_required_json(Path(str(relaunch.get("reconcile_path") or "")), label="reconcile packet from relaunch plan")
        resolved_launch_path, launch = self._load_required_json(Path(str(relaunch.get("launch_path") or "")), label="launch packet from relaunch plan")
        observe_path = self._optional_file(relaunch.get("observe_path"))
        supervise_path = self._optional_file(relaunch.get("supervise_path"))

        self._validate_relaunch_shape(relaunch)
        self._validate_resume_shape(resume, relaunch_path=resolved_relaunch_path, reconcile_path=resolved_reconcile_path)
        self._validate_reconcile_shape(reconcile, launch_path=resolved_launch_path)

        resume_lanes = {str(item.get("lane_id") or ""): item for item in resume.get("lanes") or []}
        reconcile_lanes = {str(item.get("lane_id") or ""): item for item in reconcile.get("lanes") or []}
        launch_actions = {str(item.get("lane_id") or ""): item for item in launch.get("actions") or []}
        if not launch_actions:
            raise CloseoutError("Saved closeout evidence is incomplete: launch.actions is required.")

        resolved_packet_dir = Path(packet_dir).expanduser().resolve() if packet_dir else None
        merge_ready: list[str] = []
        review_required: list[str] = []
        waiting: list[str] = []
        already_closed: list[str] = []
        lanes: list[CloseoutLane] = []
        closed_or_mergeable: set[str] = set()
        follow_on_notes: list[str] = []

        sorted_lanes = sorted(relaunch.get("lanes") or [], key=lambda lane: (int(lane.get("phase_index") or 0), str(lane.get("lane_id") or "")))
        for item in sorted_lanes:
            lane_id = str(item.get("lane_id") or "")
            if not lane_id:
                raise CloseoutError("Saved closeout evidence is contradictory: encountered an empty lane id.")
            resume_lane = resume_lanes.get(lane_id)
            reconcile_lane = reconcile_lanes.get(lane_id)
            launch_action = launch_actions.get(lane_id)
            if resume_lane is None or reconcile_lane is None or launch_action is None:
                raise CloseoutError(f"Saved closeout evidence is contradictory: lane {lane_id!r} is missing from relaunch, resume, reconcile, or launch artifacts.")

            dependencies = [
                CloseoutDependency(
                    lane_id=str(dep.get("lane_id") or ""),
                    reason=str(dep.get("reason") or ""),
                    satisfied=bool(dep.get("satisfied")),
                )
                for dep in item.get("dependencies") or []
            ]
            worktree_path = str(launch_action.get("worktree_path") or item.get("worktree_path") or "")
            worktree_state = self._worktree_state(worktree_path, branch_name=str(launch_action.get("branch_name") or ""))
            bucket, reason, next_action, human_checks = self._closeout_bucket(
                lane_id=lane_id,
                relaunch_bucket=str(item.get("relaunch_bucket") or ""),
                reconcile_bucket=str(reconcile_lane.get("bucket") or ""),
                worktree_state=worktree_state,
                dependencies=dependencies,
                source_reason=str(item.get("reason") or resume_lane.get("reason") or reconcile_lane.get("reason") or ""),
            )
            upstream_evidence_paths = [str(resolved_relaunch_path), str(resolved_resume_path), str(resolved_reconcile_path), str(resolved_launch_path)]
            if observe_path is not None:
                upstream_evidence_paths.append(str(observe_path))
            if supervise_path is not None:
                upstream_evidence_paths.append(str(supervise_path))
            packet_path = str(resolved_packet_dir / "lanes" / lane_id / "closeout.json") if resolved_packet_dir else None
            closeout_packet_path = str(resolved_packet_dir / "lanes" / lane_id / "packet.md") if resolved_packet_dir else None
            lane = CloseoutLane(
                lane_id=lane_id,
                title=str(item.get("title") or lane_id),
                phase_id=str(item.get("phase_id") or "phase-00"),
                phase_index=int(item.get("phase_index") or 0),
                serialization_group=str(item.get("serialization_group") or ""),
                branch_name=str(launch_action.get("branch_name") or item.get("branch_name") or ""),
                worktree_path=worktree_path,
                closeout_bucket=bucket,
                reason=reason,
                next_action=next_action,
                source_relaunch_bucket=str(item.get("relaunch_bucket") or ""),
                source_resume_bucket=str(resume_lane.get("resume_bucket") or ""),
                source_reconcile_bucket=str(reconcile_lane.get("bucket") or ""),
                dependencies=dependencies,
                upstream_evidence_paths=upstream_evidence_paths,
                worktree_exists=worktree_state["exists"],
                worktree_dirty=worktree_state["dirty"],
                branch_matches=worktree_state["branch_matches"],
                head_oid=worktree_state["head_oid"],
                human_checks=human_checks,
                follow_on_notes=[],
                packet_path=packet_path,
                closeout_packet_path=closeout_packet_path,
            )
            lanes.append(lane)
            if bucket == "merge-ready":
                merge_ready.append(lane_id)
                closed_or_mergeable.add(lane_id)
            elif bucket == "review-required":
                review_required.append(lane_id)
            elif bucket == "waiting":
                waiting.append(lane_id)
            elif bucket == "already-closed":
                already_closed.append(lane_id)
                closed_or_mergeable.add(lane_id)
            else:
                raise CloseoutError(f"Saved closeout evidence is contradictory: unsupported closeout bucket {bucket!r} for lane {lane_id!r}.")

        lane_map = {lane.lane_id: lane for lane in lanes}
        for lane in lanes:
            blocked_by = [dep.lane_id for dep in lane.dependencies if dep.lane_id not in closed_or_mergeable]
            if lane.closeout_bucket == "waiting" and not blocked_by:
                note = f"{lane.lane_id} becomes the next serialized lane once earlier completed lanes are merged or archived."
                lane.follow_on_notes.append(note)
                follow_on_notes.append(note)

        next_actions = ["Closeout planning is local-only and never merges branches, deletes worktrees, or mutates remotes."]
        if merge_ready:
            next_actions.append(f"Merge-ready lanes: {', '.join(merge_ready)}.")
        if review_required:
            next_actions.append(f"Human review still required before merge or archival: {', '.join(review_required)}.")
        if waiting:
            next_actions.append(f"Keep these lanes waiting and visible in the closeout packet: {', '.join(waiting)}.")
        if already_closed:
            next_actions.append(f"Preserve already-closed lanes as archival context only: {', '.join(already_closed)}.")
        next_actions.extend(follow_on_notes)
        if len(next_actions) == 1:
            next_actions.append("No lanes remain to close out from the saved artifacts.")

        return CloseoutPlan(
            schema_version="agentkit.closeout.v1",
            project_path=str(Path(relaunch.get("project_path") or root).expanduser().resolve()),
            target=str(relaunch.get("target") or "generic"),
            relaunch_path=str(resolved_relaunch_path),
            resume_path=str(resolved_resume_path),
            reconcile_path=str(resolved_reconcile_path),
            launch_path=str(resolved_launch_path),
            observe_path=str(observe_path) if observe_path else None,
            supervise_path=str(supervise_path) if supervise_path else None,
            merge_ready_lane_ids=merge_ready,
            review_required_lane_ids=review_required,
            waiting_lane_ids=waiting,
            already_closed_lane_ids=already_closed,
            packet_dir=str(resolved_packet_dir) if resolved_packet_dir else None,
            next_actions=next_actions,
            follow_on_notes=follow_on_notes,
            lanes=lanes,
        )

    def render_markdown(self, plan: CloseoutPlan) -> str:
        lines = [
            f"# Closeout plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Relaunch packet: `{plan.relaunch_path}`",
            f"- Resume packet: `{plan.resume_path}`",
            f"- Reconcile packet: `{plan.reconcile_path}`",
            f"- Launch packet: `{plan.launch_path}`",
            f"- Observe packet: `{plan.observe_path or 'not found'}`",
            f"- Supervise packet: `{plan.supervise_path or 'not found'}`",
            "",
            "## Summary",
            "",
            f"- Merge-ready: {', '.join(plan.merge_ready_lane_ids) if plan.merge_ready_lane_ids else 'none'}",
            f"- Review-required: {', '.join(plan.review_required_lane_ids) if plan.review_required_lane_ids else 'none'}",
            f"- Waiting: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Already-closed: {', '.join(plan.already_closed_lane_ids) if plan.already_closed_lane_ids else 'none'}",
            "",
            "## Next actions",
            "",
        ]
        for action in plan.next_actions:
            lines.append(f"- {action}")
        lines.extend(["", "## Lanes", ""])
        for lane in plan.lanes:
            lines.extend([
                f"### {lane.lane_id}: {lane.title}",
                "",
                f"- Closeout bucket: `{lane.closeout_bucket}`",
                f"- Relaunch bucket: `{lane.source_relaunch_bucket}`",
                f"- Reconcile bucket: `{lane.source_reconcile_bucket}`",
                f"- Reason: {lane.reason}",
                f"- Next action: {lane.next_action}",
                f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
                f"- Worktree exists: `{lane.worktree_exists}`",
                f"- Worktree dirty: `{lane.worktree_dirty}`",
                f"- Branch matches: `{lane.branch_matches}`",
            ])
            if lane.dependencies:
                lines.append("- Dependencies: " + ", ".join(f"{dep.lane_id} ({'satisfied' if dep.satisfied else 'pending'})" for dep in lane.dependencies))
            else:
                lines.append("- Dependencies: none")
            for check in lane.human_checks:
                lines.append(f"- Human check: {check}")
            for note in lane.follow_on_notes:
                lines.append(f"- Follow-on: {note}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, plan: CloseoutPlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "closeout.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "closeout.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "closeout.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "closeout.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
            (lane_dir / "packet.md").write_text(self._render_packet_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: CloseoutLane) -> str:
        lines = [
            f"# Closeout lane: {lane.lane_id}",
            "",
            f"- Title: {lane.title}",
            f"- Bucket: `{lane.closeout_bucket}`",
            f"- Reason: {lane.reason}",
            f"- Next action: {lane.next_action}",
            f"- Branch: `{lane.branch_name}`",
            f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
        ]
        if lane.human_checks:
            lines.extend(["", "## Human checks", ""])
            for item in lane.human_checks:
                lines.append(f"- {item}")
        if lane.follow_on_notes:
            lines.extend(["", "## Follow-on notes", ""])
            for item in lane.follow_on_notes:
                lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def _render_packet_markdown(self, lane: CloseoutLane) -> str:
        lines = [
            f"# Closeout packet: {lane.lane_id}",
            "",
            f"- Closeout bucket: `{lane.closeout_bucket}`",
            f"- Merge-readiness reason: {lane.reason}",
            f"- Next operator action: {lane.next_action}",
            f"- Branch: `{lane.branch_name}`",
            f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
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
        if lane.human_checks:
            lines.extend(["", "## Human verification before merge or archival", ""])
            for item in lane.human_checks:
                lines.append(f"- {item}")
        if lane.follow_on_notes:
            lines.extend(["", "## Follow-on unblock notes", ""])
            for item in lane.follow_on_notes:
                lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def _closeout_bucket(
        self,
        *,
        lane_id: str,
        relaunch_bucket: str,
        reconcile_bucket: str,
        worktree_state: dict[str, Any],
        dependencies: list[CloseoutDependency],
        source_reason: str,
    ) -> tuple[str, str, str, list[str]]:
        human_checks: list[str] = []
        if relaunch_bucket == "completed":
            if not worktree_state["exists"]:
                human_checks.append("Worktree path is stale or missing. Confirm the branch was merged, archived, or intentionally removed.")
                return (
                    "review-required",
                    source_reason or f"Lane {lane_id} is completed in saved artifacts but the local worktree is missing.",
                    "Verify the branch state manually before merge or archival.",
                    human_checks,
                )
            if worktree_state["dirty"]:
                human_checks.append("Local worktree has uncommitted changes.")
                return (
                    "review-required",
                    source_reason or f"Lane {lane_id} is completed but the worktree is dirty.",
                    "Inspect, commit, or discard local changes before merge or archival.",
                    human_checks,
                )
            if not worktree_state["branch_matches"]:
                human_checks.append("Current branch does not match the saved launch branch.")
                return (
                    "review-required",
                    source_reason or f"Lane {lane_id} is completed but branch drift requires human review.",
                    "Inspect branch drift before merge.",
                    human_checks,
                )
            human_checks.extend([
                "Verify tests or review evidence attached to the lane before merging.",
                "Merge or archive this lane locally using the saved branch and artifact chain.",
            ])
            return (
                "merge-ready",
                source_reason or f"Lane {lane_id} is complete, clean, and aligned with saved launch state.",
                "Merge this lane locally, then archive its closeout packet.",
                human_checks,
            )
        if relaunch_bucket == "waiting":
            if any(not dep.satisfied for dep in dependencies):
                human_checks.append("Upstream dependencies are still not closed out.")
            return (
                "waiting",
                source_reason or f"Lane {lane_id} must stay waiting until prerequisites clear.",
                "Keep this lane visible but do not merge or archive it yet.",
                human_checks,
            )
        if relaunch_bucket == "review-only":
            human_checks.append("Saved relaunch evidence already requires human review.")
            return (
                "review-required",
                source_reason or f"Lane {lane_id} requires manual inspection before closeout.",
                "Review the lane manually before merge, relaunch, or archival.",
                human_checks,
            )
        if relaunch_bucket == "relaunch-now":
            human_checks.append("Lane is still queued for relaunch, so it is not safe to merge.")
            return (
                "review-required",
                source_reason or f"Lane {lane_id} is not closed out because it still needs another execution pass.",
                "Relaunch or explicitly close this lane before merge planning.",
                human_checks,
            )
        if relaunch_bucket == "already-closed":
            return (
                "already-closed",
                source_reason or f"Lane {lane_id} was already closed in saved artifacts.",
                "Keep this lane as archival context only.",
                human_checks,
            )
        raise CloseoutError(f"Saved closeout evidence is contradictory: unsupported relaunch bucket {relaunch_bucket!r} for lane {lane_id!r}.")

    def _worktree_state(self, worktree_path: str, *, branch_name: str) -> dict[str, Any]:
        state = {"exists": False, "dirty": False, "branch_matches": False, "head_oid": None}
        if not worktree_path:
            return state
        path = Path(worktree_path).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return state
        state["exists"] = True
        branch = self._git(path, "rev-parse", "--abbrev-ref", "HEAD", check=False)
        head = self._git(path, "rev-parse", "HEAD", check=False)
        dirty = self._git(path, "status", "--porcelain", check=False)
        state["dirty"] = any(
            line.strip() and ".agentkit/" not in line
            for line in dirty.splitlines()
        )
        state["branch_matches"] = bool(branch_name) and branch.strip() == branch_name
        state["head_oid"] = head.strip() or None
        return state

    def _git(self, repo: Path, *args: str, check: bool) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        if check and result.returncode != 0:
            raise CloseoutError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
        return result.stdout.strip()

    def _load_relaunch(self, root: Path, *, relaunch_path: str | Path | None) -> tuple[Path, dict[str, Any]]:
        candidates: list[Path]
        if relaunch_path is None:
            candidates = [root / "relaunch.json", root / "relaunch" / "relaunch.json", root / "artifacts" / "relaunch.json", root / ".agentkit" / "relaunch.json"]
        else:
            requested = Path(relaunch_path).expanduser().resolve()
            candidates = [requested / "relaunch.json"] if requested.is_dir() else [requested]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), self._read_json(candidate)
        raise FileNotFoundError("No relaunch.json artifact found. Save a relaunch packet first, then run agentkit closeout.")

    def _load_required_json(self, path: Path, *, label: str) -> tuple[Path, dict[str, Any]]:
        value = str(path).strip()
        if not value:
            raise CloseoutError(f"Saved relaunch artifact is incomplete: missing {label}.")
        if not path.exists() or not path.is_file():
            raise CloseoutError(f"Saved relaunch artifact points at a missing {label}: {path}")
        return path.resolve(), self._read_json(path)

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CloseoutError(f"Saved closeout evidence is malformed JSON: {path}") from exc
        if not isinstance(data, dict):
            raise CloseoutError(f"Saved closeout evidence must be a JSON object: {path}")
        return data

    def _optional_file(self, path: Any) -> Path | None:
        value = str(path or "").strip()
        if not value:
            return None
        candidate = Path(value).expanduser().resolve()
        if not candidate.exists() or not candidate.is_file():
            raise CloseoutError(f"Saved relaunch artifact points at a missing upstream artifact: {candidate}")
        return candidate

    def _validate_relaunch_shape(self, relaunch: dict[str, Any]) -> None:
        if str(relaunch.get("schema_version") or "") != "agentkit.relaunch.v1":
            raise CloseoutError("Saved relaunch artifact is not a supported agentkit.relaunch.v1 packet.")
        summary = {
            "relaunch-now": {str(item) for item in relaunch.get("relaunch_now_lane_ids") or []},
            "waiting": {str(item) for item in relaunch.get("waiting_lane_ids") or []},
            "review-only": {str(item) for item in relaunch.get("review_lane_ids") or []},
            "completed": {str(item) for item in relaunch.get("completed_lane_ids") or []},
            "already-closed": {str(item) for item in relaunch.get("already_closed_lane_ids") or []},
        }
        for lane in relaunch.get("lanes") or []:
            lane_id = str(lane.get("lane_id") or "")
            bucket = str(lane.get("relaunch_bucket") or "")
            if bucket not in summary:
                raise CloseoutError(f"Saved relaunch artifact is contradictory: unsupported relaunch bucket {bucket!r} for lane {lane_id!r}.")
            if lane_id not in summary[bucket]:
                raise CloseoutError(f"Saved relaunch artifact is contradictory: lane {lane_id!r} bucket {bucket!r} disagrees with summary ids.")

    def _validate_resume_shape(self, resume: dict[str, Any], *, relaunch_path: Path, reconcile_path: Path) -> None:
        if str(resume.get("schema_version") or "") != "agentkit.resume.v1":
            raise CloseoutError("Saved resume artifact is not a supported agentkit.resume.v1 packet.")
        if Path(str(resume.get("reconcile_path") or "")).expanduser().resolve() != reconcile_path.resolve():
            raise CloseoutError("Saved closeout evidence is contradictory: resume.reconcile_path does not match relaunch.reconcile_path.")
        if not str(relaunch_path):
            raise CloseoutError("Saved closeout evidence is contradictory: missing relaunch path.")

    def _validate_reconcile_shape(self, reconcile: dict[str, Any], *, launch_path: Path) -> None:
        if str(reconcile.get("schema_version") or "") != "agentkit.reconcile.v1":
            raise CloseoutError("Saved reconcile artifact is not a supported agentkit.reconcile.v1 packet.")
        if Path(str(reconcile.get("launch_path") or "")).expanduser().resolve() != launch_path.resolve():
            raise CloseoutError("Saved closeout evidence is contradictory: reconcile.launch_path does not match relaunch.launch_path.")
