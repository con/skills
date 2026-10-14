#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Pick R1's subjects deterministically, so every arm and repeat sees the same ten.

    select_subjects.py <path to a ds007116 clone> [-n 10]

Of the subjects that have a ses-1 `rec-normrefaced` T1w, a ses-1 age, and a
shipped FreeSurfer `qc.tsv` to compare against, sort by age (ties by subject id)
and take ranks round(i*(n-1)/(N-1)). Needs only `git ls-files` and the tracked
`sessions.tsv` files — no annexed content, so it runs on a bare clone.
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import re
import subprocess
import sys

T1 = re.compile(r"(sub-[^/]+)/ses-1/anat/\1_ses-1_rec-normrefaced_run-01_T1w\.nii\.gz$")
QC = re.compile(r"derivatives/freesurfer-post/(sub-[^/]+)/\1_ses-1_desc-FreeSurfer_qc\.tsv$")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dataset", type=pathlib.Path)
    ap.add_argument("-n", "--number", type=int, default=10)
    ap.add_argument("--tsv", action="store_true", help="subject<TAB>age<TAB>t1<TAB>qc")
    args = ap.parse_args(argv)

    root = args.dataset.resolve()
    tracked = subprocess.run(["git", "ls-files"], cwd=str(root),
                             capture_output=True, text=True).stdout.splitlines()
    t1s = {m.group(1): p for p in tracked if (m := T1.match(p))}
    qcs = {m.group(1): p for p in tracked if (m := QC.match(p))}

    candidates = []
    for sub, t1 in sorted(t1s.items()):
        if sub not in qcs:
            continue
        sessions = root / sub / f"{sub}_sessions.tsv"
        if not sessions.exists():
            continue
        with sessions.open() as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                if row.get("session_id") == "ses-1" and (row.get("age") or "n/a") not in ("", "n/a"):
                    candidates.append((float(row["age"]), sub, t1, qcs[sub]))
                    break
    candidates.sort(key=lambda c: (c[0], c[1]))
    n, N = len(candidates), args.number
    if n < N:
        print(f"error: only {n} candidates, need {N}", file=sys.stderr)
        return 1
    picks = [candidates[round(i * (n - 1) / (N - 1))] for i in range(N)]

    if args.tsv:
        for age, sub, t1, qc in picks:
            print(f"{sub}\t{age}\t{t1}\t{qc}")
    else:
        print(f"{n} candidates with a ses-1 T1w, a ses-1 age and a shipped qc.tsv; {N} selected:")
        for age, sub, t1, _ in picks:
            print(f"  {sub:<14} age {age:5.2f}  {t1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
