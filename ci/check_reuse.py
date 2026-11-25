#!/usr/bin/env python3
"""Check that each skill's apm.yml ``license`` matches what REUSE says its files carry.

REUSE (``REUSE.toml``, SPDX headers, ``LICENSES/``) records the license of
every file; APM reads only the ``license`` string in a skill's ``apm.yml`` and
copies it into consumers' locks and SBOMs. Neither tool reads the other, so
this check connects them: the licenses in a skill's ``apm.yml`` expression
must be exactly the licenses REUSE resolves for the files under
``skills/<name>/``. Run it after ``reuse lint`` (``tox -e reuse``).
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from license_expression import get_spdx_licensing
import yaml

from skill_common import find_skill_dirs

ROOT = Path(__file__).resolve().parent.parent
LICENSING = get_spdx_licensing()


def license_keys(expression: str) -> set[str]:
    return set(LICENSING.license_keys(LICENSING.parse(expression, validate=True, strict=True)))


def reuse_report() -> list[dict]:
    lint = subprocess.run(['reuse', '--root', str(ROOT), 'lint', '--json'],
                          capture_output=True, text=True, check=False)
    return json.loads(lint.stdout)['files']


def main() -> int:
    by_skill: dict[str, set[str]] = {}
    for entry in reuse_report():
        parts = Path(entry['path']).parts
        if len(parts) > 2 and parts[0] == 'skills':
            for spdx in entry['spdx_expressions']:
                by_skill.setdefault(parts[1], set()).update(license_keys(spdx['value']))

    errors = []
    for skill_dir in find_skill_dirs(ROOT):
        declared = yaml.safe_load((skill_dir / 'apm.yml').read_text()).get('license')
        try:
            declared_keys = license_keys(str(declared))
        except Exception as exc:  # license_expression raises several error types
            errors.append(f'{skill_dir.name}: apm.yml license {declared!r} is not an SPDX expression ({exc})')
            continue
        found = by_skill.get(skill_dir.name, set())
        if declared_keys != found:
            errors.append(f'{skill_dir.name}: apm.yml license {declared!r} names {sorted(declared_keys)}, '
                          f'but REUSE resolves its files to {sorted(found)}')
    for error in errors:
        print(error, file=sys.stderr)
    if not errors:
        print(f'apm.yml licenses match REUSE for {len(find_skill_dirs(ROOT))} skills.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
