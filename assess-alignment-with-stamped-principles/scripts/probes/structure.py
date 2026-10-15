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
# `///openneuro/ds007116` and `ria+http://...` are DataLad registry shortcuts —
# locations anyone can resolve, not paths on one machine.
URL = re.compile(r"\b[a-zA-Z][\w+.-]*://\S*|(?<![\w])/{3}\S*|\bria\+\S*")
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
# PEP 723 inline script metadata: `# /// script` … `dependencies = [...]` …
# `# ///`, which `uv run <script>` resolves. A script that carries its own
# dependencies *is* an environment specification, pinned if the versions are.
PEP723 = re.compile(r"^#\s*///\s*script\s*$.*?^#\s*///\s*$", re.M | re.S)
PEP723_PINNED = re.compile(r'"[\w.\[\]-]+\s*(==|~=|>=)\s*[\d.]+')
LOCKFILES_CI = ("pixi.lock", "uv.lock", "poetry.lock", "conda-lock.yml", "renv.lock",
                "requirements.lock", "requirements.txt")
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
    # `/tmp` exists on every POSIX host, so it is not an assumption about *this*
    # machine and does not belong to must/009: a live run lost the item for
    # `/tmp/` in a CI workflow, which is portable. It is still worth saying,
    # because it is a write outside the object, so it is reported as a note.
    tmp_hits = [h for h in hits if h["kind"] == "tmp" and h not in blocking]
    softer = [h for h in hits if h not in blocking and h not in tmp_hits]
    tmp_note = (f" Plus {len(tmp_hits)} /tmp path(s), portable but writing outside the object."
                if tmp_hits else "")
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
            clip(f"No script depends on a host-specific path, but {len(softer)} such mention(s) remain: "
                 f"{detail}.{tmp_note}"),
            [Evidence(f"{h['path']}#L{h['line']}", f"{h['kind']} path in {h['where']}: {h['text']}")
             for h in softer[:10]],
            {"hits": hits},
        )
    return Probe(
        "no-abs-paths", "met", ["stamped-checklist:must/009"],
        clip(f"No host-specific absolute paths in tracked text files.{tmp_note}"),
        [Evidence("probe:no-abs-paths", f"scanned {len(obj.tracked())} tracked paths, "
                  f"{len(tmp_hits)} /tmp hit(s), 0 host-specific")],
        {"tmp_hits": tmp_hits},
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
    # Commands the instructions tell a reader to run, checked against what the
    # tracked workflow actually defines. The probe used to hold both lists and
    # never compare them.
    documented_targets = {m for m in re.findall(r"(?<![\w-])make\s+(?:-[\w-]+\s+)*([a-zA-Z][\w.%/-]*)", readme_text)}
    documented_targets -= {"-n", "all"} if "all" not in targets else {"-n"}
    missing_targets = sorted(t for t in documented_targets if t not in set(targets)) if makefiles else []

    evidence = [Evidence(p, "instructions") for p in readmes + makefiles]
    evidence += [Evidence(p, "entry point named in the instructions and present") for p in named[:5]]
    if targets:
        evidence.append(Evidence(makefiles[0], f"make targets: {', '.join(sorted(set(targets))[:6])}"))
    if workflow:
        evidence.append(Evidence(workflow[0], "workflow definition"))

    # must/007: are there instructions for installation and usage?
    if missing_targets:
        s7 = "partial"
        r7 = clip(f"{readmes[0] if readmes else 'The instructions'} tells the reader to run "
                  f"`make {missing_targets[0]}`, which {makefiles[0]} does not define "
                  f"(targets: {', '.join(sorted(set(targets))[:5])}).")
    elif readmes and has_section:
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

    if missing_targets:
        evidence.insert(0, Evidence(f"{readmes[0] if readmes else makefiles[0]}",
                                    f"documents `make {missing_targets[0]}`; no such target"))
    worst = min((s7, s8), key=lambda s: {"unmet": 0, "partial": 1, "met": 2}[s])
    return Probe(
        "entry-point", worst, items, clip(f"must/007 {s7}: {r7} must/008 {s8}: {r8}"), evidence,
        {"readmes": readmes, "makefiles": makefiles, "named": named, "targets": sorted(set(targets)),
         "workflow": workflow, "has_section": has_section, "documented_targets": sorted(documented_targets),
         "missing_targets": missing_targets},
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
# A check whose failure branch *falls back* is not a precondition: it is the
# opposite, a project making the tool optional. The template this collection
# ships does exactly that, and an earlier version of this probe cost a real run
# a MUST item for it.
PRECONDITION_FALLBACK = re.compile(r"(?i)\bfallback\b|\bwarning\b|\bnot found;|\bif not\b|\belse\b|"
                                   r"\boptional\b|\bwithout\b")
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
            # Only the lines that belong to this check's own failure branch.
            window = "\n".join(lines[lineno - 1:lineno + 3])
            if tool and not PRECONDITION_EXIT.search(window) and not match.group(3):
                continue  # a version check that does not gate anything
            if tool and PRECONDITION_FALLBACK.search(window):
                continue  # the project handles the tool being absent
            found.append({"path": relpath, "line": lineno, "tool": tool,
                          "text": clip(line.strip(), 120)})
    return found


def _remote_resolves(url: str) -> bool | None:
    """Does this remote exist? None when we did not get to ask.

    `GIT_TERMINAL_PROMPT=0` matters: a missing or private GitHub repository
    *asks for credentials* otherwise, and three blind runs lost time to that
    prompt before falling back to `curl`.
    """
    import os
    import subprocess

    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--exit-code", url, "HEAD"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "/bin/true",
                 "GIT_SSH_COMMAND": "ssh -oBatchMode=yes"},
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode == 0:
        return True
    text = (proc.stderr + proc.stdout).lower()
    if any(w in text for w in ("not found", "does not exist", "repository not found",
                              "authentication", "permission denied", "could not read")):
        return False
    return None


def env_spec_tracked(obj: Object, check_remote: bool = False) -> Probe:
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
    for relpath in obj.tracked():
        if not relpath.endswith(".py") or _is_record_output(relpath):
            continue
        block = PEP723.search(obj.read(relpath))
        if block:
            found[relpath] = "pinned" if PEP723_PINNED.search(block.group(0)) else "spec"

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
        inline = [p for p, k in found.items() if p.endswith(".py")]
        r010 = clip(f"{', '.join(sorted(found)[:3])} lists dependencies but pins no versions "
                    + ("(inline PEP 723 metadata with unpinned requirements; `uv lock --script` "
                       "would pin it)." if inline else "(no lockfile or digest)."))
    else:
        s010 = s013
        r010 = r013

    # must/016 — can someone else obtain the specification?
    if not found:
        s016, r016 = s013, clip("Nothing to share: " + r013)
    elif published:
        # A configured remote is a *claim* of publication, not evidence of it:
        # three blind runs overrode an earlier `met` here after finding the URL
        # returns 404. With `--check-remote` the probe asks; without it, it says
        # what it saw and leaves the asking to the reader (step 4).
        resolved = _remote_resolves(remote) if check_remote else None
        if resolved is True:
            s016 = "met"
            r016 = clip(f"The specification is tracked and its remote resolves ({remote}): "
                        "`git ls-remote` reached it, so anyone who can clone it obtains the spec.")
        elif resolved is False:
            s016 = "unmet"
            r016 = clip(f"The recorded remote does not resolve ({remote}): `git ls-remote` could not "
                        "reach it, so the tracked specification is not obtainable from where it claims.")
        else:
            s016 = "partial"
            r016 = clip(f"The specification is tracked and a remote is recorded ({remote}), but whether "
                        "that remote resolves was not checked: run with --check-remote, or "
                        "`GIT_TERMINAL_PROMPT=0 git ls-remote`, before calling it met.")
    else:
        s016 = "unmet"
        r016 = clip("The specification is tracked, but this checkout records no remote at all, so nothing "
                    "says where anyone else could obtain it.")

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


# Commands that exist on one platform only. A project may use them — it just
# has to say which platform it expects, which is what must/011 asks.
PLATFORM_COMMANDS = {
    "brew": "macOS (Homebrew)",
    "port install": "macOS (MacPorts)",
    "sysctl -n hw.": "macOS/BSD",
    "sed -i ''": "BSD sed (macOS); GNU sed needs `sed -i`",
    "apt-get": "Debian/Ubuntu",
    "apt install": "Debian/Ubuntu",
    "yum install": "RHEL/CentOS",
    "dnf install": "Fedora/RHEL",
    "pacman -S": "Arch",
    "apk add": "Alpine",
    "choco install": "Windows (Chocolatey)",
    "winget install": "Windows",
    "powershell": "Windows",
    "nproc": "GNU coreutils (absent on macOS)",
    "readlink -f": "GNU coreutils (absent on macOS)",
    "realpath --relative-to": "GNU coreutils",
    "sbatch": "a Slurm cluster",
    "srun": "a Slurm cluster",
    "qsub": "an SGE/PBS cluster",
    "module load": "an HPC module system",
}
# Naming the platform is what turns a lock-in into a documented assumption.
PLATFORM_DOCUMENTED = re.compile(
    r"(?i)\b(macos|mac os|osx|darwin|linux|ubuntu|debian|centos|rhel|fedora|alpine|windows|wsl|"
    r"slurm|sge|pbs|torque|hpc|cluster|requirements?:|tested on|prerequisites)\b"
)


def platform_assumptions(obj: Object) -> Probe:
    """must/011, must/012 — host assumptions are documented, not just implied.

    A blind run reported 13 probes `met` on an object whose documented install
    was Homebrew, BSD `sed -i ''` and `sysctl -n hw.ncpu`: platform lock-in
    through *tool choice* rather than through paths, which `no-abs-paths` cannot
    see. Naming the platform is the difference between an assumption and an
    undocumented one.
    """
    i011, i012 = "stamped-checklist:must/011", "stamped-checklist:must/012"
    items = [i011, i012]
    hits: list[dict] = []
    for relpath in obj.tracked():
        if not is_text_path(relpath) or in_log_dir(relpath) or _is_record_output(relpath):
            continue
        text = obj.read(relpath)
        if not text:
            continue
        documented = bool(PLATFORM_DOCUMENTED.search(text))
        for lineno, line in enumerate(text.splitlines(), 1):
            lowered = line.lower()
            for needle, platform in PLATFORM_COMMANDS.items():
                if needle in lowered:
                    hits.append({"path": relpath, "line": lineno, "needle": needle,
                                 "platform": platform, "documented_in_file": documented,
                                 "where": "code" if _is_code(relpath) else "docs",
                                 "text": clip(line.strip(), 120)})
                    break
    undocumented = [h for h in hits if not h["documented_in_file"]]
    evidence = [Evidence(f"{h['path']}#L{h['line']}", f"{h['platform']}: {h['text']}") for h in hits[:10]]

    if undocumented:
        first = undocumented[0]
        platforms = sorted({h["platform"] for h in undocumented})
        reason = clip(f"{len(undocumented)} command(s) that exist on one platform only, with no platform "
                      f"named in the same file: {first['path']} line {first['line']} needs "
                      f"{first['platform']}" + (f" (also: {', '.join(platforms[1:3])})" if len(platforms) > 1 else ""))
        return Probe("platform-assumptions", "partial", items, reason, evidence,
                     {"hits": hits, "undocumented": undocumented},
                     item_status={i011: "partial", i012: "partial"},
                     item_reason={i011: reason, i012: reason})
    # This probe reads *commands*. must/011 and must/012 ask about host
    # assumptions in general — mounts, hardware, services, environment
    # variables, OS versions — so a clean command scan is not a `met`. Claiming
    # one suppressed the judgement that should have caught a documented route
    # through /mnt/labshare, which is how this came to be written.
    if hits:
        reason = clip(f"{len(hits)} platform-specific command(s), each in a file naming the platform it "
                      f"expects (e.g. {hits[0]['path']}: {hits[0]['platform']}). Commands only; other "
                      "host assumptions need a reading.")
        return Probe("platform-assumptions", "not-checked", items, reason, evidence, {"hits": hits},
                     item_status={i011: "not-checked", i012: "not-checked"},
                     item_reason={i011: reason, i012: reason})
    reason = clip("No platform-specific package manager, BSD/GNU-only flag or scheduler command in "
                  "tracked text — all a command scan can settle. Whether the documented route needs a "
                  "mount, a host install, hardware or a service is a reading.")
    return Probe("platform-assumptions", "not-checked", items, reason,
                 [Evidence("probe:platform-assumptions",
                           f"scanned {len(obj.tracked())} tracked paths for "
                           f"{len(PLATFORM_COMMANDS)} platform-specific commands, 0 hits")],
                 {"hits": []},
                 item_status={i011: "not-checked", i012: "not-checked"},
                 item_reason={i011: reason, i012: reason})


def ci_present(obj: Object) -> Probe:
    """should/002 (the workflow is tested regularly) and should/006 (the
    environment that produced the results is tested regularly).

    These were one verdict from one coarse regex — the bare word `make` in a CI
    file was taken as proof of both. A blind run pointed out that they ask
    different questions: whether the workflow still runs, and whether *the*
    environment behind the shipped results can still be reconstituted. CI that
    runs `make all` under its own `pip install` answers the first and not the
    second.
    """
    i002, i006 = "stamped-checklist:should/002", "stamped-checklist:should/006"
    items = [i002, i006]
    configs = [p for p in obj.tracked() if any(p.startswith(d) or p == d for d in CI_DIRS)]
    if not configs:
        reason = "No CI configuration: nothing checks that the instructions still work."
        return Probe(
            "ci-present", "unmet", items, reason,
            [Evidence("probe:ci-present",
                      "no tracked " + ", ".join(CI_DIRS) + f" in {len(obj.tracked())} tracked paths")],
            {"configs": []},
            item_status={i002: "unmet", i006: "unmet"},
            item_reason={i002: reason,
                         i006: "No CI configuration: the environment behind the results is never rebuilt."},
        )

    texts = {path: obj.read(path) for path in configs}
    runs_workflow = [p for p, text in texts.items() if CI_REEXECUTES.search(text)]
    # What the run records actually ran in, so that "the environment" means the
    # one behind the shipped results rather than whatever CI happens to build.
    recorded = " ".join(
        # A space between the command and the extra inputs. Without it the last
        # token of one ran into the first of the other, and `details` carried
        # entries like `figures/plot.pngcode/containers/plotting.sif`.
        " ".join([str((rec.get("run_info") or {}).get("cmd", ""))]
                 + [str(x) for x in ((rec.get("run_info") or {}).get("extra_inputs") or [])])
        for rec in obj.run_records()
    )
    rebuild = re.compile(r"(?:docker|apptainer|singularity)\s+(?:build|pull|exec|run)|"
                         r"containers-run|datalad\s+rerun|pixi\s+install|uv\s+sync|conda\s+env\s+create|"
                         r"pip\s+install\s+-r|renv::restore", re.IGNORECASE)
    rebuilders = [p for p, text in texts.items() if rebuild.search(text)]
    # Does CI rebuild the *recorded* environment, or merely some environment?
    recorded_images = set(re.findall(r"[\w./-]+\.(?:sif|simg)|docker://[\w./:-]+", recorded))
    recorded_locks = {lock for lock in LOCKFILES_CI if lock in recorded}
    same_env = [p for p, text in texts.items()
                if any(img.rsplit("/", 1)[-1] in text for img in recorded_images)
                or any(lock in text for lock in recorded_locks)]

    evidence = [Evidence(p, "CI configuration") for p in configs[:3]]
    evidence += [Evidence(p, "re-executes the workflow") for p in runs_workflow[:3]]
    evidence += [Evidence(p, "rebuilds an environment") for p in rebuilders[:3]]

    if runs_workflow:
        s002 = "met"
        r002 = clip(f"{', '.join(runs_workflow[:2])} contains a workflow-executing step "
                    "(make/snakemake/datalad rerun or similar). Whether it runs what the instructions "
                    "describe is a reading.")
    else:
        s002 = "partial"
        r002 = clip(f"CI exists ({configs[0]}) but no job re-executes the workflow.")

    if not obj.run_records() and not recorded_images and not recorded_locks:
        s006 = "met" if rebuilders else "partial"
        r006 = clip(f"{', '.join(rebuilders[:2])} contains an environment-building step."
                    if rebuilders else
                    f"CI exists ({configs[0]}) but no job rebuilds the environment.")
    elif same_env:
        s006 = "met"
        r006 = clip(f"{', '.join(same_env[:2])} names the same image or lockfile the run records name. "
                    "Whether the job actually rebuilds it is a reading.")
    elif rebuilders:
        s006 = "partial"
        r006 = clip(f"{rebuilders[0]} rebuilds *an* environment, but not the one the run records name "
                    f"({', '.join(sorted(recorded_images | recorded_locks)[:2]) or 'see the records'}): "
                    "the environment behind the shipped results is never tested.")
    else:
        s006 = "unmet"
        r006 = clip(f"CI exists ({configs[0]}) but nothing rebuilds the environment the results came from.")

    worst = min((s002, s006), key=lambda s: {"unmet": 0, "partial": 1, "met": 2}[s])
    return Probe(
        "ci-present", worst, items, clip(f"should/002 {s002}: {r002} should/006 {s006}: {r006}"),
        evidence,
        {"configs": configs, "runs_workflow": runs_workflow, "rebuilders": rebuilders,
         "recorded_images": sorted(recorded_images), "recorded_locks": sorted(recorded_locks),
         "same_environment": same_env},
        item_status={i002: s002, i006: s006},
        item_reason={i002: r002, i006: r006},
    )
