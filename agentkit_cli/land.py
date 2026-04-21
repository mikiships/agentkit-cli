from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from agentkit_cli.schemas import LandDependency, LandLane, LandPlan


class LandError(Exception):
    pass


class LandEngine:
    def build(
        self,
        project_dir: str | Path,
        *,
        closeout_path: str | Path | None = None,
        packet_dir: str | Path | None = None,
    ) -> LandPlan:
        root = Path(project_dir).expanduser().resolve()
        resolved_closeout_path, closeout = self._load_closeout(root, closeout_path=closeout_path)
        resolved_relaunch_path, relaunch = self._load_required_json(Path(str(closeout.get("relaunch_path") or "")), label="relaunch packet from closeout plan")
        resolved_resume_path, resume = self._load_required_json(Path(str(closeout.get("resume_path") or "")), label="resume packet from closeout plan")
        resolved_reconcile_path, reconcile = self._load_required_json(Path(str(closeout.get("reconcile_path") or "")), label="reconcile packet from closeout plan")
        resolved_launch_path, launch = self._load_required_json(Path(str(closeout.get("launch_path") or "")), label="launch packet from closeout plan")
        observe_path = self._optional_file(closeout.get("observe_path"))
        supervise_path = self._optional_file(closeout.get("supervise_path"))

        self._validate_closeout_shape(closeout)
        self._validate_relaunch_shape(relaunch, closeout_path=resolved_closeout_path)
        self._validate_resume_shape(resume, reconcile_path=resolved_reconcile_path)
        self._validate_reconcile_shape(reconcile, launch_path=resolved_launch_path)

        relaunch_lanes = {str(item.get("lane_id") or ""): item for item in relaunch.get("lanes") or []}
        resume_lanes = {str(item.get("lane_id") or ""): item for item in resume.get("lanes") or []}
        reconcile_lanes = {str(item.get("lane_id") or ""): item for item in reconcile.get("lanes") or []}
        launch_actions = {str(item.get("lane_id") or ""): item for item in launch.get("actions") or []}
        if not launch_actions:
            raise LandError("Saved land evidence is incomplete: launch.actions is required.")

        resolved_packet_dir = Path(packet_dir).expanduser().resolve() if packet_dir else None
        target_branch = self._target_branch_context(root)
        land_now: list[str] = []
        review_required: list[str] = []
        waiting: list[str] = []
        already_closed: list[str] = []
        lanes: list[LandLane] = []
        follow_on_notes: list[str] = []
        closed_or_plannable: set[str] = set()
        blocked_groups: set[str] = set()

        sorted_lanes = sorted(closeout.get("lanes") or [], key=lambda lane: (int(lane.get("phase_index") or 0), str(lane.get("lane_id") or "")))
        for item in sorted_lanes:
            lane_id = str(item.get("lane_id") or "")
            if not lane_id:
                raise LandError("Saved land evidence is contradictory: encountered an empty lane id.")
            relaunch_lane = relaunch_lanes.get(lane_id)
            resume_lane = resume_lanes.get(lane_id)
            reconcile_lane = reconcile_lanes.get(lane_id)
            launch_action = launch_actions.get(lane_id)
            if relaunch_lane is None or resume_lane is None or reconcile_lane is None or launch_action is None:
                raise LandError(f"Saved land evidence is contradictory: lane {lane_id!r} is missing from closeout, relaunch, resume, reconcile, or launch artifacts.")

            dependencies = [
                LandDependency(
                    lane_id=str(dep.get("lane_id") or ""),
                    reason=str(dep.get("reason") or ""),
                    satisfied=bool(dep.get("satisfied")),
                )
                for dep in item.get("dependencies") or []
            ]
            worktree_path = str(launch_action.get("worktree_path") or item.get("worktree_path") or "")
            branch_name = str(launch_action.get("branch_name") or item.get("branch_name") or "")
            worktree_state = self._worktree_state(worktree_path, branch_name=branch_name)
            bucket, reason, next_action, human_checks = self._land_bucket(
                lane_id=lane_id,
                closeout_bucket=str(item.get("closeout_bucket") or ""),
                relaunch_bucket=str(relaunch_lane.get("relaunch_bucket") or ""),
                reconcile_bucket=str(reconcile_lane.get("bucket") or ""),
                worktree_state=worktree_state,
                dependencies=dependencies,
                serialization_group=str(item.get("serialization_group") or ""),
                blocked_groups=blocked_groups,
                closed_or_plannable=closed_or_plannable,
                source_reason=str(item.get("reason") or relaunch_lane.get("reason") or resume_lane.get("reason") or reconcile_lane.get("reason") or ""),
            )

            if bucket in {"review-required", "waiting"} and str(item.get("serialization_group") or ""):
                blocked_groups.add(str(item.get("serialization_group") or ""))

            upstream_evidence_paths = [
                str(resolved_closeout_path),
                str(resolved_relaunch_path),
                str(resolved_resume_path),
                str(resolved_reconcile_path),
                str(resolved_launch_path),
            ]
            if observe_path is not None:
                upstream_evidence_paths.append(str(observe_path))
            if supervise_path is not None:
                upstream_evidence_paths.append(str(supervise_path))

            sequence = len(land_now) + 1 if bucket == "land-now" else None
            lane = LandLane(
                lane_id=lane_id,
                title=str(item.get("title") or lane_id),
                phase_id=str(item.get("phase_id") or "phase-00"),
                phase_index=int(item.get("phase_index") or 0),
                serialization_group=str(item.get("serialization_group") or ""),
                branch_name=branch_name,
                worktree_path=worktree_path,
                land_bucket=bucket,
                reason=reason,
                next_action=next_action,
                source_closeout_bucket=str(item.get("closeout_bucket") or ""),
                source_relaunch_bucket=str(relaunch_lane.get("relaunch_bucket") or ""),
                source_resume_bucket=str(resume_lane.get("resume_bucket") or ""),
                source_reconcile_bucket=str(reconcile_lane.get("bucket") or ""),
                dependencies=dependencies,
                upstream_evidence_paths=upstream_evidence_paths,
                likely_target_branch=target_branch,
                landing_sequence=sequence,
                worktree_exists=worktree_state["exists"],
                worktree_dirty=worktree_state["dirty"],
                branch_matches=worktree_state["branch_matches"],
                branch_conflict=worktree_state["branch_conflict"],
                head_oid=worktree_state["head_oid"],
                human_checks=human_checks,
                follow_on_notes=[],
                packet_path=str(resolved_packet_dir / "lanes" / lane_id / "land.json") if resolved_packet_dir else None,
                landing_packet_path=str(resolved_packet_dir / "lanes" / lane_id / "packet.md") if resolved_packet_dir else None,
            )
            lanes.append(lane)
            if bucket == "land-now":
                land_now.append(lane_id)
                closed_or_plannable.add(lane_id)
            elif bucket == "review-required":
                review_required.append(lane_id)
            elif bucket == "waiting":
                waiting.append(lane_id)
            elif bucket == "already-closed":
                already_closed.append(lane_id)
                closed_or_plannable.add(lane_id)
            else:
                raise LandError(f"Saved land evidence is contradictory: unsupported land bucket {bucket!r} for lane {lane_id!r}.")

        for lane in lanes:
            blocked_by = [dep.lane_id for dep in lane.dependencies if dep.lane_id not in closed_or_plannable]
            if lane.land_bucket == "waiting" and lane.serialization_group:
                note = (
                    f"{lane.lane_id} becomes landable after earlier lanes in serialization group "
                    f"{lane.serialization_group!r} finish landing or archival review."
                )
                lane.follow_on_notes.append(note)
                follow_on_notes.append(note)
            elif lane.land_bucket == "waiting" and not blocked_by:
                note = f"{lane.lane_id} becomes the next landing candidate once currently waiting local checks clear."
                lane.follow_on_notes.append(note)
                follow_on_notes.append(note)

        landing_order_notes = [f"{index}. {lane_id}" for index, lane_id in enumerate(land_now, start=1)]
        next_actions = ["Land planning is local-only and never merges branches, deletes worktrees, or mutates remotes."]
        if land_now:
            next_actions.append(f"Land-now lanes in deterministic order: {', '.join(land_now)}.")
        if review_required:
            next_actions.append(f"Human review is still required before local landing or archival: {', '.join(review_required)}.")
        if waiting:
            next_actions.append(f"Keep these lanes waiting and visible in the landing packet: {', '.join(waiting)}.")
        if already_closed:
            next_actions.append(f"Preserve already-closed lanes as archival context only: {', '.join(already_closed)}.")
        next_actions.extend(follow_on_notes)
        if len(next_actions) == 1:
            next_actions.append("No lanes remain to plan for landing from the saved artifacts.")

        return LandPlan(
            schema_version="agentkit.land.v1",
            project_path=str(Path(closeout.get("project_path") or root).expanduser().resolve()),
            target=str(closeout.get("target") or "generic"),
            closeout_path=str(resolved_closeout_path),
            relaunch_path=str(resolved_relaunch_path),
            resume_path=str(resolved_resume_path),
            reconcile_path=str(resolved_reconcile_path),
            launch_path=str(resolved_launch_path),
            observe_path=str(observe_path) if observe_path else None,
            supervise_path=str(supervise_path) if supervise_path else None,
            likely_target_branch=target_branch,
            land_now_lane_ids=land_now,
            review_required_lane_ids=review_required,
            waiting_lane_ids=waiting,
            already_closed_lane_ids=already_closed,
            landing_order_lane_ids=land_now,
            packet_dir=str(resolved_packet_dir) if resolved_packet_dir else None,
            next_actions=next_actions,
            follow_on_notes=follow_on_notes,
            landing_order_notes=landing_order_notes,
            lanes=lanes,
        )

    def render_markdown(self, plan: LandPlan) -> str:
        lines = [
            f"# Land plan: {Path(plan.project_path).name}",
            "",
            f"- Schema: `{plan.schema_version}`",
            f"- Project: `{plan.project_path}`",
            f"- Target: `{plan.target}`",
            f"- Likely target branch: `{plan.likely_target_branch}`",
            f"- Closeout packet: `{plan.closeout_path}`",
            f"- Relaunch packet: `{plan.relaunch_path}`",
            f"- Resume packet: `{plan.resume_path}`",
            f"- Reconcile packet: `{plan.reconcile_path}`",
            f"- Launch packet: `{plan.launch_path}`",
            f"- Observe packet: `{plan.observe_path or 'not found'}`",
            f"- Supervise packet: `{plan.supervise_path or 'not found'}`",
            "",
            "## Summary",
            "",
            f"- Land now: {', '.join(plan.land_now_lane_ids) if plan.land_now_lane_ids else 'none'}",
            f"- Review-required: {', '.join(plan.review_required_lane_ids) if plan.review_required_lane_ids else 'none'}",
            f"- Waiting: {', '.join(plan.waiting_lane_ids) if plan.waiting_lane_ids else 'none'}",
            f"- Already-closed: {', '.join(plan.already_closed_lane_ids) if plan.already_closed_lane_ids else 'none'}",
            "",
            "## Landing order",
            "",
        ]
        if plan.landing_order_notes:
            for item in plan.landing_order_notes:
                lines.append(f"- {item}")
        else:
            lines.append("- none")
        lines.extend(["", "## Next actions", ""])
        for action in plan.next_actions:
            lines.append(f"- {action}")
        lines.extend(["", "## Lanes", ""])
        for lane in plan.lanes:
            lines.extend([
                f"### {lane.lane_id}: {lane.title}",
                "",
                f"- Land bucket: `{lane.land_bucket}`",
                f"- Closeout bucket: `{lane.source_closeout_bucket}`",
                f"- Relaunch bucket: `{lane.source_relaunch_bucket}`",
                f"- Reconcile bucket: `{lane.source_reconcile_bucket}`",
                f"- Reason: {lane.reason}",
                f"- Next action: {lane.next_action}",
                f"- Likely target branch: `{lane.likely_target_branch}`",
                f"- Landing order: `{lane.landing_sequence if lane.landing_sequence is not None else 'not land-now'}`",
                f"- Worktree path: `{lane.worktree_path or 'unknown'}`",
                f"- Worktree exists: `{lane.worktree_exists}`",
                f"- Worktree dirty: `{lane.worktree_dirty}`",
                f"- Branch matches: `{lane.branch_matches}`",
                f"- Branch conflict: `{lane.branch_conflict}`",
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

    def write_directory(self, plan: LandPlan, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "land.md").write_text(self.render_markdown(plan), encoding="utf-8")
        (out / "land.json").write_text(plan.to_json(), encoding="utf-8")
        lanes_dir = out / "lanes"
        for lane in plan.lanes:
            lane_dir = lanes_dir / lane.lane_id
            lane_dir.mkdir(parents=True, exist_ok=True)
            (lane_dir / "land.json").write_text(json.dumps(lane.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            (lane_dir / "land.md").write_text(self._render_lane_markdown(lane), encoding="utf-8")
            (lane_dir / "packet.md").write_text(self._render_packet_markdown(lane), encoding="utf-8")
        return out

    def _render_lane_markdown(self, lane: LandLane) -> str:
        lines = [
            f"# Land lane: {lane.lane_id}",
            "",
            f"- Title: {lane.title}",
            f"- Bucket: `{lane.land_bucket}`",
            f"- Reason: {lane.reason}",
            f"- Next action: {lane.next_action}",
            f"- Likely target branch: `{lane.likely_target_branch}`",
            f"- Landing order: `{lane.landing_sequence if lane.landing_sequence is not None else 'not land-now'}`",
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

    def _render_packet_markdown(self, lane: LandLane) -> str:
        lines = [
            f"# Landing packet: {lane.lane_id}",
            "",
            f"- Land bucket: `{lane.land_bucket}`",
            f"- Landing readiness reason: {lane.reason}",
            f"- Next operator action: {lane.next_action}",
            f"- Likely target branch: `{lane.likely_target_branch}`",
            f"- Landing order: `{lane.landing_sequence if lane.landing_sequence is not None else 'not land-now'}`",
            f"- Branch: `{lane.branch_name}`",
            f"- Current worktree path: `{lane.worktree_path or 'unknown'}`",
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
            lines.extend(["", "## Human verification before local landing or archival", ""])
            for item in lane.human_checks:
                lines.append(f"- {item}")
        if lane.follow_on_notes:
            lines.extend(["", "## Follow-on notes", ""])
            for item in lane.follow_on_notes:
                lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def _land_bucket(
        self,
        *,
        lane_id: str,
        closeout_bucket: str,
        relaunch_bucket: str,
        reconcile_bucket: str,
        worktree_state: dict[str, Any],
        dependencies: list[LandDependency],
        serialization_group: str,
        blocked_groups: set[str],
        closed_or_plannable: set[str],
        source_reason: str,
    ) -> tuple[str, str, str, list[str]]:
        human_checks: list[str] = []
        if closeout_bucket == "merge-ready":
            pending_dependencies = [dep.lane_id for dep in dependencies if not dep.satisfied and dep.lane_id not in closed_or_plannable]
            if pending_dependencies:
                human_checks.append("Saved dependencies are still not fully closed or planned ahead of this lane.")
                return (
                    "waiting",
                    source_reason or f"Lane {lane_id} cannot land yet because dependencies remain pending: {', '.join(pending_dependencies)}.",
                    "Wait for prerequisite lanes to land or close before planning this merge.",
                    human_checks,
                )
            if serialization_group and serialization_group in blocked_groups:
                human_checks.append("An earlier lane in the same serialization group still requires review or waiting.")
                return (
                    "waiting",
                    source_reason or f"Lane {lane_id} must keep waiting until earlier serialized lanes clear local landing review.",
                    "Keep this lane queued behind the unresolved serialized lane.",
                    human_checks,
                )
            if not worktree_state["exists"]:
                human_checks.append("Worktree path is stale or missing. Confirm whether the branch was already landed or intentionally removed.")
                return (
                    "review-required",
                    source_reason or f"Lane {lane_id} is marked merge-ready in closeout state but its local worktree is missing.",
                    "Inspect branch history and local refs before landing or archiving.",
                    human_checks,
                )
            if worktree_state["dirty"]:
                human_checks.append("Local worktree has uncommitted changes.")
                return (
                    "review-required",
                    source_reason or f"Lane {lane_id} is not safe to land because the worktree is dirty.",
                    "Inspect, commit, or discard local changes before landing.",
                    human_checks,
                )
            if not worktree_state["branch_matches"] or worktree_state["branch_conflict"]:
                human_checks.append("Current branch state no longer matches the saved launch branch.")
                return (
                    "review-required",
                    source_reason or f"Lane {lane_id} has conflicting local branch state and needs human review before landing.",
                    "Confirm the correct branch tip before landing.",
                    human_checks,
                )
            human_checks.extend([
                "Verify the lane's tests and review evidence one final time before local merge.",
                "Land this lane locally in the listed order, then archive its packet.",
            ])
            return (
                "land-now",
                source_reason or f"Lane {lane_id} is merge-ready, locally clean, and safe to place in the landing order.",
                "Land this lane locally, then archive its landing packet.",
                human_checks,
            )
        if closeout_bucket == "review-required":
            human_checks.append("Saved closeout state already requires human review.")
            return (
                "review-required",
                source_reason or f"Lane {lane_id} still requires manual inspection before local landing or archival.",
                "Review the lane manually before landing, relaunching, or archiving it.",
                human_checks,
            )
        if closeout_bucket == "waiting":
            if any(not dep.satisfied for dep in dependencies):
                human_checks.append("Upstream dependencies are still unresolved.")
            if relaunch_bucket == "relaunch-now" or reconcile_bucket in {"ready", "relaunch-ready"}:
                human_checks.append("Saved continuation evidence still points to active execution work, not landing.")
            return (
                "waiting",
                source_reason or f"Lane {lane_id} must remain waiting until continuation and dependency conditions clear.",
                "Keep this lane visible but do not land or archive it yet.",
                human_checks,
            )
        if closeout_bucket == "already-closed":
            return (
                "already-closed",
                source_reason or f"Lane {lane_id} is already closed and stays as archival context only.",
                "Keep this lane as archival context only.",
                human_checks,
            )
        raise LandError(f"Saved closeout evidence is contradictory: unsupported closeout bucket {closeout_bucket!r} for lane {lane_id!r}.")

    def _target_branch_context(self, root: Path) -> str:
        remote_head = self._git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
        if remote_head:
            return remote_head.split("/", 1)[-1]
        branch = self._git(root, "rev-parse", "--abbrev-ref", "HEAD", check=False)
        return branch or "main"

    def _worktree_state(self, worktree_path: str, *, branch_name: str) -> dict[str, Any]:
        state = {"exists": False, "dirty": False, "branch_matches": False, "branch_conflict": False, "head_oid": None}
        if not worktree_path:
            return state
        path = Path(worktree_path).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return state
        state["exists"] = True
        branch = self._git(path, "rev-parse", "--abbrev-ref", "HEAD", check=False)
        head = self._git(path, "rev-parse", "HEAD", check=False)
        dirty = self._git(path, "status", "--porcelain", check=False)
        state["dirty"] = any(line.strip() and ".agentkit/" not in line for line in dirty.splitlines())
        state["branch_matches"] = bool(branch_name) and branch.strip() == branch_name
        state["branch_conflict"] = bool(branch.strip()) and bool(branch_name) and branch.strip() != branch_name
        state["head_oid"] = head.strip() or None
        return state

    def _git(self, repo: Path, *args: str, check: bool) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
        if check and result.returncode != 0:
            raise LandError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
        return result.stdout.strip()

    def _load_closeout(self, root: Path, *, closeout_path: str | Path | None) -> tuple[Path, dict[str, Any]]:
        candidates: list[Path]
        if closeout_path is None:
            candidates = [root / "closeout.json", root / "closeout" / "closeout.json", root / "artifacts" / "closeout.json", root / ".agentkit" / "closeout.json"]
        else:
            requested = Path(closeout_path).expanduser().resolve()
            candidates = [requested / "closeout.json"] if requested.is_dir() else [requested]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve(), self._read_json(candidate)
        raise FileNotFoundError("No closeout.json artifact found. Save a closeout packet first, then run agentkit land.")

    def _load_required_json(self, path: Path, *, label: str) -> tuple[Path, dict[str, Any]]:
        value = str(path).strip()
        if not value:
            raise LandError(f"Saved closeout artifact is incomplete: missing {label}.")
        if not path.exists() or not path.is_file():
            raise LandError(f"Saved closeout artifact points at a missing {label}: {path}")
        return path.resolve(), self._read_json(path)

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LandError(f"Saved land evidence is malformed JSON: {path}") from exc
        if not isinstance(data, dict):
            raise LandError(f"Saved land evidence must be a JSON object: {path}")
        return data

    def _optional_file(self, path: Any) -> Path | None:
        value = str(path or "").strip()
        if not value:
            return None
        candidate = Path(value).expanduser().resolve()
        if not candidate.exists() or not candidate.is_file():
            raise LandError(f"Saved closeout artifact points at a missing upstream artifact: {candidate}")
        return candidate

    def _validate_closeout_shape(self, closeout: dict[str, Any]) -> None:
        if str(closeout.get("schema_version") or "") != "agentkit.closeout.v1":
            raise LandError("Saved closeout artifact is not a supported agentkit.closeout.v1 packet.")
        summary = {
            "merge-ready": {str(item) for item in closeout.get("merge_ready_lane_ids") or []},
            "review-required": {str(item) for item in closeout.get("review_required_lane_ids") or []},
            "waiting": {str(item) for item in closeout.get("waiting_lane_ids") or []},
            "already-closed": {str(item) for item in closeout.get("already_closed_lane_ids") or []},
        }
        for lane in closeout.get("lanes") or []:
            lane_id = str(lane.get("lane_id") or "")
            bucket = str(lane.get("closeout_bucket") or "")
            if bucket not in summary:
                raise LandError(f"Saved closeout artifact is contradictory: unsupported closeout bucket {bucket!r} for lane {lane_id!r}.")
            if lane_id not in summary[bucket]:
                raise LandError(f"Saved closeout artifact is contradictory: lane {lane_id!r} bucket {bucket!r} disagrees with summary ids.")

    def _validate_relaunch_shape(self, relaunch: dict[str, Any], *, closeout_path: Path) -> None:
        if str(relaunch.get("schema_version") or "") != "agentkit.relaunch.v1":
            raise LandError("Saved relaunch artifact is not a supported agentkit.relaunch.v1 packet.")
        if not str(closeout_path):
            raise LandError("Saved land evidence is contradictory: missing closeout path.")

    def _validate_resume_shape(self, resume: dict[str, Any], *, reconcile_path: Path) -> None:
        if str(resume.get("schema_version") or "") != "agentkit.resume.v1":
            raise LandError("Saved resume artifact is not a supported agentkit.resume.v1 packet.")
        if Path(str(resume.get("reconcile_path") or "")).expanduser().resolve() != reconcile_path.resolve():
            raise LandError("Saved land evidence is contradictory: resume.reconcile_path does not match closeout.reconcile_path.")

    def _validate_reconcile_shape(self, reconcile: dict[str, Any], *, launch_path: Path) -> None:
        if str(reconcile.get("schema_version") or "") != "agentkit.reconcile.v1":
            raise LandError("Saved reconcile artifact is not a supported agentkit.reconcile.v1 packet.")
        if Path(str(reconcile.get("launch_path") or "")).expanduser().resolve() != launch_path.resolve():
            raise LandError("Saved land evidence is contradictory: reconcile.launch_path does not match closeout.launch_path.")
