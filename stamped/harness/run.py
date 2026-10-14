#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Yaroslav Halchenko <yaroslav.o.halchenko@dartmouth.edu>
# SPDX-License-Identifier: MIT
"""Set up and launch one eval run in a throwaway sandbox.

    run.py --use-case ../use-cases/r0-freesurfer-plot --condition skill-explicit \
           --workdir /scratch/stamped/iter-1 [--model …] [--repeat 1] [--execute]

Without ``--execute`` it builds the sandbox and prints the command it would
run, which is how to inspect a condition before spending tokens on it.

Conditions (docs/stamped/PLAN.md §6.3)
--------------------------------------
``bare``            the use-case prompt only — the floor
``pointer``         plus ``../conditions/pointer-CLAUDE.md`` as the sandbox's
                    ``CLAUDE.md``/``AGENTS.md`` — today's practice
``skill-implicit``  the skills installed, the prompt not mentioning them
``skill-explicit``  the skills installed and invoked by name

Why a sandbox per run: E.1 applied to our own tests.  The sandbox is a fresh
DataLad dataset (``-c text2git``) when datalad is available, else a git
repository, and the agent's permissions are wide open **inside it only**.
``run.json`` records the condition, the model, the skill commit and the host,
because a run whose provenance is unknown cannot be compared with another.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVALS = HERE.parent
REPO = EVALS.parent.parent
SKILLS = (
    "stamped-conventions",
    "assess-alignment-with-stamped-principles",
    "align-with-stamped-principles",
    "create-stamped-project",
    "create-repronim-stamped-project",
    "do-full-research-loop",
)
CONDITIONS = ("bare", "pointer", "skill-implicit", "skill-explicit")
EXPLICIT_PREFIX = {
    "r0-freesurfer-plot": "/do-full-research-loop ",
}


def sh(cmd: list[str], cwd: pathlib.Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}… failed: {(proc.stderr or proc.stdout).strip()[:600]}")
    return proc


def skill_commit() -> str:
    proc = sh(["git", "rev-parse", "HEAD"], cwd=REPO, check=False)
    return proc.stdout.strip() or "unknown"


def install_skills(sandbox: pathlib.Path, source: pathlib.Path) -> list[str]:
    target = sandbox / ".claude" / "skills"
    target.mkdir(parents=True, exist_ok=True)
    installed = []
    for name in SKILLS:
        src = source / name
        if not (src / "SKILL.md").exists():
            continue
        shutil.copytree(src, target / name, dirs_exist_ok=True)
        installed.append(name)
    return installed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--use-case", type=pathlib.Path, required=True)
    ap.add_argument("--condition", choices=CONDITIONS, required=True)
    ap.add_argument("--workdir", type=pathlib.Path, required=True)
    ap.add_argument("--model", default=os.environ.get("STAMPED_EVAL_MODEL", "default"))
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--skills-from", type=pathlib.Path, default=REPO,
                    help="checkout to install the skills from (default: this repository)")
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--execute", action="store_true", help="actually run the agent")
    args = ap.parse_args(argv)

    use_case = args.use_case.resolve()
    prompt = (use_case / "prompt.md").read_text().strip()
    case_id = use_case.name
    run_id = f"{case_id}--{args.condition}--{args.model}--r{args.repeat}"
    sandbox = args.workdir.resolve() / run_id
    if sandbox.exists():
        print(f"error: {sandbox} exists; remove it or pick another --workdir", file=sys.stderr)
        return 1
    sandbox.parent.mkdir(parents=True, exist_ok=True)

    have_datalad = bool(shutil.which("datalad"))
    if have_datalad:
        sh(["datalad", "create", "-c", "text2git", str(sandbox)])
    else:
        sandbox.mkdir(parents=True)
        sh(["git", "init", "-q", "-b", "main"], cwd=sandbox)

    installed: list[str] = []
    if args.condition.startswith("skill"):
        installed = install_skills(sandbox, args.skills_from.resolve())
    if args.condition == "pointer":
        snippet = (EVALS / "conditions" / "pointer-CLAUDE.md").read_text()
        (sandbox / "CLAUDE.md").write_text(snippet)
        (sandbox / "AGENTS.md").write_text(snippet)

    if installed:
        # The skills are installed for the agent to read, not committed into
        # the object the graders assess: two R0 arms lost MUST items to probes
        # finding host paths and `command -v` checks inside this harness's own
        # copies of the skills.
        gitignore = sandbox / ".gitignore"
        existing = gitignore.read_text() if gitignore.exists() else ""
        if ".claude/" not in existing:
            gitignore.write_text(existing + ".claude/\n")

    task = prompt
    if args.condition == "skill-explicit":
        task = EXPLICIT_PREFIX.get(case_id, "/do-full-research-loop ") + prompt
    (sandbox / "prompt.md").write_text(task + "\n")

    meta = {
        "run_id": run_id,
        "use_case": case_id,
        "condition": args.condition,
        "model": args.model,
        "repeat": args.repeat,
        "skills_installed": installed,
        "skill_commit": skill_commit(),
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "host": {"uname": sh(["uname", "-a"], check=False).stdout.strip(),
                 "datalad": have_datalad,
                 "apptainer": bool(shutil.which("apptainer") or shutil.which("singularity"))},
    }
    (sandbox / "run.json").write_text(json.dumps(meta, indent=2) + "\n")
    sh(["git", "add", "-A"], cwd=sandbox)
    sh(["git", "-c", "user.name=stamped-evals", "-c", "user.email=evals@example.org",
        "commit", "-q", "-m", f"eval sandbox: {run_id}"], cwd=sandbox)

    agent = (
        'claude -p "$(cat prompt.md)" --output-format stream-json --verbose '
        "--dangerously-skip-permissions > transcript.jsonl"
    )
    if args.model != "default":
        agent = agent.replace("claude -p", f"claude --model {args.model} -p")
    command = (
        ["datalad", "run", "-m", f"agent run {run_id}", "--explicit", "-o", "transcript.jsonl", agent]
        if have_datalad
        else ["sh", "-c", agent]
    )

    print(f"sandbox: {sandbox}")
    print(f"condition: {args.condition}; skills installed: {', '.join(installed) or 'none'}")
    print("command: " + " ".join(f"'{c}'" if " " in c else c for c in command))
    if not args.execute:
        print("\n(dry run: pass --execute to launch the agent)")
        return 0
    if not shutil.which("claude"):
        print("error: no `claude` on PATH; this runner needs the CLI for headless runs", file=sys.stderr)
        return 1
    proc = subprocess.run(command, cwd=str(sandbox), timeout=args.timeout)
    meta["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    meta["returncode"] = proc.returncode
    (sandbox / "run.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"\nagent exited {proc.returncode}; grade it with:\n"
          f"  python3 {HERE / 'grade.py'} {sandbox} --use-case {use_case} "
          f"--transcript {sandbox / 'transcript.jsonl'} --condition {args.condition} "
          f"--model {args.model} --repeat {args.repeat} -o {sandbox / 'grading.json'}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
