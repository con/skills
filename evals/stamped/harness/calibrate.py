#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Calibrate the scripted half of the assessor against the defect mutants.

Builds the known-good R0 fixture, probes it (every answered item should come
back ``met``: that is the false-``unmet`` rate), then for each mutant copies the
fixture, injects one defect, probes again and checks that exactly the declared
items flipped.

    calibrate.py [--workdir DIR] [--only NAME ...] [-o calibration.json]

Reported numbers always carry their denominator, and a collateral flip (an item
the mutant did not declare) is reported rather than ignored: it is either a
probe that is too eager or a mutant that does more than it says.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
REPO = EVALS.parent.parent
FIXTURE = EVALS / "fixtures" / "make_r0_object.py"
MUTATE = EVALS / "mutants" / "mutate.py"
SKILLS = REPO / "skills"
RUN_PROBES = SKILLS / "assess-alignment-with-stamped-principles" / "scripts" / "run_probes.py"

sys.path.insert(0, str(EVALS / "mutants"))
sys.path.insert(0, str(EVALS / "fixtures"))
from make_r0_object import SIMULATED  # noqa: E402
from mutate import MUTANTS  # noqa: E402


COLLECTOR_FAILURE = "probe failed to run"


def _probe(path: pathlib.Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """(item id -> answer, probe name -> answer for probes with no item)."""
    out = subprocess.run(
        [sys.executable, str(RUN_PROBES), str(path), "--quiet"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"run_probes.py failed on {path}: {out.stderr.strip()}")
    payload = json.loads(out.stdout)
    # A probe that crashes is reported as `not-checked` and its items simply
    # vanish from the sweep — so a defect in a probe reads as "fewer items
    # answered" and nothing fails. One did exactly that, and only the item
    # count moving by one gave it away.
    crashed = {p["probe"]: p["reason"] for p in payload["probes"]
               if COLLECTOR_FAILURE in (p.get("reason") or "")}
    if crashed:
        raise RuntimeError("probe(s) crashed on " + str(path) + ": "
                           + "; ".join(f"{k}: {v}" for k, v in crashed.items()))
    answers: dict[str, dict] = {}
    extras: dict[str, dict] = {}
    severity = {"unmet": 0, "partial": 1, "not-checked": 2, "not-applicable": 3, "met": 4}
    for result in payload["probes"]:
        if not result["items"]:
            extras[result["probe"]] = {"status": result["status"], "reason": result["reason"]}
            continue
        for item in result["items"]:
            status = result.get("item_status", {}).get(item, result["status"])
            previous = answers.get(item)
            if previous is None or severity[status] < severity[previous["status"]]:
                answers[item] = {"status": status, "probe": result["probe"],
                                 "reason": result.get("item_reason", {}).get(item, result["reason"])}
    return answers, extras


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", type=pathlib.Path, help="where to build the objects (default: a temp dir)")
    ap.add_argument("--only", nargs="+", choices=sorted(MUTANTS))
    ap.add_argument("-o", "--output", type=pathlib.Path)
    ap.add_argument("--keep", action="store_true", help="keep the objects for inspection")
    args = ap.parse_args(argv)

    base = args.workdir or pathlib.Path(tempfile.mkdtemp(prefix="stamped-calibration-"))
    base.mkdir(parents=True, exist_ok=True)
    clean = base / "clean"
    if not (clean / ".git").exists():
        subprocess.run([sys.executable, str(FIXTURE), str(clean)], check=True, capture_output=True)

    baseline, baseline_extras = _probe(clean)
    accused = {i: a for i, a in baseline.items() if a["status"] in {"unmet", "partial"}}
    accused.update({k: v for k, v in baseline_extras.items() if v["status"] in {"unmet", "partial"}})
    # What the fixture itself declares as simulated is a correct verdict, not a
    # false accusation: the two are counted apart so that neither can hide the
    # other. The list lives with the fixture (`SIMULATED`).
    expected = {i: a for i, a in accused.items() if i in SIMULATED}
    false_unmet = {i: a for i, a in accused.items() if i not in SIMULATED}
    report: dict = {
        "clean_object": {
            "answered_items": len(baseline),
            "false_unmet": false_unmet,
            "false_unmet_rate": f"{len(false_unmet)}/{len(baseline)}",
            "expected_by_the_fixture": {i: SIMULATED[i] for i in expected},
        },
        "mutants": {},
    }

    names = args.only or sorted(MUTANTS)
    detected = 0
    for name in names:
        target = base / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(clean, target, symlinks=True)
        out = subprocess.run(
            [sys.executable, str(MUTATE), "apply", name, str(target)], capture_output=True, text=True
        )
        if out.returncode != 0:
            report["mutants"][name] = {"collector_failure": out.stderr.strip()[:400]}
            continue
        answers, extras = _probe(target)
        expect = MUTANTS[name]["expect"]
        expect_extra = MUTANTS[name].get("expect_extra") or {}
        got = {item: answers.get(item, {"status": "absent"})["status"] for item in expect}
        got_extra = {key: extras.get(key, {"status": "absent"})["status"] for key in expect_extra}
        hit = (all(got[item] == status for item, status in expect.items())
               and all(got_extra[key] == status for key, status in expect_extra.items()))
        detected += 1 if hit else 0
        also = MUTANTS[name].get("also", {})
        collateral = {
            item: answers[item]["status"]
            for item in answers
            if item not in expect
            and answers[item]["status"] != baseline.get(item, {}).get("status")
            and also.get(item) != answers[item]["status"]
        }
        report["mutants"][name] = {
            "expected": expect,
            "expected_extra": expect_extra,
            "observed": got,
            "observed_extra": got_extra,
            "detected": hit,
            "by_probe": {item: answers.get(item, {}).get("probe") for item in expect},
            "reasons": {item: answers.get(item, {}).get("reason") for item in expect},
            "collateral_flips": collateral,
        }
        flag = "detected" if hit else "MISSED  "
        shown = ", ".join(f"{i.split(':')[-1]}={s}" for i, s in got.items())
        if got_extra:
            shown += " | " + ", ".join(f"{k}={s}" for k, s in got_extra.items())
        print(f"{flag}  {name:<26} {shown}")
        if collateral:
            print("          collateral: " + ", ".join(f"{i.split(':')[-1]}={s}" for i, s in collateral.items()))

    report["sensitivity"] = f"{detected}/{len(names)}"
    print(f"\nmutants detected: {detected}/{len(names)}")
    print(f"false unmet/partial on the clean object: {len(false_unmet)}/{len(baseline)} answered items"
          + (f" ({len(expected)} more are the fixture's declared simulations)" if expected else ""))
    for item, answer in false_unmet.items():
        print(f"  {item} = {answer['status']} ({answer['probe']}): {answer['reason']}")
    for item in expected:
        print(f"  (expected) {item} = {accused[item]['status']}: {SIMULATED[item]}")
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {args.output}")
    if not args.keep and args.workdir is None:
        shutil.rmtree(base, ignore_errors=True)
    else:
        print(f"objects kept in {base}")
    return 0 if detected == len(names) and not false_unmet else 1


if __name__ == "__main__":
    sys.exit(main())
