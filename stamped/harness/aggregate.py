#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Aggregate grading files into one iteration report.

    aggregate.py <grading.json> [...] [--markdown report.md] [-o aggregate.json]
    aggregate.py --glob '/scratch/stamped/iter-1/**/grading.json'

Every number carries its denominator, results are grouped by condition and
model, and nothing is reduced to a single score.  ``not-checked`` is reported
as its own column: folding it into a failure would be a lie about what was
measured, and folding it into a pass would be worse.
"""

from __future__ import annotations

import argparse
import collections
import glob as globmod
import json
import pathlib
import statistics
import sys

STATUSES = ("met", "partial", "unmet", "not-checked", "not-applicable")


def load(paths: list[pathlib.Path]) -> list[dict]:
    out = []
    for path in paths:
        try:
            out.append(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warning: skipping {path}: {exc}", file=sys.stderr)
    return out


def _rate(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}" + (f" ({100 * numerator / denominator:.0f}%)" if denominator else "")


def aggregate(gradings: list[dict]) -> dict:
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for grading in gradings:
        run = grading.get("run", {})
        cells[(run.get("condition", "unknown"), run.get("model", "unknown"))].append(grading)

    report: dict = {"runs": len(gradings), "cells": {}, "items": {}, "disagreements": []}
    for (condition, model), runs in sorted(cells.items()):
        must_rates = []
        for grading in runs:
            passed, total = (grading["t1"]["must_pass_rate"].split("/") + ["0"])[:2]
            must_rates.append(int(passed) / int(total) if int(total) else 0.0)
        oracle_ok = sum(1 for g in runs if (g.get("oracle") or {}).get("status") == "met")
        oracle_known = sum(1 for g in runs if (g.get("oracle") or {}).get("status") in {"met", "partial", "unmet"})
        process = [g.get("process", {}) for g in runs if g.get("process", {}).get("available")]
        report["cells"][f"{condition} / {model}"] = {
            "runs": len(runs),
            "must_pass_rate_mean": round(statistics.fmean(must_rates), 3) if must_rates else None,
            "must_pass_rate_spread": (
                f"{min(must_rates):.2f}–{max(must_rates):.2f}" if len(must_rates) > 1 else None
            ),
            "must_pass_rates": [g["t1"]["must_pass_rate"] for g in runs],
            "oracle_ok": _rate(oracle_ok, oracle_known) if oracle_known else "0/0 (not checked)",
            "process": {
                "transcripts": f"{len(process)}/{len(runs)}",
                "skill_was_read": _rate(sum(1 for p in process if p.get("skill_was_read")), len(process))
                if process else "0/0",
                "commits_during_run": sum(p.get("counts", {}).get("commit_during_run", 0) for p in process),
                "absolute_home_paths": sum(p.get("counts", {}).get("absolute_home_path", 0) for p in process),
                "questions_asked_median": (
                    statistics.median([p.get("questions_asked", 0) for p in process]) if process else None
                ),
                "output_tokens_median": (
                    statistics.median([p.get("tokens", {}).get("output", 0) for p in process]) if process else None
                ),
            },
        }

    per_item: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for grading in gradings:
        for item, answer in (grading.get("t1", {}).get("items") or {}).items():
            per_item[item][answer["status"]] += 1
        for item, verdicts in (grading.get("t2", {}).get("disagreements_with_t1") or {}).items():
            report["disagreements"].append(
                {"run": grading.get("run", {}).get("object"), "item": item, **verdicts}
            )
    for item, counter in sorted(per_item.items()):
        total = sum(counter.values())
        report["items"][item] = {
            **{status: counter.get(status, 0) for status in STATUSES},
            "n": total,
            "met_rate": _rate(counter.get("met", 0), total),
        }
    return report


def markdown(report: dict) -> str:
    lines = [f"# Iteration report ({report['runs']} runs)", "",
             "## Conditions", "",
             "| condition / model | runs | MUST pass (mean) | spread | oracle | skill read | commits during run |",
             "|---|---|---|---|---|---|---|"]
    for cell, data in report["cells"].items():
        process = data["process"]
        lines.append(
            f"| {cell} | {data['runs']} | "
            f"{data['must_pass_rate_mean'] if data['must_pass_rate_mean'] is not None else '—'} | "
            f"{data['must_pass_rate_spread'] or '—'} | {data['oracle_ok']} | "
            f"{process['skill_was_read']} | {process['commits_during_run']} |"
        )
    lines += ["", "## Per item", "", "| item | met | partial | unmet | not-checked | n/a | n |", "|---|---|---|---|---|---|---|"]
    for item, data in report["items"].items():
        lines.append(
            f"| {item.split(':')[-1]} | {data['met']} | {data['partial']} | {data['unmet']} | "
            f"{data['not-checked']} | {data['not-applicable']} | {data['n']} |"
        )
    if report["disagreements"]:
        lines += ["", "## T1 / T2 disagreements (for the human to settle)", ""]
        for row in report["disagreements"]:
            lines.append(f"- `{row['item']}`: probes say **{row['t1']}**, the blind assessor says **{row['t2']}** — {row['run']}")
    lines += ["", "Rates are numerator/denominator; `not-checked` is never folded into a failure."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gradings", nargs="*", type=pathlib.Path)
    ap.add_argument("--glob", dest="pattern", help="glob for grading files (recursive)")
    ap.add_argument("-o", "--output", type=pathlib.Path)
    ap.add_argument("--markdown", type=pathlib.Path)
    args = ap.parse_args(argv)

    paths = list(args.gradings)
    if args.pattern:
        paths += [pathlib.Path(p) for p in globmod.glob(args.pattern, recursive=True)]
    if not paths:
        print("error: no grading files given", file=sys.stderr)
        return 2
    report = aggregate(load(paths))
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {args.output}")
    if args.markdown:
        args.markdown.write_text(markdown(report))
        print(f"wrote {args.markdown}")
    if not args.output and not args.markdown:
        sys.stdout.write(markdown(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
