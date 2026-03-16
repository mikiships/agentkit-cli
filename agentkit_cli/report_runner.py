"""Tool runner utilities for agentkit report command.

All quartet tool invocations are delegated to ``ToolAdapter`` in ``tools.py``.
These functions maintain backward-compatible signatures.
"""
from __future__ import annotations

import logging
from typing import Optional

from agentkit_cli.tools import get_adapter

logger = logging.getLogger(__name__)

TOOL_TIMEOUT = 60  # kept for backward compat (ToolAdapter has its own default)
REFLECT_TIMEOUT = 30


def run_agentlint_check(path: str) -> Optional[dict]:
    """Run agentlint check-context on path, return parsed JSON or None."""
    return get_adapter().agentlint_check_context(path)


def run_agentmd_score(path: str) -> Optional[dict]:
    """Run agentmd score on path, return parsed JSON or None."""
    return get_adapter().agentmd_score(path)


def run_coderace_bench(path: str) -> Optional[dict]:
    """Check coderace benchmark history for cached results."""
    return get_adapter().coderace_benchmark_history(path)


def run_agentreflect_analyze(path: str) -> Optional[dict]:
    """Run agentreflect generate on path, return dict with markdown suggestions."""
    return get_adapter().agentreflect_from_git(path)
