#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Defect injectors for calibrating the assessor.

Each mutant takes a copy of the known-good R0 fixture
(``../fixtures/make_r0_object.py``), injects exactly **one** defect, and
declares which checklist items that defect should flip and to what.  The
calibrator in ``../harness/calibrate.py`` then measures per-item sensitivity
and the false-``unmet`` rate on the clean object.

A mutant is the regression artifact behind a lesson: when a run shows the
assessor missing a real defect, the fix is a mutant plus a probe change, not a
paragraph of prose.

    mutate.py list
    mutate.py apply <name> <dir>        # <dir> is a copy of the fixture
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ENV = {
    "GIT_AUTHOR_NAME": "STAMPED mutant", "GIT_AUTHOR_EMAIL": "mutant@example.org",
    "GIT_COMMITTER_NAME": "STAMPED mutant", "GIT_COMMITTER_EMAIL": "mutant@example.org",
    "GIT_AUTHOR_DATE": "2026-10-02T12:00:00+00:00", "GIT_COMMITTER_DATE": "2026-10-02T12:00:00+00:00",
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
}


def git(root: pathlib.Path, *args: str) -> str:
    import os

    proc = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True,
        env={**ENV, "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {root}: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


# --- the injectors ---------------------------------------------------------

def abs_path_in_script(root: pathlib.Path) -> str:
    """A script that only runs on the machine it was written on."""
    path = root / "code" / "plot_volumes.py"
    text = path.read_text()
    # Assembled at runtime so this file carries no literal home path itself.
    hardcoded = "/" + "home/" + "researcher/data/ds007116"
    text = text.replace(
        '    args = ap.parse_args()',
        f'    args = ap.parse_args()\n    fallback = "{hardcoded}"  # where the inputs live',
        1,
    )
    path.write_text(text)
    git(root, "add", "code/plot_volumes.py")
    git(root, "commit", "-q", "-m", "point the plotting script at the input directory")
    return "code/plot_volumes.py now carries an absolute home path"


def large_binary_in_git(root: pathlib.Path, size_mb: int = 50) -> str:
    """A big image committed as a git blob instead of content-addressed."""
    path = root / "results" / "sub-01_T1w_brain.nii.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(b"\0" * (size_mb * 1024 * 1024))
    git(root, "add", "-f", "results/sub-01_T1w_brain.nii.gz")
    git(root, "commit", "-q", "-m", "add the brain-extracted volume")
    return f"a {size_mb} MiB NIfTI is a plain git blob"


def container_latest(root: pathlib.Path) -> str:
    """An environment that drifts under you."""
    path = root / "code" / "containers.json"
    spec = json.loads(path.read_text())
    spec["containers"]["plotting"] = {
        "image": "docker://python:latest",
        "registered_from": "code/containers.json",
    }
    path.write_text(json.dumps(spec, indent=2) + "\n")
    git(root, "add", "code/containers.json")
    git(root, "commit", "-q", "-m", "track the latest python image")
    return "the container is referenced as :latest, with no digest"


def relative_subdataset_url(root: pathlib.Path) -> str:
    """The failure that breaks a fresh clone (compression-comparisons-t261-study)."""
    git(root, "config", "-f", ".gitmodules", "submodule.sourcedata/ds007116.url", "../..")
    git(root, "add", ".gitmodules")
    git(root, "commit", "-q", "-m", "record the input module relative to the superdataset")
    return ".gitmodules points the input module at ../.., which resolves only here"


def readme_reproduce_removed(root: pathlib.Path) -> str:
    """Instructions that no longer say how to run anything."""
    path = root / "README.md"
    text = path.read_text()
    head = text.split("## Install")[0]
    path.write_text(head + "The method is described in the paper.\n")
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "trim the README")
    return "the README no longer names an install, usage or entry point"


def outputs_into_inputs(root: pathlib.Path) -> str:
    """Results written into the input module."""
    sub = root / "sourcedata" / "ds007116"
    target = sub / "derivatives" / "freesurfer-post" / "volumes-recomputed.tsv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("session_id\tbrainseg\nses-1\t1150000\n")
    git(sub, "add", "derivatives/freesurfer-post/volumes-recomputed.tsv")
    git(sub, "commit", "-q", "-m", "write the recomputed volumes next to the inputs")
    return "the input module now carries this project's output, and differs from the recorded commit"


def untracked_figure(root: pathlib.Path) -> str:
    """A result that exists only in somebody's working tree."""
    path = root / "figures" / "gm-wm-ratio-vs-age.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PNG-placeholder:uncommitted")
    return "figures/gm-wm-ratio-vs-age.png exists but was never committed"


def derived_without_record(root: pathlib.Path) -> str:
    """A result nobody can re-create."""
    path = root / "results" / "volumes-by-hand.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("session_id\tbrainseg\nses-4\t1300000\n")
    git(root, "add", "results/volumes-by-hand.tsv")
    git(root, "commit", "-q", "-m", "add the volumes for the extra session")
    return "results/volumes-by-hand.tsv came from an ordinary commit, with no run record"


# --- registry --------------------------------------------------------------

MUTANTS: dict[str, dict] = {
    "abs-path-in-script": {
        "apply": abs_path_in_script,
        "expect": {"stamped-checklist:must/009": "unmet"},
        "probe": "no-abs-paths",
    },
    "large-binary-in-git": {
        "apply": large_binary_in_git,
        "expect": {"stamped-checklist:must/005": "unmet"},
        "probe": "large-in-annex",
    },
    "container-latest": {
        "apply": container_latest,
        "expect": {"stamped-checklist:must/015": "unmet"},
        "probe": "run-env-linked",
    },
    "relative-subdataset-url": {
        "apply": relative_subdataset_url,
        "expect": {"stamped-checklist:must/002": "unmet", "stamped-checklist:must/016": "unmet"},
        "probe": "subdatasets-resolvable",
    },
    "readme-reproduce-removed": {
        "apply": readme_reproduce_removed,
        # The Makefile survives, so must/008 (a starting point exists) stays
        # `met` and only must/007 (instructions for install and usage) falls.
        # A MUST at `partial` is a MUST failure, so this is still a detection.
        "expect": {"stamped-checklist:must/007": "partial"},
        "probe": "entry-point",
    },
    "outputs-into-inputs": {
        "apply": outputs_into_inputs,
        "expect": {"stamped-checklist:should/003": "unmet"},
        # A modified submodule pointer is also uncommitted superdataset state.
        "also": {"stamped-checklist:must/004": "unmet"},
        "probe": "inputs-untouched",
    },
    "untracked-figure": {
        "apply": untracked_figure,
        "expect": {"stamped-checklist:must/004": "unmet"},
        "probe": "tree-clean",
    },
    "derived-without-record": {
        "apply": derived_without_record,
        "expect": {"stamped-checklist:must/006": "partial"},
        "probe": "derived-have-records",
    },
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list the mutants and what each should flip")
    p_apply = sub.add_parser("apply", help="inject one defect into a copy of the fixture")
    p_apply.add_argument("name", choices=sorted(MUTANTS))
    p_apply.add_argument("dir", type=pathlib.Path)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for name, spec in sorted(MUTANTS.items()):
            flips = ", ".join(f"{i.split(':')[-1]}->{s}" for i, s in spec["expect"].items())
            print(f"{name:<26} probe:{spec['probe']:<24} {flips}")
        return 0

    spec = MUTANTS[args.name]
    if not (args.dir / ".git").exists():
        print(f"error: {args.dir} is not a git repository (copy the fixture there first)", file=sys.stderr)
        return 2
    what = spec["apply"](args.dir)
    print(f"{args.name}: {what}")
    print("expected flips: " + ", ".join(f"{i}={s}" for i, s in spec["expect"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
