from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from agentkit_cli.analyze import parse_target
from agentkit_cli.models import (
    RepoMap,
    RepoMapContractHandoff,
    RepoMapEntryPoint,
    RepoMapHint,
    RepoMapImportantPath,
    RepoMapScript,
    RepoMapSubsystem,
    RepoMapSummary,
    RepoMapTestSurface,
)
from agentkit_cli.search import SearchEngine

IGNORED_DIRS = {
    '.git', '.hg', '.svn', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '.tox', '.venv', 'venv', 'node_modules', 'dist', 'build', '.next', '.turbo',
    'coverage', '.coverage', '.idea', '.vscode'
}
IMPORTANT_FILENAMES = [
    'README.md', 'README.rst', 'pyproject.toml', 'package.json', 'Cargo.toml', 'go.mod',
    'Makefile', 'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', 'AGENTS.md',
    'CLAUDE.md', '.agentkit.toml', '.agentkit/source.md'
]
ENTRYPOINT_FILES = {
    'main.py', '__main__.py', 'app.py', 'server.py', 'manage.py', 'index.js', 'index.ts',
    'main.ts', 'main.js', 'cli.py', 'cli.ts', 'wsgi.py', 'asgi.py'
}
TEST_DIR_MARKERS = {'tests', 'test', '__tests__', 'spec'}
LANGUAGE_BY_SUFFIX = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.rs': 'Rust',
    '.go': 'Go',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.sh': 'Shell',
    '.zsh': 'Shell',
}


class RepoMapEngine:
    def map_target(self, target: str) -> RepoMap:
        resolved, _name = parse_target(target)
        if target.startswith(('.', '/', '~')):
            return self.map_local_path(Path(resolved))

        url = target
        if target.startswith('github:'):
            slug = target[len('github:'):]
            info = SearchEngine().check_repo(*slug.split('/', 1))
            return RepoMap(
                target=target,
                target_kind='github',
                resolved_path=None,
                repo_slug=info.full_name,
                summary=RepoMapSummary(name=info.repo, root='github:' + info.full_name, total_files=0, total_dirs=0),
                languages=[],
                important_paths=[],
                entrypoints=[],
                scripts=[],
                tests=[],
                subsystems=[],
                hints=[RepoMapHint(kind='remote_target', severity='info', title='Remote target requires a checkout', detail='Run agentkit map on a local checkout to generate the full repo map offline.')],
                risks=[],
                contract_handoff=RepoMapContractHandoff(
                    suggested_artifact='map.json',
                    summary_lines=['Fetch or clone the repo, then re-run agentkit map on the checkout.'],
                    contract_prompt='Use the generated local repo map as the explorer artifact before drafting a build contract.',
                ),
            )
        raise ValueError(f'Unsupported target: {url}')

    def map_local_path(self, root: Path) -> RepoMap:
        root = root.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f'Path not found: {root}')

        files: list[Path] = []
        dirs: set[Path] = {root}
        for dirpath, dirnames, filenames in self._walk(root):
            current = Path(dirpath)
            dirs.add(current)
            for name in sorted(filenames):
                path = current / name
                files.append(path)

        rel_files = [p.relative_to(root) for p in files]
        language_counts = Counter()
        top_dirs = Counter()
        important_paths: list[RepoMapImportantPath] = []
        entrypoints: list[RepoMapEntryPoint] = []
        scripts: list[RepoMapScript] = []
        tests: list[RepoMapTestSurface] = []
        test_dirs: set[str] = set()
        code_dirs: Counter[str] = Counter()

        package_json = self._read_json(root / 'package.json')
        pyproject_text = self._read_text(root / 'pyproject.toml')

        for rel_path in rel_files:
            suffix = rel_path.suffix.lower()
            if suffix in LANGUAGE_BY_SUFFIX:
                language_counts[LANGUAGE_BY_SUFFIX[suffix]] += 1
            top = rel_path.parts[0] if len(rel_path.parts) > 1 else '.'
            top_dirs[top] += 1
            if self._is_code_file(rel_path):
                code_dirs[top] += 1

            rel_str = rel_path.as_posix()
            file_name = rel_path.name
            if file_name in IMPORTANT_FILENAMES or rel_str in IMPORTANT_FILENAMES:
                important_paths.append(RepoMapImportantPath(path=rel_str, kind='config' if suffix in {'.toml', '.json', '.yml', '.yaml'} else 'doc'))

            if file_name in ENTRYPOINT_FILES or rel_str in {'src/__main__.py'}:
                entrypoints.append(RepoMapEntryPoint(path=rel_str, kind=self._entrypoint_kind(file_name), reason='matched known entrypoint filename'))
            elif file_name == 'package.json' and package_json:
                if 'bin' in package_json:
                    entrypoints.append(RepoMapEntryPoint(path=rel_str, kind='cli', reason='package.json bin field present'))
                if any(key in package_json for key in ('main', 'module', 'exports')):
                    entrypoints.append(RepoMapEntryPoint(path=rel_str, kind='package', reason='package.json runtime entry fields present'))
            elif file_name == 'pyproject.toml' and ('[project.scripts]' in pyproject_text or '[project.entry-points' in pyproject_text):
                entrypoints.append(RepoMapEntryPoint(path=rel_str, kind='cli', reason='pyproject defines scripts or entry points'))

            if file_name == 'package.json' and package_json:
                for script_name, command in sorted((package_json.get('scripts') or {}).items()):
                    scripts.append(RepoMapScript(name=script_name, command=str(command), source=rel_str))
            elif file_name == 'Makefile':
                for target in self._parse_makefile_targets(root / rel_path):
                    scripts.append(RepoMapScript(name=target, command=f'make {target}', source=rel_str))

            if self._is_test_path(rel_path):
                area = rel_path.parts[0] if len(rel_path.parts) > 1 else rel_path.parent.as_posix()
                test_dirs.add(area)
                tests.append(RepoMapTestSurface(path=rel_str, kind=self._test_kind(rel_path), related_area=self._related_area(rel_path)))

        important_paths = self._sorted_unique_paths(important_paths)
        entrypoints = self._sorted_unique_entrypoints(entrypoints)
        scripts.sort(key=lambda item: (item.name, item.command, item.source))
        tests.sort(key=lambda item: (item.path, item.kind, item.related_area or ''))

        subsystems = self._infer_subsystems(root, top_dirs, code_dirs, test_dirs, rel_files, package_json, pyproject_text)
        hints, risks = self._build_hints(root, subsystems, scripts, tests, important_paths, rel_files)

        summary = RepoMapSummary(
            name=root.name,
            root=str(root),
            total_files=len(rel_files),
            total_dirs=max(len(dirs) - 1, 0),
            primary_language=self._primary_language(language_counts),
        )
        contract_handoff = self._build_contract_handoff(summary, subsystems, hints, scripts)

        return RepoMap(
            target=str(root),
            target_kind='local',
            resolved_path=str(root),
            repo_slug=None,
            summary=summary,
            languages=[{'language': k, 'files': language_counts[k]} for k in sorted(language_counts)],
            important_paths=important_paths,
            entrypoints=entrypoints,
            scripts=scripts,
            tests=tests,
            subsystems=subsystems,
            hints=hints,
            risks=risks,
            contract_handoff=contract_handoff,
        )

    def render_markdown(self, repo_map: RepoMap) -> str:
        lines = [
            f"# Repo map: {repo_map.summary.name}",
            '',
            '## Summary',
            f"- Root: `{repo_map.summary.root}`",
            f"- Files: {repo_map.summary.total_files}",
            f"- Directories: {repo_map.summary.total_dirs}",
            f"- Primary language: {repo_map.summary.primary_language or 'Unknown'}",
            '',
        ]
        lines.extend(self._section_lines('Languages', [f"- {row['language']}: {row['files']} file(s)" for row in repo_map.languages], empty='- None detected'))
        lines.extend(self._section_lines('Important paths', [f"- `{item.path}` ({item.kind})" for item in repo_map.important_paths], empty='- None'))
        lines.extend(self._section_lines('Entrypoints', [f"- `{item.path}` [{item.kind}] - {item.reason}" for item in repo_map.entrypoints], empty='- None detected'))
        lines.extend(self._section_lines('Scripts', [f"- `{item.name}` from `{item.source}`: `{item.command}`" for item in repo_map.scripts], empty='- None detected'))
        lines.extend(self._section_lines('Tests', [f"- `{item.path}` [{item.kind}]" + (f" -> {item.related_area}" if item.related_area else '') for item in repo_map.tests], empty='- No tests detected'))
        lines.extend(self._section_lines('Subsystems', [f"- **{item.name}** (`{item.path}`): {item.why}" for item in repo_map.subsystems], empty='- No subsystem boundaries inferred'))
        lines.extend(self._section_lines('Likely work surfaces', [f"- {item.title}: {item.detail}" for item in repo_map.hints if item.kind in {'next_task', 'work_surface'}], empty='- No hints generated'))
        lines.extend(self._section_lines('Risks', [f"- {item.title}: {item.detail}" for item in repo_map.risks], empty='- No major risks flagged'))
        lines.extend([
            '## Contract handoff',
            f"- Suggested artifact: `{repo_map.contract_handoff.suggested_artifact}`",
            *[f"- {line}" for line in repo_map.contract_handoff.summary_lines],
            '',
            '```text',
            repo_map.contract_handoff.contract_prompt,
            '```',
            '',
        ])
        return '\n'.join(lines).rstrip() + '\n'

    def render_text(self, repo_map: RepoMap) -> str:
        return self.render_markdown(repo_map).replace('`', '')

    @staticmethod
    def to_json(repo_map: RepoMap) -> str:
        return json.dumps(repo_map.to_dict(), indent=2, sort_keys=True)

    def _walk(self, root: Path) -> Iterable[tuple[str, list[str], list[str]]]:
        for dirpath, dirnames, filenames in __import__('os').walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRS and not d.startswith('.DS_Store'))
            filenames = [f for f in filenames if f != '.DS_Store']
            yield dirpath, dirnames, filenames

    def _read_json(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            return None

    def _read_text(self, path: Path) -> str:
        if not path.exists():
            return ''
        return path.read_text(encoding='utf-8', errors='replace')

    def _parse_makefile_targets(self, path: Path) -> list[str]:
        if not path.exists():
            return []
        targets: list[str] = []
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            if ':' not in line or line.startswith(('.', '\t', '#')):
                continue
            target = line.split(':', 1)[0].strip()
            if target and ' ' not in target:
                targets.append(target)
        return sorted(set(targets))

    def _is_code_file(self, rel_path: Path) -> bool:
        return rel_path.suffix.lower() in LANGUAGE_BY_SUFFIX and not self._is_test_path(rel_path)

    def _is_test_path(self, rel_path: Path) -> bool:
        parts = {part.lower() for part in rel_path.parts}
        name = rel_path.name.lower()
        return bool(parts & TEST_DIR_MARKERS) or name.startswith('test_') or name.endswith(('_test.py', '.spec.ts', '.test.ts', '.test.js'))

    def _test_kind(self, rel_path: Path) -> str:
        suffix = rel_path.suffix.lower()
        if suffix in {'.py', '.js', '.ts', '.tsx'}:
            return 'unit-or-integration'
        return 'test-artifact'

    def _related_area(self, rel_path: Path) -> str | None:
        parts = list(rel_path.parts)
        for marker in ('tests', 'test', '__tests__'):
            if marker in parts:
                idx = parts.index(marker)
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        return None

    def _entrypoint_kind(self, file_name: str) -> str:
        if 'cli' in file_name or file_name in {'manage.py', '__main__.py'}:
            return 'cli'
        if file_name in {'app.py', 'server.py', 'wsgi.py', 'asgi.py', 'index.js', 'index.ts'}:
            return 'service'
        return 'entrypoint'

    def _sorted_unique_paths(self, items: list[RepoMapImportantPath]) -> list[RepoMapImportantPath]:
        seen = {}
        for item in items:
            seen[(item.path, item.kind)] = item
        return [seen[key] for key in sorted(seen)]

    def _sorted_unique_entrypoints(self, items: list[RepoMapEntryPoint]) -> list[RepoMapEntryPoint]:
        seen = {}
        for item in items:
            seen[(item.path, item.kind, item.reason)] = item
        return [seen[key] for key in sorted(seen)]

    def _infer_subsystems(self, root: Path, top_dirs: Counter, code_dirs: Counter, test_dirs: set[str], rel_files: list[Path], package_json: dict | None, pyproject_text: str) -> list[RepoMapSubsystem]:
        candidates: list[RepoMapSubsystem] = []
        for name in sorted(code_dirs):
            if name == '.' or code_dirs[name] == 0:
                continue
            reasons = [f'{code_dirs[name]} code file(s)']
            if name in test_dirs:
                reasons.append('paired test directory')
            candidates.append(RepoMapSubsystem(name=name, path=name, why=', '.join(reasons)))
        if package_json and {'packages', 'workspaces'} & set(package_json.keys()):
            candidates.append(RepoMapSubsystem(name='workspace', path='package.json', why='package.json declares workspace-like structure'))
        if '[tool.pytest' in pyproject_text or '[project.scripts]' in pyproject_text:
            candidates.append(RepoMapSubsystem(name='python-tooling', path='pyproject.toml', why='pyproject centralizes Python build/test/tooling config'))
        uniq = {(c.name, c.path): c for c in candidates}
        return [uniq[key] for key in sorted(uniq)]

    def _build_hints(self, root: Path, subsystems: list[RepoMapSubsystem], scripts: list[RepoMapScript], tests: list[RepoMapTestSurface], important_paths: list[RepoMapImportantPath], rel_files: list[Path]) -> tuple[list[RepoMapHint], list[RepoMapHint]]:
        hints: list[RepoMapHint] = []
        risks: list[RepoMapHint] = []
        has_agents = any(item.path in {'AGENTS.md', 'CLAUDE.md', '.agentkit/source.md'} for item in important_paths)
        if not has_agents:
            risks.append(RepoMapHint(kind='risk', severity='warn', title='Missing agent context files', detail='No AGENTS.md, CLAUDE.md, or .agentkit/source.md found.'))
        if scripts:
            names = ', '.join(script.name for script in scripts[:3])
            hints.append(RepoMapHint(kind='work_surface', severity='info', title='Execution surfaces', detail=f'Start with scripts such as {names}.'))
        for subsystem in subsystems[:4]:
            hints.append(RepoMapHint(kind='next_task', severity='info', title=f'Explore {subsystem.name}', detail=f'Read {subsystem.path} and the nearest tests before changing behavior.'))
        test_paths = {test.related_area for test in tests if test.related_area}
        subsystem_names = {subsystem.name for subsystem in subsystems}
        missing_test_areas = sorted(name for name in subsystem_names if name not in test_paths and name not in {'python-tooling', 'workspace'})
        for area in missing_test_areas[:4]:
            risks.append(RepoMapHint(kind='risk', severity='warn', title=f'Low test coverage signal near {area}', detail=f'Found code in {area} without an obvious paired test surface.'))
        if any(path.name == 'package.json' for path in rel_files) and not any(script.name in {'test', 'lint', 'build'} for script in scripts):
            risks.append(RepoMapHint(kind='risk', severity='warn', title='Script-heavy repo lacks standard npm surfaces', detail='package.json exists but test/lint/build scripts are missing or unclear.'))
        if not tests:
            risks.append(RepoMapHint(kind='risk', severity='warn', title='No tests detected', detail='The repo map found no obvious test files or test directories.'))
        return self._unique_hints(hints), self._unique_hints(risks)

    def _unique_hints(self, items: list[RepoMapHint]) -> list[RepoMapHint]:
        uniq = {(item.kind, item.severity, item.title, item.detail): item for item in items}
        return [uniq[key] for key in sorted(uniq)]

    def _build_contract_handoff(self, summary: RepoMapSummary, subsystems: list[RepoMapSubsystem], hints: list[RepoMapHint], scripts: list[RepoMapScript]) -> RepoMapContractHandoff:
        summary_lines = [
            f'Repo: {summary.name}',
            f'Primary language: {summary.primary_language or "Unknown"}',
            'Subsystems: ' + (', '.join(item.name for item in subsystems[:5]) if subsystems else 'none inferred'),
            'Scripts: ' + (', '.join(item.name for item in scripts[:5]) if scripts else 'none detected'),
        ]
        next_tasks = [item.title for item in hints if item.kind == 'next_task'][:3]
        contract_prompt = '\n'.join([
            f'Use this repo map for {summary.name} as the explorer artifact.',
            'Keep deliverables grounded in these inferred work surfaces:',
            *(f'- {task}' for task in next_tasks),
            'Validate with the repo-native test/build commands surfaced in the map.',
        ])
        return RepoMapContractHandoff(
            suggested_artifact='map.json',
            summary_lines=summary_lines,
            contract_prompt=contract_prompt,
        )

    def _primary_language(self, counts: Counter) -> str | None:
        if not counts:
            return None
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _section_lines(self, title: str, body: list[str], empty: str) -> list[str]:
        return [f'## {title}', *(body or [empty]), '']
