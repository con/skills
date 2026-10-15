#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Copy a run's object and untrack the files the harness itself put in it.

    correct_object.py <object> <destination> [--also PATH ...]

Why this exists: a grader must never accuse an object of the harness's own
mess. R0's four arms had to be corrected by hand because `run.py` committed its
copies of the skills under test into the sandbox; R1's first two arms both lost
must/009 to `HOST-NOTES.md`, a file the harness wrote, carrying an absolute
cache path it needed for this host. `run.py` now ignores both, so this script is
for runs made *before* that fix — and the correction is a copy with a commit of
its own, so the original object and the corrected one can both be graded and
the difference reported.

Harness files are exactly those `run.py` creates. Anything the agent wrote is
the object's own doing and stays.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

# Written by run.py, not by the run under test.
HARNESS_FILES = ("HOST-NOTES.md", "prompt.md", "run.json")


def git(root: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("object", type=pathlib.Path)
    ap.add_argument("destination", type=pathlib.Path)
    ap.add_argument("--also", action="append", default=[], help="another harness-written path to untrack")
    ap.add_argument("--keep", nargs="*", default=[], help="harness files to leave tracked")
    args = ap.parse_args(argv)

    source, dest = args.object.resolve(), args.destination.resolve()
    if dest.exists():
        print(f"error: {dest} exists", file=sys.stderr)
        return 1
    shutil.copytree(source, dest, symlinks=True)

    tracked = set(git(dest, "ls-files").stdout.split())
    targets = [p for p in (*HARNESS_FILES, *args.also) if p in tracked and p not in args.keep]
    if not targets:
        print(f"{dest}: nothing to correct (no harness file is tracked)")
        return 0
    git(dest, "rm", "--cached", "-q", *targets)
    gitignore = dest / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    missing = [p for p in targets if p not in existing]
    if missing:
        gitignore.write_text(existing + "".join(f"{p}\n" for p in missing))
        git(dest, "add", ".gitignore")
    out = git(dest, "-c", "user.name=stamped-evals", "-c", "user.email=evals@example.org",
              "commit", "-q", "-m",
              "harness correction: untrack files run.py wrote into the sandbox\n\n"
              + "".join(f"- {p}\n" for p in targets)
              + "\nThe grader must not accuse an object of the harness's own mess; see\n"
                "evals/stamped/harness/correct_object.py.")
    if out.returncode != 0:
        print(f"error: commit failed: {(out.stderr or out.stdout).strip()[:300]}", file=sys.stderr)
        return 1
    print(f"{dest}: untracked {', '.join(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
