# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Tests for the STAMPED probes, the mutants and the response encoder.

They live outside the skill directories on purpose (K-Dense convention): a
skill ships its instructions and its scripts, not its test suite.

    python3 -m pytest evals/stamped/tests -q
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[3]
EVALS = REPO / "evals" / "stamped"
ASSESS = REPO / "assess-alignment-with-stamped-principles"
CONVENTIONS = REPO / "stamped-conventions"

sys.path.insert(0, str(ASSESS / "scripts"))
sys.path.insert(0, str(CONVENTIONS / "scripts"))
sys.path.insert(0, str(EVALS / "mutants"))

from encode_response import Checklist, app_payload, decode, encode, template, validate  # noqa: E402
from mutate import MUTANTS  # noqa: E402
from probes import REGISTRY, Object  # noqa: E402


@pytest.fixture(scope="session")
def clean(tmp_path_factory) -> pathlib.Path:
    root = tmp_path_factory.mktemp("fixture") / "clean"
    subprocess.run(
        [sys.executable, str(EVALS / "fixtures" / "make_r0_object.py"), str(root)],
        check=True, capture_output=True,
    )
    return root


def _statuses(root: pathlib.Path) -> dict[str, str]:
    obj = Object(root)
    severity = {"unmet": 0, "partial": 1, "not-checked": 2, "not-applicable": 3, "met": 4}
    out: dict[str, str] = {}
    for probe in REGISTRY.values():
        result = probe(obj)
        for item in result.items:
            status = result.status_of(item)
            if item not in out or severity[status] < severity[out[item]]:
                out[item] = status
    return out


# `platform-assumptions` never returns `met`: it can only flag platform-specific
# commands, and must/011 and must/012 ask about host assumptions in general. Its
# silence is a prompt to read, not a pass — an earlier version claimed `met` and
# a blind run took that at face value, missing a documented route through a lab
# mount. The items it covers are therefore expected to come back `not-checked`.
PROBE_NEVER_MET = {"stamped-checklist:must/011", "stamped-checklist:must/012"}


def test_fixture_is_clean_and_all_probes_pass(clean):
    statuses = _statuses(clean)
    assert statuses, "no probe answered any item"
    bad = {item: status for item, status in statuses.items()
           if status != "met" and item not in PROBE_NEVER_MET}
    assert not bad, f"the known-good fixture should be all met, got {bad}"
    for item in PROBE_NEVER_MET:
        assert statuses.get(item) == "not-checked", (
            f"{item} should be left for judgement, got {statuses.get(item)}"
        )


def test_every_probe_returns_a_known_status(clean):
    obj = Object(clean)
    allowed = {"met", "partial", "unmet", "not-checked", "not-applicable"}
    checklist = Checklist()
    for name, probe in REGISTRY.items():
        result = probe(obj)
        assert result.status in allowed, f"{name} returned {result.status}"
        assert len(result.reason) <= 250, f"{name} reason is too long for the checklist app"
        for item in result.items:
            assert item in checklist.by_id, f"{name} answers unknown item {item}"
        if result.status in {"met", "partial", "unmet"}:
            assert result.evidence, f"{name} reported {result.status} without evidence"


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_mutant_flips_its_items(clean, tmp_path, name):
    target = tmp_path / name
    shutil.copytree(clean, target, symlinks=True)
    subprocess.run(
        [sys.executable, str(EVALS / "mutants" / "mutate.py"), "apply", name, str(target)],
        check=True, capture_output=True,
    )
    statuses = _statuses(target)
    for item, expected in MUTANTS[name]["expect"].items():
        assert statuses.get(item) == expected, (
            f"{name}: {item} is {statuses.get(item)}, expected {expected}"
        )


def test_probes_do_not_modify_the_object(clean, tmp_path):
    target = tmp_path / "untouched"
    shutil.copytree(clean, target, symlinks=True)
    before = subprocess.run(["git", "status", "--porcelain"], cwd=target,
                            capture_output=True, text=True).stdout
    head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target,
                                 capture_output=True, text=True).stdout
    _statuses(target)
    after = subprocess.run(["git", "status", "--porcelain"], cwd=target,
                           capture_output=True, text=True).stdout
    head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=target,
                                capture_output=True, text=True).stdout
    assert (before, head_before) == (after, head_after)


def test_run_probes_writes_a_valid_response(clean, tmp_path):
    response = tmp_path / "response.json"
    subprocess.run(
        [sys.executable, str(ASSESS / "scripts" / "run_probes.py"), str(clean),
         "--kind", "study", "--response", str(response), "--quiet"],
        check=True, capture_output=True,
    )
    payload = json.loads(response.read_text())
    checklist = Checklist()
    assert set(payload["responses"]) == set(checklist.by_id)
    problems = validate(payload, checklist)
    # A draft is not a finished response: validate() must refuse it, and the
    # only reasons it refuses are the two a draft legitimately has — items no
    # probe answered still carrying the placeholder, and probe verdicts whose
    # evidence the assessor has not yet cited.
    assert problems, "validate() accepted a probe draft as a finished response"
    unexpected = [
        p for p in problems
        if "placeholder" not in p and "needs at least one evidence" not in p
    ]
    assert unexpected == [], unexpected
    assert any("placeholder" in p for p in problems)


def test_checklist_pin_matches_the_lock():
    out = subprocess.run(
        [sys.executable, str(CONVENTIONS / "scripts" / "vendor_checklist.py"), "--check"],
        capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr


def test_response_round_trips_through_the_app_url():
    checklist = Checklist()
    response = template(checklist)
    first = next(iter(response["responses"]))
    response["responses"][first] = {
        "value": None, "reason": "code/plot.py hardcodes an input path", "status": "unmet",
        "evidence": [{"uri": "code/plot.py#L12", "description": "absolute path", "sha256": None}],
        "source": "probe:no-abs-paths",
    }
    url = encode(response, checklist)
    assert "format=3" in url and "responses=" in url
    back = decode(url, checklist)
    assert set(back["responses"]) == set(checklist.by_id)
    assert back["responses"][first]["value"] == "no"
    assert back["responses"][first]["reason"].startswith("code/plot.py")


def test_app_payload_only_carries_what_the_app_accepts():
    checklist = Checklist()
    response = template(checklist)
    first = next(iter(response["responses"]))
    response["responses"][first].update(status="met", reason="x" * 400)
    payload = app_payload(response, checklist)
    answer = payload["responses"][first]
    assert set(answer) == {"value", "reason"}
    assert answer["value"] == "yes"
    assert len(answer["reason"]) == 250


def test_must_items_are_never_satisfied_by_partial():
    checklist = Checklist()
    response = template(checklist)
    must = next(i["id"] for i in checklist.items if i["level"] == "must")
    response["responses"][must] = {
        "value": None, "reason": "met in code, violated in derivatives", "status": "partial",
        "evidence": [{"uri": "derivatives/", "description": "no run record", "sha256": None}],
        "source": "judgement",
    }
    assert app_payload(response, checklist)["responses"][must]["value"] == "no"


def test_unknown_item_id_is_refused():
    checklist = Checklist()
    response = template(checklist)
    response["responses"]["stamped-checklist:must/999"] = {
        "value": "yes", "reason": "", "status": "met", "evidence": [{"uri": "x", "description": "y"}],
    }
    problems = validate(response, checklist)
    assert any("unknown item ids" in p for p in problems)


def _tiny_reproducible_object(root: pathlib.Path) -> pathlib.Path:
    """A git repository whose documented entry point re-creates its output."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "Makefile").write_text("all: results.tsv\nresults.tsv:\n\tprintf 'a\\tb\\n1\\t2\\n' > $@\n")
    (root / "results.tsv").write_text("a\tb\n1\t2\n")
    (root / "README.md").write_text("# demo\n\n## Usage\n\n`make all`\n")
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.org",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.org",
    }
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "demo"]):
        subprocess.run(cmd, cwd=root, env=env, check=True, capture_output=True)
    return root


def test_fresh_rerun_reproduces_a_reproducible_object(tmp_path):
    source = _tiny_reproducible_object(tmp_path / "source")
    report = tmp_path / "fresh-rerun.json"
    subprocess.run(
        [sys.executable, str(ASSESS / "scripts" / "fresh_rerun.py"), "--path", str(source),
         "--entry", "rm -f results.tsv && make all", "--outputs", "*.tsv",
         "--workdir", str(tmp_path / "work"), "-o", str(report)],
        check=True, capture_output=True,
    )
    result = json.loads(report.read_text())
    assert result["status"] == "met", result["reason"]
    assert result["comparison"]["identical"] == ["results.tsv"]


def test_fresh_rerun_reports_a_difference_as_such(tmp_path):
    source = _tiny_reproducible_object(tmp_path / "drifting")
    # The entry point writes something else: the object does not reproduce.
    (source / "Makefile").write_text("all: results.tsv\nresults.tsv:\n\tprintf 'a\\tb\\n9\\t9\\n' > $@\n")
    subprocess.run(["git", "commit", "-qam", "drift"], cwd=source, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "fixture",
                        "GIT_AUTHOR_EMAIL": "fixture@example.org",
                        "GIT_COMMITTER_NAME": "fixture",
                        "GIT_COMMITTER_EMAIL": "fixture@example.org"})
    report = tmp_path / "fresh-rerun-2.json"
    subprocess.run(
        [sys.executable, str(ASSESS / "scripts" / "fresh_rerun.py"), "--path", str(source),
         "--entry", "rm -f results.tsv && make all", "--outputs", "*.tsv",
         "--workdir", str(tmp_path / "work2"), "-o", str(report)],
        check=True, capture_output=True,
    )
    result = json.loads(report.read_text())
    assert result["status"] in {"unmet", "partial"}, result
    assert result["comparison"]["differing"] == ["results.tsv"]


# The path classifier is the probe that a blind run caught being blind, so its
# cases are pinned individually: each line here is a verdict somebody argued
# about once.
@pytest.mark.parametrize(("line", "expected"), [
    ('WV=/data/yoh/compression-comparisons/vendor/wavpack', "host"),
    ('inputs=/mnt/labshare/openneuro/ds007116', "host"),
    ('home = "/home/researcher/data"', "home"),
    ('out > /tmp/scratch-file', "tmp"),
    # DataLad registry shortcuts are locations anyone can resolve.
    ('"SourceDatasets": [{"URL": "///openneuro/ds000003"}]', None),
    ('datalad clone ///repronim/containers code/containers', None),
    ('url = ria+http://store.datalad.org#~abc', None),
    # System roots and URLs are not host paths.
    ('#!/usr/bin/env python3', None),
    ('export FREESURFER_HOME=/opt/local/freesurfer-7.4.1', None),
    ('pip install "datalad @ git+https://github.com/datalad/datalad.git@30b6dee"', None),
])
def test_absolute_path_classifier(line, expected):
    from probes.structure import _classify_path

    assert _classify_path(line) == expected


def test_judgement_mutants_do_not_trip_the_probes(clean, tmp_path):
    """A judgement mutant that a script catches is not testing judgement."""
    sys.path.insert(0, str(EVALS / "mutants"))
    from judgement import JUDGEMENT_MUTANTS

    baseline = _statuses(clean)
    for name, spec in sorted(JUDGEMENT_MUTANTS.items()):
        target = tmp_path / name
        shutil.copytree(clean, target, symlinks=True)
        subprocess.run(
            [sys.executable, str(EVALS / "mutants" / "judgement.py"), "apply", name, str(target)],
            check=True, capture_output=True,
        )
        after = _statuses(target)
        expected = {**baseline, **(spec.get("probes_expected") or {})}
        changed = {i: s for i, s in after.items() if expected.get(i) != s}
        assert not changed, f"{name} changed probe verdicts: {changed}"


def test_skill_states_the_coverage_it_actually_has(clean):
    """The counts in SKILL.md must match what the probes answer.

    Two blind runs in a row reported that the skill's "probes answer N of the
    MUST items, M SHOULD items" sentence was wrong after the probe set grew. A
    doc that drifts from the code is a doc nobody can trust, so the sentence is
    pinned here.
    """
    import re

    statuses = _statuses(clean)
    checklist = Checklist()
    answered = {level: sum(1 for i in checklist.items
                           if i["level"] == level and i["id"] in statuses)
                for level in ("must", "should", "may")}
    text = (ASSESS / "SKILL.md").read_text()
    match = re.search(r"answers (\d+) of the (\d+) MUST items, (\d+) SHOULD items", text)
    assert match, "SKILL.md no longer states its probe coverage in the expected form"
    stated_must, stated_total, stated_should = (int(g) for g in match.groups())
    assert stated_must == answered["must"], f"SKILL.md says {stated_must} MUST, probes answer {answered['must']}"
    assert stated_should == answered["should"], (
        f"SKILL.md says {stated_should} SHOULD, probes answer {answered['should']}"
    )
    assert stated_total == sum(1 for i in checklist.items if i["level"] == "must")


# The guards create-stamped-project installs are artifacts, so they are tested
# like artifacts: on the clean fixture they pass, on a mutant they fail.
TEMPLATES = REPO / "create-stamped-project" / "templates"


def test_preflight_passes_on_the_clean_fixture(clean):
    out = subprocess.run(["sh", str(TEMPLATES / "preflight.sh")], cwd=clean,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


@pytest.mark.parametrize("name", ["abs-path-in-script", "relative-subdataset-url", "untracked-figure"])
def test_preflight_refuses_a_mutant(clean, tmp_path, name):
    target = tmp_path / name
    shutil.copytree(clean, target, symlinks=True)
    subprocess.run([sys.executable, str(EVALS / "mutants" / "mutate.py"), "apply", name, str(target)],
                   check=True, capture_output=True)
    out = subprocess.run(["sh", str(TEMPLATES / "preflight.sh")], cwd=target,
                         capture_output=True, text=True)
    assert out.returncode == 1, f"preflight passed on {name}: {out.stdout}"


def test_run_guard_refuses_an_outside_commit(tmp_path):
    """And allows the run's own commit, which is the whole difficulty."""
    repo = tmp_path / "guarded"
    repo.mkdir()
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True, env=env)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_bytes((TEMPLATES / "pre-commit-run-guard").read_bytes())
    hook.chmod(0o755)
    (repo / "f").write_text("x\n")
    subprocess.run(["git", "add", "f"], cwd=repo, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "first"], cwd=repo, check=True, env=env)

    (repo / ".datalad-run-in-flight").touch()
    (repo / "f").write_text("y\n")
    subprocess.run(["git", "add", "f"], cwd=repo, check=True, env=env)
    blocked = subprocess.run(["git", "commit", "-qm", "outside"], cwd=repo,
                             capture_output=True, text=True, env=env)
    assert blocked.returncode != 0, "the guard let an outside commit through"
    assert "run is in flight" in blocked.stderr

    allowed = subprocess.run(["git", "commit", "-qm", "the run's own"], cwd=repo,
                             capture_output=True, text=True, env={**env, "IN_FLIGHT_OK": "1"})
    assert allowed.returncode == 0, allowed.stderr
