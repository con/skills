#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Judgement mutants: defects only a reader can catch.

The mutants in `mutate.py` are caught by scripts, which is what makes them
cheap. These are the other half: each injects a defect that **no probe can
see** — prose that describes an execution that cannot work, or that works only
on the machine it was written on — and the grader is a blind subagent running
`assess-alignment-with-stamped-principles`, not a `grep`.

Every judgement mutant declares three things, because a judgement grader needs
all three to be scored honestly:

* ``probes_expected`` — what the scripted probes must still say. The default is
  "everything they answered on the clean object", i.e. **green**: a judgement
  mutant that trips a probe is not testing judgement.
* ``flag_any`` — the checklist items of which at least one must come back as
  something other than ``met``. Judgement verdicts vary between readers; which
  of two related items an assessor pins a prose defect on is not the thing
  under test, so the expectation is deliberately a set.
* ``mention_any`` — strings the report must contain, which is where the real
  grading happens. A `partial` on must/007 proves nothing; naming the target
  that does not exist proves the assessor read the instructions.

Usage is through ``../harness/judgement_calibrate.py``; this module is the
catalogue.

    judgement.py list
    judgement.py apply <name> <dir>
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mutate import git  # noqa: E402  (same commit identity and env hygiene)


# --- injectors -------------------------------------------------------------

def readme_misdescribes_target(root: pathlib.Path) -> str:
    """The documented command exists, and does not do what the prose says.

    `readme-wrong-make-target` used to live here, until a blind run pointed out
    that comparing the README's `make <target>` against the Makefile's targets
    is mechanical; it is now a scripted mutant. What remains judgement is prose
    that names a *real* target and describes it wrongly, which no name lookup
    catches.
    """
    path = root / "README.md"
    text = path.read_text()
    text = text.replace("""```console
make all          # joins the tables, then draws the figure
```""", """```console
make all          # fetches the input dataset, joins the tables, draws the figure,
                  # and writes the brain-mask volumes for every session
```""")
    text = text.replace("Outputs land in `results/` and `figures/`",
                        "`make all` also installs the environment and fetches the inputs, so the "
                        "clone above is the only manual step. Outputs land in `results/` and `figures/`")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "describe what the entry point does")
    return ("README says `make all` fetches the inputs, installs the environment and computes brain-mask "
            "volumes; the target does none of those three things")


def readme_wrong_tool(root: pathlib.Path) -> str:
    """Instructions for a tool the object does not use."""
    path = root / "README.md"
    text = path.read_text()
    text = text.replace("""python3 -m venv .venv && .venv/bin/pip install -r requirements.lock""",
                        """pixi install          # resolves the environment from pixi.toml""")
    text = text.replace("make all          # joins the tables, then draws the figure",
                        "pixi run all      # joins the tables, then draws the figure")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "document the pixi workflow")
    return ("the documented environment and entry point are pixi, but the object tracks "
            "requirements.lock and a Makefile and has no pixi.toml")


def readme_steps_out_of_order(root: pathlib.Path) -> str:
    """A reproduce section whose steps cannot run in the order given."""
    path = root / "README.md"
    text = path.read_text()
    text = text.replace("""```console
git clone <this object> && cd <this object>
git submodule update --init sourcedata/ds007116
make all
```""", """```console
make all
git clone <this object> && cd <this object>
python3 code/plot_volumes.py --input results/volumes.tsv --output figures/brain-volume-vs-age.png
python3 code/collect_volumes.py --input sourcedata/ds007116 --output results/volumes.tsv
git submodule update --init sourcedata/ds007116
```""")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "expand the reproduce section step by step")
    return ("the reproduce steps are in an impossible order: build before clone, plot before the table "
            "it plots, inputs fetched last")


def readme_claims_absent_container(root: pathlib.Path) -> str:
    """Prose promising an environment the object does not carry."""
    path = root / "README.md"
    text = path.read_text()
    # Replace the object's honest account of its two routes with a false one.
    honest = text[text.index("**Two ways to run"):text.index("## Layout")]
    text = text.replace(honest,
                        "Every step runs inside the `neurodesk-freesurfer` container from "
                        "`///repronim/containers`, so no local installation is needed and the "
                        "environment is identical everywhere — `make all`, CI and the run records "
                        "all go through it.\n\n")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "describe the container the analysis runs in")
    return ("README promises a `neurodesk-freesurfer` container from ///repronim/containers that is "
            "registered nowhere in the object, while the tracked registration names another image")


def readme_host_path_in_instructions(root: pathlib.Path) -> str:
    """The documented route works on one host only — and only prose says so."""
    path = root / "README.md"
    text = path.read_text()
    text = text.replace("""## Reproduce""", """## Reproduce

Set the shared inputs first (they are on the lab filer):

```console
export DS007116=/mnt/labshare/openneuro/ds007116
export FREESURFER_HOME=/opt/local/freesurfer-7.4.1
```""")
    path.write_text(text)
    git(root, "add", "README.md")
    git(root, "commit", "-q", "-m", "note where the shared inputs live")
    return ("the documented route depends on /mnt/labshare and a host FreeSurfer install, neither of "
            "which travels with the object, and the input is already a subdataset")


def dataset_description_contradicts_layout(root: pathlib.Path) -> str:
    """Metadata that describes a different project."""
    path = root / "dataset_description.json"
    spec = {
        "Name": "Brain volume versus age in ds007116",
        "BIDSVersion": "1.11.0",
        "DatasetType": "raw",
        "License": "CC0",
        "GeneratedBy": [{"Name": "fMRIPrep", "Version": "23.2.0",
                         "Description": "Preprocessing of the anatomical images."}],
        "SourceDatasets": [{"URL": "///openneuro/ds000003"}],
    }
    path.write_text(json.dumps(spec, indent=2) + "\n")
    git(root, "add", "dataset_description.json")
    git(root, "commit", "-q", "-m", "add dataset metadata")
    return ("dataset_description.json says DatasetType raw, credits fMRIPrep, and points at ds000003: "
            "none of which matches an object whose own records show a Makefile and ds007116")


# --- the catalogue ---------------------------------------------------------

JUDGEMENT_MUTANTS: dict[str, dict] = {
    "readme-misdescribes-target": {
        "apply": readme_misdescribes_target,
        # Widened after the first run: it read the prose, caught the falsehood
        # and named it, then pinned it on should/002 (CI does not exercise what
        # the README describes) and must/017 rather than on must/007. Which item
        # a reader chooses for a prose defect is not under test — `mention_any`
        # is what carries the weight.
        "flag_any": ["stamped-checklist:must/007", "stamped-checklist:must/008",
                     "stamped-checklist:must/012", "stamped-checklist:must/017",
                     "stamped-checklist:should/002"],
        "mention_any": ["fetch", "install", "brain-mask", "does not", "claims"],
        "stay_met": ["stamped-checklist:must/004", "stamped-checklist:must/009",
                     "stamped-checklist:must/005"],
        "tests": "A1: the command exists and the description of it is false. Name lookup cannot "
                 "catch this; only reading the Makefile against the prose can.",
    },
    "readme-wrong-tool": {
        "apply": readme_wrong_tool,
        "flag_any": ["stamped-checklist:must/007", "stamped-checklist:must/008",
                     "stamped-checklist:must/017", "stamped-checklist:must/012"],
        "mention_any": ["pixi"],
        "stay_met": ["stamped-checklist:must/013", "stamped-checklist:must/010"],
        "tests": "A1/P2: the documented environment is not the tracked one. env-spec-tracked is "
                 "right that a pinned spec exists; it cannot know the README names another.",
    },
    "readme-steps-out-of-order": {
        "apply": readme_steps_out_of_order,
        "flag_any": ["stamped-checklist:must/007", "stamped-checklist:must/008"],
        "mention_any": ["order", "before", "clone", "sequence"],
        "stay_met": ["stamped-checklist:must/004", "stamped-checklist:must/006"],
        "tests": "A1: instructions sufficient to reproduce. Each command is real; the sequence is "
                 "impossible.",
    },
    "readme-claims-absent-container": {
        "apply": readme_claims_absent_container,
        "flag_any": ["stamped-checklist:must/015", "stamped-checklist:must/017",
                     "stamped-checklist:must/012", "stamped-checklist:must/003"],
        "mention_any": ["neurodesk", "repronim/containers", "not registered", "no such container"],
        "stay_met": ["stamped-checklist:must/006", "stamped-checklist:must/013"],
        "tests": "E/D: prose promising an environment nobody can get. The run records name a "
                 "different, pinned image, so every probe is satisfied.",
    },
    "readme-host-path-in-instructions": {
        "apply": readme_host_path_in_instructions,
        # The host path is in documentation, so `no-abs-paths` drops to `partial`
        # by design: it is not a script. The judgement question is whether the
        # *documented route* is portable at all.
        "probes_expected": {"stamped-checklist:must/009": "partial"},
        "flag_any": ["stamped-checklist:must/011", "stamped-checklist:must/012",
                     "stamped-checklist:must/009", "stamped-checklist:must/001"],
        "mention_any": ["/mnt/labshare", "labshare", "FREESURFER_HOME", "lab filer"],
        "stay_met": ["stamped-checklist:must/004", "stamped-checklist:must/013"],
        "tests": "P1: the documented route needs a mount and a host install, and the object already "
                 "carries the input as a module.",
    },
    "dataset-description-contradicts-layout": {
        "apply": dataset_description_contradicts_layout,
        "flag_any": ["stamped-checklist:must/012", "stamped-checklist:must/017",
                     "stamped-checklist:must/011", "stamped-checklist:may/002"],
        "mention_any": ["fMRIPrep", "ds000003", "DatasetType", "raw", "contradict"],
        "stay_met": ["stamped-checklist:must/004", "stamped-checklist:must/006"],
        "tests": "Goal fit: metadata describing another project. Nothing mechanical contradicts it; "
                 "reading the object does.",
    },
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list the judgement mutants and what each tests")
    p_apply = sub.add_parser("apply", help="inject one prose defect into a copy of the fixture")
    p_apply.add_argument("name", choices=sorted(JUDGEMENT_MUTANTS))
    p_apply.add_argument("dir", type=pathlib.Path)
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for name, spec in sorted(JUDGEMENT_MUTANTS.items()):
            print(f"{name}\n    flag any of: "
                  + ", ".join(i.split(':')[-1] for i in spec["flag_any"])
                  + "\n    must mention one of: " + ", ".join(repr(m) for m in spec["mention_any"])
                  + "\n    " + spec["tests"])
        return 0

    spec = JUDGEMENT_MUTANTS[args.name]
    if not (args.dir / ".git").exists():
        print(f"error: {args.dir} is not a git repository (copy the fixture there first)", file=sys.stderr)
        return 2
    print(f"{args.name}: {spec['apply'](args.dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
