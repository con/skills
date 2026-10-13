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


def host_mount_path_in_script(root: pathlib.Path) -> str:
    """A script pinned to a mount that exists on one machine.

    Regression artifact for the worst false negative a blind run found: the
    probe only knew about `/home` and `/tmp`, so `/data/<user>/...` in two
    entry points of compression-comparisons-t261-study read as clean.
    """
    path = root / "code" / "collect_volumes.py"
    text = path.read_text()
    hardcoded = "/" + "data/" + "yoh/ds007116/vendor/freesurfer"
    text = text.replace(
        "    args = ap.parse_args()",
        f'    args = ap.parse_args()\n    freesurfer = "{hardcoded}"  # tables live here',
        1,
    )
    path.write_text(text)
    git(root, "add", "code/collect_volumes.py")
    git(root, "commit", "-q", "-m", "read the FreeSurfer tables from the shared mount")
    return "code/collect_volumes.py is pinned to a host-specific mount outside any home directory"


def host_tool_precondition(root: pathlib.Path) -> str:
    """An entry point that requires a tool to be installed on the host already.

    Regression artifact for a blind run's override: the probe hedged at
    `partial` because a specification *might* live in an uninstalled module,
    while the object carried positive evidence of relying on host tools.
    """
    path = root / "code" / "run.sh"
    path.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "# The sweep needs the patched build, not whatever is on PATH.\n"
        "command -v mri_segstats || { echo 'please install FreeSurfer first' >&2; exit 1; }\n"
        "make all\n"
    )
    path.chmod(0o755)
    git(root, "add", "code/run.sh")
    git(root, "commit", "-q", "-m", "add the sweep entry point")
    return "code/run.sh requires FreeSurfer to be on PATH already, and no tracked spec carries it"


def large_text_in_git(root: pathlib.Path, size_mb: int = 12) -> str:
    """A negative control: 12 MiB of *text* in git.

    Real clone weight, and deliberately **not** a must/005 defect — that item
    asks about large *binary* data. The probe used to call this `partial` on
    must/005; a blind run caught it applying a criterion the item does not
    state.
    """
    path = root / "logs" / "duct-usage.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = '{"timestamp": 0.0, "pmem": 0.1, "pcpu": 1.0, "rss": 1048576, "vsz": 2097152}\n'
    with path.open("w") as fh:
        while path.stat().st_size < size_mb * 1024 * 1024:
            fh.writelines([line] * 20000)
            fh.flush()
    git(root, "add", "-f", "logs/duct-usage.jsonl")
    git(root, "commit", "-q", "-m", "keep the duct resource trace")
    return f"a {size_mb} MiB JSONL trace sits in git: clone weight, but not binary data"


def outputs_under_inputs(root: pathlib.Path) -> str:
    """Derived output written into the input tree of the superdataset itself."""
    path = root / "sourcedata" / "derivatives" / "volumes.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("session_id\tbrainseg\nses-1\t1150000\n")
    git(root, "add", "sourcedata/derivatives/volumes.tsv")
    git(root, "commit", "-q", "-m", "stage the volumes next to the inputs")
    return "sourcedata/derivatives/ mixes this object's output into the input tree"


def remote_removed(root: pathlib.Path) -> str:
    """Nothing records where the object (and so its environment spec) is published."""
    git(root, "remote", "remove", "origin")
    return "no published remote is recorded, so there is no evidence anyone else can obtain the spec"


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


def readme_wrong_make_target(root: pathlib.Path) -> str:
    """The documented command names a target the Makefile does not have.

    Promoted from a judgement mutant after a blind run observed that
    `entry-point` already had both the README's commands and the Makefile's
    targets and never compared them: a defect a script can catch belongs in
    the cheap half.
    """
    path = root / "README.md"
    text = path.read_text()
    text = text.replace("make all          # joins the tables, then draws the figure",
                        "make brain-volumes   # joins the tables, then draws the figure")
    text = text.replace("make all\n```\n\nOutputs land", "make brain-volumes\n```\n\nOutputs land")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "name the sweep target in the README")
    return "README tells the reader to run `make brain-volumes`, which the Makefile does not define"


def readme_platform_specific_steps(root: pathlib.Path) -> str:
    """Instructions that only work on one operating system.

    Promoted from a judgement mutant: a blind run reported 13 probes `met` on
    this object, and the fix was a probe (`platform-assumptions`) rather than a
    sentence. What stays judgement is prose whose *meaning* is wrong, not prose
    naming a platform-specific command.
    """
    path = root / "README.md"
    text = path.read_text()
    text = text.replace("""## Install

```console
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
```""", """## Install

```console
brew install python@3.12 freesurfer
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
sed -i '' 's|REPLACE_ME|'"$(pwd)"'|' code/containers.json
make all -j $(sysctl -n hw.ncpu)
```""")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "spell out the install steps")
    return ("the documented install uses Homebrew, BSD `sed -i ''` and `sysctl -n hw.ncpu`: "
            "it runs on one developer's macOS and nowhere else")


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
        "expect": {"stamped-checklist:must/002": "unmet"},
        "probe": "subdatasets-resolvable",
    },
    "readme-platform-specific-steps": {
        "apply": readme_platform_specific_steps,
        "expect": {"stamped-checklist:must/011": "partial"},
        "probe": "platform-assumptions",
    },
    "readme-wrong-make-target": {
        "apply": readme_wrong_make_target,
        "expect": {"stamped-checklist:must/007": "partial"},
        "probe": "entry-point",
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
        # A modified submodule pointer is uncommitted superdataset state, and
        # `inputs-untouched` reports the input drift as an extra finding: no
        # 0.3.1 item asks whether an input was modified.
        "expect": {"stamped-checklist:must/004": "unmet"},
        "expect_extra": {"inputs-untouched": "unmet"},
        "probe": "inputs-untouched",
    },
    "outputs-under-inputs": {
        "apply": outputs_under_inputs,
        "expect": {"stamped-checklist:should/003": "unmet"},
        "probe": "modules-separated",
    },
    "host-mount-path-in-script": {
        "apply": host_mount_path_in_script,
        "expect": {"stamped-checklist:must/009": "unmet"},
        "probe": "no-abs-paths",
    },
    "host-tool-precondition": {
        "apply": host_tool_precondition,
        "expect": {"stamped-checklist:must/010": "unmet"},
        "probe": "env-spec-tracked",
    },
    "large-text-in-git": {
        "apply": large_text_in_git,
        # Negative control: must/005 asks about binary data and must NOT move.
        "expect": {"stamped-checklist:must/005": "met"},
        "expect_extra": {"clone-weight": "partial"},
        "probe": "clone-weight",
    },
    "remote-removed": {
        "apply": remote_removed,
        "expect": {"stamped-checklist:must/016": "partial"},
        "probe": "env-spec-tracked",
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
            extra = ", ".join(f"{k}->{v}" for k, v in (spec.get("expect_extra") or {}).items())
            print(f"{name:<26} probe:{spec['probe']:<24} {flips}" + (f" | extra: {extra}" if extra else ""))
        return 0

    spec = MUTANTS[args.name]
    if not (args.dir / ".git").exists():
        print(f"error: {args.dir} is not a git repository (copy the fixture there first)", file=sys.stderr)
        return 2
    what = spec["apply"](args.dir)
    print(f"{args.name}: {what}")
    print("expected flips: " + ", ".join(f"{i}={s}" for i, s in spec["expect"].items()))
    if spec.get("expect_extra"):
        print("expected extras: " + ", ".join(f"{k}={v}" for k, v in spec["expect_extra"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
