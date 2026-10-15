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
* and separately, a **control run on the unmutated object**, whose only score is
  how many judgement items it accused: without it, "it flagged something" cannot
  be told apart from "it flags everything";
* **probes stayed green** — the scripted half was not what caught it (checked
  in `prepare`).

A mutant counts as detected only when the first three hold.

A response that is still the probe draft — every judgement item carrying the
"No probe covers this item" placeholder — is reported as **not run**, not as a
miss: reading a file while the agent is still working is a collector failure,
and the plan is explicit that those are kept apart from real results.
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

# The control is the clean fixture, and two of its properties are simulated so
# that it can be built offline (see the object's own FIXTURE.md): its input is
# pinned to a locally generated commit, and its remote is not published. A
# careful assessor finds both — the first control run did, by fetching the
# commit and querying the remote — so they are *expected* accusations, not
# false ones. Anything else the control accuses is a false accusation and is
# reported as such.
# The fixture declares what is simulated about it; both calibrators read that
# one list rather than keeping their own copies of it.
sys.path.insert(0, str(EVALS / "fixtures"))
from make_r0_object import SIMULATED as CONTROL_EXPECTED  # noqa: E402


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
    if not args.no_control:
        # The control: the same prompt on the *unmutated* object. Without it,
        # "it flagged something" cannot be told apart from "it flags everything".
        prepared = subprocess.run(
            [sys.executable, str(BLIND_RUN), "prepare",
             "--skill", "assess-alignment-with-stamped-principles",
             "--object", str(clean), "--workdir", str(workdir / "control-clean")],
            capture_output=True, text=True,
        )
        if prepared.returncode != 0:
            print(prepared.stderr, file=sys.stderr)
            return 1
        index["control-clean"] = {
            "object": str(clean), "prompt": str(workdir / "control-clean" / "prompt.md"),
            "outdir": str(workdir / "control-clean" / "out"),
            "injected": "nothing: this is the control", "probes_unchanged": True, "control": True,
        }
        print(f"control-clean\n  object: {clean}\n  prompt: {workdir / 'control-clean' / 'prompt.md'}\n"
              "  no defect injected: every non-met judgement verdict here is a false accusation")
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
        spec = JUDGEMENT_MUTANTS.get(name)
        outdir = pathlib.Path(entry["outdir"])
        response_path = next(iter(sorted(outdir.glob("*response.json"), key=lambda p: -p.stat().st_mtime)), None)
        if response_path is None:
            report["mutants"][name] = {"scored": False, "why": "no response JSON in the run's outdir"}
            print(f"not run   {name:<42} (no response JSON yet)")
            continue
        response = json.loads(response_path.read_text()).get("responses") or {}
        # `run_probes.py --response` writes a draft in which every judgement item
        # carries a placeholder. Scoring that would blame the agent for the
        # harness reading a file mid-flight: a collector failure, not a miss.
        placeholder = sum(1 for a in response.values()
                          if "No probe covers this item" in (a.get("reason") or ""))
        if placeholder >= 5:
            report["mutants"][name] = {
                "scored": False,
                "why": f"{response_path.name} is still the probe draft ({placeholder} placeholder "
                       "reasons): the run has not written its answers yet",
            }
            print(f"not run   {name:<42} (draft only, {placeholder} items unanswered)")
            continue
        prose = " ".join(
            [p.read_text() for p in sorted(outdir.glob("*.md"))]
            + [a.get("reason", "") for a in response.values()]
        ).lower()

        if spec is None:
            # An override is a judgement: `probe:<name>+judgement` counts here,
            # a bare `probe:<name>` does not.
            judged = {i: a.get("status") for i, a in response.items()
                      if "judgement" in (a.get("source") or "")}
            accused = {i: s for i, s in judged.items() if s in {"unmet", "partial"}}
            if entry.get("control"):
                expected = {i: s for i, s in accused.items() if i in CONTROL_EXPECTED}
                false_accusations = {i: s for i, s in accused.items() if i not in CONTROL_EXPECTED}
                report["mutants"][name] = {
                    "scored": True, "control": True, "judgement_items": len(judged),
                    "accused": accused, "expected": expected,
                    "false_accusations": false_accusations,
                    "false_accusation_rate": f"{len(false_accusations)}/{len(judged)}",
                    "model": _model(outdir, args.model),
                }
                print(f"control   {name:<42} {len(false_accusations)}/{len(judged)} false accusation(s)"
                      + (f": {', '.join(i.split(':')[-1] for i in false_accusations)}"
                         if false_accusations else "")
                      + (f" | {len(expected)} expected (the fixture's simulated properties: "
                         f"{', '.join(i.split(':')[-1] for i in expected)})" if expected else ""))
            else:
                # A mutant that was promoted to the scripted set since this run.
                report["mutants"][name] = {"scored": False, "why": "retired from the judgement set "
                                           "(the defect became script-catchable)"}
                print(f"retired   {name:<42} now a scripted mutant; see mutants/mutate.py")
            continue
        scored += 1
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
            "response": str(response_path), "model": _model(outdir, args.model),
        }
        flag = "detected" if hit else "MISSED  "
        print(f"{flag}  {name:<42} "
              f"flagged={', '.join(f'{i.split(':')[-1]}={s}' for i, s in flagged.items())}"
              f" | named={named or 'nothing'}"
              + (f" | collateral={list(collateral)}" if collateral else ""))

    report["detection"] = f"{detected}/{scored}"
    report["model"] = args.model
    print(f"\njudgement mutants detected: {detected}/{scored} scored"
          f" ({len(index)} prepared)")
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {args.output}")
    return 0 if scored and detected == scored else 1


def _model(outdir: pathlib.Path, default: str) -> str:
    """Which tier this one run was made on.

    The gate in evals.md §10.1 is per tier (>= 80 % on the frontier model,
    >= 60 % on the smaller one), so a detection count with no tier attached
    cannot be read against it. A run directory may carry its own `model.txt`,
    because one round is often mixed.
    """
    for candidate in (outdir / "model.txt", outdir.parent / "model.txt"):
        if candidate.exists():
            return candidate.read_text().strip() or default
    return default


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare", help="build the objects and the prompts")
    p.add_argument("--workdir", type=pathlib.Path, required=True)
    p.add_argument("--only", nargs="+", choices=sorted(JUDGEMENT_MUTANTS))
    p.add_argument("--no-control", action="store_true",
                   help="skip the clean-object control run (not recommended)")
    s = sub.add_parser("score", help="score the responses the runs produced")
    s.add_argument("--workdir", type=pathlib.Path, required=True)
    s.add_argument("--model", default="unknown",
                   help="model tier these runs were made on; a run directory may override it "
                        "with a one-line model.txt. The v1.0 gate is per tier (evals.md §10.1), "
                        "so a score without it cannot be read against the criterion.")
    s.add_argument("-o", "--output", type=pathlib.Path)
    args = ap.parse_args(argv)
    return prepare(args) if args.cmd == "prepare" else score(args)


if __name__ == "__main__":
    sys.exit(main())
