# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Probes over module boundaries: are linked components retrievable by others,
and are inputs left alone."""

from __future__ import annotations

import re
import subprocess

from .common import Evidence, Object, Probe, clip

# A URL that only resolves relative to wherever the superdataset happens to sit,
# or only on one machine.  `url = ../..` is the single most common real-world
# failure (compression-comparisons-t261-study).
RELATIVE_URL = re.compile(r"^\.{1,2}/")
LOCAL_URL = re.compile(r"^(?:file://|/|~|[A-Za-z]:\\)")
REMOTE_URL = re.compile(r"^(?:https?://|git://|ssh://|git@|[\w.-]+@[\w.-]+:)")
# DataLad's registry shortcuts resolve through a public catalogue, so they are
# retrievable even though they are not URLs.
DATALAD_RIA = re.compile(r"^(?:///|ria\+)")


def subdatasets_resolvable(obj: Object, check_remote: bool = False) -> Probe:
    """must/002 and may/001 — linked components resolve from a fresh clone.

    It used to answer must/016 as well, which asks whether *environment
    specifications* are shared where others can get them: a different property,
    now answered by `env-spec-tracked` (found by a blind run of this skill).
    """
    items = ["stamped-checklist:must/002", "stamped-checklist:may/001"]
    mods = obj.submodules()
    if not mods:
        return Probe(
            "subdatasets-resolvable", "not-checked", items,
            "No submodules or subdatasets: whether external inputs are linked at all needs a reading of the object.",
            [], {"submodules": []},
        )

    bad: list[dict] = []
    good: list[dict] = []
    for mod in mods:
        url = (mod.get("url") or "").strip()
        path = mod.get("path", mod["name"])
        if not url:
            bad.append({"path": path, "url": url, "why": "no url recorded in .gitmodules"})
        elif RELATIVE_URL.match(url):
            bad.append({"path": path, "url": url, "why": "relative url: resolves only next to this superdataset"})
        elif LOCAL_URL.match(url):
            bad.append({"path": path, "url": url, "why": "local path: resolves only on one machine"})
        elif REMOTE_URL.match(url) or DATALAD_RIA.match(url):
            good.append({"path": path, "url": url})
        else:
            bad.append({"path": path, "url": url, "why": "url is neither a remote URL nor a datalad registry shortcut"})

    unreachable: list[dict] = []
    if check_remote:
        recorded = {m.get("path", m["name"]): m.get("recorded_commit", "").lstrip("+-U")
                    for m in mods}
        for mod in good:
            url = mod["url"]
            if not url.startswith(("http://", "https://")):
                continue  # ssh and registry shortcuts need credentials or datalad
            proc = subprocess.run(
                ["git", "ls-remote", "--exit-code", url, "HEAD"],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode != 0:
                unreachable.append({**mod, "why": clip(proc.stderr.strip(), 120)})
                continue
            # A live url pinned to a commit nobody can fetch fails a fresh clone
            # just as surely as a bad url. A blind run found exactly this in the
            # eval fixture, which the shape check had called fine.
            commit = recorded.get(mod["path"])
            if not commit:
                continue
            fetch = subprocess.run(
                ["git", "fetch", "--depth=1", "--no-tags", url, commit],
                capture_output=True, text=True, timeout=300,
                cwd=str(obj.root),
            )
            if fetch.returncode != 0:
                unreachable.append({**mod, "commit": commit,
                                    "why": f"url answers, but commit {commit[:9]} is not fetchable from it: "
                                           + clip(fetch.stderr.strip(), 90)})

    details = {"resolvable": good, "unresolvable": bad, "unreachable": unreachable}
    # may/001 asks whether external components are linked as modules at all; a
    # url that does not resolve elsewhere is must/002 and must/016, not may/001.
    may = {
        "stamped-checklist:may/001": "met",
    }
    may_reason = {
        "stamped-checklist:may/001": clip(
            f"{len(mods)} external component(s) are linked as modules: "
            f"{', '.join(m.get('path', m['name']) for m in mods[:3])}"
        )
    }
    if bad:
        first = bad[0]
        return Probe(
            "subdatasets-resolvable", "unmet", items,
            clip(f"{len(bad)} of {len(mods)} linked module(s) do not resolve elsewhere: "
                 f"{first['path']} url={first['url'] or '(none)'} — {first['why']}"),
            [Evidence(".gitmodules", f"{b['path']}: url={b['url'] or '(none)'} — {b['why']}") for b in bad[:10]],
            details, item_status=may, item_reason=may_reason,
        )
    if unreachable:
        return Probe(
            "subdatasets-resolvable", "partial", items,
            clip(f"{len(unreachable)} linked module(s) are well-formed but do not resolve in fact: "
                 f"{unreachable[0]['path']} — {unreachable[0]['why']}"),
            [Evidence(".gitmodules", f"{u['path']}: {u['url']} — {u['why']}") for u in unreachable[:5]],
            details, item_status=may, item_reason=may_reason,
        )
    return Probe(
        "subdatasets-resolvable", "met", items,
        clip(f"All {len(mods)} linked module(s) carry urls that resolve from elsewhere: "
             f"{', '.join(m['path'] for m in good[:3])}"),
        [Evidence(".gitmodules", f"{m['path']}: {m['url']}") for m in good[:10]],
        details, item_status=may, item_reason=may_reason,
    )


def inputs_untouched(obj: Object) -> Probe:
    """Extra (no checklist item) — inputs stay at the state the object records.

    should/003 asks whether components are *separated into distinct modules*,
    which `modules-separated` reads from the committed layout. Whether an input
    was modified is a different question, no 0.3.1 item asks it, and answering
    should/003 with it hid real layout evidence behind `not-checked` (found by a
    blind run of this skill).
    """
    items: list[str] = []
    mods = obj.submodules()
    if not mods:
        return Probe(
            "inputs-untouched", "not-applicable", items,
            "N/A: no linked modules, so there is no recorded input state to compare against.",
            [],
        )
    uninit = [m for m in mods if not m.get("initialized", False)]
    modified = [m for m in mods if m.get("differs")]
    conflicted = [m for m in mods if m.get("conflict")]
    if modified or conflicted:
        worst = (modified + conflicted)[0]
        return Probe(
            "inputs-untouched", "unmet", items,
            clip(f"{len(modified) + len(conflicted)} linked module(s) differ from the recorded commit, "
                 f"e.g. {worst.get('path')}: results may have been written into an input."),
            [Evidence(m.get("path", m["name"]), "differs from the commit the superdataset records")
             for m in (modified + conflicted)[:10]],
            {"modified": [m.get("path") for m in modified + conflicted]},
        )
    if uninit:
        return Probe(
            "inputs-untouched", "not-checked", items,
            clip(f"{len(uninit)} of {len(mods)} module(s) are not installed here, so their state cannot be read: "
                 f"{', '.join(m.get('path', m['name']) for m in uninit[:3])}"),
            [Evidence("git submodule status", f"{m.get('path')} not initialized") for m in uninit[:10]],
            {"uninitialized": [m.get("path") for m in uninit]},
        )
    return Probe(
        "inputs-untouched", "met", items,
        clip(f"All {len(mods)} linked module(s) are clean and at the commit the superdataset records."),
        [Evidence("git submodule status", "no '+' or 'U' flags")],
    )


# Where each kind of component conventionally lives.  Layout, not tooling: a
# plain repository with `data/`, `scripts/` and `results/` satisfies M.1 as well
# as a DataLad superdataset with subdatasets does.
INPUT_DIRS = ("sourcedata", "rawbids", "rawdata", "inputs", "input", "raw", "data")
CODE_DIRS = ("code", "scripts", "src", "workflow", "analysis")
DERIVED_DIRS = ("derivatives", "derivative", "results", "outputs", "output", "figures", "figs", "plots")
CODE_NAMES = ("Makefile", "makefile", "GNUmakefile", "Snakefile", "dvc.yaml", "main.nf")
ENV_NAMES = (
    "requirements.txt", "requirements.lock", "pyproject.toml", "environment.yml", "environment.yaml",
    "pixi.toml", "pixi.lock", "uv.lock", "poetry.lock", "renv.lock", "Dockerfile", "Singularity",
    "conda-lock.yml", "containers.json",
)


def modules_separated(obj: Object) -> Probe:
    """should/003 (M.1) — raw data, derived data, code and environment are distinct modules."""
    items = ["stamped-checklist:should/003"]
    tracked = obj.tracked()
    module_paths = [m.get("path", m["name"]) for m in obj.submodules()]

    def under(prefixes: tuple[str, ...]) -> list[str]:
        return sorted({p.split("/")[0] for p in tracked if p.split("/")[0] in prefixes})

    found: dict[str, list[str]] = {
        "inputs": sorted(set(under(INPUT_DIRS)) | {m for m in module_paths if m.split("/")[0] in INPUT_DIRS}),
        "code": sorted(set(under(CODE_DIRS)) | {p for p in tracked if p in CODE_NAMES}),
        "derived": under(DERIVED_DIRS),
        "environment": sorted({p for p in tracked if p.rsplit("/", 1)[-1] in ENV_NAMES}),
    }
    # Any input module that also holds this object's own derived output is the
    # failure this item is really about.
    mixed = [
        p for p in tracked
        if p.split("/")[0] in INPUT_DIRS and any(f"/{d}/" in f"/{p}" for d in DERIVED_DIRS)
    ]
    present = [kind for kind, paths in found.items() if paths]
    evidence = [Evidence(path, f"{kind} module") for kind, paths in found.items() for path in paths[:2]]

    if mixed:
        return Probe(
            "modules-separated", "unmet", items,
            clip(f"{len(mixed)} derived file(s) live inside an input tree, e.g. {mixed[0]}: "
                 "raw and processed data are not separate modules."),
            [Evidence(p, "derived output inside an input module") for p in mixed[:10]],
            {"found": found, "mixed": mixed},
        )
    if len(present) >= 3:
        return Probe(
            "modules-separated", "met", items,
            clip(f"{len(present)} kinds of component live in distinct places: "
                 + "; ".join(f"{kind} in {', '.join(found[kind][:2])}" for kind in present)),
            evidence, {"found": found},
        )
    if present:
        missing = [kind for kind in found if not found[kind]]
        return Probe(
            "modules-separated", "partial", items,
            clip(f"Only {', '.join(present)} are separate here; no distinct place for {', '.join(missing)}."),
            evidence, {"found": found},
        )
    return Probe(
        "modules-separated", "unmet", items,
        clip("Nothing distinguishes raw data, derived data, code and environment: no module or directory "
             "of any of those kinds is tracked."),
        [Evidence("probe:modules-separated", f"{len(tracked)} tracked paths, none in a recognised layout")],
        {"found": found},
    )
