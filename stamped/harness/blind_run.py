#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Prepare a blind subagent run, and diff what comes back.

The core test of a skill is a fresh subagent given the skill snapshot and a
concrete scope, and nothing else (``AGENTS.md``, "Test a skill by handing it to
an independent subagent"; ``docs/stamped/PLAN.md`` §6.2).  This script is that
pattern as an artifact, so the isolation clauses cannot be forgotten one run at
a time.

    blind_run.py prepare --skill assess-alignment-with-stamped-principles \
        --object /path/to/a/clone --workdir /scratch/blind-1
    blind_run.py prepare --skill create-stamped-project \
        --prompt-file evals/stamped/use-cases/r0-freesurfer-plot/prompt.md \
        --workdir /scratch/blind-2 --explicit

`prepare` snapshots the skill and its conventions sibling outside the
repository, writes the subagent prompt with the scope and the isolation rules
filled in, and prints it: the orchestrating session pastes that into its
subagent call.  It deliberately does not spawn the agent — the session that
owns the conversation does that, and keeping the two apart is what lets the
same prompt be replayed by hand, on another model, or on another day.

    blind_run.py compare <candidate-response.json> <reference-response.json>

`compare` is the other half: a per-item diff of two responses, so a blind run's
31 verdicts can be read against the reference answer in one table.  Every
difference needs a classification from §6.8 — skill wording, missing artifact,
harness fault, model limit, or a defect in the reference — and only the first
two change the skill.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
REPO = EVALS.parent.parent
CONVENTIONS = "stamped-conventions"

PROMPT = """You are running a skill. Treat this as a normal user request.

The skill `{skill}` is installed (not as a slash command, so read it from disk) at:

    {skill_md}

Its sibling `{conventions}` skill is installed next to it in the same directory, so the
relative paths `../{conventions}/...` that the SKILL.md refers to resolve.

**Your task:** {task}

Read the SKILL.md and follow its procedure, exactly as written, including reading the
conventions files it tells you to read.

Operating constraints for this run:

1. **Write your outputs into** `{outdir}/` — whatever the skill says it produces. Do not
   write anything into the target you are working on.
2. **The user is not available to answer questions.** Where the skill asks you to settle
   something with the user, state it as an explicit, labelled assumption in your output,
   as the skill directs.
3. **Do NOT read or search `{repo}`**, except the two paths this prompt names — the
   target above and the snapshot below, which may happen to live under it in an ignored
   scratch area. Everything else under that path is off-limits for this run, including any
   reference answer, plan document or earlier report. Your conclusions must come from the
   target itself plus the skill's own instructions and scripts under `{snapshot}`. (This
   is a blind run: a reference answer exists and comparing against it is the point, so
   seeing it would destroy the test.)
4. {forbidden}
5. Network access is available if you need it, but `gh` is not authenticated.

**What to return as your final message** (a machine-read return value, keep it compact):

- The per-item result table the skill's output format calls for: item id, status, source
  (which probe, or judgement), and the first dozen words of your reason.
- The verdict counts, with their denominators.
- Up to 5 bullets: anything in the SKILL.md or the conventions files that was ambiguous,
  missing, contradictory, or that slowed you down — **be specific and critical, quoting
  the wording at fault**. This is the most valuable part of your return: the skill is
  under development and your friction is the data.
- Any place where you disagreed with a script's verdict and overrode it, and why.
"""

DEFAULT_FORBIDDEN = (
    "Do not run the target's pipeline, and do not attempt any check the skill marks as "
    "expensive; handle those the way the skill says to handle a check you cannot run."
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, text=True).stdout.strip()


def prepare(args: argparse.Namespace) -> int:
    skill_dir = REPO / args.skill
    if not (skill_dir / "SKILL.md").exists():
        print(f"error: {skill_dir}/SKILL.md not found", file=sys.stderr)
        return 2
    if not args.object and not args.prompt_file and not args.prompt:
        print("error: a blind run needs a scope: --object, --prompt or --prompt-file", file=sys.stderr)
        return 2

    workdir = args.workdir.resolve()
    snapshot = workdir / "snapshot"
    outdir = workdir / "out"
    if snapshot.exists():
        shutil.rmtree(snapshot)
    snapshot.mkdir(parents=True)
    outdir.mkdir(parents=True, exist_ok=True)
    for name in (args.skill, CONVENTIONS):
        source = REPO / name
        if not source.is_dir():
            print(f"error: {source} is missing; the snapshot must carry the conventions skill too",
                  file=sys.stderr)
            return 2
        shutil.copytree(source, snapshot / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    prompt_text = args.prompt or (args.prompt_file.read_text().strip() if args.prompt_file else "")
    task = f"/{args.skill}" if args.explicit or not prompt_text else ""
    if args.object:
        task = f"{task} {pathlib.Path(args.object).resolve()}".strip()
    if prompt_text:
        task = f"{task}\n\n{prompt_text}".strip() if task else prompt_text
    if not args.explicit and prompt_text and not args.object:
        # implicit condition: the prompt must not name the skill at all
        task = prompt_text

    rendered = PROMPT.format(
        skill=args.skill,
        skill_md=snapshot / args.skill / "SKILL.md",
        conventions=CONVENTIONS,
        task=task,
        outdir=outdir,
        repo=REPO,
        snapshot=snapshot,
        forbidden=args.forbid or DEFAULT_FORBIDDEN,
    )
    (workdir / "prompt.md").write_text(rendered)
    meta = {
        "skill": args.skill,
        "skill_commit": git("rev-parse", "HEAD"),
        "skill_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "condition": "skill-explicit" if args.explicit or args.object else "skill-implicit",
        "scope": {"object": str(pathlib.Path(args.object).resolve()) if args.object else None,
                  "prompt": prompt_text or None},
        "snapshot": str(snapshot),
        "outdir": str(outdir),
        "prepared_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    (workdir / "run.json").write_text(json.dumps(meta, indent=2) + "\n")

    if meta["dirty"]:
        print("warning: con/skills has uncommitted changes, so this run is not reproducible "
              "from the recorded commit alone\n", file=sys.stderr)
    print(f"snapshot: {snapshot}")
    print(f"outputs:  {outdir}")
    print(f"metadata: {workdir / 'run.json'}")
    print(f"prompt:   {workdir / 'prompt.md'}\n")
    print("--- paste the following to a fresh subagent ---\n")
    print(rendered)
    return 0


def _load(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text())
    return data.get("responses") or {}


def compare(args: argparse.Namespace) -> int:
    candidate = _load(args.candidate)
    reference = _load(args.reference)
    ids = sorted(set(candidate) | set(reference))
    rows, agree, differ, missing = [], 0, 0, 0
    for item in ids:
        this = candidate.get(item) or {}
        that = reference.get(item) or {}
        a, b = this.get("status", "(absent)"), that.get("status", "(absent)")
        if "(absent)" in (a, b):
            missing += 1
        elif a == b:
            agree += 1
            continue  # only differences are worth a row
        else:
            differ += 1
        rows.append((item, a, b, this.get("source", ""), that.get("source", ""),
                     (this.get("reason") or "")[:90], (that.get("reason") or "")[:90]))

    print(f"items: {len(ids)} · agree {agree} · differ {differ} · missing on one side {missing}\n")
    if rows:
        print(f"{'item':<34} {'candidate':<15} {'reference':<15} source (candidate / reference)")
        for item, a, b, sa, sb, ra, rb in rows:
            print(f"{item.split(':')[-1]:<34} {a:<15} {b:<15} {sa} / {sb}")
            print(f"    candidate: {ra}")
            print(f"    reference: {rb}")
        print("\nClassify every row above as one of (PLAN.md §6.8):")
        print("  skill wording · missing artifact · harness fault · model limit · reference defect")
        print("Only the first two change the skill.")
    else:
        print("no per-item differences")
    if args.output:
        args.output.write_text(json.dumps(
            {"agree": agree, "differ": differ, "missing": missing,
             "rows": [dict(zip(("item", "candidate", "reference", "candidate_source",
                                "reference_source", "candidate_reason", "reference_reason"), r))
                      for r in rows]}, indent=2) + "\n")
        print(f"\nwrote {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare", help="snapshot a skill and render the subagent prompt")
    p.add_argument("--skill", required=True, help="skill directory name in this repository")
    p.add_argument("--workdir", type=pathlib.Path, required=True)
    p.add_argument("--object", help="scope: a path or repository the skill should work on")
    p.add_argument("--prompt", help="scope: a PROMPT, inline")
    p.add_argument("--prompt-file", type=pathlib.Path, help="scope: a PROMPT, from a file")
    p.add_argument("--explicit", action="store_true",
                   help="name the skill in the task (otherwise the prompt must trigger it on its own)")
    p.add_argument("--forbid", help="replace the default 'do not run the pipeline' clause")

    c = sub.add_parser("compare", help="per-item diff of two response JSONs")
    c.add_argument("candidate", type=pathlib.Path)
    c.add_argument("reference", type=pathlib.Path)
    c.add_argument("-o", "--output", type=pathlib.Path)

    args = ap.parse_args(argv)
    return prepare(args) if args.cmd == "prepare" else compare(args)


if __name__ == "__main__":
    sys.exit(main())
