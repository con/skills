#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Build a known-good R0-shaped research object, for calibrating the probes.

The object is deliberately *not* DataLad-specific: it keeps its environment in a
lockfile, drives its work from a tracked ``Makefile``, and records each
execution as a ``[DATALAD RUNCMD]`` commit, so the probes are exercised on both
the workflow and the run-record kinds of evidence at once.  Everything is built
with plain ``git``, so the fixture needs neither datalad nor network.

    make_r0_object.py <dir> [--input-remote URL]

What makes it "good" (every probe should answer `met`, or `not-applicable` with
a reason):

* one root, one git repository, clean tree;
* the input dataset linked as a submodule with a URL that resolves elsewhere;
* a pinned environment (``requirements.lock``) and a container pinned by digest;
* a README with an install/usage section naming ``code/plot_volumes.py``;
* every derived file last touched by a run record that names the container;
* a licence and a CI workflow that re-executes the entry point.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

DATE = "2026-10-01T12:00:00+00:00"
ENV = {
    "GIT_AUTHOR_NAME": "STAMPED fixture", "GIT_AUTHOR_EMAIL": "fixture@example.org",
    "GIT_COMMITTER_NAME": "STAMPED fixture", "GIT_COMMITTER_EMAIL": "fixture@example.org",
    "GIT_AUTHOR_DATE": DATE, "GIT_COMMITTER_DATE": DATE,
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_TERMINAL_PROMPT": "0",
}
CONTAINER_DIGEST = "sha256:3e0f1b6c5a2d4e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f7"
RUN_SEP_TOP = "=== Do not change lines below ==="
RUN_SEP_BOTTOM = "^^^ Do not change lines above ^^^"

FILES: dict[str, str] = {
    "README.md": """# Brain volume versus age in ds007116 (R0)

A tiny, fully recorded study: it reads the FreeSurfer tables that
[ds007116](https://github.com/OpenNeuroDatasets/ds007116) ships, joins them with
the per-session ages, and plots brain volume with the GM/WM ratio on a secondary
axis against age.

## Install

```console
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock
```

The analysis step runs inside the container pinned in `code/containers.json`.

## Usage

```console
make all          # joins the tables, then draws the figure
```

Entry point: `code/plot_volumes.py`, called by `make figures/brain-volume-vs-age.png`.

## Layout

| Path | What it is |
|---|---|
| `sourcedata/ds007116` | the input dataset, linked as a module and never modified |
| `code/` | the two steps, their `requirements.in`, and the container registration |
| `code/containers/` | the image the run records name, pinned by digest in `containers.json` |
| `results/`, `figures/` | the products; each arrives in its own run record |
| `docs/` | how the method works and how to navigate the above |

Each part can be replaced on its own: a different input module, a different
container digest, or a different plotting step, without touching the others —
the `Makefile` rules are the only coupling, and they name files rather than
steps.

## Reproduce

```console
git clone <this object> && cd <this object>
git submodule update --init sourcedata/ds007116
make all
```

Outputs land in `results/` and `figures/`, and every one of them has a run
record in the history (`git log --grep='[DATALAD RUNCMD]'`).
""",
    "Makefile": """.PHONY: all clean
all: results/volumes.tsv figures/brain-volume-vs-age.png

results/volumes.tsv: code/collect_volumes.py sourcedata/ds007116
\tpython3 code/collect_volumes.py --input sourcedata/ds007116 --output $@

figures/brain-volume-vs-age.png: code/plot_volumes.py results/volumes.tsv
\tpython3 code/plot_volumes.py --input results/volumes.tsv --output $@

clean:
\trm -f results/volumes.tsv figures/brain-volume-vs-age.png
""",
    "requirements.lock": """# pinned with `uv pip compile code/requirements.in`
matplotlib==3.9.2
pandas==2.2.3
""",
    "code/requirements.in": "matplotlib\npandas\n",
    # The image the run records name. A real object holds a built container
    # here (or an annexed pointer to one); the fixture needs the path to exist
    # so that the records it carries are self-consistent — a blind run on a
    # smaller model caught the earlier version claiming an image that was never
    # created, which is a defect in the fixture, not in the object under test.
    "code/containers/plotting.sif.README": (
        "The run records in this object's history reference\n"
        "`code/containers/plotting.sif`, pinned by digest in `../containers.json`.\n"
        "In the fixture the image itself is not shipped (it would be ~200 MB);\n"
        "`plotting.sif` beside this file is a placeholder of a few bytes so that\n"
        "every path a run record names exists.\n"
    ),
    "code/containers/plotting.sif": "apptainer-image-placeholder\n",
    "code/containers.json": json.dumps(
        {
            "containers": {
                "plotting": {
                    "image": "docker://python",
                    "digest": CONTAINER_DIGEST,
                    "registered_from": "code/containers.json",
                }
            }
        },
        indent=2,
    )
    + "\n",
    "code/collect_volumes.py": '''#!/usr/bin/env python3
"""Join the shipped FreeSurfer tables with the per-session ages."""
import argparse
import csv
import pathlib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    args = ap.parse_args()
    rows = []
    for qc in sorted(args.input.glob("derivatives/freesurfer-post/*_qc.tsv")):
        with qc.open() as fh:
            rows.extend(dict(row) for row in csv.DictReader(fh, delimiter="\\t"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["session_id", "age", "brainseg", "gm_wm_ratio"], delimiter="\\t")
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "code/plot_volumes.py": '''#!/usr/bin/env python3
"""Plot brain volume against age, GM/WM ratio on a secondary axis."""
import argparse
import csv
import pathlib


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    args = ap.parse_args()
    with args.input.open() as fh:
        rows = list(csv.DictReader(fh, delimiter="\\t"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # The fixture does not need a real figure, only a recorded derived file.
    args.output.write_bytes(b"PNG-placeholder:" + str(len(rows)).encode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "results/volumes.tsv": "session_id\tage\tbrainseg\tgm_wm_ratio\n"
    "ses-1\t9.1\t1150000\t1.21\nses-2\t12.4\t1210000\t1.18\nses-3\t17.8\t1265000\t1.12\n",
    "figures/brain-volume-vs-age.png": "PNG-placeholder:3",
    "LICENSE": "MIT License\n\nCopyright (c) 2026 STAMPED fixture\n",
    ".github/workflows/rerun.yml": """name: rerun
on: [push, pull_request]
jobs:
  rerun:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {submodules: recursive}
      - run: pip install -r requirements.lock
      # The records name a container; CI has to exercise *that* environment,
      # not merely some environment (should/006 asks about the one the results
      # came from).
      - run: python3 -c "import json;d=json.load(open('code/containers.json'));print(d['containers']['plotting']['digest'])"
      - run: test -e code/containers/plotting.sif
      - run: make all
      - run: git diff --exit-code results figures
""",
    "docs/README.md": """# Notes on the method, and how to navigate this object

**The question:** does brain volume grow with age over 8–20 years, and does the
grey/white matter ratio fall over the same range?

**Where things are.** `../README.md` has the layout table; this file explains
how the pieces relate:

1. `sourcedata/ds007116` is an input module. It is never written to. Swapping it
   for another BIDS dataset with FreeSurfer derivatives is the intended way to
   re-use this object.
2. `code/collect_volumes.py` reads only `derivatives/freesurfer-post/*_qc.tsv`
   from that module and writes one row per session to `results/volumes.tsv`.
   It is the only step that knows the input's layout.
3. `code/plot_volumes.py` reads that table and nothing else, so a different
   plot, or a different table with the same columns, needs no change upstream.
4. The container in `code/containers/`, pinned by digest in
   `code/containers.json`, is what both steps run inside; the run records name
   it, so the environment and the action are linked in the history.

**Re-running one step.** `make results/volumes.tsv` or
`make figures/brain-volume-vs-age.png`; each target depends only on what it
actually reads.
""",
    # Stated inside the object, because a careful assessor checks and finds out:
    # a blind control run fetched the pinned input commit and queried this
    # object's own remote, and was right that neither exists.
    "FIXTURE.md": """# This object is a test fixture

It exists to calibrate `assess-alignment-with-stamped-principles`, and two
things about it are **simulated**:

- `sourcedata/ds007116` records the URL of the real OpenNeuro dataset, but is
  pinned to a commit generated locally when this fixture was built. That commit
  does not exist upstream, so `git submodule update --init` from a fresh clone
  cannot succeed.
- `remote.origin.url` names a repository that is not published.

Everything else — the layout, the pinned environment, the run records, the
entry point, the CI job — is as a good R0-shaped object would have it. The two
simulations are what make the fixture buildable offline in seconds; they are
also why an honest assessment of *this* object cannot answer must/002 or
must/016 `met`. See `evals/stamped/harness/judgement_calibrate.py`, which
expects exactly those two.
""",
}

RUNS = [
    {
        "message": "collect the shipped FreeSurfer volumes",
        "paths": ["results/volumes.tsv"],
        "run_info": {
            "cmd": "apptainer exec code/containers/plotting.sif "
                   "python3 code/collect_volumes.py --input sourcedata/ds007116 --output results/volumes.tsv",
            "inputs": ["sourcedata/ds007116/derivatives/freesurfer-post"],
            "extra_inputs": [f"code/containers/plotting.sif ({CONTAINER_DIGEST})"],
            "outputs": ["results/volumes.tsv"],
            "chain": [],
            "dsid": "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9",
            "pwd": ".",
        },
    },
    {
        "message": "plot brain volume against age",
        "paths": ["figures/brain-volume-vs-age.png"],
        "run_info": {
            "cmd": "apptainer exec code/containers/plotting.sif "
                   "python3 code/plot_volumes.py --input results/volumes.tsv "
                   "--output figures/brain-volume-vs-age.png",
            "inputs": ["results/volumes.tsv"],
            "extra_inputs": [f"code/containers/plotting.sif ({CONTAINER_DIGEST})"],
            "outputs": ["figures/brain-volume-vs-age.png"],
            "chain": [],
            "dsid": "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9",
            "pwd": ".",
        },
    },
]


def git(root: pathlib.Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, env={**ENV, "PATH": _path()})
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def _path() -> str:
    import os

    return os.environ.get("PATH", "/usr/bin:/bin")


def write(root: pathlib.Path, relpath: str, content: str) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def run_message(message: str, run_info: dict) -> str:
    return (
        f"[DATALAD RUNCMD] {message}\n\n{RUN_SEP_TOP}\n"
        + json.dumps(run_info, indent=1, sort_keys=True)
        + f"\n{RUN_SEP_BOTTOM}\n"
    )


def build(root: pathlib.Path, input_remote: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", ENV["GIT_AUTHOR_NAME"])
    git(root, "config", "user.email", ENV["GIT_AUTHOR_EMAIL"])
    git(root, "config", "protocol.file.allow", "always")

    # The input dataset: a local stand-in, linked with a URL that resolves elsewhere.
    inputs = root.parent / (root.name + "-input")
    if not (inputs / ".git").exists():
        inputs.mkdir(parents=True, exist_ok=True)
        git(inputs, "init", "-q", "-b", "main")
        git(inputs, "config", "user.name", ENV["GIT_AUTHOR_NAME"])
        git(inputs, "config", "user.email", ENV["GIT_AUTHOR_EMAIL"])
        write(inputs, "dataset_description.json",
              json.dumps({"Name": "ds007116 (stand-in)", "BIDSVersion": "1.11.0", "License": "CC0"}, indent=2) + "\n")
        write(inputs, "derivatives/freesurfer-post/ses-1_desc-FreeSurfer_qc.tsv",
              "session_id\tage\tbrainseg\tgm_wm_ratio\nses-1\t9.1\t1150000\t1.21\n")
        git(inputs, "add", "-A")
        git(inputs, "commit", "-q", "-m", "ds007116 stand-in: shipped FreeSurfer tables")

    derived = {path for run in RUNS for path in run["paths"]}
    for relpath, content in FILES.items():
        if relpath in derived:
            continue  # derived files arrive with their run record, below
        write(root, relpath, content)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "R0: layout, pinned environment, entry point, CI")

    git(root, "-c", "protocol.file.allow=always", "submodule", "--quiet", "add",
        str(inputs), "sourcedata/ds007116")
    # Record the public URL rather than the local path it was cloned from: a
    # local path would not resolve for anyone else (must/002, must/016).
    git(root, "config", "-f", ".gitmodules", "submodule.sourcedata/ds007116.url", input_remote)
    git(root, "add", ".gitmodules", "sourcedata/ds007116")
    git(root, "commit", "-q", "-m", "link the input dataset as a module")

    # Each derived file's most recent commit is its run record.
    for run in RUNS:
        for relpath in run["paths"]:
            write(root, relpath, FILES[relpath])
        git(root, "add", *run["paths"])
        git(root, "commit", "-q", "-m", run_message(run["message"], run["run_info"]))

    # A STAMPED object has somewhere others can retrieve it from.  The URL is a
    # stand-in (nothing is published from this fixture), recorded so that the
    # probes which ask "can anyone else obtain this?" have something to read.
    git(root, "remote", "add", "origin", "https://github.com/con/stamped-eval-fixture-r0.git")

    status = git(root, "status", "--porcelain")
    if status.strip():
        raise RuntimeError(f"fixture is not clean after build:\n{status}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir", type=pathlib.Path)
    ap.add_argument("--input-remote", default="https://github.com/OpenNeuroDatasets/ds007116.git")
    args = ap.parse_args(argv)
    if (args.dir / ".git").exists():
        print(f"error: {args.dir} already holds a git repository", file=sys.stderr)
        return 1
    build(args.dir, args.input_remote)
    print(f"built the clean R0 fixture in {args.dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
