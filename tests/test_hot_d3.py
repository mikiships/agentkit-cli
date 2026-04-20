"""Tests for agentkit hot D3 — post-hot.sh script."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "post-hot.sh"


def test_post_hot_sh_exists():
    assert SCRIPT_PATH.exists(), f"post-hot.sh not found at {SCRIPT_PATH}"


def test_post_hot_sh_is_executable():
    assert os.access(SCRIPT_PATH, os.X_OK), "post-hot.sh is not executable"


def test_post_hot_sh_has_dry_run_flag():
    content = SCRIPT_PATH.read_text()
    assert "--dry-run" in content


def test_post_hot_sh_has_share_flag():
    content = SCRIPT_PATH.read_text()
    assert "--share" in content


def test_post_hot_sh_logs_to_jsonl():
    content = SCRIPT_PATH.read_text()
    assert "hot-post-log.jsonl" in content


def test_post_hot_sh_uses_agentkit_hot():
    content = SCRIPT_PATH.read_text()
    assert "agentkit hot" in content


def test_post_hot_sh_uses_frigatebird():
    content = SCRIPT_PATH.read_text()
    assert "frigatebird" in content


def test_post_hot_sh_has_shebang():
    content = SCRIPT_PATH.read_text()
    assert content.startswith("#!/usr/bin/env bash")


def test_post_hot_sh_dry_run_exits_0(tmp_path, monkeypatch):
    """--dry-run should exit 0 when agentkit hot produces output."""
    # Create a fake agentkit that just echoes tweet text
    fake_agentkit = tmp_path / "agentkit"
    fake_agentkit.write_text("#!/usr/bin/env bash\necho 'Test tweet from agentkit hot'\n")
    fake_agentkit.chmod(0o755)

    # Create a fake jq that just echoes '{}'
    fake_jq = tmp_path / "jq"
    fake_jq.write_text("#!/usr/bin/env bash\necho '{}'\n")
    fake_jq.chmod(0o755)

    env = {
        "HOME": str(tmp_path),
        "XDG_DATA_HOME": str(tmp_path / ".local" / "share"),
        "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
    }

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"


def test_post_hot_sh_dry_run_prints_tweet(tmp_path):
    """--dry-run should print the tweet text."""
    fake_agentkit = tmp_path / "agentkit"
    fake_agentkit.write_text("#!/usr/bin/env bash\necho 'flask is #1 trending (45/100)'\n")
    fake_agentkit.chmod(0o755)

    fake_jq = tmp_path / "jq"
    fake_jq.write_text("#!/usr/bin/env bash\necho '{}'\n")
    fake_jq.chmod(0o755)

    env = {
        "HOME": str(tmp_path),
        "XDG_DATA_HOME": str(tmp_path / ".local" / "share"),
        "PATH": str(tmp_path) + ":" + os.environ.get("PATH", ""),
    }

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert "flask" in result.stdout or "trending" in result.stdout or "DRY RUN" in result.stdout
