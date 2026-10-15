#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Science oracle for R1: did the run actually compute brain masks, and are they right?

    check_r1.py <object> [--dataset PATH] [--min-subjects 10]
                [--ratio-min 0.85] [--ratio-max 1.20] [-o oracle.json]

Three questions, in order of how easy they are to fake:

1. **Is there a product?** A tracked table outside the input modules with one
   row per subject carrying an age and a volume, for at least `--min-subjects`
   of the subjects the use case names, plus a non-empty figure.
2. **Did it compute, or copy?** From R1 on, the shipped FreeSurfer derivatives
   are the *oracle*, not an allowed result. A volume column byte-equal to
   `mask_maskvol`, or a product file byte-identical to a shipped one, is the R0
   shortcut taken at the wrong rung and fails here.
3. **Are the numbers plausible?** Each computed volume within
   [`--ratio-min`, `--ratio-max`] of that subject's shipped `mask_maskvol`.
   Ratios, not absolutes: a legitimate tool with a different mask definition
   still passes (SynthStrip and BET agree to 0.24 % and sit 3.4 % above
   `mask_maskvol`; `brainseg_brainsegvol` is 32 % away and is the wrong
   comparator).

It says nothing about STAMPED properties — that is the probes' job — and nothing
about whether the figure looks right.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys

INPUT_DIRS = ("sourcedata", "rawbids", "rawdata", "inputs", "input", "raw", "ds007116")
FIGURES = (".png", ".pdf", ".svg", ".jpg", ".jpeg")
SUBJECT = re.compile(r"(sub-[A-Za-z0-9]+)")
AGE_KEYS = ("age", "age_years", "session_age", "scan_age")
VOLUME_KEYS = ("volume", "vol", "mask", "brain", "size")
NOT_VOLUME = ("ratio", "age", "etiv_ratio")


def tracked(root: pathlib.Path) -> list[str]:
    return subprocess.run(["git", "ls-files"], cwd=str(root),
                          capture_output=True, text=True).stdout.splitlines()


def shipped_mask_volumes(dataset: pathlib.Path) -> dict[str, float]:
    """subject -> mask_maskvol from the dataset's own FreeSurfer tables."""
    out: dict[str, float] = {}
    for qc in sorted(dataset.glob("derivatives/freesurfer-post/*/*_ses-1_desc-FreeSurfer_qc.tsv")):
        m = SUBJECT.search(qc.name)
        if not m:
            continue
        try:
            with qc.open() as fh:
                row = next(csv.DictReader(fh, delimiter="\t"), None)
        except OSError:
            continue
        if row and row.get("mask_maskvol"):
            try:
                out[m.group(1)] = float(row["mask_maskvol"])
            except ValueError:
                pass
    return out


def _is_input(path: str) -> bool:
    return any(path.startswith(d + "/") or f"/{d}/" in path for d in INPUT_DIRS)


def _volume_column(fields: list[str]) -> str | None:
    for name in fields:
        low = name.lower()
        if any(k in low for k in VOLUME_KEYS) and not any(b in low for b in NOT_VOLUME):
            return name
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("object", type=pathlib.Path)
    ap.add_argument("--dataset", type=pathlib.Path,
                    help="a ds007116 clone with the shipped qc.tsv files (default: the object's own input module)")
    ap.add_argument("--min-subjects", type=int, default=10)
    ap.add_argument("--ratio-min", type=float, default=0.90)
    ap.add_argument("--ratio-max", type=float, default=1.34)
    ap.add_argument("-o", "--output", type=pathlib.Path)
    args = ap.parse_args(argv)

    root = args.object.resolve()
    paths = tracked(root)
    findings: list[str] = []
    report: dict = {"object": str(root)}

    dataset = args.dataset
    if dataset is None:
        for path in paths:
            for d in INPUT_DIRS:
                if path == d or path.startswith(d + "/"):
                    candidate = root / d
                    if (candidate / "derivatives").is_dir():
                        dataset = candidate
                        break
            if dataset:
                break
    if dataset is None or not dataset.exists():
        report.update(status="not-checked",
                      reason="No ds007116 clone to compare against; pass --dataset.")
        return _finish(report, args)
    shipped = shipped_mask_volumes(dataset.resolve())
    report["comparator_subjects"] = len(shipped)
    if not shipped:
        # Without the comparator every later check silently passes: no exact
        # matches, no ratios, no out-of-band values, and the run would be
        # declared `met` on the strength of a table nobody checked. In a real
        # clone this means the qc.tsv content was never fetched.
        report.update(status="not-checked",
                      reason=(f"{dataset} carries no mask_maskvol values (annexed content not "
                              "fetched?), so nothing can be compared; the product was not judged."))
        return _finish(report, args)

    # (1) the product
    tables = [p for p in paths if p.endswith((".tsv", ".csv")) and not _is_input(p)]
    figures = [p for p in paths if p.endswith(FIGURES) and not _is_input(p)
               and (root / p).exists() and (root / p).stat().st_size > 0]
    best: dict | None = None
    for relpath in tables:
        try:
            with (root / relpath).open(newline="", errors="replace") as fh:
                delim = "\t" if relpath.endswith(".tsv") else ","
                reader = csv.DictReader(fh, delimiter=delim)
                rows = list(reader)
                fields = list(reader.fieldnames or [])
        except (OSError, csv.Error):
            continue
        vol_key = _volume_column(fields)
        age_key = next((f for f in fields if f.lower() in AGE_KEYS or "age" in f.lower()), None)
        if not vol_key:
            continue
        measured: dict[str, float] = {}
        ages: dict[str, float] = {}
        for row in rows:
            blob = " ".join(str(v) for v in row.values() if v)
            m = SUBJECT.search(blob)
            if not m:
                continue
            try:
                measured[m.group(1)] = float(row[vol_key])
            except (TypeError, ValueError):
                continue
            if age_key:
                try:
                    ages[m.group(1)] = float(row[age_key])
                except (TypeError, ValueError):
                    pass
        if best is None or len(measured) > len(best["measured"]):
            best = {"path": relpath, "volume_column": vol_key, "age_column": age_key,
                    "measured": measured, "ages": ages}

    if best is None or not best["measured"]:
        report.update(status="unmet",
                      reason="No tracked table outside the inputs carries a per-subject volume.")
        report["tables_considered"] = tables
        return _finish(report, args)

    report["product"] = {k: v for k, v in best.items() if k not in ("measured", "ages")}
    report["subjects_measured"] = len(best["measured"])
    report["figures"] = figures
    if len(best["measured"]) < args.min_subjects:
        findings.append(f"only {len(best['measured'])} subjects with a volume (<{args.min_subjects})")
    if not figures:
        findings.append("no non-empty figure outside the input modules")
    if not best["ages"]:
        findings.append("no age column in the product table, so brain size cannot be plotted against age")

    # (2) computed, or copied?
    exact = [s for s, v in best["measured"].items()
             if s in shipped and abs(v - shipped[s]) < 1e-6]
    if exact and len(exact) == len(best["measured"]):
        findings.append(f"every volume equals the shipped mask_maskvol exactly ({len(exact)} subjects): "
                        "the shipped derivative was copied, not computed")
    report["identical_to_shipped"] = exact
    digests = {}
    for relpath in [best["path"]] + figures:
        try:
            digests[relpath] = hashlib.sha256((root / relpath).read_bytes()).hexdigest()
        except OSError:
            pass
    shipped_digests = set()
    for qc in sorted(dataset.glob("derivatives/freesurfer-post/*/*.tsv")):
        try:
            shipped_digests.add(hashlib.sha256(qc.read_bytes()).hexdigest())
        except OSError:
            pass
    copied = [p for p, d in digests.items() if d in shipped_digests]
    if copied:
        findings.append(f"product file is byte-identical to a shipped derivative: {copied[0]}")
    report["byte_identical_products"] = copied

    # (3) plausible?
    ratios = {s: best["measured"][s] / shipped[s]
              for s in best["measured"] if s in shipped and shipped[s]}
    report["ratios"] = {s: round(r, 4) for s, r in sorted(ratios.items())}
    out_of_band = {s: round(r, 4) for s, r in ratios.items()
                   if not (args.ratio_min <= r <= args.ratio_max)}
    report["out_of_band"] = out_of_band
    unmatched = sorted(set(best["measured"]) - set(shipped))
    report["no_comparator"] = unmatched
    if len(ratios) < args.min_subjects:
        findings.append(f"only {len(ratios)} of {len(best['measured'])} volumes have a shipped "
                        f"mask_maskvol to compare against (<{args.min_subjects}): "
                        f"no comparator for {', '.join(unmatched[:5]) or 'some subjects'}")
    if out_of_band:
        worst = max(out_of_band.items(), key=lambda kv: abs(kv[1] - 1))
        findings.append(f"{len(out_of_band)} volume(s) outside [{args.ratio_min}, {args.ratio_max}] of the "
                        f"shipped mask_maskvol, worst {worst[0]} at {worst[1]}")
    if ratios:
        mean = sum(ratios.values()) / len(ratios)
        report["ratio_mean"] = round(mean, 4)
        report["ratio_spread"] = [round(min(ratios.values()), 4), round(max(ratios.values()), 4)]
    if best["ages"] and len(best["ages"]) >= 3:
        xs = [best["ages"][s] for s in best["ages"] if s in best["measured"]]
        ys = [best["measured"][s] for s in best["ages"] if s in best["measured"]]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        if sxx > 0 and syy > 0:
            report["correlation_age_volume"] = round(
                sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy), 3)

    report["findings"] = findings
    if not findings:
        report.update(status="met",
                      reason=(f"{len(best['measured'])} subjects computed, all within "
                              f"[{args.ratio_min}, {args.ratio_max}] of the shipped mask_maskvol "
                              f"(mean ratio {report.get('ratio_mean')}), figure present"))
    else:
        report.update(status="partial" if len(best["measured"]) else "unmet", reason="; ".join(findings))
    return _finish(report, args)


def _finish(report: dict, args) -> int:
    out = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(out)
        print(f"{report['status']}: {report['reason']}")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
