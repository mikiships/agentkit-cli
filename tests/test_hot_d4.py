"""Tests for agentkit hot D4 — doctor integration and run integration."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest


def test_doctor_has_hot_check():
    from agentkit_cli.doctor import check_hot_trending_access
    assert callable(check_hot_trending_access)


def test_hot_trending_access_pass():
    from agentkit_cli.doctor import check_hot_trending_access
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = check_hot_trending_access()
    assert result.status == "pass"
    assert result.id == "hot.trending_access"
    assert result.category == "hot"


def test_hot_trending_access_warn_non_200():
    from agentkit_cli.doctor import check_hot_trending_access
    mock_resp = MagicMock()
    mock_resp.status = 503
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = check_hot_trending_access()
    assert result.status == "warn"


def test_hot_trending_access_warn_on_exception():
    from agentkit_cli.doctor import check_hot_trending_access
    with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
        result = check_hot_trending_access()
    assert result.status == "warn"
    assert "timeout" in result.summary


def test_doctor_includes_hot_check():
    """run_doctor should include the hot.trending_access check."""
    from pathlib import Path
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "README.md").write_text("# test")
        (p / "pyproject.toml").write_text("[project]\nname='test'\n")

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'{"rate":{"remaining":60}}'
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_resp

            from agentkit_cli.doctor import run_doctor
            report = run_doctor(root=p)

        check_ids = [c.id for c in report.checks]
        assert "hot.trending_access" in check_ids


def test_hot_command_importable():
    from agentkit_cli.commands.hot_cmd import hot_command
    assert callable(hot_command)


def test_hot_engine_importable():
    from agentkit_cli.hot import HotEngine
    assert HotEngine is not None


def test_hot_registered_in_app():
    """agentkit app should have a 'hot' command registered."""
    from agentkit_cli.main import app
    command_names = [c.name for c in app.registered_commands]
    assert "hot" in command_names
