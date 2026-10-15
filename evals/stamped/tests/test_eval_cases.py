# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""The done criteria of docs/stamped/evals.md §10.1, as ordinary pytest.

`pytest-evals` was adopted for exactly this layer and nothing more
(docs/stamped/eval-platforms.md, recommendation 2): one **eval case** per
mutant, and one **analysis test** per eval that asserts the criterion over all
of them. The object generators, the probes and the scorers stay as they are —
no framework models "a filled STAMPED checklist".

    pytest evals/stamped/tests --run-eval --run-eval-analysis

Without those flags every test here is skipped, which is why the ordinary suite
in `test_probes.py` remains the fast gate and this file is the slow one.

Two evals, and they are different kinds of evidence:

* **scripted-mutants** runs now, deterministically: build the fixture, inject
  one defect, probe, compare with what the mutant declares. The "model" is the
  probe suite, so a failure here is a code regression.
* **judgement-mutants** cannot be re-run without spending tokens on model
  sessions, so its cases *read the recorded rounds* under `blind-runs/` and
  hold them to the gate. That keeps the criterion in the suite rather than in
  prose, and it is honest about its provenance: the analysis test prints the
  tier of every run it counted.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
sys.path.insert(0, str(EVALS / "harness"))
sys.path.insert(0, str(EVALS / "mutants"))
sys.path.insert(0, str(EVALS / "fixtures"))

from calibrate import FIXTURE, MUTATE, _probe  # noqa: E402
from make_r0_object import SIMULATED  # noqa: E402
from mutate import MUTANTS  # noqa: E402

# §10.1: ">= 90 % mutant detection per mechanically checkable MUST item, and
# <= 10 % false `unmet` on clean objects"; for the judgement half, ">= 80 %
# detected (flagged *and* named) on the frontier tier and >= 60 % on the
# smaller tier, with no collateral accusation on the clean fixture".
SCRIPTED_DETECTION = 0.90
FALSE_ACCUSATION = 0.10
JUDGEMENT_BY_TIER = {"frontier": 0.80, "smaller": 0.60}
SMALLER_TIERS = {"haiku"}
# The control's unexplained accusations: 7/19, 3/19, 6/22 (once the judgement
# denominator grew and rule 10 turned out to be over-applied), then **0/19**
# after the fixture documented its system requirements and the rule said what
# it is for. That is the §10.1 gate, so the ratchet is now the gate itself.
# Checked against the *most recent* round only: an earlier round cannot
# improve, and holding history to today's bar would freeze the number.
CONTROL_FALSE_ACCUSATION_CEILING = 0


@pytest.fixture(scope="session")
def clean_object(tmp_path_factory) -> pathlib.Path:
    base = tmp_path_factory.mktemp("stamped-eval-cases")
    clean = base / "clean"
    subprocess.run([sys.executable, str(FIXTURE), str(clean)], check=True, capture_output=True)
    return clean


@pytest.fixture(scope="session")
def clean_answers(clean_object) -> tuple[dict, dict]:
    return _probe(clean_object)


@pytest.mark.eval(name="scripted-mutants")
@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_scripted_mutant(name, clean_object, clean_answers, tmp_path, eval_bag):
    baseline, _ = clean_answers
    target = tmp_path / name
    shutil.copytree(clean_object, target, symlinks=True)
    subprocess.run([sys.executable, str(MUTATE), "apply", name, str(target)],
                   check=True, capture_output=True)
    answers, extras = _probe(target)

    spec = MUTANTS[name]
    expect, expect_extra = spec["expect"], spec.get("expect_extra") or {}
    got = {item: answers.get(item, {"status": "absent"})["status"] for item in expect}
    got_extra = {key: extras.get(key, {"status": "absent"})["status"] for key in expect_extra}
    also = spec.get("also", {})
    collateral = {item: answers[item]["status"] for item in answers
                  if item not in expect
                  and answers[item]["status"] != baseline.get(item, {}).get("status")
                  and also.get(item) != answers[item]["status"]}

    eval_bag.mutant = name
    eval_bag.model = "scripted probes"
    eval_bag.items = sorted(expect)
    eval_bag.expected = expect
    eval_bag.observed = got
    eval_bag.collateral = collateral
    eval_bag.detected = (all(got[i] == s for i, s in expect.items())
                         and all(got_extra[k] == s for k, s in expect_extra.items()))
    assert eval_bag.detected, f"{name}: expected {expect}, observed {got} {got_extra}"


@pytest.mark.eval(name="scripted-mutants")
def test_clean_object_is_not_accused(clean_answers, eval_bag):
    """The other half of the criterion: the floor under the ceiling."""
    baseline, extras = clean_answers
    accused = {i: a["status"] for i, a in baseline.items() if a["status"] in {"unmet", "partial"}}
    accused.update({k: v["status"] for k, v in extras.items() if v["status"] in {"unmet", "partial"}})
    # What the fixture declares about itself is a correct verdict (SIMULATED,
    # in the fixture builder): counted, reported, and not called false.
    declared = {i: s for i, s in accused.items() if i in SIMULATED}
    accused = {i: s for i, s in accused.items() if i not in SIMULATED}
    eval_bag.mutant = "clean"
    eval_bag.model = "scripted probes"
    eval_bag.items = []
    eval_bag.detected = not accused
    eval_bag.answered = len(baseline)
    eval_bag.false_accusations = accused
    eval_bag.declared_by_the_fixture = declared
    assert not accused, f"clean fixture accused on {accused}"


@pytest.mark.eval_analysis(name="scripted-mutants")
def test_scripted_detection_meets_the_gate(eval_results):
    per_item: dict[str, list[bool]] = {}
    clean = None
    for result in eval_results:
        bag = result.result
        if bag["mutant"] == "clean":
            clean = bag
            continue
        for item in bag["items"]:
            per_item.setdefault(item, []).append(bag["detected"])

    print("\nper-item detection (evals.md §10.1: >= 90 %)")
    weak = {}
    for item, hits in sorted(per_item.items()):
        rate = sum(hits) / len(hits)
        print(f"  {item.split(':')[-1]:<12} {sum(hits)}/{len(hits)}")
        if rate < SCRIPTED_DETECTION:
            weak[item] = f"{sum(hits)}/{len(hits)}"
    assert not weak, f"items below {SCRIPTED_DETECTION:.0%} detection: {weak}"

    assert clean is not None, "the clean-object case did not run; the false-accusation rate is unmeasured"
    rate = len(clean["false_accusations"]) / max(clean["answered"], 1)
    print(f"  false unmet/partial on the clean object: "
          f"{len(clean['false_accusations'])}/{clean['answered']}")
    assert rate <= FALSE_ACCUSATION, f"false accusation rate {rate:.0%} on the clean fixture"

    collateral = {r.result["mutant"]: r.result["collateral"] for r in eval_results
                  if r.result.get("collateral")}
    assert not collateral, f"collateral item flips (a probe too eager, or a mutant doing more " \
                           f"than it declares): {collateral}"


def _judgement_rounds() -> list[pathlib.Path]:
    return sorted((EVALS / "blind-runs").glob("*/score*.json"))


def _latest_round(paths: list[str]) -> str | None:
    """The most recent recorded round, by the date its directory carries."""
    return sorted(paths)[-1] if paths else None


@pytest.mark.eval(name="judgement-mutants")
@pytest.mark.parametrize("record", _judgement_rounds(), ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_recorded_judgement_round(record, eval_bag):
    """A recorded round, held to the gate.

    These runs are model sessions: re-running one costs tokens, so the case
    reads what was recorded instead of spending them again. The analysis test
    says which tier each counted run was on.
    """
    report = json.loads(record.read_text())
    scored = {n: e for n, e in report["mutants"].items() if e.get("scored")}
    eval_bag.round = f"{record.parent.name}/{record.stem}"
    eval_bag.detected = [n for n, e in scored.items() if e.get("detected")]
    eval_bag.missed = [n for n, e in scored.items() if not e.get("detected") and not e.get("control")]
    eval_bag.models = {n: e.get("model", report.get("model", "unknown")) for n, e in scored.items()}
    eval_bag.controls = {n: e for n, e in scored.items() if e.get("control")}
    assert scored, f"{record} records no scored run"


@pytest.mark.eval_analysis(name="judgement-mutants")
def test_recorded_judgement_rounds_meet_the_gate(eval_results):
    by_tier: dict[str, list[bool]] = {}
    controls: dict[str, str] = {}
    counts: dict[str, int] = {}
    for result in eval_results:
        bag = result.result
        for mutant, model in bag["models"].items():
            if mutant in bag["controls"]:
                continue
            tier = "smaller" if model in SMALLER_TIERS else "frontier"
            by_tier.setdefault(tier, []).append(mutant in bag["detected"])
        for mutant, entry in bag["controls"].items():
            key = f"{bag['round']}:{mutant}"
            controls[key] = entry.get("false_accusation_rate", "")
            counts[key] = len(entry.get("false_accusations") or {})
    latest = _latest_round(list(counts))
    worst_control = counts.get(latest, 0) if latest else 0

    print("\njudgement detection by tier (evals.md §10.1)")
    for tier, hits in sorted(by_tier.items()):
        print(f"  {tier:<9} {sum(hits)}/{len(hits)}  (gate {JUDGEMENT_BY_TIER[tier]:.0%})")
    print(f"  control false accusations: {controls or 'none recorded'}")
    print(f"  ratchet applies to the most recent round: {latest or 'none'}")

    for tier, hits in by_tier.items():
        rate = sum(hits) / len(hits)
        assert rate >= JUDGEMENT_BY_TIER[tier], \
            f"{tier} tier detected {sum(hits)}/{len(hits)}, below {JUDGEMENT_BY_TIER[tier]:.0%}"
    assert worst_control <= CONTROL_FALSE_ACCUSATION_CEILING, (
        f"the most recent control run ({latest}) made {worst_control} unexplained accusations, "
        f"above the current ratchet of {CONTROL_FALSE_ACCUSATION_CEILING}; the §10.1 gate is zero"
    )
