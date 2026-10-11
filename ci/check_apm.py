#!/usr/bin/env python3
"""Check con/skills packaging and metadata-only restoration using real APM."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import yaml

from skill_common import find_skill_dirs

ROOT = Path(__file__).resolve().parent.parent


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', help='Published owner/repository#full-SHA')
    args = parser.parse_args()
    if args.source and not re.fullmatch(r'[\w.-]+/[\w.-]+#[0-9a-f]{40}', args.source):
        parser.error('--source must name owner/repository and a full commit SHA')
    names = [p.name for p in find_skill_dirs(ROOT)]
    if not names:
        raise RuntimeError('empty skill collection')
    # Local CI checks the complete collection; Git CI checks selective deployment.
    selection = ['install-apm-skills', 'author-apm-skills'] if args.source else names
    with tempfile.TemporaryDirectory(prefix='con-skills-apm-') as directory:
        base = Path(directory)
        package = base / 'package'
        package.mkdir()
        shutil.copy2(ROOT / 'apm.yml', package / 'apm.yml')
        for name in selection:
            shutil.copytree(ROOT / 'skills' / name, package / 'skills' / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        consumer = base / 'consumer'
        consumer.mkdir()
        run('git', 'init', '--quiet', cwd=consumer)
        if args.source:
            # Exercise the same public CLI route documented for consumers.
            run('apm', 'install', args.source, '--target', 'agent-skills',
                *[arg for name in selection for arg in ('--skill', name)],
                '--no-policy', cwd=consumer)
        else:
            (consumer / 'apm.yml').write_text(yaml.safe_dump({
                'name': 'con-skills-consumer', 'version': '0.0.0',
                'targets': ['agent-skills'],
                'dependencies': {'apm': [{'path': '../package', 'skills': selection}]},
            }))
            # Disposable fixtures have no organization policy or credentials.
            run('apm', 'install', '--no-policy', cwd=consumer)
        (consumer / '.gitignore').write_text((consumer / '.gitignore').read_text() + ''.join(
            f'/.agents/skills/{name}/\n' for name in selection))
        metadata = {name: (consumer / name).read_bytes()
                    for name in ('apm.yml', 'apm.lock.yaml', '.gitignore')}
        installed = snapshot(consumer / '.agents/skills')
        actual_names = {p.parts[0] for p in map(Path, installed)}
        if actual_names != set(selection):
            raise RuntimeError(f'unexpected deployed skills: {actual_names}')
        for relative, content in snapshot(package / 'skills').items():
            if relative not in installed:
                raise RuntimeError(f'missing deployed resource: {relative}')
            # APM rewrites Markdown links; other bundled resources must be exact.
            if not relative.endswith('.md') and installed[relative] != content:
                raise RuntimeError(f'changed deployed resource: {relative}')
        fresh = base / 'fresh'
        fresh.mkdir()
        for name, content in metadata.items():
            (fresh / name).write_bytes(content)
        run('git', 'init', '--quiet', cwd=fresh)
        run('git', 'add', '.', cwd=fresh)
        run('apm', 'install', '--frozen', '--no-policy', cwd=fresh)
        run('apm', 'audit', '--ci', '--no-policy', cwd=fresh)
        if snapshot(fresh / '.agents/skills') != installed:
            raise RuntimeError('frozen restore changed deployed content')
        run('git', 'diff', '--exit-code', cwd=fresh)
        untracked = subprocess.check_output(
            ['git', 'ls-files', '--others', '--exclude-standard'], cwd=fresh, text=True)
        if untracked.strip():
            raise RuntimeError(f'unexpected untracked files: {untracked}')
        if args.source:
            lock = yaml.safe_load((fresh / 'apm.lock.yaml').read_text())
            if not any(d.get('resolved_commit') == args.source.split('#')[1]
                       for d in lock['dependencies']):
                raise RuntimeError('lock does not contain the requested commit')
    print('Package resources and metadata-only restoration verified.')


if __name__ == '__main__':
    main()
