"""SyncEngine: read HistoryDB → build entries → merge with data.json → write."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agentkit_cli.history import HistoryDB
from agentkit_cli.commands.pages_refresh import score_to_grade

DOCS_DIR = Path("docs")
DATA_JSON = DOCS_DIR / "data.json"


class SyncEngine:
    """Sync local history DB entries into docs/data.json."""

    def __init__(
        self,
        db: Optional[HistoryDB] = None,
        docs_dir: Optional[Path] = None,
    ) -> None:
        self._db = db or HistoryDB()
        self._docs_dir = docs_dir or DOCS_DIR
        self._data_json_path = self._docs_dir / "data.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read_history(self, limit: Optional[int] = None) -> list[dict]:
        """Return latest overall-score run per github: repo from history DB."""
        all_rows = self._db.get_history(tool="overall", limit=100_000)

        # Keep only github: repos
        github_rows = [r for r in all_rows if r["project"].startswith("github:")]

        # Pick latest run per repo
        seen: dict[str, dict] = {}
        for row in github_rows:
            project = row["project"]
            if project not in seen or row["ts"] > seen[project]["ts"]:
                seen[project] = row

        entries = list(seen.values())
        # Sort by score descending
        entries.sort(key=lambda r: r["score"], reverse=True)

        if limit is not None and limit > 0:
            entries = entries[:limit]

        return entries

    def build_entries(self, history_rows: list[dict]) -> list[dict]:
        """Convert history rows → data.json entry format with source=community."""
        result = []
        for row in history_rows:
            project = row["project"]  # e.g. "github:owner/repo"
            repo_name = project.removeprefix("github:")
            score = round(float(row["score"]), 1)
            details = row.get("details") or {}
            ecosystem = details.get("ecosystem", "") if isinstance(details, dict) else ""
            grade = score_to_grade(score)
            entry = {
                "name": repo_name,
                "url": f"https://github.com/{repo_name}",
                "score": score,
                "grade": grade,
                "ecosystem": ecosystem,
                "source": "community",
                "synced_at": row.get("ts", ""),
            }
            result.append(entry)
        return result

    def load_existing(self) -> dict:
        """Load existing data.json or return empty structure."""
        if self._data_json_path.exists():
            try:
                return json.loads(self._data_json_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"generated_at": "", "repos": [], "stats": {}}

    def merge_entries(
        self,
        existing_data: dict,
        new_entries: list[dict],
    ) -> tuple[dict, int, int]:
        """Merge new_entries into existing_data. Returns (merged_data, added, updated)."""
        # Build existing map: name -> entry
        existing_repos = existing_data.get("repos", [])

        # Ensure existing ecosystem entries have source field
        for entry in existing_repos:
            if "source" not in entry:
                entry["source"] = "ecosystem"

        existing_map: dict[str, dict] = {r["name"]: r for r in existing_repos}

        added = 0
        updated = 0

        for entry in new_entries:
            name = entry["name"]
            if name not in existing_map:
                existing_map[name] = entry
                added += 1
            else:
                existing = existing_map[name]
                # Ecosystem entries win if they exist (don't downgrade source)
                # Community entry only wins for non-ecosystem repos or if newer score
                existing_source = existing.get("source", "ecosystem")
                if existing_source == "ecosystem":
                    # Ecosystem wins — don't overwrite, but could update score if newer
                    # Per contract: "ecosystem entries win if they exist and are newer"
                    # We keep ecosystem source but update score if community run is newer
                    existing_synced = existing.get("synced_at", existing.get("generated_at", ""))
                    new_synced = entry.get("synced_at", "")
                    if new_synced and existing_synced and new_synced > existing_synced:
                        existing["score"] = entry["score"]
                        existing["grade"] = entry["grade"]
                        existing["synced_at"] = new_synced
                        updated += 1
                else:
                    # Community → community: newer wins
                    existing_synced = existing.get("synced_at", "")
                    new_synced = entry.get("synced_at", "")
                    if not existing_synced or (new_synced and new_synced >= existing_synced):
                        existing_map[name] = entry
                        updated += 1

        all_repos = sorted(existing_map.values(), key=lambda r: r["score"], reverse=True)

        import statistics as _stats
        scores = [r["score"] for r in all_repos]
        stats = {
            "total": len(all_repos),
            "median": round(_stats.median(scores), 1) if scores else 0,
            "top_score": round(max(scores), 1) if scores else 0,
        }

        merged = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repos": all_repos,
            "stats": stats,
        }
        return merged, added, updated

    def write_data_json(self, data: dict) -> None:
        """Write merged data to docs/data.json."""
        self._docs_dir.mkdir(parents=True, exist_ok=True)
        self._data_json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def git_push(self, total: int) -> bool:
        """Stage, commit and push docs/data.json. Returns True on success."""
        commit_msg = f"chore: update leaderboard [{total} repos]"
        cmds = [
            ["git", "add", str(self._data_json_path)],
            ["git", "commit", "-m", commit_msg],
            ["git", "push", "origin", "main"],
        ]
        for cmd in cmds:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # If nothing to commit that's fine
                if "nothing to commit" in result.stdout + result.stderr:
                    return True
                return False
        return True

    def sync(
        self,
        push: bool = True,
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> dict:
        """Run full sync. Returns summary dict."""
        history_rows = self.read_history(limit=limit)
        new_entries = self.build_entries(history_rows)
        existing_data = self.load_existing()
        merged_data, added, updated = self.merge_entries(existing_data, new_entries)
        total = merged_data["stats"]["total"]

        pushed = False
        if not dry_run:
            self.write_data_json(merged_data)
            if push:
                pushed = self.git_push(total)

        return {
            "added": added,
            "updated": updated,
            "total": total,
            "pushed": pushed,
            "dry_run": dry_run,
        }
