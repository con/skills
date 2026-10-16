"""Regression checks for the frozen external assessor's evidence boundary."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"
sys.path.insert(0, str(SKILLS / "stamped-conventions" / "scripts"))
from encode_response import Checklist, template, validate

spec = importlib.util.spec_from_file_location(
    "freeze_fresh_rerun",
    SKILLS / "assess-alignment-with-stamped-principles" / "scripts" / "fresh_rerun.py",
)
rerun = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rerun)


def completed():
    response = template(Checklist())
    response["object"] = {"commit": "a" * 40, "captured_at": "2026-10-15T17:00:00Z", "kind": "study"}
    response["assessor"] = {
        "skill": "assess-alignment-with-stamped-principles", "version": "0.1.0",
        "harness": "pytest fixture", "model": "unavailable (deterministic fixture)",
        "date": "2026-10-15", "dependencies": ["stamped-conventions@0.1.0"],
    }
    response["scope"] = "Validation fixture; no scientific object assessed."
    for answer in response["responses"].values():
        answer.update(reason="Not executed: metadata validation fixture.")
    return response


def test_completed_response_accepts_truthful_not_checked():
    assert validate(completed(), Checklist()) == []


@pytest.mark.parametrize(("section", "field", "value"), [
    ("assessor", "model", None), ("assessor", "harness", ""),
    ("assessor", "dependencies", []), ("assessor", "date", "2026-99-99"),
    ("object", "kind", "something-else"), ("object", "commit", "main"),
    ("object", "captured_at", "yesterday"),
    ("checklist_source", "commit", "b" * 40),
])
def test_response_rejects_missing_or_false_stamp(section, field, value):
    response = completed()
    response[section][field] = value
    assert any(field in p for p in validate(response, Checklist()))


@pytest.mark.parametrize("evidence", ["README.md", [{}], [{"uri": ""}], [{"uri": "README.md", "sha256": "bad"}]])
def test_response_rejects_truthy_but_malformed_evidence(evidence):
    response = completed()
    response["responses"][next(iter(response["responses"]))].update(
        status="met", value="yes", reason="Observed", evidence=evidence,
    )
    assert validate(response, Checklist())


@pytest.mark.parametrize(("before", "after", "expected"), [
    ("group,value\ncontrol,1\n", "group,value\npatient,1\n", False),
    ("group,value\ncontrol,1\n", "group,value\ncontrol,nan\n", False),
    ("group,value\ncontrol,nan\n", "group,value\ncontrol,1\n", False),
    ("group,value\ncontrol,inf\n", "group,value\ncontrol,-inf\n", False),
    ("group,value\ncontrol,inf\n", "group,value\ncontrol,1\n", False),
    ("group,value\ncontrol,NaN\n", "group,value\ncontrol,nan\n", True),
    ("group,value\ncontrol,1\n", "group,value\ncontrol,1.0000001\n", True),
    ('group,value\n"A,B",1\n', 'group,value\n"A,B",1.0000001\n', True),
    ("group,value\ncontrol,0.00000001\n", "group,value\ncontrol,0.00000002\n", False),
])
def test_table_comparison_preserves_labels_missingness_and_relative_tolerance(tmp_path, before, after, expected):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text(before)
    b.write_text(after)
    assert rerun._numeric_close(a, b, 1e-6) is expected


def test_missing_published_comparator_is_never_met(tmp_path, monkeypatch):
    def fake_run(command, **kwargs):
        if command[:2] == ["git", "clone"]:
            clone = pathlib.Path(command[-1])
            clone.mkdir()
            (clone / "results.tsv").symlink_to("missing-annex-payload")
        return 0, ""

    monkeypatch.setattr(rerun, "_run", fake_run)
    # This fixture mocks cloning; it has no real source Git configuration.
    monkeypatch.setattr(rerun, "_local_annex_routes", lambda source, clone: {"routes": []})
    monkeypatch.setattr(rerun.shutil, "which", lambda executable: None)
    report = tmp_path / "report.json"
    rerun.main(["--path", "fixture", "--entry", "true", "--workdir", str(tmp_path / "run"), "-o", str(report)])
    result = json.loads(report.read_text())
    assert result["status"] == "not-checked"
    assert result["unavailable_comparators"] == ["results.tsv"]
    assert not any(s["step"].startswith("entry:") for s in result["steps"])


def test_preserved_outputs_are_not_proof_of_execution(tmp_path, monkeypatch):
    def fake_run(command, **kwargs):
        if command[:2] == ["git", "clone"]:
            clone = pathlib.Path(command[-1])
            clone.mkdir()
            (clone / "results.tsv").write_text("x\n1\n")
        return 0, ""

    monkeypatch.setattr(rerun, "_run", fake_run)
    monkeypatch.setattr(rerun, "_local_annex_routes", lambda source, clone: {"routes": []})
    monkeypatch.setattr(rerun.shutil, "which", lambda executable: None)
    report = tmp_path / "report.json"
    rerun.main(["--path", "fixture", "--entry", "true", "--keep-outputs", "--workdir", str(tmp_path / "run"), "-o", str(report)])
    assert json.loads(report.read_text())["status"] == "not-checked"


def test_prefixed_run_record_is_not_native_replayable(monkeypatch, tmp_path):
    sys.path.insert(0, str(SKILLS / "assess-alignment-with-stamped-principles" / "scripts"))
    from probes.common import Object

    body = '[DATALAD RUNCMD] fixture\n\n=== Do not change lines below ===\n{"cmd":"true","outputs":["result"]}\n^^^ Do not change lines above ^^^'
    for prefix, replayable in (("", True), ("feat: record run\n\n", False)):
        obj = Object(tmp_path)
        monkeypatch.setattr(obj, "git", lambda *args: "\x1e" + "a" * 40 + "\n" + prefix + body)
        record = obj.run_records()[0]
        assert bool(record["run_info"]) is replayable
