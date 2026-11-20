#!/usr/bin/env python3
"""Print the per-skill release tags `<name>--v<version>` that do not exist yet.

APM resolves a semver range on a skill (a subdirectory package of this
repository) against tags named `<name>--v<version>`.  After a pull request
that bumps a skill's `apm.yml` version merges, a maintainer runs this on an
up-to-date `master` checkout and creates the printed tags on that merge
commit, e.g.:

    git checkout master && git pull --ff-only origin master && git fetch --tags origin
    tags=$(python3 ci/skill_tags.py)
    for tag in $tags; do git tag -a "$tag" -m "$tag"; done
    git push origin $tags
"""
from __future__ import annotations

from pathlib import Path
import subprocess

import yaml

from skill_common import find_skill_dirs

ROOT = Path(__file__).resolve().parent.parent


def release_tag(skill_dir: Path) -> str:
    version = yaml.safe_load((skill_dir / 'apm.yml').read_text())['version']
    return f'{skill_dir.name}--v{version}'


def main() -> None:
    existing = set(subprocess.check_output(['git', 'tag', '--list'], cwd=ROOT, text=True).split())
    for skill_dir in find_skill_dirs(ROOT):
        tag = release_tag(skill_dir)
        if tag not in existing:
            print(tag)


if __name__ == '__main__':
    main()
