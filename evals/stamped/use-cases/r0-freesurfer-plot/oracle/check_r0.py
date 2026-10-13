#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Science oracle for R0: did the run actually produce the asked-for product?

    check_r0.py <object> [--min-sessions 50] [--forbid-shipped-as-result] [-o oracle.json]

Finds the produced table by looking for a tracked TSV/CSV outside the input
modules that carries an age column and a volume column, and checks the values.
It says nothing about STAMPED properties — that is the probes' job — and
nothing about whether the figure looks right.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import subprocess
import sys

AGE_KEYS = ("age", "age_years", "session_age", "age_at_scan", "scan_age")
VOLUME_KEYS = ("brain", "volume", "etiv", "brainseg", "tiv", "icv", "brainvol")
RATIO_KEYS = ("ratio", "gm_wm", "gmwm", "gm/wm")
INPUT_DIRS = ("sourcedata/", "rawbids/", "inputs/", "input/", "ds0")
FIGURE_SUFFIXES = (".png", ".pdf", ".svg", ".jpg", ".jpeg")


def tracked(root: pathlib.Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=str(root), capture_output=True, text=True)
    return [p for p in out.stdout.split("\0") if p]


def _match(fieldnames: list[str], keys: tuple[str, ...]) -> str | None:
    for name in fieldnames:
        lowered = name.lower()
        if any(key in lowered for key in keys):
            return name
    return None


def _read_table(path: pathlib.Path) -> tuple[list[dict], list[str]]:
    delimiter = "\t" if path.suffix == ".tsv" else ","
    with path.open(newline="", errors="replace") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        rows = [row for row in reader]
        return rows, list(reader.fieldnames or [])


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("object", type=pathlib.Path)
    ap.add_argument("--min-sessions", type=int, default=50)
    ap.add_argument("--forbid-shipped-as-result", action="store_true",
                    help="fail if the product is a copy of a file from an input module (R1 and up)")
    ap.add_argument("-o", "--output", type=pathlib.Path)
    args = ap.parse_args(argv)

    root = args.object.resolve()
    findings: list[str] = []
    paths = tracked(root)
    tables = [
        p for p in paths
        if p.endswith((".tsv", ".csv")) and not any(p.startswith(d) or f"/{d}" in p for d in INPUT_DIRS)
    ]
    figures = [
        p for p in paths
        if p.endswith(FIGURE_SUFFIXES) and not any(p.startswith(d) for d in INPUT_DIRS)
        and (root / p).exists() and (root / p).stat().st_size > 0
    ]

    best: dict | None = None
    for relpath in tables:
        try:
            rows, fields = _read_table(root / relpath)
        except (OSError, csv.Error):
            continue
        age_key = _match(fields, AGE_KEYS)
        vol_key = _match(fields, VOLUME_KEYS)
        if not age_key or not vol_key:
            continue
        pairs = []
        for row in rows:
            try:
                age, volume = float(row[age_key]), float(row[vol_key])
            except (TypeError, ValueError):
                continue
            pairs.append((age, volume))
        if best is None or len(pairs) > len(best["pairs"]):
            best = {"path": relpath, "age_key": age_key, "volume_key": vol_key,
                    "ratio_key": _match(fields, RATIO_KEYS), "rows": len(rows), "pairs": pairs}

    report: dict = {
        "object": str(root),
        "tables_considered": tables,
        "figures": figures,
        "product": {k: v for k, v in (best or {}).items() if k != "pairs"},
    }
    if best is None:
        report.update(status="unmet", reason="No tracked table carries both an age and a volume column.")
        findings.append("no product table")
    else:
        ages = [a for a, _ in best["pairs"]]
        volumes = [v for _, v in best["pairs"]]
        report["sessions"] = len(best["pairs"])
        report["age_range"] = [min(ages), max(ages)] if ages else None
        report["correlation_age_volume"] = _pearson(ages, volumes)
        if len(best["pairs"]) < args.min_sessions:
            findings.append(f"only {len(best['pairs'])} sessions with age and volume (<{args.min_sessions})")
        if ages and not (7.5 <= min(ages) and max(ages) <= 21.5):
            findings.append(f"ages {min(ages)}–{max(ages)} fall outside ds007116's 8–21 years")
        correlation = report["correlation_age_volume"]
        if correlation is not None and correlation <= 0:
            findings.append(f"brain volume does not grow with age (r={correlation:.2f})")
        if not best["ratio_key"]:
            findings.append("no GM/WM ratio column in the product table")
        if not figures:
            findings.append("no non-empty figure outside the input modules")
        if args.forbid_shipped_as_result:
            shipped = [p for p in paths if any(p.startswith(d) for d in INPUT_DIRS) and p.endswith((".tsv", ".csv"))]
            product = (root / best["path"]).read_bytes() if (root / best["path"]).exists() else b""
            for candidate in shipped:
                if (root / candidate).exists() and (root / candidate).read_bytes() == product:
                    findings.append(f"the product is a byte-identical copy of the input {candidate}")
        report.update(
            status="met" if not findings else ("partial" if report["sessions"] else "unmet"),
            reason="; ".join(findings) if findings else
                   f"{report['sessions']} sessions, r(age, volume)={correlation:.2f}, figure present",
        )

    report["findings"] = findings
    out = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(out)
        print(f"{report['status']}: {report['reason']}")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
