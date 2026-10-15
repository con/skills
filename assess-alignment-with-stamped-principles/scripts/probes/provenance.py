# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Probes over provenance: does every derived file come from a re-executable
record, and do those records name the environment they ran in."""

from __future__ import annotations

import fnmatch
import re

from .common import Evidence, Object, Probe, clip

DERIVED_DIRS = (
    "derivatives/", "derivative/", "outputs/", "output/", "results/", "result/",
    "figures/", "figure/", "figs/", "plots/", "reports/",
)
DERIVED_SUFFIXES = (
    ".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff",
    ".tsv", ".csv", ".nii", ".nii.gz", ".mgz", ".npy", ".npz", ".h5", ".hdf5",
)
# Not products of this object: inputs, documentation illustrations, packaging.
NOT_DERIVED = (
    "sourcedata/", "rawbids/", "rawdata/", "inputs/", "input/", "sub-", "docs/",
    "doc/", ".github/", "templates/", "template/", "assets/", "stories/", "tests/",
    "test/", "code/containers/", "fixtures/", "paper/", "manuscript/", "expected_output/",
)
# A tracked PDF at the root of a project is its paper or poster, not an output
# of its pipeline: a blind run had to explain to the probe that
# `AVERYSimpleRe-ExecutableNeuroimagingPublication_v3.pdf` is the publication.
NOT_DERIVED_NAMES = re.compile(r"(?i)(?:paper|manuscript|poster|preprint|publication|slides|"
                               r"README|LICENSE|CITATION)[\w.-]*\.(?:pdf|docx?|pptx?)$")
CONTAINER_IMAGE = re.compile(r"(?:\.sif|\.simg|\.img\b|docker://|shub://|oras://|sha256:[0-9a-f]{12,})")
# A per-run environment *capture* (duct, reprozip, a recorded `pip freeze`) is
# weaker evidence than a specification that reconstitutes the environment, but
# it is not nothing: it links the action to the environment it ran in.
ENV_CAPTURE = re.compile(r"(?:\bduct\b|REPRONIM_USE_DUCT|reprozip|duct-info\.json|pip[ -]freeze|conda\s+env\s+export)")
LOCKFILES = ("pixi.lock", "uv.lock", "poetry.lock", "conda-lock.yml", "renv.lock", "requirements.lock")
UNPINNED_TAG = re.compile(r"(?:docker://|shub://|FROM\s+)[\w./-]+:latest\b|[\w./-]+:latest\b")


def _derived_candidates(obj: Object) -> list[str]:
    out = []
    for relpath in obj.tracked():
        if any(relpath.startswith(p) or f"/{p}" in relpath for p in NOT_DERIVED):
            continue
        if NOT_DERIVED_NAMES.search(relpath.rsplit("/", 1)[-1]):
            continue
        lower = relpath.lower()
        if any(relpath.startswith(d) or f"/{d}" in relpath for d in DERIVED_DIRS) or lower.endswith(DERIVED_SUFFIXES):
            out.append(relpath)
    return out


def _last_commit_per_path(obj: Object) -> dict[str, str]:
    """Most recent commit that touched each tracked path."""
    out = obj.git("log", "--format=%x1e%H", "--name-only", "--no-renames")
    last: dict[str, str] = {}
    for block in out.split("\x1e"):
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        commit, paths = lines[0].strip(), lines[1:]
        for path in paths:
            last.setdefault(path, commit)
    return last


def _workflow_targets(obj: Object) -> tuple[list[str], list[str]]:
    """(patterns a tracked workflow declares as outputs, the files declaring them)."""
    patterns: list[str] = []
    sources: list[str] = []
    for relpath in obj.tracked():
        name = relpath.rsplit("/", 1)[-1]
        if name in {"Makefile", "makefile", "GNUmakefile"}:
            text = obj.read(relpath)
            found = re.findall(r"^([^\s:#=][^:=\n]*?):(?!=)", text, re.M)
            patterns += [t.strip() for target in found for t in target.split() if not t.startswith(".")]
            sources.append(relpath)
        elif name in {"Snakefile"} or name.endswith(".smk"):
            text = obj.read(relpath)
            for block in re.findall(r"output:\s*((?:\s*[^\n]*\n)+?)(?=\s*(?:input|run|shell|params|log|rule|$))", text):
                patterns += re.findall(r'["\']([^"\']+)["\']', block)
            sources.append(relpath)
        elif name == "dvc.yaml":
            text = obj.read(relpath)
            patterns += re.findall(r"^\s*-\s*([\w./*{}-]+)\s*$", text, re.M)
            sources.append(relpath)
    # Snakemake and Make wildcards are close enough to fnmatch for a probe.
    patterns = [re.sub(r"\{[^}]*\}", "*", p) for p in patterns]
    return patterns, sources


# Provenance a tool other than datalad recorded: nipype's PROV export, a
# CWL/WDL provenance bundle, an RO-Crate. `verdicts.md` rule 7 — equivalent
# evidence counts — and a real object (ReproNim/simple_workflow) ships nipype
# `.provn`/`.trig` files that this probe did not know how to see.
PROV_FILES = (".provn", ".trig", ".ttl", "prov.json", "ro-crate-metadata.json", ".nidm.ttl")


def _prov_artifacts(obj: Object) -> list[str]:
    return [p for p in obj.tracked()
            if p.endswith(PROV_FILES) or p.rsplit("/", 1)[-1] in {"prov.json", "ro-crate-metadata.json"}]


def derived_have_records(obj: Object) -> Probe:
    """must/006 and A.2 — every derived file traces back to a re-executable record."""
    items = ["stamped-checklist:must/006"]
    candidates = _derived_candidates(obj)
    records = obj.run_records()
    wf_patterns, wf_sources = _workflow_targets(obj)
    prov = _prov_artifacts(obj)

    if not candidates:
        return Probe(
            "derived-have-records", "not-applicable", items,
            "N/A: no tracked file looks like a product of this object (no derivatives, tables or figures).",
            [], {"records": len(records), "workflow_sources": wf_sources},
        )
    if not records and not wf_patterns and prov:
        # Provenance in another tool's format: enough to link results to what
        # produced them, not enough to re-execute from the history, so
        # `partial` with the mechanism named rather than `unmet` for "no
        # [DATALAD RUNCMD] here".
        return Probe(
            "derived-have-records", "partial", items,
            clip(f"{len(candidates)} derived file(s) and no run record or tracked workflow, but "
                 f"{len(prov)} provenance artefact(s) record what produced them "
                 f"(e.g. {prov[0]}): a reader can see the tools and versions, not re-execute them."),
            [Evidence(p, "provenance artefact from another tool") for p in prov[:5]]
            + [Evidence(p, "derived file") for p in candidates[:5]],
            {"candidates": candidates, "provenance_artifacts": prov},
        )
    if not records and not wf_patterns:
        return Probe(
            "derived-have-records", "unmet", items,
            clip(f"{len(candidates)} derived file(s) tracked (e.g. {candidates[0]}) and no run record or "
                 "tracked workflow that would re-create any of them."),
            [Evidence(p, "derived file with no re-executable record") for p in candidates[:10]],
            {"candidates": candidates},
        )

    run_commits = {r["commit"] for r in records}
    record_outputs: list[str] = []
    for rec in records:
        info = rec.get("run_info") or {}
        for out in info.get("outputs") or []:
            record_outputs.append(out)
    last = _last_commit_per_path(obj)

    covered: dict[str, str] = {}
    uncovered: list[str] = []
    for path in candidates:
        if last.get(path) in run_commits:
            covered[path] = f"run record {last[path][:7]}"
        elif any(fnmatch.fnmatch(path, pat) or path == pat for pat in record_outputs):
            covered[path] = "named as an output of a run record"
        elif any(fnmatch.fnmatch(path, pat) or path == pat for pat in wf_patterns):
            covered[path] = f"declared as an output by {wf_sources[0]}"
        else:
            uncovered.append(path)

    details = {
        "candidates": len(candidates), "covered": len(covered), "uncovered": uncovered,
        "run_records": len(records), "workflow_sources": wf_sources,
    }
    if not uncovered:
        example = next(iter(covered.items()))
        return Probe(
            "derived-have-records", "met", items,
            clip(f"All {len(candidates)} derived file(s) trace to a re-executable record "
                 f"({len(records)} run record(s), workflows: {', '.join(wf_sources) or 'none'})."),
            [Evidence(p, why) for p, why in list(covered.items())[:10]] or [Evidence(example[0], example[1])],
            details,
        )
    status = "partial" if covered else "unmet"
    return Probe(
        "derived-have-records", status, items,
        clip(f"{len(uncovered)} of {len(candidates)} derived file(s) have no re-executable record, "
             f"e.g. {uncovered[0]}; last touched by an ordinary commit."),
        [Evidence(p, "no run record or workflow rule produces this file") for p in uncovered[:10]],
        details,
    )


def run_env_linked(obj: Object) -> Probe:
    """must/006 (records name their environment) and must/015 (that environment is pinned)."""
    i006, i015 = "stamped-checklist:must/006", "stamped-checklist:must/015"
    items = [i006, i015]
    records = obj.run_records()
    unpinned: list[tuple[str, str]] = []
    for relpath in list(obj.tracked()) + ([".datalad/config"] if obj.exists(".datalad/config") else []):
        name = relpath.rsplit("/", 1)[-1]
        if name not in {"Dockerfile", "Singularity", "config", "docker-compose.yml"} and not name.endswith(
            (".def", ".yml", ".yaml", ".toml", ".cfg", ".json", ".sh", ".txt")
        ):
            continue
        for lineno, line in enumerate(obj.read(relpath).splitlines(), 1):
            if "latest" in line and UNPINNED_TAG.search(line):
                unpinned.append((f"{relpath}#L{lineno}", clip(line.strip(), 120)))

    with_env: list[dict] = []
    without_env: list[dict] = []
    for rec in records:
        info = rec.get("run_info") or {}
        blob = " ".join(
            [str(info.get("cmd", ""))]
            + [str(x) for x in (info.get("extra_inputs") or [])]
            + [str(x) for x in (info.get("inputs") or [])]
        )
        has_container = bool(CONTAINER_IMAGE.search(blob)) or "containers-run" in rec["body"]
        has_lock = any(lock in blob for lock in LOCKFILES)
        has_capture = bool(ENV_CAPTURE.search(blob)) or any(
            "duct" in str(out) for out in (info.get("outputs") or [])
        )
        mechanism = ("container" if has_container else "lockfile" if has_lock
                     else "capture" if has_capture else None)
        (with_env if mechanism else without_env).append(
            {"commit": rec["commit"], "cmd": clip(str(info.get("cmd", ""))[:160], 160),
             "mechanism": mechanism}
        )

    # What *kind* of evidence each record carried, because the three are not
    # equal: a container or a lockfile can reconstitute the environment, a
    # run-time capture only describes it. A blind run on another model tier
    # overrode must/006 precisely because the reason did not say which of the
    # three it had counted, so the basis is now in the reason and in `details`.
    by_mechanism = {m: sum(1 for r in with_env if r["mechanism"] == m)
                    for m in ("container", "lockfile", "capture")}
    details = {"records": len(records), "with_env": len(with_env), "without_env": without_env[:20],
               "by_mechanism": by_mechanism, "unpinned": unpinned}
    reconstitutable = by_mechanism["container"] + by_mechanism["lockfile"]

    # must/006 — do the run records name the environment they ran in?
    if not records:
        s006 = "not-checked"
        r006 = "No run records, so no record names the environment it ran in."
    elif not without_env and all(r["mechanism"] == "capture" for r in with_env):
        s006 = "partial"
        r006 = clip(f"All {len(records)} run record(s) capture the environment they ran in (duct or similar), "
                    "but none names a container image or lockfile that would reconstitute it.")
    elif not without_env:
        s006 = "met"
        r006 = clip(f"All {len(records)} run record(s) name a container image, a lockfile or an "
                    "environment capture.")
    elif with_env and not reconstitutable:
        s006 = "partial"
        r006 = clip(f"{len(without_env)} of {len(records)} run record(s) name no environment at all, and "
                    f"the other {len(with_env)} carry only a run-time capture (duct or similar), which "
                    f"describes the environment without reconstituting it.")
    elif with_env:
        s006 = "partial"
        r006 = clip(f"{len(without_env)} of {len(records)} run record(s) name no container or lockfile "
                    f"({by_mechanism['container']} name a container, {by_mechanism['lockfile']} a "
                    f"lockfile, {by_mechanism['capture']} only a capture), "
                    f"e.g. {without_env[0]['commit'][:7]}: {without_env[0]['cmd']}")
    else:
        s006 = "unmet"
        r006 = clip(f"None of the {len(records)} run record(s) name a container or a lockfile.")

    # must/015 — is that environment pinned, or does it float?
    if unpinned:
        s015 = "unmet"
        r015 = clip(f"{len(unpinned)} environment reference(s) use the floating ':latest' tag, "
                    f"e.g. {unpinned[0][0]} — a rerun cannot land in the same environment.")
    elif any(r["mechanism"] in {"container", "lockfile"} for r in with_env):
        s015 = "met"
        r015 = clip(f"{len(with_env)} run record(s) reference a pinned image or lockfile, and no ':latest' "
                    "reference is tracked.")
    elif with_env:
        s015 = "unmet"
        r015 = clip("The run records capture the environment but nothing pins one: there is no image digest "
                    "or frozen manifest another person could replicate from.")
    else:
        s015 = "not-checked"
        r015 = "Nothing names an environment to check for a pin."

    evidence = [Evidence(u[0], u[1]) for u in unpinned[:5]]
    evidence += [Evidence(f"commit:{r['commit'][:7]}", f"{r['mechanism']}: {r['cmd']}") for r in with_env[:5]]
    evidence += [Evidence(f"commit:{r['commit'][:7]}", f"no environment named: {r['cmd']}") for r in without_env[:5]]

    worst = min((s006, s015), key=lambda s: {"unmet": 0, "partial": 1, "not-checked": 2, "met": 3}[s])
    return Probe(
        "run-env-linked", worst, items, clip(f"must/006 {s006}: {r006} must/015 {s015}: {r015}"),
        evidence, details,
        item_status={i006: s006, i015: s015},
        item_reason={i006: r006, i015: r015},
    )
