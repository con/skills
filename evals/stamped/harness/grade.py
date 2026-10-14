#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Grade one eval run: T1 probes, the science oracle, and process metrics.

    grade.py <object> --use-case ../use-cases/r0-freesurfer-plot
             [--transcript transcript.jsonl] [--condition skill-explicit]
             [--model …] [--skill-commit …] [-o grading.json]

Three independent sources, kept apart on purpose:

* **T1** — the scripted probes, the same code the assessor skill runs.
* **oracle** — the use case's own science check.
* **process** — what the transcript says the agent *did*, which is not evidence
  about the object but is evidence about the skill.

T2 (a blind run of the assessor over the object) is a separate, model-driven
step; its response JSON is merged in with ``--t2 response.json``.

Numbers are reported with denominators.  A grading file never carries a single
overall score.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
REPO = EVALS.parent.parent
RUN_PROBES = REPO / "assess-alignment-with-stamped-principles" / "scripts" / "run_probes.py"
CONVENTIONS = REPO / "stamped-conventions"

# What the transcript is scanned for; each is a STAMPED invariant from
# stamped-conventions/SKILL.md that a run can be seen to break.
PROCESS_PATTERNS = {
    "commit_during_run": re.compile(r"datalad\s+(?:save|run)\b[\s\S]{0,400}?git\s+commit", re.I),
    "git_commit_calls": re.compile(r"\bgit\s+commit\b"),
    "datalad_run_calls": re.compile(r"\bdatalad\s+(?:containers-)?run\b"),
    "absolute_home_path": re.compile("/" + "home/" + r"[a-z][\w.-]+/|/Users/[A-Za-z][\w.-]+/"),
    "manual_edit_of_derived": re.compile(r"\b(?:sed -i|>\s*)(?:\S*/)?(?:derivatives|results|figures)/\S+"),
    "forced_add": re.compile(r"\bgit\s+add\s+(?:-f|--force)\b"),
}


def _json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:3])}… failed: {proc.stderr.strip()[:500]}")
    return json.loads(proc.stdout)


def t1(obj: pathlib.Path) -> dict:
    payload = _json([sys.executable, str(RUN_PROBES), str(obj), "--quiet"])
    severity = {"unmet": 0, "partial": 1, "not-checked": 2, "not-applicable": 3, "met": 4}
    items: dict[str, dict] = {}
    for result in payload["probes"]:
        for item in result["items"]:
            status = result.get("item_status", {}).get(item, result["status"])
            previous = items.get(item)
            if previous is None or severity[status] < severity[previous["status"]]:
                items[item] = {"status": status, "probe": result["probe"],
                               "reason": result.get("item_reason", {}).get(item, result["reason"])}
    return {"probes": payload["probes"], "items": items, "checklist_version": payload["checklist_version"]}


def oracle(obj: pathlib.Path, use_case: pathlib.Path, extra: list[str]) -> dict | None:
    import yaml

    spec = yaml.safe_load((use_case / "use_case.yaml").read_text())
    script = (spec.get("oracle") or {}).get("script")
    if not script:
        return None
    path = use_case / script
    if not path.exists():
        return {"status": "not-checked", "reason": f"oracle script {script} is missing"}
    proc = subprocess.run([sys.executable, str(path), str(obj), *extra], capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"status": "not-checked", "reason": f"oracle did not return JSON: {proc.stderr.strip()[:200]}"}


def process_metrics(transcript: pathlib.Path | None) -> dict:
    if transcript is None or not transcript.exists():
        return {"available": False,
                "note": "no transcript: process metrics are unknown, which is not the same as zero"}
    commands: list[str] = []
    reads: list[str] = []
    questions = 0
    tokens = {"input": 0, "output": 0}
    turns = 0
    for line in transcript.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = event.get("message") or {}
        usage = message.get("usage") or event.get("usage") or {}
        tokens["input"] += usage.get("input_tokens", 0) or 0
        tokens["output"] += usage.get("output_tokens", 0) or 0
        content = message.get("content")
        if isinstance(content, list):
            turns += 1
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name", "")
                payload = block.get("input") or {}
                if name == "Bash":
                    commands.append(str(payload.get("command", "")))
                elif name in {"Read", "Glob", "Grep"}:
                    reads.append(str(payload.get("file_path") or payload.get("pattern") or ""))
                elif name == "AskUserQuestion":
                    questions += 1
    blob = "\n".join(commands)
    counts = {name: len(pattern.findall(blob)) for name, pattern in PROCESS_PATTERNS.items()}
    skill_reads = [r for r in reads if "stamped" in r.lower() or "SKILL.md" in r]
    return {
        "available": True,
        "turns": turns,
        "bash_calls": len(commands),
        "questions_asked": questions,
        "tokens": tokens,
        "counts": counts,
        # A skill path being present does not show the skill was used; a read of
        # it in the transcript does.
        "skill_files_read": skill_reads[:20],
        "skill_was_read": bool(skill_reads),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("object", type=pathlib.Path)
    ap.add_argument("--use-case", type=pathlib.Path, required=True)
    ap.add_argument("--transcript", type=pathlib.Path)
    ap.add_argument("--t2", type=pathlib.Path, help="response JSON from a blind assessor run")
    ap.add_argument("--condition", default="unknown")
    ap.add_argument("--model", default="unknown")
    ap.add_argument("--skill-commit", default="unknown")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--oracle-arg", action="append", default=[])
    ap.add_argument("-o", "--output", type=pathlib.Path)
    args = ap.parse_args(argv)

    # Never write inside the object being graded: a grading file left in the
    # tree makes the next sweep report must/004 `unmet`, which is the grader
    # accusing the object of the grader's own mess. Found when exactly that
    # happened to an R0 arm.
    obj_root = args.object.resolve()
    if args.output:
        out = args.output.resolve()
        if out == obj_root or obj_root in out.parents:
            redirected = obj_root.parent / f"{obj_root.name}.grading.json"
            print(f"note: {out} is inside the object; writing {redirected} instead "
                  "(a grading file in the tree would dirty it)", file=sys.stderr)
            args.output = redirected

    import yaml

    rubric = yaml.safe_load((args.use_case / "rubric.yaml").read_text())
    scripted_musts = rubric.get("must_items_mechanically_checkable") or []

    t1_result = t1(args.object.resolve())
    oracle_result = oracle(args.object.resolve(), args.use_case, args.oracle_arg)
    process = process_metrics(args.transcript)

    passed = [i for i in scripted_musts if t1_result["items"].get(i, {}).get("status") == "met"]
    failed = [i for i in scripted_musts
              if t1_result["items"].get(i, {}).get("status") in {"unmet", "partial"}]
    unknown = [i for i in scripted_musts if i not in passed and i not in failed]

    t2_items = {}
    if args.t2 and args.t2.exists():
        t2_response = json.loads(args.t2.read_text())
        t2_items = {i: a.get("status") for i, a in (t2_response.get("responses") or {}).items()}
    disagreements = {
        i: {"t1": t1_result["items"][i]["status"], "t2": t2_items[i]}
        for i in t1_result["items"]
        if i in t2_items and t2_items[i] != t1_result["items"][i]["status"]
    }

    grading = {
        "run": {
            "object": str(args.object.resolve()),
            "use_case": rubric.get("use_case"),
            "condition": args.condition,
            "model": args.model,
            "skill_commit": args.skill_commit,
            "repeat": args.repeat,
            "graded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "checklist_version": t1_result["checklist_version"],
        },
        "t1": {
            "items": t1_result["items"],
            "probes": t1_result["probes"],
            "must_pass_rate": f"{len(passed)}/{len(scripted_musts)}",
            "must_passed": passed,
            "must_failed": failed,
            "must_unknown": unknown,
        },
        "t2": {"items": t2_items, "disagreements_with_t1": disagreements},
        "oracle": oracle_result,
        "process": process,
        # skill-creator's shape, so its viewer can open these files too.
        "checks": [
            {"text": f"T1 {item}", "passed": answer["status"] == "met", "evidence": answer["reason"]}
            for item, answer in sorted(t1_result["items"].items())
        ]
        + ([{"text": "science oracle", "passed": oracle_result.get("status") == "met",
             "evidence": oracle_result.get("reason", "")}] if oracle_result else []),
    }

    out = json.dumps(grading, indent=2) + "\n"
    if args.output:
        args.output.write_text(out)
        print(f"MUST (mechanically checkable): {grading['t1']['must_pass_rate']}"
              + (f" · oracle: {oracle_result['status']}" if oracle_result else "")
              + (f" · T1/T2 disagreements: {len(disagreements)}" if t2_items else ""))
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
