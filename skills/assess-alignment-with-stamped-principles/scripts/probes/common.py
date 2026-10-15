# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Shared helpers for the STAMPED probes.

A probe is a deterministic, tool-agnostic check over *committed* state.  It
returns a :class:`Probe` result carrying a status from
``../stamped-conventions/references/verdicts.md``, the checklist items it speaks
to, a reason short enough for the checklist app, and evidence a reader can
open.  A probe never writes to the object it inspects, and it never reports
``met`` without evidence.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import subprocess

REASON_MAX = 250

# Directories whose content is log/record output rather than project source.
LOG_DIRS = ("logs/", ".duct/", ".datalad/environments/")

TEXT_SUFFIXES = {
    ".md", ".rst", ".txt", ".py", ".sh", ".bash", ".zsh", ".r", ".R", ".m",
    ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini", ".tsv", ".csv",
    ".make", ".mk", ".smk", ".nf", ".jl", ".pl", ".rb", ".c", ".h", ".cpp",
    ".js", ".ts", ".html", ".tex", ".bib", ".do", ".sql", ".def", ".env",
}
TEXT_NAMES = {
    "Makefile", "makefile", "GNUmakefile", "Snakefile", "Dockerfile",
    "Singularity", "README", "LICENSE", "CITATION", "config", ".gitmodules",
}


@dataclasses.dataclass
class Evidence:
    uri: str
    description: str
    sha256: str | None = None

    def asdict(self) -> dict:
        return {"uri": self.uri, "description": self.description, "sha256": self.sha256}


@dataclasses.dataclass
class Probe:
    name: str
    status: str  # met | partial | unmet | not-checked | not-applicable
    items: list[str]
    reason: str
    evidence: list[Evidence] = dataclasses.field(default_factory=list)
    details: dict = dataclasses.field(default_factory=dict)
    # One probe can answer two items differently: `entry-point` can find a
    # Makefile that is a clear starting point (must/008) while the README has
    # lost its installation instructions (must/007).  Items absent from this
    # mapping take ``status``.
    item_status: dict = dataclasses.field(default_factory=dict)
    item_reason: dict = dataclasses.field(default_factory=dict)

    def status_of(self, item_id: str) -> str:
        return self.item_status.get(item_id, self.status)

    def reason_of(self, item_id: str) -> str:
        return (self.item_reason.get(item_id) or self.reason)[:REASON_MAX]

    def asdict(self) -> dict:
        return {
            "probe": self.name,
            "status": self.status,
            "items": self.items,
            "reason": self.reason[:REASON_MAX],
            "evidence": [e.asdict() for e in self.evidence],
            "details": self.details,
            "item_status": {i: self.status_of(i) for i in self.items},
            "item_reason": {i: self.reason_of(i) for i in self.items},
        }


class Object:
    """A checked-out research object: a git repository, possibly a DataLad dataset."""

    def __init__(self, root: pathlib.Path) -> None:
        self.root = root.resolve()
        self._cache: dict = {}

    # -- git plumbing --------------------------------------------------------

    def git(self, *args: str, cwd: pathlib.Path | None = None, check: bool = False) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.root),
            capture_output=True,
            text=True,
            errors="replace",
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout

    def git_ok(self, *args: str, cwd: pathlib.Path | None = None) -> bool:
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd or self.root), capture_output=True, text=True
        )
        return proc.returncode == 0

    @property
    def is_git(self) -> bool:
        return (self.root / ".git").exists()

    @property
    def is_datalad(self) -> bool:
        return (self.root / ".datalad").is_dir()

    @property
    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()

    def tracked(self) -> list[str]:
        """Tracked paths, relative to the object root, sorted."""
        if "tracked" not in self._cache:
            out = self.git("ls-files", "-z")
            self._cache["tracked"] = sorted(p for p in out.split("\0") if p)
        return self._cache["tracked"]

    def blobs(self) -> list[tuple[str, int, str]]:
        """(path, size, mode) for every blob in HEAD; size -1 when unknown."""
        if "blobs" not in self._cache:
            rows = []
            for line in self.git("ls-tree", "-r", "-l", "HEAD", "-z").split("\0"):
                if not line.strip():
                    continue
                meta, _, path = line.partition("\t")
                parts = meta.split()
                if len(parts) < 4 or parts[1] != "blob":
                    continue
                mode, _, _, size = parts[0], parts[1], parts[2], parts[3]
                rows.append((path, int(size) if size.isdigit() else -1, mode))
            self._cache["blobs"] = rows
        return self._cache["blobs"]

    def read(self, relpath: str, limit: int = 2_000_000) -> str:
        path = self.root / relpath
        try:
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
        except (OSError, UnicodeError):
            return ""

    def exists(self, relpath: str) -> bool:
        return (self.root / relpath).exists()

    # -- submodules ----------------------------------------------------------

    def submodules(self) -> list[dict]:
        """One entry per .gitmodules record: name, path, url, plus status flags."""
        if "submodules" in self._cache:
            return self._cache["submodules"]
        mods: dict[str, dict] = {}
        if self.exists(".gitmodules"):
            out = self.git("config", "-f", ".gitmodules", "--list", "-z")
            for chunk in out.split("\0"):
                if not chunk or "\n" not in chunk:
                    continue
                key, _, value = chunk.partition("\n")
                if not key.startswith("submodule."):
                    continue
                _, name, field = key.split(".", 2)
                mods.setdefault(name, {"name": name})[field] = value
        for line in self.git("submodule", "status", "--recursive").splitlines():
            if not line.strip():
                continue
            flag = line[0] if line[0] in "+-U " else " "
            rest = line[1:].strip().split()
            if len(rest) < 2:
                continue
            commit, path = rest[0], rest[1]
            for mod in mods.values():
                if mod.get("path") == path:
                    mod["recorded_commit"] = commit
                    mod["initialized"] = flag != "-"
                    mod["differs"] = flag == "+"
                    mod["conflict"] = flag == "U"
        self._cache["submodules"] = list(mods.values())
        return self._cache["submodules"]

    # -- run records ---------------------------------------------------------

    def run_records(self) -> list[dict]:
        """``[DATALAD RUNCMD]`` records in history, parsed.

        Each entry carries ``commit``, ``subject`` and the ``run_info`` JSON
        datalad embeds in the commit message (``cmd``, ``inputs``, ``outputs``,
        ``dsid``, ``extra_inputs``, …).
        """
        if "run_records" in self._cache:
            return self._cache["run_records"]
        sep = "\x1e"
        out = self.git("log", f"--format={sep}%H%n%B", "--grep=\\[DATALAD RUNCMD\\]")
        records = []
        for block in out.split(sep):
            if not block.strip():
                continue
            lines = block.splitlines()
            commit, body = lines[0].strip(), "\n".join(lines[1:])
            subject = lines[1].strip() if len(lines) > 1 else ""
            start = body.find("{")
            info = None
            if start != -1:
                try:
                    info, _ = json.JSONDecoder().raw_decode(body[start:])
                except ValueError:
                    info = None
            records.append({"commit": commit, "subject": subject, "run_info": info, "body": body})
        self._cache["run_records"] = records
        return records


def is_text_path(relpath: str) -> bool:
    path = pathlib.PurePosixPath(relpath)
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES


def in_log_dir(relpath: str) -> bool:
    return any(relpath.startswith(d) or f"/{d}" in relpath for d in LOG_DIRS)


def clip(text: str, limit: int = REASON_MAX) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
