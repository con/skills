#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""The `fresh-rerun` probe: clone the published object elsewhere and re-run it.

This is the one probe that tests A.1, P.1-P.3, E.1, D.1 and should/004 together,
because it is the only one that leaves the machine the results were made on.

    fresh_rerun.py --url <published url> [--entry 'make all'] [--in-container IMAGE]
                   [--outputs 'results/*.tsv' 'figures/*.png'] [--rtol 1e-6]
                   [--workdir DIR] [-o fresh-rerun.json]

It never touches the original object: everything happens in a temporary clone
(kept under --workdir when given, so the evidence survives the probe).

Steps
-----
1. clone from the published location (``datalad clone`` when available, else
   ``git clone``) — a clone that fails is already D.1 ``unmet``;
2. install the modules without content (``datalad get -n -r``) and fetch only
   what fits under ``--max-get-gb``: an unbounded ``datalad get -r .`` pulled
   **87 GB** of container images on its first real R1 object before it was
   stopped, because a module of ``///repronim/containers`` carries every image
   the registry knows. The entry point fetches its own declared inputs;
3. record the checksums the clone *shipped* for the output files;
4. run the entry point, in a container when ``--in-container`` is given;
5. compare: identical checksums, or numeric agreement within ``--rtol`` for
   tables, and report anything else as a difference for a human to look at.

Exit code 0 means the probe ran, not that the object reproduced; read
``status`` in the JSON.
"""

from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ITEMS = [
    "stamped-checklist:must/007",
    "stamped-checklist:must/008",
    "stamped-checklist:must/015",
    "stamped-checklist:must/017",
    "stamped-checklist:should/004",
    "stamped-checklist:should/006",
]
TABLE_SUFFIXES = (".tsv", ".csv", ".txt")


def _annexed_bytes_missing(clone: pathlib.Path) -> int:
    """Bytes of annexed content not here yet, this dataset and its modules.

    Asked *before* fetching, because the honest answer to "how much is this
    about to download" is the one number nobody had: the first real R1 rerun
    pulled 87 GB of container images and had to be killed by hand.
    """
    total = 0
    for gitdir in [clone, *sorted(p.parent for p in clone.rglob(".git") if p.parent != clone)]:
        proc = subprocess.run(
            ["git", "annex", "find", "--not", "--in", "here", "--format=${bytesize}\n"],
            cwd=str(gitdir), capture_output=True, text=True)
        for line in proc.stdout.split():
            try:
                total += int(line)
            except ValueError:
                continue
    return total


def _run(cmd: list[str], cwd: pathlib.Path | None = None, timeout: int = 7200) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                          errors="replace", timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr)[-8000:]


def _sha256(path: pathlib.Path) -> str | None:
    try:
        if path.is_symlink() and not path.exists():
            return None  # annexed content not present
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _collect(root: pathlib.Path, patterns: list[str]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for pattern in patterns:
        for match in sorted(glob.glob(str(root / pattern), recursive=True)):
            path = pathlib.Path(match)
            if path.is_file() or path.is_symlink():
                out[str(path.relative_to(root))] = _sha256(path)
    return out


def _numeric_close(a: pathlib.Path, b: pathlib.Path, rtol: float) -> bool | None:
    """True/False when both files parse as tables of numbers, None when they do not."""
    def parse(path: pathlib.Path) -> list[list[float]] | None:
        rows = []
        try:
            text = path.read_text(errors="replace")
        except OSError:
            return None
        for line in text.splitlines():
            fields = line.replace("\t", ",").split(",")
            row = []
            for field in fields:
                field = field.strip()
                try:
                    row.append(float(field))
                except ValueError:
                    row.append(float("nan")) if field.lower() in {"nan", "na", ""} else row.append(None)
            rows.append(row)
        return rows

    rows_a, rows_b = parse(a), parse(b)
    if rows_a is None or rows_b is None or len(rows_a) != len(rows_b):
        return None
    for ra, rb in zip(rows_a, rows_b):
        if len(ra) != len(rb):
            return None
        for va, vb in zip(ra, rb):
            if va is None or vb is None:
                continue  # a header or a label; compared by checksum instead
            if va != va and vb != vb:  # both NaN
                continue
            if abs(va - vb) > rtol * max(1.0, abs(va), abs(vb)):
                return False
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="published location to clone from (what D.1 promises)")
    source.add_argument("--path", help="local path to clone from (indicative only: does not test D.1)")
    ap.add_argument("--entry", help="command to run (default: datalad rerun, else make)")
    ap.add_argument("--outputs", nargs="+", default=["**/*.tsv", "**/*.csv", "**/*.png", "**/*.pdf"],
                    help="glob(s) naming the outputs to compare")
    ap.add_argument("--in-container", dest="container", help="apptainer/singularity image to run --entry inside")
    ap.add_argument("--rtol", type=float, default=1e-6, help="relative tolerance for tables")
    ap.add_argument("--workdir", type=pathlib.Path, help="keep the clone here instead of a temp dir")
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--max-get-gb", type=float, default=5.0,
                    help="skip the up-front content fetch when it would exceed this (default 5 GiB); "
                         "a module of a container registry can be hundreds of GB")
    ap.add_argument("-o", "--output", type=pathlib.Path)
    args = ap.parse_args(argv)

    base = args.workdir or pathlib.Path(tempfile.mkdtemp(prefix="stamped-fresh-rerun-"))
    base.mkdir(parents=True, exist_ok=True)
    clone = base / "clone"
    report: dict = {
        "probe": "fresh-rerun",
        "items": ITEMS,
        "source": args.url or args.path,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "host": {"uname": " ".join(_run(["uname", "-a"])[1].split()[:6]),
                 "datalad": bool(shutil.which("datalad")),
                 "container_runtime": shutil.which("apptainer") or shutil.which("singularity")},
        "steps": [],
    }

    def step(name: str, code: int, log: str) -> None:
        report["steps"].append({"step": name, "returncode": code, "log": log[-4000:]})

    cloner = ["datalad", "clone"] if shutil.which("datalad") else ["git", "clone"]
    code, log = _run([*cloner, args.url or args.path, str(clone)], timeout=args.timeout)
    step(" ".join(cloner), code, log)
    if code != 0:
        report.update(status="unmet", reason=f"clone from {args.url or args.path} failed: nothing to reproduce.")
        return _finish(report, args)

    get_failed = False
    if shutil.which("datalad"):
        # Modules first, without content: a rerun needs the submodules present
        # to resolve paths, and that costs nothing.
        code, log = _run(["datalad", "get", "-n", "-r", "."], cwd=clone, timeout=args.timeout)
        step("datalad get -n -r .", code, log)
        get_failed = code != 0
        pending = _annexed_bytes_missing(clone)
        report["content_to_fetch_bytes"] = pending
        budget = int(args.max_get_gb * 1024 ** 3)
        if pending and pending <= budget:
            code, log = _run(["datalad", "get", "-r", "-J4", "."], cwd=clone, timeout=args.timeout)
            step(f"datalad get -r . ({pending / 1024 ** 3:.1f} GiB)", code, log)
            get_failed = get_failed or code != 0
        elif pending:
            step(f"skipped datalad get -r . ({pending / 1024 ** 3:.1f} GiB > "
                 f"--max-get-gb {args.max_get_gb})", 0,
                 "Left to the entry point, which fetches its own declared inputs. "
                 "Raise --max-get-gb to fetch everything up front.")

    before = _collect(clone, args.outputs)
    report["outputs_shipped"] = dict(before)
    # Keep the shipped copies aside: the rerun overwrites them in place, and a
    # comparison has to be against what the object published, not against itself.
    shipped = base / "shipped"
    for path in before:
        target = shipped / path
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(clone / path, target, follow_symlinks=True)
        except OSError:
            pass  # annexed content that is not present; recorded as None above
    if not before:
        report.update(status="not-checked",
                      reason="The clone ships no file matching --outputs, so there is nothing to compare.")
        return _finish(report, args)

    entry = args.entry
    if not entry:
        entry = "datalad rerun" if (clone / ".datalad").is_dir() and shutil.which("datalad") else "make"
    cmd = ["sh", "-c", entry]
    if args.container:
        runtime = report["host"]["container_runtime"]
        if not runtime:
            report.update(status="not-checked", reason="--in-container given but no apptainer/singularity found.")
            return _finish(report, args)
        cmd = [runtime, "exec", "--cleanenv", args.container, "sh", "-c", entry]
    code, log = _run(cmd, cwd=clone, timeout=args.timeout)
    step(f"entry: {entry}", code, log)
    if code != 0:
        report.update(status="unmet",
                      reason=f"The documented entry point failed in a fresh clone: `{entry}` exited {code}.")
        return _finish(report, args)

    after = _collect(clone, args.outputs)
    identical, close, differing, vanished = [], [], [], []
    for path, digest in before.items():
        new = after.get(path)
        if new is None:
            vanished.append(path)
        elif digest is None:
            continue  # content was not available to compare against
        elif new == digest:
            identical.append(path)
        elif path.endswith(TABLE_SUFFIXES) and (shipped / path).exists():
            verdict = _numeric_close(shipped / path, clone / path, args.rtol)
            close.append(path) if verdict else differing.append(path)
        else:
            differing.append(path)

    report["comparison"] = {"identical": identical, "within_tolerance": close,
                            "differing": differing, "missing_after_rerun": vanished}
    total = len(identical) + len(close) + len(differing) + len(vanished)
    if (differing or vanished) and get_failed:
        # A collector failure is not an object defect: the inputs never arrived,
        # so a difference cannot be attributed to the object.
        report.update(
            status="not-checked",
            reason=(f"`datalad get` could not fetch the clone's content, so the rerun ran without its inputs and "
                    f"{len(differing) + len(vanished)} of {total} output(s) differ for that reason. "
                    "Re-run where the input modules are reachable."),
        )
    elif differing or vanished:
        report.update(status="partial" if identical or close else "unmet",
                      reason=(f"{len(differing) + len(vanished)} of {total} output(s) did not come back the same "
                              f"in a fresh clone, e.g. {(differing + vanished)[0]}."))
    else:
        report.update(status="met",
                      reason=f"All {total} compared output(s) reproduced from a fresh clone via `{entry}`.")
    return _finish(report, args)


def _finish(report: dict, args) -> int:
    report["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    out = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(out)
        print(f"{report['status']}: {report['reason']}")
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
