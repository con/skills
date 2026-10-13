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
    """must/002, must/016, may/001 — linked components resolve from a fresh clone."""
    items = ["stamped-checklist:must/002", "stamped-checklist:must/016", "stamped-checklist:may/001"]
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
            clip(f"{len(unreachable)} module url(s) are well-formed but did not answer: {unreachable[0]['path']}"),
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
    """should/003 (M.1) — inputs stay at their recorded state; results go elsewhere."""
    items = ["stamped-checklist:should/003"]
    mods = obj.submodules()
    if not mods:
        return Probe(
            "inputs-untouched", "not-checked", items,
            "No submodules: whether raw data, derivatives and code are separate modules needs a reading of the layout.",
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
