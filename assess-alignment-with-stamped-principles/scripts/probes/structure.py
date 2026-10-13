# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Probes over the object's tree: tracking, paths, large content, entry point,
environment specification, licences and CI."""

from __future__ import annotations

import fnmatch
import re

from .common import Evidence, Object, Probe, clip, in_log_dir, is_text_path

# Absolute, host-specific paths.  Built from parts so this file does not itself
# contain a literal user home path (ci/validate_skills.py E003).
_HOME = "/home/" + r"[a-z][\w.-]+/"
_USERS = "/Users/" + r"[A-Za-z][\w.-]+/"
_WIN = r"[A-Za-z]:\\+(?:Users|home)\\+"
HOME_PATH = re.compile("|".join((_HOME, _USERS, _WIN)))
TMP_PATH = re.compile(r"(?<![\w.:])/(?:tmp|var/tmp)/[\w.${}-]+")
# Any other absolute path whose root is not a standard system location: a
# cluster mount, a second disk, somebody's scratch space.  `/data/<user>/...`
# is exactly as unportable as a home directory, and missing that was this
# probe's worst false negative (see evals/stamped/blind-runs/).
ABSOLUTE_PATH = re.compile(r"(?<![\w.:$])/([a-zA-Z][\w.-]*)(/[\w.${}-]+)+")
# Roots that exist on any POSIX host, so an absolute path into them is not a
# portability defect: interpreters, system tools, container-internal trees.
SYSTEM_ROOTS = {
    "usr", "bin", "sbin", "lib", "lib32", "lib64", "libexec", "etc", "opt",
    "dev", "proc", "sys", "run", "boot", "srv", "snap", "nix", "var",
}
# URLs carry path components that are not host paths; strip them before looking.
URL = re.compile(r"\b[a-zA-Z][\w+.-]*://\S*")
# Documentation placeholders, which are instructions to the reader rather than
# paths the scripts use.
PLACEHOLDER_ROOTS = {"path", "paths", "your", "some", "somewhere", "foo", "bar", "abs"}

# Files that may legitimately contain such a string: git's own module records,
# and vendored upstream data (the checklist item text quotes an example path).
ABS_PATH_ALLOW = (".gitmodules", "*/stamped-checklist-*.json", "stamped-checklist-*.json")

# Documentation mentioning a host path is a smaller problem than a script
# depending on one; must/009 asks about scripts.
CODE_SUFFIXES = {
    ".py", ".sh", ".bash", ".zsh", ".r", ".R", ".m", ".jl", ".pl", ".rb",
    ".yml", ".yaml", ".toml", ".cfg", ".ini", ".json", ".smk", ".nf", ".def",
    ".mk", ".make", ".do", ".sql", ".env",
}
CODE_NAMES = {"Makefile", "makefile", "GNUmakefile", "Snakefile", "Dockerfile", "Singularity", "config"}

# Output of a recorded execution: a duct trace, a tool's own log or manifest.
# These *should* carry the host path they ran on — that is provenance, not a
# portability defect of the scripts must/009 asks about.
RECORD_DIRS = ("derivatives/", "derivative/", "outputs/", "output/", "results/", "logs/", "log/",
               ".duct/", ".snakemake/", ".sweep-logs/")
RECORD_NAMES = re.compile(
    r"^(?:duct-|manifest|provenance|dataset_description\.json$|.*-std(?:out|err)$|.*usage\.jsonl$"
    r"|.*info\.json$|.*\.log$|.*_log\.txt$|params\.py$)"
)
RUNNABLE_SUFFIXES = (".py", ".sh", ".smk", ".nf", ".R", ".r", ".jl", ".m", ".do", ".bash")

LARGE_SUFFIXES = {
    ".nii", ".gz", ".nii.gz", ".mgz", ".zip", ".tar", ".h5", ".hdf5", ".nwb",
    ".mat", ".zarr", ".dcm", ".sif", ".simg", ".img", ".bin", ".npy", ".npz",
}

ENV_SPECS = {
    "pixi.lock": "pinned", "uv.lock": "pinned", "poetry.lock": "pinned",
    "conda-lock.yml": "pinned", "renv.lock": "pinned", "package-lock.json": "pinned",
    "Pipfile.lock": "pinned", "requirements.lock": "pinned",
    "requirements.txt": "spec", "pyproject.toml": "spec", "setup.py": "spec",
    "environment.yml": "spec", "environment.yaml": "spec", "pixi.toml": "spec",
    "Dockerfile": "spec", "Singularity": "spec", "DESCRIPTION": "spec",
    "Pipfile": "spec", "setup.cfg": "spec",
}
CI_DIRS = (".github/workflows/", ".gitlab-ci.yml", ".circleci/", ".forgejo/workflows/", ".gitea/workflows/")
CI_REEXECUTES = re.compile(
    r"\b(datalad\s+rerun|datalad\s+run|make\b|snakemake|nextflow|pixi\s+run|uv\s+sync|"
    r"docker\s+build|apptainer\s+build|singularity\s+build|conda\s+env\s+create|tox\b)",
    re.IGNORECASE,
)


def tree_clean(obj: Object) -> Probe:
    """must/004 — code, text, documentation and configuration are under version
    control, and nothing that matters is left outside it."""
    out = obj.git("status", "--porcelain", "--untracked-files=normal")
    dirty = [line for line in out.splitlines() if line.strip()]
    sub_dirty = [m.get("path", m["name"]) for m in obj.submodules() if m.get("differs")]
    tracked_text = [p for p in obj.tracked() if is_text_path(p)]
    if not dirty and not sub_dirty:
        return Probe(
            "tree-clean", "met", ["stamped-checklist:must/004"],
            clip(f"git tracks {len(tracked_text)} text, code and configuration file(s), and `git status` is "
                 "empty including submodules: the committed state is the whole state."),
            [Evidence("git ls-files", f"{len(tracked_text)} tracked text/code/config paths of "
                                      f"{len(obj.tracked())} tracked paths"),
             Evidence("git status --porcelain", "no output")],
            {"tracked_text": len(tracked_text)},
        )
    shown = ", ".join(d.strip() for d in dirty[:5]) or ", ".join(sub_dirty[:5])
    return Probe(
        "tree-clean", "unmet", ["stamped-checklist:must/004"],
        clip(f"{len(dirty) + len(sub_dirty)} path(s) are not committed, so the repository is not the whole "
             f"state: {shown}"),
        [Evidence("git status --porcelain", clip(shown, 200))],
        {"dirty": dirty, "submodules_modified": sub_dirty, "tracked_text": len(tracked_text)},
    )


def _is_code(relpath: str) -> bool:
    name = relpath.rsplit("/", 1)[-1]
    suffix = ("." + name.rsplit(".", 1)[-1]) if "." in name else ""
    return name in CODE_NAMES or suffix in CODE_SUFFIXES


def _is_record_output(relpath: str) -> bool:
    name = relpath.rsplit("/", 1)[-1]
    under_record_dir = any(relpath.startswith(d) or f"/{d}" in relpath for d in RECORD_DIRS)
    return bool(RECORD_NAMES.match(name)) or (under_record_dir and not _looks_like_source(relpath))


def _looks_like_source(relpath: str) -> bool:
    """A script or workflow that happens to sit under a results directory."""
    name = relpath.rsplit("/", 1)[-1]
    return name in CODE_NAMES or name.endswith((".sh", ".smk", ".nf")) or (
        name.endswith(".py") and not RECORD_NAMES.match(name)
    )


def _classify_path(raw: str) -> str | None:
    """Which kind of unportable absolute path this line carries, if any."""
    line = URL.sub(" ", raw)
    if HOME_PATH.search(line):
        return "home"
    for match in ABSOLUTE_PATH.finditer(line):
        root = match.group(1)
        if root in SYSTEM_ROOTS or root in PLACEHOLDER_ROOTS:
            continue
        if root in {"tmp"}:
            return "tmp"
        return "host"  # a mount that exists on one machine
    if TMP_PATH.search(line):
        return "tmp"
    return None


def no_abs_paths(obj: Object, allow: tuple[str, ...] = ()) -> Probe:
    """must/009 — scripts use relative paths, not host-specific absolute ones."""
    patterns = ABS_PATH_ALLOW + tuple(allow)
    hits: list[dict] = []
    for relpath in obj.tracked():
        if not is_text_path(relpath) or in_log_dir(relpath):
            continue
        if any(fnmatch.fnmatch(relpath, pat) for pat in patterns):
            continue
        text = obj.read(relpath)
        if not text:
            continue
        where = "record" if _is_record_output(relpath) else ("code" if _is_code(relpath) else "docs")
        for lineno, line in enumerate(text.splitlines(), 1):
            kind = _classify_path(line)
            if kind:
                hits.append({"path": relpath, "line": lineno, "kind": kind,
                             "where": where, "text": clip(line.strip(), 120)})
            if len(hits) >= 200:
                break
        if len(hits) >= 200:
            break

    # A script that names a path only one machine has cannot run elsewhere.
    blocking = [h for h in hits if h["kind"] in {"home", "host"} and h["where"] == "code"]
    softer = [h for h in hits if h not in blocking]
    if blocking:
        first = blocking[0]
        files = sorted({h["path"] for h in blocking})
        return Probe(
            "no-abs-paths", "unmet", ["stamped-checklist:must/009"],
            clip(f"{len(blocking)} host-specific absolute path(s) in {len(files)} script(s) or config(s), "
                 f"e.g. {first['path']} line {first['line']}: {first['text']}"),
            [Evidence(f"{h['path']}#L{h['line']}", f"{h['kind']} path: {h['text']}") for h in blocking[:10]],
            {"hits": hits, "blocking_files": files},
        )
    if softer:
        records = [h for h in softer if h["where"] == "record"]
        first = (softer if not records or len(records) < len(softer) else records)[0]
        label = {"home": "a home directory", "host": "a host-specific mount", "tmp": "/tmp"}[first["kind"]]
        detail = (f"{len(records)} of them in recorded run output, which is provenance rather than a script"
                  if records else f"e.g. {first['path']} line {first['line']} ({label}, in {first['where']})")
        return Probe(
            "no-abs-paths", "partial", ["stamped-checklist:must/009"],
            clip(f"No script depends on a host-specific path, but {len(softer)} such mention(s) remain: {detail}"),
            [Evidence(f"{h['path']}#L{h['line']}", f"{h['kind']} path in {h['where']}: {h['text']}")
             for h in softer[:10]],
            {"hits": hits},
        )
    return Probe(
        "no-abs-paths", "met", ["stamped-checklist:must/009"],
        "No host-specific absolute paths in tracked text files.",
        [Evidence("probe:no-abs-paths", f"scanned {len(obj.tracked())} tracked paths, 0 hits")],
    )


def _is_binary(obj: Object, relpath: str) -> bool:
    path = obj.root / relpath
    try:
        with path.open("rb") as fh:
            chunk = fh.read(8192)
        return b"\0" in chunk
    except OSError:
        # Content not present (annexed, or a broken pointer): fall back to the
        # suffix, and say so in the evidence rather than guessing silently.
        return relpath.lower().endswith(tuple(LARGE_SUFFIXES))


def large_in_annex(obj: Object, max_bytes: int = 10 * 1024 * 1024) -> Probe:
    """must/005 — large *binary* data is content-addressed rather than a git blob.

    The item asks about binary data, so a large *text* blob is not a violation of
    it; `clone-weight` reports that separately (a blind run of this skill caught
    this probe applying a size criterion the item does not state).
    """
    blobs = obj.blobs()
    big_binary = [(p, s) for p, s, _ in blobs if s > max_bytes and _is_binary(obj, p)]
    annexed = sum(1 for _, _, mode in blobs if mode == "120000")
    has_lfs = obj.exists(".gitattributes") and "filter=lfs" in obj.read(".gitattributes")
    mechanism = "git-annex" if obj.is_datalad or annexed else ("git-lfs" if has_lfs else None)
    limit_mib = max_bytes // 1024 // 1024
    details = {"mechanism": mechanism, "annex_pointers": annexed,
               "large_binary": [{"path": p, "size": s} for p, s in big_binary]}
    if big_binary:
        worst = max(big_binary, key=lambda t: t[1])
        return Probe(
            "large-in-annex", "unmet", ["stamped-checklist:must/005"],
            clip(f"{len(big_binary)} binary blob(s) over {limit_mib} MiB committed to git, "
                 f"largest {worst[0]} at {worst[1] // 1024 // 1024} MiB"),
            [Evidence(p, f"{s} bytes of binary data in a git blob")
             for p, s in sorted(big_binary, key=lambda t: -t[1])[:10]],
            details,
        )
    if mechanism:
        return Probe(
            "large-in-annex", "met", ["stamped-checklist:must/005"],
            clip(f"{mechanism} carries the binary content ({annexed} pointer(s) tracked) and no binary blob "
                 f"over {limit_mib} MiB is in git."),
            [Evidence("git ls-tree -r -l HEAD", f"no binary blob over {max_bytes} bytes"),
             Evidence(".gitattributes" if has_lfs else ".datalad/config",
                      f"{mechanism} in use for large content")],
            details,
        )
    return Probe(
        "large-in-annex", "met", ["stamped-checklist:must/005"],
        clip(f"No binary blob over {limit_mib} MiB in git, and no large-content mechanism is needed: "
             "nothing in this object is large binary data."),
        [Evidence("git ls-tree -r -l HEAD", f"no binary blob over {max_bytes} bytes; "
                                            f"{len(blobs)} blobs tracked")],
        details,
    )


def clone_weight(obj: Object, max_bytes: int = 10 * 1024 * 1024) -> Probe:
    """Extra (no checklist item) — oversized *text* in git, which every clone carries.

    `-c text2git` deliberately keeps text in git; an 11 MiB log is still weight
    a reader pays before any `datalad get`, which is worth saying without
    pretending the checklist asks about it.
    """
    limit_mib = max_bytes // 1024 // 1024
    big_text = [(p, s) for p, s, _ in obj.blobs() if s > max_bytes and not _is_binary(obj, p)]
    if not big_text:
        return Probe(
            "clone-weight", "met", [],
            clip(f"No text blob in git exceeds {limit_mib} MiB."),
            [Evidence("git ls-tree -r -l HEAD", f"largest text blob under {max_bytes} bytes")],
        )
    worst = max(big_text, key=lambda t: t[1])
    total = sum(s for _, s in big_text)
    return Probe(
        "clone-weight", "partial", [],
        clip(f"{len(big_text)} text blob(s) exceed {limit_mib} MiB ({total // 1024 // 1024} MiB in total, "
             f"largest {worst[0]}) — every clone carries them in full. Not a must/005 defect: they are text."),
        [Evidence(p, f"{s} bytes of text in a git blob")
         for p, s in sorted(big_text, key=lambda t: -t[1])[:10]],
        {"large_text": [{"path": p, "size": s} for p, s in big_text]},
    )


def entry_point(obj: Object) -> Probe:
    """must/007 (instructions for install and usage) and must/008 (a starting point)."""
    readmes = [p for p in obj.tracked() if p.lower() in {"readme.md", "readme.rst", "readme", "readme.txt"}]
    makefiles = [p for p in obj.tracked() if p in {"Makefile", "makefile", "GNUmakefile"}]
    items = ["stamped-checklist:must/007", "stamped-checklist:must/008"]
    tracked = set(obj.tracked())
    make_text = "\n".join(obj.read(p) for p in makefiles)
    readme_text = "\n".join(obj.read(p) for p in readmes)
    text = readme_text + "\n" + make_text

    targets = [t for t in re.findall(r"^([a-zA-Z0-9_.%/-]+):\s*(?:[^=]|$)", make_text, re.M) if not t.startswith(".")]
    workflow = sorted(p for p in tracked if p.rsplit("/", 1)[-1] in {"Snakefile", "main.nf", "dvc.yaml"}
                      or p.endswith(".smk"))
    named = sorted(p for p in tracked if p.endswith(RUNNABLE_SUFFIXES)
                   and (p in text or p.rsplit("/", 1)[-1] in text))
    has_section = bool(re.search(r"(?i)^#+.*\b(reproduc|rerun|usage|quick\s*start|install|how to run|getting started)",
                                 readme_text, re.M))

    evidence = [Evidence(p, "instructions") for p in readmes + makefiles]
    evidence += [Evidence(p, "entry point named in the instructions and present") for p in named[:5]]
    if targets:
        evidence.append(Evidence(makefiles[0], f"make targets: {', '.join(sorted(set(targets))[:6])}"))
    if workflow:
        evidence.append(Evidence(workflow[0], "workflow definition"))

    # must/007: are there instructions for installation and usage?
    if readmes and has_section:
        s7 = "met"
        r7 = clip(f"{readmes[0]} has an install/usage/reproduce section.")
    elif readmes and (targets or workflow):
        s7 = "partial"
        r7 = clip(f"{readmes[0]} has no install or usage section; usage is only implied by "
                  f"{makefiles[0] if targets else workflow[0]}.")
    elif targets:
        s7 = "partial"
        r7 = clip(f"No README; {makefiles[0]} carries the usage implicitly in its targets.")
    else:
        s7 = "unmet"
        r7 = "Neither a README with install/usage instructions nor a Makefile."

    # must/008: is there a clear starting point, and does it exist?
    starting = named[:1] or ([f"make {targets[0]}"] if targets else workflow[:1])
    if starting:
        s8 = "met"
        r8 = clip(f"Starting point present: {starting[0]}.")
    else:
        s8 = "unmet"
        r8 = clip("No script, make target or workflow definition that a reader could start from"
                  + (f" is named in {readmes[0]}." if readmes else "."))

    worst = min((s7, s8), key=lambda s: {"unmet": 0, "partial": 1, "met": 2}[s])
    return Probe(
        "entry-point", worst, items, clip(f"must/007 {s7}: {r7} must/008 {s8}: {r8}"), evidence,
        {"readmes": readmes, "makefiles": makefiles, "named": named, "targets": sorted(set(targets)),
         "workflow": workflow, "has_section": has_section},
        item_status={items[0]: s7, items[1]: s8},
        item_reason={items[0]: r7, items[1]: r8},
    )


# A tracked script that checks for a tool on PATH, or tells the reader to
# install one, is positive evidence that the environment is *not* contained:
# must/009 asks about paths, must/010 about pre-installed tools.
TOOL_PRECONDITION = re.compile(
    r"(?:command\s+-v|which|type\s+-p|hash)\s+([\w.+-]{2,})"
    r"|\b([\w.+-]{2,})\s+--version\b"
    r"|(please install|must be installed|not found on PATH|install with|needs? to be installed)",
    re.IGNORECASE,
)
PRECONDITION_EXIT = re.compile(r"\bexit\s+[1-9]|\breturn\s+[1-9]|\bdie\b")
PRECONDITION_IGNORE = {"echo", "then", "else", "fi", "do", "done", "if", "set", "the", "this", "python3", "python"}


def _host_tool_preconditions(obj: Object) -> list[dict]:
    """Places a tracked script requires a tool to be present on the host already."""
    found: list[dict] = []
    for relpath in obj.tracked():
        name = relpath.rsplit("/", 1)[-1]
        if not (name.endswith((".sh", ".bash", ".zsh", ".py")) or name in CODE_NAMES):
            continue
        if _is_record_output(relpath):
            continue
        lines = obj.read(relpath).splitlines()
        for lineno, line in enumerate(lines, 1):
            match = TOOL_PRECONDITION.search(line)
            if not match:
                continue
            tool = next((g for g in match.groups()[:2] if g), None)
            if tool and tool.lower() in PRECONDITION_IGNORE:
                continue
            window = "\n".join(lines[max(0, lineno - 9):lineno + 8])
            if tool and not PRECONDITION_EXIT.search(window) and not match.group(3):
                continue  # a version check that does not gate anything
            found.append({"path": relpath, "line": lineno, "tool": tool,
                          "text": clip(line.strip(), 120)})
    return found


def env_spec_tracked(obj: Object) -> Probe:
    """must/010 (nothing assumed pre-installed), must/013 (the spec is tracked),
    must/016 (the spec is published where others can get it)."""
    i010, i013, i016 = ("stamped-checklist:must/010", "stamped-checklist:must/013",
                        "stamped-checklist:must/016")
    items = [i010, i013, i016]
    found: dict[str, str] = {}
    for relpath in obj.tracked():
        name = relpath.rsplit("/", 1)[-1]
        kind = ENV_SPECS.get(name)
        if kind is None and (name.endswith(".def") or name.startswith("Singularity.")):
            kind = "spec"
        if kind is None and name.startswith("requirements") and name.endswith(".txt"):
            kind = "spec"
        if kind:
            found[relpath] = kind
    if obj.exists(".datalad/config") and "containers." in obj.read(".datalad/config"):
        found[".datalad/config"] = "pinned"

    pinned = sorted(p for p, k in found.items() if k == "pinned")
    uninstalled = [m.get("path", m["name"]) for m in obj.submodules() if not m.get("initialized", False)]
    preconditions = _host_tool_preconditions(obj)
    remote = obj.git("config", "--get", "remote.origin.url").strip()
    published = bool(remote) and not remote.startswith(("/", ".", "file://", "~"))

    evidence = [Evidence(p, f"{k} environment specification") for p, k in sorted(found.items())]
    evidence += [Evidence(f"{h['path']}#L{h['line']}",
                          f"requires {h['tool'] or 'a tool'} to be installed on the host already: {h['text']}")
                 for h in preconditions[:5]]
    evidence += [Evidence(path, "linked module, not installed: cannot be read") for path in uninstalled[:3]]

    # must/013 — is a specification tracked at all?
    if found:
        s013 = "met"
        r013 = clip(f"Tracked: {', '.join(sorted(found)[:3])}.")
    elif uninstalled:
        s013 = "partial"
        r013 = clip("No specification in this object; it may be inside the module(s) not installed here: "
                    f"{', '.join(uninstalled[:3])}.")
    else:
        s013 = "unmet"
        r013 = "No tracked environment specification (lockfile, container definition or registration)."

    # must/010 — are the dependencies in it, rather than assumed present?
    if preconditions:
        first = preconditions[0]
        s010 = "unmet"
        r010 = clip(f"{len(preconditions)} tracked script(s) require a tool to be installed on the host "
                    f"already, e.g. {first['path']} line {first['line']} ({first['tool'] or 'see line'}); "
                    "that dependency is not in any tracked specification.")
    elif pinned:
        s010 = "met"
        r010 = clip(f"Dependencies are pinned in {', '.join(pinned[:3])}, and no tracked script expects a "
                    "tool to be present already.")
    elif found:
        s010 = "partial"
        r010 = clip(f"{', '.join(sorted(found)[:3])} lists dependencies but pins no versions "
                    "(no lockfile or digest).")
    else:
        s010 = s013
        r010 = r013

    # must/016 — can someone else obtain the specification?
    if not found:
        s016, r016 = s013, clip("Nothing to share: " + r013)
    elif published:
        s016 = "met"
        r016 = clip(f"The specification is tracked in a repository published at {remote}, so it travels with "
                    "the object for anyone who can clone it.")
    else:
        s016 = "partial"
        r016 = clip("The specification is tracked, but this checkout records no published remote, so there is "
                    "no evidence anyone else can obtain it.")

    worst = min((s010, s013, s016), key=lambda s: {"unmet": 0, "partial": 1, "not-checked": 2,
                                                   "not-applicable": 3, "met": 4}[s])
    return Probe(
        "env-spec-tracked", worst, items,
        clip(f"must/010 {s010}: {r010} must/013 {s013}. must/016 {s016}."),
        evidence,
        {"specs": found, "uninstalled_modules": uninstalled, "preconditions": preconditions,
         "remote": remote or None},
        item_status={i010: s010, i013: s013, i016: s016},
        item_reason={i010: r010, i013: r013, i016: r016},
    )


def license_declared(obj: Object) -> Probe:
    """Paper S.2/D.3 — no checklist item covers licensing in 0.3.1, so this is an extra."""
    tracked = obj.tracked()
    hits = [p for p in tracked if p.split("/")[0] in {"LICENSE", "LICENSES", "COPYING", "REUSE.toml"}
            or p.startswith("LICENSES/") or p.startswith("LICENSE")]
    data_license = None
    for relpath in tracked:
        if relpath.endswith("dataset_description.json"):
            text = obj.read(relpath)
            if '"License"' in text:
                data_license = relpath
    if hits or data_license:
        evidence = [Evidence(p, "licence declaration") for p in sorted(set(hits))[:5]]
        if data_license:
            evidence.append(Evidence(data_license, "BIDS License field"))
        code_and_data = bool(hits) and bool(data_license)
        return Probe(
            "license-declared", "met" if code_and_data or not data_license else "partial",
            [], clip(f"Licence declared in {', '.join(sorted(set(hits))[:3] or [data_license])}."),
            evidence,
        )
    return Probe(
        "license-declared", "unmet", [],
        "No LICENSE, LICENSES/, REUSE.toml or BIDS License field: reuse terms are unstated.",
        [Evidence("probe:license-declared", f"no licence file among {len(tracked)} tracked paths, and no "
                                            "License field in any dataset_description.json")],
    )


def ci_present(obj: Object) -> Probe:
    """should/002, should/006 — the workflow or the environment is exercised automatically."""
    items = ["stamped-checklist:should/002", "stamped-checklist:should/006"]
    configs = [p for p in obj.tracked() if any(p.startswith(d) or p == d for d in CI_DIRS)]
    if not configs:
        return Probe(
            "ci-present", "unmet", items,
            "No CI configuration: nothing checks that the instructions still work.",
            [Evidence("probe:ci-present",
                      "no tracked " + ", ".join(CI_DIRS) + " in " + str(len(obj.tracked())) + " tracked paths")],
        )
    reexec = [p for p in configs if CI_REEXECUTES.search(obj.read(p))]
    evidence = [Evidence(p, "CI configuration") for p in configs[:5]]
    if reexec:
        return Probe(
            "ci-present", "met", items,
            clip(f"{', '.join(reexec[:2])} re-executes the workflow or rebuilds the environment."),
            [Evidence(p, "re-executes the workflow or rebuilds the environment") for p in reexec[:5]],
        )
    return Probe(
        "ci-present", "partial", items,
        clip(f"CI exists ({configs[0]}) but no job re-executes the workflow or rebuilds the environment."),
        evidence,
    )
