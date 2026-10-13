#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Calibrate the *judgement* half of the assessor against prose defects.

`calibrate.py` measures whether the scripts catch a defect. This measures
whether a **reader** catches one that the scripts cannot see, which is the only
way to know that the parts of the skill made of sentences do any work.

Two phases, because a script cannot spawn an agent in this harness and should
not pretend to: the orchestrating session (or a human) runs the agent in
between, which is also what makes a run replayable on another model.

    judgement_calibrate.py prepare --workdir /scratch/j1 [--only NAME ...]
        # builds one object per judgement mutant, asserts the probes stay
        # green on it, and writes the blind-run prompt for each

    judgement_calibrate.py score --workdir /scratch/j1
        # reads each out/response.json (+ assessment.md) and scores it

Scoring, per mutant:

* **noticed** — at least one item in ``flag_any`` came back as something other
  than ``met``;
* **named it** — the report or a reason contains one of ``mention_any``: the
  part that separates reading the instructions from guessing;
* **no collateral** — every item in ``stay_met`` is still ``met``, so the
  assessor did not simply get suspicious of everything;
* **probes stayed green** — the scripted half was not what caught it (checked
  in `prepare`, re-checked here).

A mutant counts as detected only when the first three hold.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
REPO = EVALS.parent.parent
FIXTURE = EVALS / "fixtures" / "make_r0_object.py"
JUDGEMENT = EVALS / "mutants" / "judgement.py"
BLIND_RUN = HERE / "blind_run.py"
RUN_PROBES = REPO / "assess-alignment-with-stamped-principles" / "scripts" / "run_probes.py"

sys.path.insert(0, str(EVALS / "mutants"))
from judgement import JUDGEMENT_MUTANTS  # noqa: E402

SEVERITY = {"unmet": 0, "partial": 1, "not-checked": 2, "not-applicable": 3, "met": 4}


def _probe_items(path: pathlib.Path) -> dict[str, str]:
    out = subprocess.run([sys.executable, str(RUN_PROBES), str(path), "--quiet"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"run_probes.py failed on {path}: {out.stderr.strip()[:400]}")
    items: dict[str, str] = {}
    for result in json.loads(out.stdout)["probes"]:
        for item in result["items"]:
            status = result.get("item_status", {}).get(item, result["status"])
            if item not in items or SEVERITY[status] < SEVERITY[items[item]]:
                items[item] = status
    return items


def prepare(args: argparse.Namespace) -> int:
    workdir = args.workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    clean = workdir / "clean"
    if not (clean / ".git").exists():
        subprocess.run([sys.executable, str(FIXTURE), str(clean)], check=True, capture_output=True)
    baseline = _probe_items(clean)

    names = args.only or sorted(JUDGEMENT_MUTANTS)
    index = {}
    for name in names:
        spec = JUDGEMENT_MUTANTS[name]
        target = workdir / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(clean, target / "object", symlinks=True)
        obj = target / "object"
        out = subprocess.run([sys.executable, str(JUDGEMENT), "apply", name, str(obj)],
                             capture_output=True, text=True)
        if out.returncode != 0:
            print(f"error: injecting {name} failed: {out.stderr.strip()[:300]}", file=sys.stderr)
            return 1
        what = out.stdout.strip()

        # A judgement mutant that trips a probe is not testing judgement.
        after = _probe_items(obj)
        expected = {**baseline, **(spec.get("probes_expected") or {})}
        unexpected = {i: s for i, s in after.items() if expected.get(i) != s}
        if unexpected:
            print(f"error: {name} changed what the probes say, so it does not isolate judgement: "
                  + ", ".join(f"{i.split(':')[-1]}={s} (expected {expected.get(i)})"
                              for i, s in unexpected.items()), file=sys.stderr)
            return 1

        prepared = subprocess.run(
            [sys.executable, str(BLIND_RUN), "prepare",
             "--skill", "assess-alignment-with-stamped-principles",
             "--object", str(obj), "--workdir", str(target)],
            capture_output=True, text=True,
        )
        if prepared.returncode != 0:
            print(prepared.stderr, file=sys.stderr)
            return 1
        index[name] = {"object": str(obj), "prompt": str(target / "prompt.md"),
                       "outdir": str(target / "out"), "injected": what,
                       "probes_unchanged": True}
        print(f"{name}\n  object: {obj}\n  prompt: {target / 'prompt.md'}\n  {what}")

    (workdir / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(f"\n{len(index)} judgement mutant(s) prepared, probes verified unchanged on each.")
    print(f"index: {workdir / 'index.json'}")
    print("Run one blind subagent per prompt, then: judgement_calibrate.py score --workdir "
          f"{workdir}")
    return 0


def score(args: argparse.Namespace) -> int:
    workdir = args.workdir.resolve()
    index = json.loads((workdir / "index.json").read_text())
    report: dict = {"mutants": {}}
    detected = 0
    scored = 0
    for name, entry in sorted(index.items()):
        spec = JUDGEMENT_MUTANTS[name]
        outdir = pathlib.Path(entry["outdir"])
        response_path = next(iter(sorted(outdir.glob("*response.json"))), None)
        if response_path is None:
            report["mutants"][name] = {"scored": False, "why": "no response JSON in the run's outdir"}
            print(f"not run   {name:<42} (no response JSON yet)")
            continue
        scored += 1
        response = json.loads(response_path.read_text()).get("responses") or {}
        prose = " ".join(
            [p.read_text() for p in sorted(outdir.glob("*.md"))]
            + [a.get("reason", "") for a in response.values()]
        ).lower()

        flagged = {i: response.get(i, {}).get("status", "(absent)") for i in spec["flag_any"]}
        noticed = any(s not in {"met", "(absent)"} for s in flagged.values())
        named = [m for m in spec["mention_any"] if m.lower() in prose]
        collateral = {i: response.get(i, {}).get("status", "(absent)")
                      for i in spec.get("stay_met", [])
                      if response.get(i, {}).get("status") != "met"}
        hit = noticed and bool(named) and not collateral
        detected += 1 if hit else 0
        report["mutants"][name] = {
            "scored": True, "detected": hit, "noticed": noticed, "named": named,
            "flagged": flagged, "collateral": collateral, "injected": entry["injected"],
            "response": str(response_path),
        }
        flag = "detected" if hit else "MISSED  "
        print(f"{flag}  {name:<42} "
              f"flagged={', '.join(f'{i.split(':')[-1]}={s}' for i, s in flagged.items())}"
              f" | named={named or 'nothing'}"
              + (f" | collateral={list(collateral)}" if collateral else ""))

    report["detection"] = f"{detected}/{scored}"
    print(f"\njudgement mutants detected: {detected}/{scored} scored"
          f" ({len(index)} prepared)")
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {args.output}")
    return 0 if scored and detected == scored else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="build the objects and the prompts")
    p.add_argument("--workdir", type=pathlib.Path, required=True)
    p.add_argument("--only", nargs="+", choices=sorted(JUDGEMENT_MUTANTS))
    s = sub.add_parser("score", help="score the responses the runs produced")
    s.add_argument("--workdir", type=pathlib.Path, required=True)
    s.add_argument("-o", "--output", type=pathlib.Path)
    args = ap.parse_args(argv)
    return prepare(args) if args.cmd == "prepare" else score(args)


if __name__ == "__main__":
    sys.exit(main())
