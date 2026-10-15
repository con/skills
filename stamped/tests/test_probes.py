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
ENCODE = CONVENTIONS / "scripts" / "encode_response.py"

sys.path.insert(0, str(ASSESS / "scripts"))
sys.path.insert(0, str(CONVENTIONS / "scripts"))
sys.path.insert(0, str(EVALS / "mutants"))
sys.path.insert(0, str(EVALS / "fixtures"))

from encode_response import Checklist, app_payload, decode, encode, template, validate  # noqa: E402
from make_r0_object import SIMULATED  # noqa: E402
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
           if status != "met" and item not in PROBE_NEVER_MET and item not in SIMULATED}
    assert not bad, f"the known-good fixture should be all met, got {bad}"
    # `SIMULATED` is about what no *honest assessment* can call met, which is
    # not the same as what the probes can see: the unfetchable pin and the
    # placeholder container look fine offline, so the probes answer `met` on
    # must/002 and should/006 and a reading run is what catches them. The place
    # that checks the declaration is still current is the judgement control
    # run, whose "expected" list is exactly this one.
    for item in PROBE_NEVER_MET:
        assert statuses.get(item) == "not-checked", (
            f"{item} should be left for judgement, got {statuses.get(item)}"
        )


def test_no_probe_crashes_on_the_clean_fixture(clean, tmp_path):
    """A crashed probe is `not-checked` and its items disappear.

    Nothing failed when one did: the sweep simply answered one item fewer,
    and the calibration reported a smaller denominator as if that were normal.
    """
    out = subprocess.run([sys.executable, str(ASSESS / "scripts" / "run_probes.py"),
                          str(clean), "--quiet"], capture_output=True, text=True, check=True)
    payload = json.loads(out.stdout)
    crashed = {p["probe"]: p["reason"] for p in payload["probes"]
               if "probe failed to run" in (p.get("reason") or "")}
    assert not crashed, crashed
    answered = {item for p in payload["probes"] for item in p["items"]}
    assert "stamped-checklist:must/009" in answered


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
    # A path relative to a variable is portable, and three of these cost a
    # real object its must/009 in a blind run.
    ('- run: cp results ${HOME}/artifacts/out.tsv', None),
    ('TMPDIR=${RUNNER_TEMP}/work', None),
    ('out="$CI_PROJECT_DIR/results/table.tsv"', None),
    ('cd ~/scratch/ds007116', None),
    # The tail of a relative glob: three slashes after the variable, and the
    # one before `ses-1` used to read as the root of an absolute path. It cost
    # a real R1 arm must/009 twice.
    ('for m in sorted(glob.glob(f"{maskdir}/sub-*/ses-1/anat/*_mask.nii.gz")):', None),
    ('- **Products**: `derivatives/synthstrip-7.4.1/sub-*/ses-1/anat/*_desc-brain_mask.nii.gz`', None),
    ('out = f"{outdir}/sub-{sid}/ses-1/anat"', None),
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
    match = re.search(r"covers (\d+) of the (\d+) MUST items, (\d+) SHOULD items", text)
    assert match, "SKILL.md no longer states its probe coverage in the expected form"
    stated_must, stated_total, stated_should = (int(g) for g in match.groups())
    assert stated_must == answered["must"], f"SKILL.md says {stated_must} MUST, probes cover {answered['must']}"
    # Covered is not answered, and the skill now says both numbers: the ones
    # that come back with a verdict, and the ones a probe can only hand over.
    with_verdict = sum(1 for item, status in statuses.items()
                       if item.endswith(tuple(f"must/{n:03d}" for n in range(1, 18)))
                       and status != "not-checked")
    verdict_match = re.search(r"so (\w+) come back with a verdict", text)
    words = {"eleven": 11, "twelve": 12, "thirteen": 13, "ten": 10, "nine": 9}
    assert verdict_match and words.get(verdict_match.group(1)) == with_verdict, (
        f"SKILL.md says {verdict_match.group(1) if verdict_match else '?'} MUST items come back with a "
        f"verdict; on the clean fixture {with_verdict} do"
    )
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


def _guarded_repo(root: pathlib.Path) -> dict:
    """A repository with the guard installed and one commit, plus its env."""
    root.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True, env=env)
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.write_bytes((TEMPLATES / "pre-commit-run-guard").read_bytes())
    hook.chmod(0o755)
    wrapper = root / "run-recorded.sh"
    wrapper.write_bytes((TEMPLATES / "run-recorded.sh").read_bytes())
    wrapper.chmod(0o755)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "first"], cwd=root, check=True, env=env)
    return env


# Three bugs an agent hit while using this template for real, each now pinned.
def test_run_recorded_clears_its_marker(tmp_path):
    """`exec` would replace the process and skip the cleanup trap, leaving the
    marker behind so the guard refused every later commit — the guard
    inflicting the hazard it exists to prevent."""
    root = tmp_path / "wrapper"
    env = _guarded_repo(root)
    done = subprocess.run(["sh", "./run-recorded.sh", "-m", "write a file", "--",
                           "sh", "-c", "echo out > made.txt"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode == 0, done.stderr
    assert not (root / ".git" / "datalad-run-in-flight").exists(), "marker survived a successful run"
    # and the next commit is not blocked
    (root / "another").write_text("x\n")
    subprocess.run(["git", "add", "another"], cwd=root, check=True, env=env)
    after = subprocess.run(["git", "commit", "-qm", "after the run"], cwd=root,
                           capture_output=True, text=True, env=env)
    assert after.returncode == 0, after.stderr


def test_run_recorded_clears_its_marker_when_the_command_fails(tmp_path):
    root = tmp_path / "wrapper-fail"
    env = _guarded_repo(root)
    done = subprocess.run(["sh", "./run-recorded.sh", "-m", "fail on purpose", "--",
                           "sh", "-c", "exit 3"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode != 0
    assert not (root / ".git" / "datalad-run-in-flight").exists(), "marker survived a failed run"


def test_run_recorded_keeps_a_multiword_message_intact(tmp_path):
    """Unquoted `$@` re-split the message and `datalad run` tried to execute a
    word of it."""
    root = tmp_path / "wrapper-msg"
    env = _guarded_repo(root)
    message = "collect per-session brain volumes"
    done = subprocess.run(["sh", "./run-recorded.sh", "-m", message, "--",
                           "sh", "-c", "echo out > made.txt"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode == 0, done.stderr
    assert "per-session: not found" not in done.stderr
    log = subprocess.run(["git", "log", "--format=%B", "-1"], cwd=root,
                         capture_output=True, text=True, env=env).stdout
    assert message in log or "made.txt" in log


def test_run_recorded_leaves_the_worktree_clean_for_datalad(tmp_path):
    """The marker must not be an untracked worktree file: `datalad run` refuses
    to start when there are untracked files."""
    root = tmp_path / "wrapper-clean"
    env = _guarded_repo(root)
    script = root / "probe-worktree.sh"
    script.write_text("#!/bin/sh\ngit status --porcelain --untracked-files=all > /tmp/wt-status\n")
    script.chmod(0o755)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "add probe"], cwd=root, check=True, env=env)
    subprocess.run(["sh", "./run-recorded.sh", "-m", "check", "--", "sh", "./probe-worktree.sh"],
                   cwd=root, check=True, capture_output=True, text=True, env=env)
    status = pathlib.Path("/tmp/wt-status").read_text()
    assert "datalad-run-in-flight" not in status, f"marker is visible in the worktree: {status}"


def _stub_datalad(root: pathlib.Path) -> pathlib.Path:
    """A `datalad` on PATH that records how it was called and does nothing."""
    bindir = root / "stub-bin"
    bindir.mkdir(parents=True, exist_ok=True)
    stub = bindir / "datalad"
    stub.write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$DATALAD_STUB_LOG\"\n"
        # `DATALAD_STUB_EXIT` lets a test exercise the path where *datalad*
        # fails rather than the command, which is where a real run reported a
        # marker surviving.
        "exit ${DATALAD_STUB_EXIT:-0}\n"
    )
    stub.chmod(0o755)
    return bindir


@pytest.mark.parametrize(
    "argv, expected",
    [
        (["-m", "plain", "--", "true"], "run -m plain -- true"),
        (["-n", "synthstrip", "-m", "strip", "--", "true"],
         "containers-run -n synthstrip -m strip -- true"),
        # The mistake an R1 arm actually made: naming the subcommand in the
        # command position, which nested one record inside another and declared
        # no inputs or outputs.
        (["datalad", "containers-run", "-m", "strip", "--", "true"],
         "containers-run -m strip -- true"),
    ],
)
def test_run_recorded_dispatches_containers_run(tmp_path, argv, expected):
    root = tmp_path / "dispatch"
    env = _guarded_repo(root)
    log = tmp_path / "datalad-calls.log"
    env = {**env, "PATH": f"{_stub_datalad(tmp_path)}:{env['PATH']}",
           "DATALAD_STUB_LOG": str(log)}
    done = subprocess.run(["sh", "./run-recorded.sh", *argv],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert log.read_text().strip() == expected


def test_preflight_ignores_installed_tooling(tmp_path, clean):
    """A harness directory's own files are not the project's: flagging them
    produced a FAIL an agent could not fix."""
    target = tmp_path / "with-harness"
    shutil.copytree(clean, target, symlinks=True)
    skills = target / ".claude" / "skills" / "some-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("Example: /home/someone/data/in/a/doc\n")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "install a skill"], cwd=target, check=True, env=env)
    out = subprocess.run(["sh", str(TEMPLATES / "preflight.sh")], cwd=target,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr


# R1's oracle, pinned in all three directions it can be wrong: an honest
# product passes, the R0 shortcut (copying the shipped column) fails, and a
# short run fails. The numbers come from the 2026-10-14 two-container pilot.
R1 = EVALS / "use-cases" / "r1-brain-extraction"


def _r1_object(root: pathlib.Path, rows: list[tuple[str, float, float]],
               header: str = "subject\tage\tmask_volume_mm3",
               fmt=lambda v: f"{v:.0f}") -> pathlib.Path:
    (root / "results").mkdir(parents=True)
    (root / "figures").mkdir(parents=True)
    lines = [header] + [f"{s}\t{a}\t{fmt(v)}" for s, a, v in rows]
    (root / "results" / "brain_size.tsv").write_text("\n".join(lines) + "\n")
    (root / "figures" / "brain_size_vs_age.png").write_bytes(b"PNG-placeholder")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "product"], cwd=root, check=True, env=env)
    return root


def _fake_dataset(root: pathlib.Path, shipped: dict[str, float]) -> pathlib.Path:
    """A stand-in ds007116 carrying only the comparator column."""
    root.mkdir(parents=True, exist_ok=True)
    for sub, vol in shipped.items():
        qc = root / "derivatives" / "freesurfer-post" / sub / f"{sub}_ses-1_desc-FreeSurfer_qc.tsv"
        qc.parent.mkdir(parents=True, exist_ok=True)
        qc.write_text(f"session_id\tmask_maskvol\nses-1\t{vol}\n")
    return root


def _run_r1_oracle(obj: pathlib.Path, dataset: pathlib.Path) -> dict:
    out = subprocess.run([sys.executable, str(R1 / "oracle" / "check_r1.py"), str(obj),
                          "--dataset", str(dataset)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_r1_oracle_accepts_an_honest_product(tmp_path):
    shipped = {f"sub-{i:05d}": 1_500_000.0 for i in range(1, 11)}
    _fake_dataset(tmp_path / "ds", shipped)
    rows = [(s, 9.0 + i * 0.8, v * 1.06) for i, (s, v) in enumerate(shipped.items())]
    obj = _r1_object(tmp_path / "obj", rows)
    result = _run_r1_oracle(obj, tmp_path / "ds")
    assert result["status"] == "met", result["reason"]
    assert result["subjects_measured"] == 10


def test_r1_oracle_rejects_copying_the_shipped_column(tmp_path):
    """From R1 on the shipped derivatives are the comparator, not a result."""
    shipped = {f"sub-{i:05d}": 1_500_000.0 + i for i in range(1, 11)}
    _fake_dataset(tmp_path / "ds", shipped)
    rows = [(s, 9.0 + i * 0.8, v) for i, (s, v) in enumerate(shipped.items())]
    obj = _r1_object(tmp_path / "obj", rows)
    result = _run_r1_oracle(obj, tmp_path / "ds")
    assert result["status"] != "met"
    assert "copied, not computed" in result["reason"]


def test_r1_oracle_rejects_a_short_run_and_an_implausible_volume(tmp_path):
    shipped = {f"sub-{i:05d}": 1_500_000.0 for i in range(1, 11)}
    _fake_dataset(tmp_path / "ds", shipped)
    short = [(s, 9.0 + i, v * 1.06) for i, (s, v) in enumerate(list(shipped.items())[:3])]
    result = _run_r1_oracle(_r1_object(tmp_path / "short", short), tmp_path / "ds")
    assert result["status"] != "met" and "only 3 subjects" in result["reason"]

    wild = [(s, 9.0 + i * 0.8, v * (3.0 if i == 0 else 1.06))
            for i, (s, v) in enumerate(shipped.items())]
    result = _run_r1_oracle(_r1_object(tmp_path / "wild", wild), tmp_path / "ds")
    assert result["status"] != "met" and "outside" in result["reason"]


def test_r1_oracle_will_not_pass_a_product_it_could_not_compare(tmp_path):
    """No comparator is `not-checked`, never `met`.

    Every check after the comparator lookup is a comparison, so an unfetched
    `qc.tsv` made all of them vacuously true and the oracle declared a run
    good on the strength of a table nobody had checked.
    """
    _fake_dataset(tmp_path / "empty", {})
    rows = [(f"sub-{i:05d}", 9.0 + i, 1_590_000.0) for i in range(1, 11)]
    obj = _r1_object(tmp_path / "obj", rows)
    result = _run_r1_oracle(obj, tmp_path / "empty")
    assert result["status"] == "not-checked", result
    assert "no mask_maskvol" in result["reason"]

    # Half the subjects comparable is not enough either: that is a finding
    # about the measurement, reported rather than averaged away.
    shipped = {f"sub-{i:05d}": 1_500_000.0 for i in range(1, 6)}
    _fake_dataset(tmp_path / "half", shipped)
    result = _run_r1_oracle(_r1_object(tmp_path / "obj2", rows), tmp_path / "half")
    assert result["status"] != "met"
    assert "no comparator for" in result["reason"]


def test_r1_oracle_reads_the_unit_the_column_declares(tmp_path):
    """Millilitres are good science; a thousandfold ratio is not a finding.

    The first two R1 arms shipped `brain_volume_mm3` and `brain_vol_ml`. With
    the unit ignored, the second read as ten implausible volumes (worst ratio
    0.0009) rather than as the same brain in other units.
    """
    shipped = {f"sub-{i:05d}": 1_500_000.0 for i in range(1, 11)}
    _fake_dataset(tmp_path / "ds", shipped)
    rows = [(s, 9.0 + i * 0.8, v * 1.06) for i, (s, v) in enumerate(shipped.items())]
    obj = _r1_object(tmp_path / "ml", rows, header="subject\tage\tbrain_vol_ml",
                     fmt=lambda v: f"{v / 1000:.1f}")
    result = _run_r1_oracle(obj, tmp_path / "ds")
    assert result["status"] == "met", result["reason"]
    assert result["unit"]["mm3_per_unit"] == 1000.0
    assert 1.05 < result["ratio_mean"] < 1.07

    # And the copy check still bites through the unit conversion: the shipped
    # column in millilitres is still the shipped column.
    copied = [(s, 9.0 + i, v) for i, (s, v) in enumerate(shipped.items())]
    obj = _r1_object(tmp_path / "ml-copy", copied, header="subject\tage\tbrain_vol_ml",
                     fmt=lambda v: f"{v / 1000:.6f}")
    result = _run_r1_oracle(obj, tmp_path / "ds")
    assert result["status"] != "met" and "copied, not computed" in result["reason"]


def test_r1_oracle_prefers_a_volume_over_a_voxel_count(tmp_path):
    """A count is a volume only when the voxels happen to be 1 mm^3."""
    shipped = {f"sub-{i:05d}": 1_500_000.0 for i in range(1, 11)}
    _fake_dataset(tmp_path / "ds", shipped)
    root = tmp_path / "obj"
    (root / "results").mkdir(parents=True)
    (root / "figures").mkdir(parents=True)
    lines = ["subject\tage\tmask_voxels\tbrain_volume_mm3"]
    for i, (sub, vol) in enumerate(shipped.items()):
        # 2 mm isotropic: the count is an eighth of the volume in mm^3.
        lines.append(f"{sub}\t{9.0 + i * 0.8}\t{vol * 1.06 / 8:.0f}\t{vol * 1.06:.0f}")
    (root / "results" / "brain_size.tsv").write_text("\n".join(lines) + "\n")
    (root / "figures" / "brain_size_vs_age.png").write_bytes(b"PNG-placeholder")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "product"], cwd=root, check=True, env=env)

    result = _run_r1_oracle(root, tmp_path / "ds")
    assert result["product"]["volume_column"] == "brain_volume_mm3", result["product"]
    assert result["status"] == "met", result["reason"]


def test_run_recorded_propagates_a_failure(tmp_path):
    """`if datalad …; then` reports the *if*'s status, which is always 0.

    The wrapper swallowed every failure for one commit because of that, which
    is worse than the bug it was added to report.
    """
    root = tmp_path / "wrapper-status"
    env = _guarded_repo(root)
    done = subprocess.run(["sh", "./run-recorded.sh", "-m", "fail", "--", "sh", "-c", "exit 3"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode != 0, done.stdout + done.stderr


def test_guard_clears_a_marker_whose_run_is_gone(tmp_path):
    """A killed run must not lock the repository out of committing.

    SIGKILL skips the wrapper's cleanup trap, and the marker it leaves then
    refuses every later commit — the guard inflicting the hazard it exists to
    prevent, which an agent hit for real.
    """
    root = tmp_path / "stale"
    env = _guarded_repo(root)
    marker = root / ".git" / "datalad-run-in-flight"

    # A pid that cannot be running: 0 is never a user process here.
    marker.write_text("2147483646\n")
    (root / "later.txt").write_text("work after the crash\n")
    subprocess.run(["git", "add", "later.txt"], cwd=root, check=True, env=env)
    done = subprocess.run(["git", "commit", "-qm", "after a killed run"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode == 0, done.stdout + done.stderr
    assert not marker.exists(), "the stale marker should have been removed"

    # A live run still refuses: the marker names this very process.
    marker.write_text(f"{os.getpid()}\n")
    (root / "during.txt").write_text("work during a run\n")
    subprocess.run(["git", "add", "during.txt"], cwd=root, check=True, env=env)
    done = subprocess.run(["git", "commit", "-qm", "during a run"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode != 0
    assert "in flight" in done.stdout + done.stderr


def test_tmp_paths_do_not_cost_must_009(tmp_path, clean):
    """`/tmp` is on every POSIX host, so it is not an assumption about *this* one.

    A live run lost must/009 for `/tmp/` in a CI workflow. The path is still
    worth reporting — it writes outside the object — but as a note.
    """
    target = tmp_path / "tmp-path"
    shutil.copytree(clean, target, symlinks=True)
    workflow = target / ".github" / "workflows" / "rerun.yml"
    workflow.write_text(workflow.read_text() + "      - run: make all > /tmp/build.log\n")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "log the build to /tmp"], cwd=target, check=True, env=env)

    obj = Object(target)
    result = REGISTRY["no-abs-paths"](obj)
    assert result.status == "met", (result.status, result.reason)
    assert "/tmp" in result.reason


def test_encode_response_set_and_table(tmp_path):
    """The two subcommands that exist because three runs hand-rolled them."""
    response = tmp_path / "response.json"
    subprocess.run([sys.executable, str(ENCODE), "template", "-o", str(response)],
                   check=True, capture_output=True)
    done = subprocess.run(
        [sys.executable, str(ENCODE), "set", str(response), "--item", "must/011",
         "--status", "met", "--source", "judgement",
         "--reason", "no host assumptions beyond a POSIX shell and the tracked lockfile",
         "--evidence", "README.md#requirements=the documented list"],
        capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    answer = json.loads(response.read_text())["responses"]["stamped-checklist:must/011"]
    assert answer["status"] == "met" and answer["source"] == "judgement"
    assert answer["evidence"][0]["uri"] == "README.md#requirements"

    # An unknown item is refused rather than written: a typo in an id would
    # otherwise make the app reject the whole load.
    done = subprocess.run(
        [sys.executable, str(ENCODE), "set", str(response), "--item", "must/999",
         "--status", "met", "--reason", "x"], capture_output=True, text=True)
    assert done.returncode == 2 and "not an item" in done.stderr

    out = subprocess.run([sys.executable, str(ENCODE), "table", str(response)],
                         capture_output=True, text=True, check=True).stdout
    assert out.startswith("| item | principles | status |")
    assert "| must/011 | " in out and "judgement" in out
    # MUST before SHOULD before MAY, as the report layout asks.
    assert out.index("must/001") < out.index("should/001") < out.index("may/001")


def test_run_recorded_declares_the_environment_spec(tmp_path):
    """must/006 asks that the record name the environment it ran in.

    Two of three live runs forgot: a `datalad run` with unchanged outputs
    writes no commit, so declaring the lockfile afterwards records nothing.
    The wrapper declares it on every run instead.
    """
    root = tmp_path / "env-input"
    env = _guarded_repo(root)
    (root / "requirements.lock").write_text("pandas==2.2.3\n")
    subprocess.run(["git", "add", "requirements.lock"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "pin the environment"], cwd=root, check=True, env=env)
    log = tmp_path / "calls.log"
    env = {**env, "PATH": f"{_stub_datalad(tmp_path)}:{env['PATH']}", "DATALAD_STUB_LOG": str(log)}

    subprocess.run(["sh", "./run-recorded.sh", "-m", "a recorded step", "--", "true"],
                   cwd=root, capture_output=True, text=True, env=env, check=True)
    assert log.read_text().strip() == "run -i requirements.lock -m a recorded step -- true"

    # Opting out is this wrapper's own flag and must not reach datalad — and
    # dropping it must not re-split the multi-word message.
    log.write_text("")
    subprocess.run(["sh", "./run-recorded.sh", "--no-env-input", "-m", "no env please", "--", "true"],
                   cwd=root, capture_output=True, text=True, env=env, check=True)
    assert log.read_text().strip() == "run -m no env please -- true"

    # `containers-run` already names an image, so nothing is added.
    log.write_text("")
    subprocess.run(["sh", "./run-recorded.sh", "-n", "img", "-m", "in a container", "--", "true"],
                   cwd=root, capture_output=True, text=True, env=env, check=True)
    assert log.read_text().strip() == "containers-run -n img -m in a container -- true"


def test_fresh_rerun_refuses_an_unbounded_fetch(tmp_path):
    """The step that pulled 87 GB of container images on its first real object.

    `datalad get -r .` is recursive and unbounded, and a module of a container
    registry carries every image the registry knows. The probe now asks how
    much it is about to fetch and skips the up-front fetch above the budget.
    """
    source = assess_scripts_fresh_rerun = ASSESS / "scripts" / "fresh_rerun.py"
    text = source.read_text()
    assert "--max-get-gb" in text
    assert 'datalad", "get", "-n", "-r"' in text, "modules must be installed without content first"
    # No unconditional recursive content fetch remains.
    assert text.count('"get", "-r", "-J4"') == 1
    budgeted = text.split("budget = ")[1]
    assert "pending <= budget" in budgeted


def test_remote_check_does_not_prompt_or_hang(tmp_path):
    """`git ls-remote` on a missing repository must fail, not ask.

    Without `GIT_TERMINAL_PROMPT=0` a missing or private GitHub repository
    prompts for credentials; three blind runs lost time to that before falling
    back to `curl`, and in a non-interactive harness it is a hang.
    """
    import time

    from probes.structure import _remote_resolves

    started = time.monotonic()
    # A path that cannot exist, so the answer is "no" without network.
    assert _remote_resolves(str(tmp_path / "nothing-here.git")) is False
    # And a URL that needs credentials: False (refused) or None (undecidable),
    # never a prompt and never a wait.
    assert _remote_resolves("https://github.com/con/this-repo-does-not-exist-9q7.git") in (False, None)
    assert time.monotonic() - started < 60, "the remote check should not block a run"


def test_entry_point_accepts_numbered_instructions(tmp_path, clean):
    """Instructions are instructions, heading or not.

    A real object (ReproNim/simple_workflow) lost must/007 because its README
    numbers its steps instead of putting them under a Markdown heading, and a
    blind run had to override the probe to say so.
    """
    target = tmp_path / "numbered"
    shutil.copytree(clean, target, symlinks=True)
    (target / "README.md").write_text(
        "# A simple workflow\n\n"
        "1. Install FSL and curl.\n"
        "2. Run `make all` to produce the table and the figure.\n"
        "3. Compare with `expected_output/`.\n"
    )
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "numbered instructions"], cwd=target, check=True, env=env)

    result = REGISTRY["entry-point"](Object(target))
    assert result.status_of("stamped-checklist:must/007") == "met", result.reason


def test_env_spec_pinned_when_every_dependency_is(tmp_path, clean):
    """`environment.yml` pinned to build strings is pinned, not a loose spec."""
    target = tmp_path / "conda"
    shutil.copytree(clean, target, symlinks=True)
    (target / "environment.yml").write_text(
        "name: demo\nchannels:\n  - conda-forge\ndependencies:\n"
        "  - python=3.11.9=h0755675_0\n  - numpy=1.26.4=py311h64a7726_0\n"
    )
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    # The lockfile and the registered container both go, so must/010 can only
    # be answered from the conda file. (The fixture carries a container
    # registration, which is itself a pinned specification — leaving it in
    # would make both halves of this test pass for the wrong reason.)
    subprocess.run(["git", "rm", "-q", "requirements.lock"], cwd=target, check=True, env=env)
    subprocess.run(["git", "rm", "-q", "-r", ".datalad", "code/containers"],
                   cwd=target, check=True, env=env)
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "conda environment, fully pinned"],
                   cwd=target, check=True, env=env)

    result = REGISTRY["env-spec-tracked"](Object(target))
    assert result.status_of("stamped-checklist:must/010") == "met", result.reason

    # And a floating one is still a floating one.
    (target / "environment.yml").write_text(
        "name: demo\nchannels:\n  - conda-forge\ndependencies:\n  - python\n  - numpy\n")
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "unpinned"], cwd=target, check=True, env=env)
    result = REGISTRY["env-spec-tracked"](Object(target))
    assert result.status_of("stamped-checklist:must/010") != "met", result.reason


def test_other_tools_provenance_counts_and_a_paper_is_not_a_product(tmp_path, clean):
    """Rule 7: name the mechanism you found, not the one you expected.

    A real object ships nipype PROV exports and a paper PDF. The probe called
    it `unmet` ("no run record"), counting the publication as a derived file it
    could not explain — two mistakes in one verdict, and a blind run had to
    talk it out of both.
    """
    target = tmp_path / "prov"
    shutil.copytree(clean, target, symlinks=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    # Strip the [DATALAD RUNCMD] history by re-creating the tree in a fresh
    # repository: what is left is files, a workflow-free layout and PROV.
    plain = tmp_path / "plain"
    plain.mkdir()
    for name in ("results", "figures"):
        shutil.copytree(target / name, plain / name)
    (plain / "README.md").write_text("# demo\n\n## Usage\n\nSee the provenance exports.\n")
    (plain / "results" / "workflow.provn").write_text(
        'document prefix nipype <http://nipy.org/nipype/terms/> entity(nipype:a) endDocument\n')
    (plain / "AVerySimplePublication_v3.pdf").write_bytes(b"%PDF-1.4 paper\n")
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"],
                ["git", "commit", "-qm", "products, provenance and the paper"]):
        subprocess.run(cmd, cwd=plain, check=True, env=env, capture_output=True)

    result = REGISTRY["derived-have-records"](Object(plain))
    assert result.status == "partial", (result.status, result.reason)
    assert "provenance artefact" in result.reason or "provenance" in result.reason
    assert "AVerySimplePublication_v3.pdf" not in str(result.details.get("candidates"))


def test_fresh_rerun_does_not_credit_an_entry_point_that_does_nothing(tmp_path):
    """`--entry true` must not score `met`.

    The probe recorded the shipped outputs, ran the entry point, and compared —
    so an entry point that did nothing left them untouched and scored as
    reproduction. Caught by running the probe with `--entry true` as a smoke
    test and getting `met`.
    """
    source = _tiny_reproducible_object(tmp_path / "noop-source")
    report = tmp_path / "noop.json"
    subprocess.run(
        [sys.executable, str(ASSESS / "scripts" / "fresh_rerun.py"), "--path", str(source),
         "--entry", "true", "--outputs", "*.tsv", "-o", str(report)],
        check=True, capture_output=True, text=True)
    result = json.loads(report.read_text())
    assert result["status"] != "met", result["reason"]
    assert "results.tsv" in str(result.get("comparison") or result["reason"])


def test_run_env_linked_reads_a_registered_container(tmp_path):
    """`datalad containers-add` with a locally built image leaves no `.sif`.

    The image lands at `.datalad/environments/<name>/image`, with no extension
    at all, and `containers-run` records the *expanded* call, so neither the
    image-suffix regex nor the word "containers-run" appears in the record.
    A blind run on the smaller model tier built exactly that layout; the probe
    called all seven of its records environment-less and must/006 came back
    `unmet` on an object where two records named a tracked, content-addressed
    image. The run had to override the probe by hand, which is the failure
    mode this probe exists to prevent.
    """
    root = tmp_path / "registered"
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True, env=env)
    (root / ".datalad").mkdir()
    (root / ".datalad" / "config").write_text(
        '[datalad "dataset"]\n\tid = 170f095d-4543-43e4-8e32-0b994e987e4a\n'
        '[datalad "containers.py313"]\n'
        "\timage = .datalad/environments/py313/image\n"
        "\tcmdexec = apptainer exec {img} {cmd}\n"
    )
    (root / ".datalad" / "environments" / "py313").mkdir(parents=True)
    (root / ".datalad" / "environments" / "py313" / "image").write_text("not really a SIF\n")
    (root / "results").mkdir()
    (root / "results" / "table.tsv").write_text("a\tb\n1\t2\n")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "register the container"], cwd=root, check=True, env=env)

    def record(message: str, cmd: str, outputs: list[str], extra: list[str]) -> None:
        info = {"chain": [], "cmd": cmd, "dsid": "170f095d-4543-43e4-8e32-0b994e987e4a",
                "exit": 0, "extra_inputs": extra, "inputs": extra, "outputs": outputs, "pwd": "."}
        body = ("[DATALAD RUNCMD] " + message + "\n\n=== Do not change lines below ===\n"
                + json.dumps(info, indent=1, sort_keys=True)
                + "\n^^^ Do not change lines above ^^^\n")
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", body], cwd=root,
                       check=True, env=env)

    record("build the table in container py313",
           "apptainer exec --bind ./lib:/lib .datalad/environments/py313/image "
           "python3 code/collect.py results/table.tsv",
           ["results/table.tsv"], [".datalad/environments/py313/image"])
    statuses = _statuses(root)
    assert statuses["stamped-checklist:must/006"] == "met", statuses
    # The image is a tracked file, so it is as pinned as a digest.
    assert statuses["stamped-checklist:must/015"] == "met", statuses

    # And a bare runtime invocation now reaches must/015 at all: before the
    # registered-image fix, a record naming a floating tag named "no
    # environment", so the float was invisible rather than reported.
    record("the same step, from a floating tag",
           "docker run myorg/analysis:latest python3 code/collect.py results/table.tsv",
           ["results/table.tsv"], [])
    statuses = _statuses(root)
    assert statuses["stamped-checklist:must/006"] == "met", statuses
    assert statuses["stamped-checklist:must/015"] == "unmet", statuses


def test_entry_point_reads_a_heading_that_is_not_a_keyword_first(tmp_path):
    """`## Entry point and reproduce` is a usage section however it is titled.

    A blind run wrote `## Requirements` (host tools, pinned image, lockfile)
    over `## Entry point and reproduce` (five commands), and must/007 came back
    `unmet` with "neither a README with install/usage instructions nor a
    Makefile" — the probe matching the word only at the start of a line and so
    grading the prose style rather than the question the item asks.
    """
    root = tmp_path / "headings"
    root.mkdir(parents=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True, env=env)
    (root / "code").mkdir()
    (root / "code" / "collect.py").write_text("print('hi')\n")

    def commit(readme: str) -> str:
        (root / "README.md").write_text(readme)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True, env=env)
        subprocess.run(["git", "commit", "-qm", "readme"], cwd=root, check=True, env=env)
        obj = Object(root)
        result = REGISTRY["entry-point"](obj)
        return result.status_of("stamped-checklist:must/007")

    assert commit(
        "# A study\n\n## Requirements\n\n- Linux, git-annex, apptainer.\n\n"
        "## Entry point and reproduce\n\n    python3 code/collect.py\n"
    ) == "met"

    # A README that genuinely says nothing about running it still fails, which
    # is the half of this probe that must not be loosened away.
    assert commit("# A study\n\n## Results\n\nThe brain got bigger.\n") == "unmet"


def test_must016_reads_every_remote_and_names_a_local_one(tmp_path, clean):
    """Two corrections, both from the conventions' own advice being followed.

    The probe read `remote.origin.url` only, so a project that did exactly what
    `create-stamped-project` asks — `datalad siblings add --name published` —
    was told it "records no remote at all". And a filesystem path is a real
    remote: reporting it as none denies the push happened, where the true
    finding is narrower and more useful.
    """
    target = tmp_path / "remotes"
    shutil.copytree(clean, target, symlinks=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    subprocess.run(["git", "remote", "remove", "origin"], cwd=target, check=True, env=env)

    def status_and_reason() -> tuple[str, str]:
        result = REGISTRY["env-spec-tracked"](Object(target))
        item = "stamped-checklist:must/016"
        return result.status_of(item), result.reason_of(item)

    status, reason = status_and_reason()
    assert status == "unmet" and "no remote at all" in reason

    # A sibling under any name is a remote.
    bare = tmp_path / "published.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, env=env)
    subprocess.run(["git", "remote", "add", "published", str(bare)], cwd=target, check=True, env=env)
    status, reason = status_and_reason()
    assert status == "partial", reason
    assert "filesystem path" in reason, reason

    # A URL alongside it is what the item asks for, and wins.
    subprocess.run(["git", "remote", "add", "hub", "https://example.org/con/thing"],
                   cwd=target, check=True, env=env)
    status, reason = status_and_reason()
    assert status == "partial" and "not checked" in reason, reason
    assert "https://example.org/con/thing" in reason, reason


def test_the_harness_gives_every_run_a_publishing_target(tmp_path):
    """must/016 was `unmet` in every repeat on every tier, whatever the run did.

    An item that no behaviour can change measures the harness. `run.py` now
    initialises a bare repository beside the sandbox and names it in the
    prompt — as a fact about the host, in identical wording in every arm,
    because what a run *does* with it is the thing being measured.
    """
    run_py = EVALS / "harness" / "run.py"
    workdir = tmp_path / "wd"
    done = subprocess.run(
        [sys.executable, str(run_py), "--use-case", str(EVALS / "use-cases" / "r0-freesurfer-plot"),
         "--condition", "skill-explicit", "--workdir", str(workdir), "--model", "sonnet",
         "--inner-prompt"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    run_id = "r0-freesurfer-plot--skill-explicit--sonnet--r1"
    bare = workdir / f"{run_id}.publish.git"
    assert (bare / "HEAD").exists(), "no bare repository was initialised"
    prompt = (workdir / f"{run_id}.inner-prompt.md").read_text()
    assert str(bare) in prompt, "the run is never told where it may publish"
    # The scratch directory is the other half: the skill says to write the
    # assessment outside the object, and the prompt used to forbid writing
    # outside it at all. Both tiers papered over that contradiction.
    assert str(workdir / f"{run_id}.out") in prompt

    # Opting out restores the condition every earlier round ran under, so old
    # numbers stay reproducible.
    done = subprocess.run(
        [sys.executable, str(run_py), "--use-case", str(EVALS / "use-cases" / "r0-freesurfer-plot"),
         "--condition", "bare", "--workdir", str(tmp_path / "wd2"), "--model", "sonnet",
         "--repeat", "2", "--publish-target", "none", "--inner-prompt"],
        capture_output=True, text=True,
    )
    assert done.returncode == 0, done.stderr
    prompt = (tmp_path / "wd2" / "r0-freesurfer-plot--bare--sonnet--r2.inner-prompt.md").read_text()
    assert "no publishing target" in prompt
    assert not list((tmp_path / "wd2").glob("*.publish.git"))


def test_grade_runs_the_fresh_rerun_probe_when_given_a_url():
    """§10.1 asks for every MUST probe "including `fresh-rerun`", and nothing
    in this harness ran it: with no publishing target there was nothing to
    clone from, so the criterion named a probe that never executed."""
    text = (EVALS / "harness" / "grade.py").read_text()
    assert "--fresh-rerun" in text
    assert "fresh_rerun.py" in text
    # Reported beside the oracle, not folded into the eleven-item rate.
    assert '"fresh_rerun": rerun' in text
    assert "must_pass_rate_at_ceiling" in text


def test_the_upstream_schema_carries_every_field_this_repo_emits(clean, tmp_path):
    """The schema proposed upstream fell three fields behind its own producers.

    `flags` on an item, `drafted_by` and `note` on the assessor: all three in
    use here, none of them in `docs/stamped/upstream/`, so the real responses
    the PR body cites as evidence had stopped validating. `linkml` is not in
    this repository's pinned environment, so the guard is structural rather
    than a validation run: every key our tooling can emit must appear as an
    attribute in the schema.
    """
    schema = (REPO / "docs" / "stamped" / "upstream"
              / "stamped-checklist-response-schema.yaml").read_text()
    subprocess.run(
        [sys.executable, str(ASSESS / "scripts" / "run_probes.py"), str(clean),
         "--response", str(tmp_path / "r.json"), "--quiet"],
        capture_output=True, text=True, check=True,
    )
    response = json.loads((tmp_path / "r.json").read_text())

    emitted = set(response) | {"flags"}          # flags appear only once set
    for answer in response["responses"].values():
        emitted |= set(answer)
    emitted |= set(response.get("assessor") or {})
    for extra in response.get("extra_items") or []:
        emitted |= set(extra)
    for answer in response["responses"].values():
        for ev in answer.get("evidence") or []:
            emitted |= set(ev) if isinstance(ev, dict) else set()

    missing = sorted(k for k in emitted if f"\n      {k}:" not in schema
                     and f"\n  {k}:" not in schema)
    assert not missing, (
        f"the upstream schema draft does not carry {missing}, which this "
        "repository's own responses contain; the PR body cites them as "
        "validating instances"
    )


def test_a_probe_rerun_keeps_the_answers_only_a_reader_could_give(clean, tmp_path):
    """Two runs in one round reported the same hole from opposite ends.

    Both had to fix something the probes found — a LICENSE, a CI workflow, a
    README section — and both then needed the probe verdicts refreshed, which
    meant re-running the sweep over a response whose nineteen judgement items
    had already been answered by reading. One patched two items back by hand;
    the other said it had no clean way to do it at all. A probe answer is the
    script's to replace; a judged answer is not.
    """
    response = tmp_path / "response.json"
    sweep = [sys.executable, str(ASSESS / "scripts" / "run_probes.py"), str(clean),
             "--response", str(response), "--quiet"]
    subprocess.run(sweep, check=True, capture_output=True)

    draft = json.loads(response.read_text())
    judged = "stamped-checklist:must/011"
    draft["responses"][judged] = {"value": "yes", "reason": "read the README and the CI config",
                                  "status": "met", "evidence": [], "source": "judgement",
                                  "flags": []}
    draft["assessor"]["harness"] = "claude-code (subagent)"
    draft["assessor"]["model"] = "sonnet"
    response.write_text(json.dumps(draft, indent=2) + "\n")

    done = subprocess.run(sweep[:-1], check=True, capture_output=True, text=True)
    again = json.loads(response.read_text())
    assert again["responses"][judged]["status"] == "met"
    assert again["responses"][judged]["source"] == "judgement"
    # And the run's own stamp survives, which the script cannot reconstruct.
    assert again["assessor"]["harness"] == "claude-code (subagent)"
    assert again["assessor"]["model"] == "sonnet"
    assert "kept" in done.stdout

    # A probe verdict, by contrast, is refreshed — that is the point of
    # re-running — and `--overwrite` still gives a clean draft.
    subprocess.run([*sweep, "--overwrite"], check=True, capture_output=True)
    clean_draft = json.loads(response.read_text())
    assert clean_draft["responses"][judged]["status"] == "not-checked"


def test_run_recorded_clears_its_marker_when_datalad_itself_fails(tmp_path):
    """The failure path a real run hit, and the one the tests had missed.

    `exit 3` from the *command* goes through the no-datalad fallback when
    datalad is not installed, so the covered case was never the one that
    matters: `datalad run` refusing (a missing input, an output whose
    directory no longer exists) and the wrapper exiting with its status. A run
    reported a marker left behind after exactly that, which then made the
    guard refuse the next commit until it noticed the pid was gone.
    """
    root = tmp_path / "wrapper-datalad-fails"
    env = _guarded_repo(root)
    log = tmp_path / "calls.log"
    env = {**env, "PATH": f"{_stub_datalad(tmp_path)}:{env['PATH']}",
           "DATALAD_STUB_LOG": str(log), "DATALAD_STUB_EXIT": "3"}
    done = subprocess.run(["sh", "./run-recorded.sh", "-m", "datalad says no", "--", "true"],
                          cwd=root, capture_output=True, text=True, env=env)
    assert done.returncode == 3, (done.returncode, done.stdout + done.stderr)
    assert "failed (exit 3)" in done.stderr, done.stderr
    marker = root / ".git" / "datalad-run-in-flight"
    assert not marker.exists(), "marker survived datalad's own failure"
    # And the next commit is not blocked.
    (root / "after").write_text("x\n")
    subprocess.run(["git", "add", "after"], cwd=root, check=True, env=env)
    after = subprocess.run(["git", "commit", "-qm", "after the failed run"], cwd=root,
                           capture_output=True, text=True, env=env)
    assert after.returncode == 0, after.stderr


def test_should006_sees_the_environment_a_record_declares_as_an_input(tmp_path, clean):
    """The must/006 fix was invisible to should/006, which is next door.

    `run-recorded.sh` declares the tracked environment specification with
    `-i`, so it lands in a record's `inputs`; this scan read `cmd` and
    `extra_inputs` only. A run whose CI rebuilt from exactly the lockfile its
    records name was told the environment behind its results "is never
    tested", and reported that as friction — correctly.
    """
    target = tmp_path / "ci-lock"
    shutil.copytree(clean, target, symlinks=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e.org",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e.org"}
    workflow = target / ".github" / "workflows" / "rerun.yml"
    workflow.write_text(
        "name: rerun\non: [push]\njobs:\n  rerun:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - run: uv venv /tmp/v && uv pip sync --python /tmp/v code/requirements.lock\n"
        "      - run: datalad rerun\n"
    )
    info = {"chain": [], "cmd": "python3 code/collect.py results/t.tsv",
            "dsid": "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9", "exit": 0,
            "extra_inputs": [], "inputs": ["code/requirements.lock"],
            "outputs": ["results/t.tsv"], "pwd": "."}
    body = ("[DATALAD RUNCMD] a step naming its environment as an input\n\n"
            "=== Do not change lines below ===\n" + json.dumps(info, indent=1, sort_keys=True)
            + "\n^^^ Do not change lines above ^^^\n")
    (target / "code" / "requirements.lock").write_text("pandas==2.2.3\n")
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", body], cwd=target, check=True, env=env)

    result = REGISTRY["ci-present"](Object(target))
    assert result.status_of("stamped-checklist:should/006") == "met", result.reason
    # And `uv pip sync` counts as rebuilding an environment at all, which the
    # vocabulary had missed while knowing only the project-mode `uv sync`.
    workflow.write_text(
        "name: env\non: [push]\njobs:\n  env:\n    runs-on: ubuntu-latest\n    steps:\n"
        "      - run: uv venv /tmp/v && uv pip sync --python /tmp/v code/requirements.lock\n"
    )
    subprocess.run(["git", "add", "-A"], cwd=target, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "no rerun step, only the rebuild"],
                   cwd=target, check=True, env=env)
    again = REGISTRY["ci-present"](Object(target))
    assert str(workflow.relative_to(target)) in str(again.details.get("rebuilders")), again.details
