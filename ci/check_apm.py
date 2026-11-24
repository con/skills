#!/usr/bin/env python3
"""Check con/skills packaging and metadata-only restoration using real APM.

Every skill is its own APM package (``skills/<name>/apm.yml``), so consumers
depend on ``skills/<name>`` as a subdirectory of this repository and their
lock records that skill's own version.  This check installs each skill that
way into a disposable consumer, verifies the deployed files and the versions
in the lock, restores a fresh consumer from the manifest and lock with
``apm install --frozen``, audits it, and confirms the audit catches tampering.
The repository root is not a package: nobody installs con/skills as a whole.
"""
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


def skill_version(skill_dir: Path) -> str:
    return yaml.safe_load((skill_dir / 'apm.yml').read_text())['version']


def lock_entries(lock: object) -> list[dict]:
    dependencies = lock.get('dependencies') if isinstance(lock, dict) else None
    if not isinstance(dependencies, list):
        raise RuntimeError('lock has no dependency list')
    return [dep for dep in dependencies if isinstance(dep, dict)]


def check_pin(lock: object, source: str, versions: dict[str, str]) -> None:
    """Each skill is locked as its own subdirectory package at the requested commit.

    ``versions`` maps skill name to the version its ``apm.yml`` declares.
    """
    repository, commit = source.split('#')
    entries = lock_entries(lock)
    for name, version in versions.items():
        if not any(
            dep.get('resolved_commit') == commit
            and dep.get('repo_url') == repository.lower()
            and dep.get('host', 'github.com') == 'github.com'
            and dep.get('virtual_path') == f'skills/{name}'
            and dep.get('version') == version
            for dep in entries
        ):
            raise RuntimeError(f'lock does not pin skills/{name} {version} at the requested '
                               'repository and commit')


def check_local_versions(lock: object, versions: dict[str, str]) -> None:
    """Local-path packages are locked under their own name and version."""
    locked = {dep.get('name'): dep.get('version') for dep in lock_entries(lock)}
    for name, version in versions.items():
        if locked.get(name) != version:
            raise RuntimeError(f'lock records {name} as {locked.get(name)!r}, apm.yml says {version!r}')


def check_deployed(consumer: Path, package: Path, selection: list[str]) -> dict[str, bytes]:
    installed = snapshot(consumer / '.agents/skills')
    actual_names = {p.parts[0] for p in map(Path, installed)}
    if actual_names != set(selection):
        raise RuntimeError(f'unexpected deployed skills: {actual_names}')
    expected = {relative: content for relative, content in snapshot(package / 'skills').items()
                if Path(relative).parts[0] in selection}
    if installed.keys() != expected.keys():
        raise RuntimeError('deployed resource paths differ from package')
    for relative, content in expected.items():
        # APM rewrites Markdown links; other bundled resources must be exact.
        if not relative.endswith('.md') and installed[relative] != content:
            raise RuntimeError(f'changed deployed resource: {relative}')
    return installed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', help='Published owner/repository#full-SHA')
    args = parser.parse_args()
    if args.source and not re.fullmatch(r'[\w.-]+/[\w.-]+#[0-9a-f]{40}', args.source):
        parser.error('--source must name owner/repository and a full commit SHA')
    skill_dirs = find_skill_dirs(ROOT)
    if not skill_dirs:
        raise RuntimeError('empty skill collection')
    names = [p.name for p in skill_dirs]
    # Local CI checks the complete collection; Git CI checks selective deployment.
    selection = names[:2] if args.source else names
    versions = {p.name: skill_version(p) for p in skill_dirs if p.name in selection}
    with tempfile.TemporaryDirectory(prefix='con-skills-apm-') as directory:
        base = Path(directory)
        package = base / 'package'
        package.mkdir()
        for name in names:
            shutil.copytree(ROOT / 'skills' / name, package / 'skills' / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

        consumer = base / 'consumer'
        consumer.mkdir()
        run('git', 'init', '--quiet', cwd=consumer)
        # --no-policy is only for these disposable fixtures, which have no
        # organization policy or credentials.
        if args.source:
            # Exercise the same public CLI route documented for consumers.
            repository, commit = args.source.split('#')
            # One call: separate calls leave `target: legacy` deployments in
            # the lock, which a later frozen restore rewrites.
            run('apm', 'install', *[f'{repository}/skills/{name}#{commit}' for name in selection],
                '--target', 'agent-skills', '--no-policy', cwd=consumer)
        else:
            (consumer / 'apm.yml').write_text(yaml.safe_dump({
                'name': 'con-skills-consumer', 'version': '0.0.0',
                'targets': ['agent-skills'],
                'dependencies': {'apm': [{'path': f'../package/skills/{name}'}
                                         for name in selection]},
            }))
            run('apm', 'install', '--no-policy', cwd=consumer)
        ignore = consumer / '.gitignore'
        existing = ignore.read_text() if ignore.exists() else ''
        ignore.write_text(existing.rstrip('\n') + '\n/apm_modules/\n' + ''.join(
            f'/.agents/skills/{name}/\n' for name in selection))
        metadata = {name: (consumer / name).read_bytes()
                    for name in ('apm.yml', 'apm.lock.yaml', '.gitignore')}
        installed = check_deployed(consumer, package, selection)
        lock = yaml.safe_load(metadata['apm.lock.yaml'])
        if args.source:
            check_pin(lock, args.source, versions)
        else:
            check_local_versions(lock, versions)

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
        tampered = fresh / '.agents/skills' / selection[0] / 'SKILL.md'
        tampered.write_text(tampered.read_text() + '\nUnexpected modification.\n')
        audit = subprocess.run(['apm', 'audit', '--ci', '--no-policy'], cwd=fresh)
        if audit.returncode == 0:
            raise RuntimeError('audit accepted tampered skill content')
    print('Per-skill packages, versions in the lock, and metadata-only restoration verified.')


if __name__ == '__main__':
    main()
