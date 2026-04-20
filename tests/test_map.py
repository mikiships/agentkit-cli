from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.map_engine import RepoMapEngine

runner = CliRunner()
FIXTURES = Path(__file__).parent / 'fixtures' / 'map'


def test_map_engine_basic_fixture():
    repo_map = RepoMapEngine().map_local_path(FIXTURES / 'basic_repo')

    assert repo_map.summary.name == 'basic_repo'
    assert repo_map.summary.total_files >= 6
    assert repo_map.summary.primary_language == 'Python'
    assert any(item.path == 'src/main.py' for item in repo_map.entrypoints)
    assert any(item.name == 'python-tooling' for item in repo_map.subsystems)
    assert any(item.path == 'tests/test_service.py' for item in repo_map.tests)
    assert any(item.title == 'Explore src' for item in repo_map.hints)
    assert repo_map.contract_handoff.suggested_artifact == 'map.json'


def test_map_engine_monorepo_fixture_infers_workspace():
    repo_map = RepoMapEngine().map_local_path(FIXTURES / 'monorepo')

    assert any(item.name == 'build' for item in repo_map.scripts)
    assert any(item.name == 'workspace' for item in repo_map.subsystems)
    assert any(item.path == 'package.json' for item in repo_map.entrypoints)
    assert any(risk.title.startswith('Low test coverage signal near packages') for risk in repo_map.risks)


def test_map_empty_repo_is_clean():
    repo_map = RepoMapEngine().map_local_path(FIXTURES / 'empty_repo')
    assert repo_map.summary.total_files == 1
    assert repo_map.tests == []
    assert any(risk.title == 'No tests detected' for risk in repo_map.risks)


def test_map_ignores_junk_directories(tmp_path):
    repo = tmp_path / 'junk-repo'
    (repo / 'src').mkdir(parents=True)
    (repo / 'node_modules' / 'left-pad').mkdir(parents=True)
    (repo / 'src' / 'main.py').write_text('print("hi")\n', encoding='utf-8')
    (repo / 'node_modules' / 'left-pad' / 'index.js').write_text('ignored\n', encoding='utf-8')

    repo_map = RepoMapEngine().map_local_path(repo)
    assert repo_map.summary.total_files == 1
    assert repo_map.summary.primary_language == 'Python'


def test_map_local_path_with_spaces(tmp_path):
    source = FIXTURES / 'basic_repo'
    target = tmp_path / 'repo with spaces'
    shutil.copytree(source, target)

    result = runner.invoke(app, ['map', str(target), '--json'])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data['summary']['name'] == 'repo with spaces'
    assert any(item['path'] == 'src/main.py' for item in data['entrypoints'])


def test_map_markdown_output_and_contract_handoff(tmp_path):
    out = tmp_path / 'map.md'
    result = runner.invoke(app, ['map', str(FIXTURES / 'basic_repo'), '--format', 'markdown', '--output', str(out)])
    assert result.exit_code == 0, result.output
    text = out.read_text(encoding='utf-8')
    assert '## Contract handoff' in text
    assert 'Use this repo map for basic_repo as the explorer artifact.' in text


def test_map_json_output_shape():
    result = runner.invoke(app, ['map', str(FIXTURES / 'basic_repo'), '--json'])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert set(data) >= {'summary', 'languages', 'important_paths', 'entrypoints', 'scripts', 'tests', 'subsystems', 'hints', 'risks', 'contract_handoff'}


def test_map_cli_text_output():
    result = runner.invoke(app, ['map', str(FIXTURES / 'script_heavy')])
    assert result.exit_code == 0, result.output
    assert 'repo map' in result.output.lower()
    assert 'Contract handoff' in result.output


def test_map_help():
    result = runner.invoke(app, ['map', '--help'])
    assert result.exit_code == 0
    assert '--format' in result.output


def test_map_invalid_path_exits_nonzero():
    result = runner.invoke(app, ['map', 'does-not-exist'])
    assert result.exit_code == 1
