"""Tests for D4: agentkit demo --record VHS tape generation."""
from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.demo_cmd import _DEMO_TAPE_CONTENT, demo_record_command

runner = CliRunner()


def test_demo_record_flag_exists():
    """--record flag should be recognized."""
    result = runner.invoke(app, ["demo", "--help"])
    assert "--record" in result.output


def test_demo_record_creates_tape(tmp_path):
    """demo --record should write demo.tape to the output path."""
    tape_path = tmp_path / "demo.tape"
    result = runner.invoke(app, ["demo", "--record", "--record-output", str(tape_path)])
    assert result.exit_code == 0, f"Exit {result.exit_code}: {result.output}"
    assert tape_path.exists(), "demo.tape should be created"


def test_demo_tape_content_valid(tmp_path):
    """demo.tape content should be valid VHS syntax."""
    tape_path = tmp_path / "demo.tape"
    runner.invoke(app, ["demo", "--record", "--record-output", str(tape_path)])
    content = tape_path.read_text()
    assert "Output" in content
    assert "Type" in content
    assert "agentkit quickstart" in content


def test_demo_tape_has_gif_output():
    """Tape content should reference an Output gif."""
    assert "demo.gif" in _DEMO_TAPE_CONTENT


def test_demo_tape_has_vhs_directives():
    """Tape should have Sleep and Set directives."""
    assert "Sleep" in _DEMO_TAPE_CONTENT
    assert "Set" in _DEMO_TAPE_CONTENT


def test_demo_record_prints_instructions(tmp_path):
    """Should print recording instructions to console."""
    tape_path = tmp_path / "demo.tape"
    result = runner.invoke(app, ["demo", "--record", "--record-output", str(tape_path)])
    assert "vhs" in result.output.lower() or "VHS" in result.output


def test_demo_record_does_not_run_pipeline(tmp_path):
    """With --record, the demo pipeline should NOT run (no project detection)."""
    tape_path = tmp_path / "demo.tape"
    result = runner.invoke(app, ["demo", "--record", "--record-output", str(tape_path)])
    # Should NOT contain pipeline table output
    assert "Pipeline Steps" not in result.output


def test_readme_has_demo_section():
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "Demo" in readme
    assert "demo.tape" in readme or "demo --record" in readme
