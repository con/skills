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
# A path under someone's home directory cannot resolve on another machine; a
# path under /tmp resolves but leaks host state, so the two are weighed apart.
HOME_PATH = re.compile("|".join((_HOME, _USERS, _WIN)))
TMP_PATH = re.compile(r"(?<![\w.])/tmp/[\w.${}-]+")

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
    """must/004 — committed state is the whole state."""
    out = obj.git("status", "--porcelain", "--untracked-files=normal")
    dirty = [line for line in out.splitlines() if line.strip()]
    sub_dirty: list[str] = []
    for mod in obj.submodules():
        if mod.get("differs"):
            sub_dirty.append(mod.get("path", mod["name"]))
    if not dirty and not sub_dirty:
        return Probe(
            "tree-clean", "met", ["stamped-checklist:must/004"],
            "git status is empty, including submodules: the committed state is the whole state.",
            [Evidence("git status --porcelain", "no output", None)],
        )
    shown = ", ".join(d.strip() for d in dirty[:5]) or ", ".join(sub_dirty[:5])
    return Probe(
        "tree-clean", "unmet", ["stamped-checklist:must/004"],
        clip(f"{len(dirty) + len(sub_dirty)} path(s) not committed: {shown}"),
        [Evidence("git status --porcelain", clip(shown, 200))],
        {"dirty": dirty, "submodules_modified": sub_dirty},
    )


def _is_code(relpath: str) -> bool:
    name = relpath.rsplit("/", 1)[-1]
    suffix = ("." + name.rsplit(".", 1)[-1]) if "." in name else ""
    return name in CODE_NAMES or suffix in CODE_SUFFIXES


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
        code = _is_code(relpath)
        for lineno, line in enumerate(text.splitlines(), 1):
            kind = "home" if HOME_PATH.search(line) else ("tmp" if TMP_PATH.search(line) else None)
            if kind:
                hits.append({"path": relpath, "line": lineno, "kind": kind,
                             "where": "code" if code else "docs", "text": clip(line.strip(), 120)})
            if len(hits) >= 100:
                break
        if len(hits) >= 100:
            break

    blocking = [h for h in hits if h["kind"] == "home" and h["where"] == "code"]
    softer = [h for h in hits if h not in blocking]
    if blocking:
        first = blocking[0]
        return Probe(
            "no-abs-paths", "unmet", ["stamped-checklist:must/009"],
            clip(f"{len(blocking)} absolute home path(s) in scripts or configs, "
                 f"e.g. {first['path']} line {first['line']}"),
            [Evidence(f"{h['path']}#L{h['line']}", h["text"]) for h in blocking[:10]],
            {"hits": hits},
        )
    if softer:
        first = softer[0]
        label = {"home": "a home directory", "tmp": "/tmp"}[first["kind"]]
        return Probe(
            "no-abs-paths", "partial", ["stamped-checklist:must/009"],
            clip(f"No scripts depend on a home path, but {len(softer)} mention(s) of host paths remain, "
                 f"e.g. {first['path']} line {first['line']} ({label}, in {first['where']})"),
            [Evidence(f"{h['path']}#L{h['line']}", f"{h['kind']} path in {h['where']}: {h['text']}")
             for h in softer[:10]],
            {"hits": hits},
        )
    return Probe(
        "no-abs-paths", "met", ["stamped-checklist:must/009"],
        "No host-specific absolute paths in tracked text files.",
        [Evidence("probe:no-abs-paths", f"scanned {len(obj.tracked())} tracked paths, 0 hits")],
    )


def large_in_annex(obj: Object, max_bytes: int = 10 * 1024 * 1024) -> Probe:
    """must/005 — large binaries are content-addressed, not git blobs."""
    big = [(p, s) for p, s, _ in obj.blobs() if s > max_bytes]
    annexed = sum(1 for _, _, mode in obj.blobs() if mode == "120000")
    has_lfs = obj.exists(".gitattributes") and "filter=lfs" in obj.read(".gitattributes")
    mechanism = "git-annex" if obj.is_datalad or annexed else ("git-lfs" if has_lfs else None)
    if not big:
        return Probe(
            "large-in-annex", "met", ["stamped-checklist:must/005"],
            clip(
                f"No tracked git blob exceeds {max_bytes // 1024 // 1024} MiB"
                + (f"; large content is handled by {mechanism}." if mechanism else ".")
            ),
            [Evidence("git ls-tree -r -l HEAD", f"largest blob under {max_bytes} bytes")],
            {"mechanism": mechanism, "annex_pointers": annexed},
        )
    worst = max(big, key=lambda t: t[1])
    return Probe(
        "large-in-annex", "unmet", ["stamped-checklist:must/005"],
        clip(
            f"{len(big)} blob(s) over {max_bytes // 1024 // 1024} MiB committed to git, "
            f"largest {worst[0]} at {worst[1] // 1024 // 1024} MiB"
        ),
        [Evidence(p, f"{s} bytes in a git blob") for p, s in sorted(big, key=lambda t: -t[1])[:10]],
        {"mechanism": mechanism, "large_blobs": [{"path": p, "size": s} for p, s in big]},
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


def env_spec_tracked(obj: Object) -> Probe:
    """must/010, must/013 — the environment, including the project's own tooling, is specified and tracked."""
    items = ["stamped-checklist:must/010", "stamped-checklist:must/013"]
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
    containers = obj.exists(".datalad/config") and "containers." in obj.read(".datalad/config")
    if containers:
        found[".datalad/config"] = "pinned"
    if not found:
        return Probe(
            "env-spec-tracked", "unmet", items,
            "No tracked environment specification (lockfile, container definition or container registration).",
            [],
        )
    pinned = [p for p, k in found.items() if k == "pinned"]
    evidence = [Evidence(p, f"{k} environment specification") for p, k in sorted(found.items())]
    if pinned:
        return Probe(
            "env-spec-tracked", "met", items,
            clip(f"Tracked and pinned: {', '.join(sorted(pinned)[:3])}."),
            evidence, {"specs": found},
        )
    return Probe(
        "env-spec-tracked", "partial", items,
        clip(f"{', '.join(sorted(found)[:3])} is tracked but nothing pins versions (no lockfile or digest)."),
        evidence, {"specs": found},
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
        [],
    )


def ci_present(obj: Object) -> Probe:
    """should/002, should/006 — the workflow or the environment is exercised automatically."""
    items = ["stamped-checklist:should/002", "stamped-checklist:should/006"]
    configs = [p for p in obj.tracked() if any(p.startswith(d) or p == d for d in CI_DIRS)]
    if not configs:
        return Probe("ci-present", "unmet", items, "No CI configuration: nothing checks that the instructions still work.", [])
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
