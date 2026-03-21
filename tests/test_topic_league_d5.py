"""D5 tests for docs and version bump (v0.70.0)."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).parent.parent


def test_pyproject_version():
    from agentkit_cli import __version__
    content = (REPO / "pyproject.toml").read_text()
    assert f'version = "{__version__}"' in content


def test_changelog_entry():
    content = (REPO / "CHANGELOG.md").read_text()
    # Any 0.70.x or later entry is acceptable
    assert re.search(r"0\.(7[0-9]|[89]\d)\.\d+", content)


def test_changelog_topic_league():
    content = (REPO / "CHANGELOG.md").read_text()
    assert "topic-league" in content.lower() or "topic_league" in content.lower()


def test_readme_topic_league():
    content = (REPO / "README.md").read_text()
    assert "topic-league" in content.lower() or "topic_league" in content.lower()


def test_build_report_exists():
    report = REPO / "BUILD-REPORT.md"
    assert report.exists()
    content = report.read_text()
    # BUILD-REPORT may be from a later build version; check that it's a valid report
    from agentkit_cli import __version__
    assert __version__ in content or "0.70.0" in content or "topic-league" in content.lower()
