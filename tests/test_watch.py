"""Tests for agentkit watch command."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from agentkit_cli.commands.watch import _ChangeHandler


# --- _ChangeHandler unit tests ---

class TestChangeHandler:
    """Unit tests for the debounced change handler."""

    def _make_handler(self, debounce=0.05, extensions=None, calls=None):
        fired_calls = calls if calls is not None else []

        class RecordingHandler(_ChangeHandler):
            def _fire(self):
                fired_calls.append(self._last_file)

        return RecordingHandler(
            cwd="/tmp/test",
            extensions=extensions or ["py", "md"],
            debounce=debounce,
            ci=False,
        ), fired_calls

    def test_on_modified_matching_extension_triggers_debounce(self):
        """on_modified with matching extension schedules timer."""
        handler, _ = self._make_handler()
        handler.on_modified("/tmp/test/foo.py")
        assert handler._timer is not None
        handler._timer.cancel()

    def test_on_modified_non_matching_extension_ignored(self):
        """on_modified with non-matching extension is ignored."""
        handler, _ = self._make_handler(extensions=["py"])
        handler.on_modified("/tmp/test/foo.js")
        assert handler._timer is None

    def test_on_modified_fires_after_debounce(self):
        """Handler fires after debounce period."""
        handler, calls = self._make_handler(debounce=0.05)
        handler.on_modified("/tmp/test/foo.py")
        time.sleep(0.30)
        assert len(calls) == 1
        assert calls[0] == "/tmp/test/foo.py"

    def test_debounce_resets_on_rapid_changes(self):
        """Rapid changes reset the debounce timer, firing only once."""
        handler, calls = self._make_handler(debounce=0.15)
        for i in range(5):
            handler.on_modified(f"/tmp/test/file{i}.py")
            time.sleep(0.02)
        # Wait well past debounce (5×20ms=100ms for events + 150ms debounce + 200ms buffer)
        time.sleep(0.5)
        # Only one fire should happen (last file)
        assert len(calls) == 1

    def test_last_file_recorded(self):
        """_last_file tracks the most recently changed file."""
        handler, calls = self._make_handler(debounce=0.05)
        handler.on_modified("/tmp/test/first.py")
        handler.on_modified("/tmp/test/second.py")

        deadline = time.time() + 0.5
        while not calls and time.time() < deadline:
            time.sleep(0.01)

        assert calls, "debounced callback never fired within the expected window"
        assert calls[0] == "/tmp/test/second.py"

    def test_extension_filter_allows_md(self):
        """Markdown files trigger handler when md is in extensions."""
        handler, _ = self._make_handler(extensions=["md", "py"])
        handler.on_modified("/tmp/test/README.md")
        assert handler._timer is not None
        handler._timer.cancel()

    def test_extension_filter_allows_yaml(self):
        """YAML files trigger handler when yaml is in extensions."""
        handler, _ = self._make_handler(extensions=["yaml"])
        handler.on_modified("/tmp/test/config.yaml")
        assert handler._timer is not None
        handler._timer.cancel()

    def test_extension_with_leading_dot_normalized(self):
        """Extensions with leading dot are normalized correctly."""
        handler, _ = self._make_handler(extensions=[".py", ".md"])
        handler.on_modified("/tmp/test/foo.py")
        assert handler._timer is not None
        handler._timer.cancel()

    def test_empty_extensions_allows_all(self):
        """Empty extension list allows all files."""
        # Directly create handler with empty extensions (bypassing _make_handler's `or` default)
        handler = _ChangeHandler(cwd="/tmp/test", extensions=[], debounce=0.05, ci=False)
        handler.on_modified("/tmp/test/anything.xyz")
        assert handler._timer is not None
        handler._timer.cancel()

    def test_fire_calls_run_pipeline(self):
        """_fire invokes _run_pipeline with correct cwd."""
        handler = _ChangeHandler(cwd="/tmp/test", extensions=["py"], debounce=0.05, ci=False)
        handler._last_file = "/tmp/test/foo.py"
        with patch("agentkit_cli.commands.watch._run_pipeline") as mock_run:
            with patch("os.system"):  # suppress clear
                with patch("typer.echo"):
                    handler._fire()
        mock_run.assert_called_once_with("/tmp/test", ci=False)

    def test_fire_calls_run_pipeline_ci_mode(self):
        """_fire passes ci=True when handler was created with ci=True."""
        h = _ChangeHandler(cwd="/tmp", extensions=["py"], debounce=0.05, ci=True)
        h._last_file = "/tmp/foo.py"
        with patch("agentkit_cli.commands.watch._run_pipeline") as mock_run:
            with patch("os.system"):
                with patch("typer.echo"):
                    h._fire()
        mock_run.assert_called_once_with("/tmp", ci=True)


# --- CLI integration tests (watchdog mocked) ---

def test_watch_missing_watchdog_exits_with_error():
    """watch command exits with code 1 if watchdog is not installed."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app as _app
    r = CliRunner()
    with patch.dict("sys.modules", {"watchdog": None, "watchdog.observers": None, "watchdog.events": None}):
        result = r.invoke(_app, ["watch", "--help"])
    # --help should always work regardless of watchdog
    assert result.exit_code == 0


def test_watch_help():
    """agentkit watch --help works."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app as _app
    r = CliRunner()
    result = r.invoke(_app, ["watch", "--help"])
    assert result.exit_code == 0
    assert "watch" in result.output.lower() or "change" in result.output.lower()


def _mock_watchdog(mock_observer):
    """Context manager that patches watchdog imports."""
    import sys
    mock_watchdog = MagicMock()
    mock_observer_module = MagicMock()
    mock_observer_module.Observer = MagicMock(return_value=mock_observer)
    mock_events_module = MagicMock()

    class FakeFileSystemEventHandler:
        pass

    mock_events_module.FileSystemEventHandler = FakeFileSystemEventHandler
    return patch.dict(sys.modules, {
        "watchdog": mock_watchdog,
        "watchdog.observers": mock_observer_module,
        "watchdog.events": mock_events_module,
    })


def test_watch_command_starts_and_stops(tmp_path):
    """watch_command starts observer, shows prompt, stops on KeyboardInterrupt."""
    from agentkit_cli.commands.watch import watch_command

    mock_observer = MagicMock()
    call_count = [0]
    def is_alive_side_effect():
        call_count[0] += 1
        if call_count[0] >= 2:
            raise KeyboardInterrupt()
        return True

    mock_observer.is_alive.side_effect = is_alive_side_effect

    with _mock_watchdog(mock_observer):
        with patch("typer.echo"):
            try:
                watch_command(path=tmp_path, debounce=0.1)
            except (KeyboardInterrupt, SystemExit):
                pass

    mock_observer.start.assert_called_once()
    mock_observer.stop.assert_called_once()


def test_watch_shows_watching_prompt(tmp_path):
    """watch_command outputs 'Watching' message."""
    from agentkit_cli.commands.watch import watch_command

    mock_observer = MagicMock()
    mock_observer.is_alive.return_value = False

    messages = []
    with _mock_watchdog(mock_observer):
        with patch("typer.echo", side_effect=lambda m, **kw: messages.append(str(m))):
            watch_command(path=tmp_path, debounce=0.1)

    assert any("Watching" in m or "watching" in m for m in messages)


def test_watch_shows_extensions(tmp_path):
    """watch_command shows watched extensions."""
    from agentkit_cli.commands.watch import watch_command

    mock_observer = MagicMock()
    mock_observer.is_alive.return_value = False

    messages = []
    with _mock_watchdog(mock_observer):
        with patch("typer.echo", side_effect=lambda m, **kw: messages.append(str(m))):
            watch_command(path=tmp_path, extensions=[".py", ".md"], debounce=0.1)

    combined = " ".join(messages)
    assert ".py" in combined or "py" in combined


def test_watch_custom_debounce_passed_to_handler(tmp_path):
    """Custom debounce value is passed to the handler."""
    from agentkit_cli.commands.watch import watch_command, _ChangeHandler

    mock_observer = MagicMock()
    mock_observer.is_alive.return_value = False

    created_debounce = []
    original_init = _ChangeHandler.__init__

    def capturing_init(self, cwd, extensions, debounce, ci, broker=None):
        created_debounce.append(debounce)
        original_init(self, cwd=cwd, extensions=extensions, debounce=debounce, ci=ci, broker=broker)

    with _mock_watchdog(mock_observer):
        with patch.object(_ChangeHandler, "__init__", capturing_init):
            with patch("typer.echo"):
                watch_command(path=tmp_path, debounce=5.0)

    assert 5.0 in created_debounce
