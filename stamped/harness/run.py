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
    "r1-brain-extraction": "/do-full-research-loop ",
}

# The inner-loop prompt, as an artifact rather than wording retyped per run.
# R0's four arms were launched from prompts composed by hand in the
# orchestrating session, so the one thing a reader cannot reconstruct from that
# run record is what each arm was actually told.  This is that text, with the
# per-condition paragraph the only thing that differs between arms.
INNER_PROMPT = """You are a fresh session working in a sandbox. Treat this as a normal user request.

**Working directory:** `{sandbox}` — a git{datalad} repository, already initialised and
committed. The products of the task go inside it.

**Scratch directory:** `{outdir}` — for anything that is *about* the work rather than
part of it: logs, an assessment report, notes you do not intend to commit. A recorded
run refuses to start with untracked files in the worktree, so keeping these out of the
object is not tidiness but a requirement. Write nowhere else: these two directories are
the whole of your writable space.

**Your task:** {task}

{condition_paragraph}

Operating constraints for this run:

1. `HOST-NOTES.md` in the sandbox describes the machine: read it first. It is the same
   file in every arm of this evaluation.
2. **The user is not available to answer questions.** Where you would ask, state the
   decision and your reason for it in the project instead, and carry on. Do not stop to
   wait for an answer.
3. **Do NOT read or search `{repo}`**, with the single exception of the two
   directories named above (which happen to live under it, in an ignored scratch area):
   everything else under that path is off-limits for this run, including any plan,
   rubric, reference answer, or any other arm of this evaluation. This is a blind run:
   what you build is graded against criteria you must not see, and seeing them would
   destroy the measurement. Work from your task, the sandbox, and whatever you fetch from
   the network.
4. You may install packages, pull containers and fetch data. Permissions are wide open
   **inside the sandbox and the scratch directory only**.
5. Carry the task through to its stated product. A plan with no result is a failed run.
6. {publish_paragraph}

**What to return as your final message** (keep it compact — it is read by a harness):

- What you built: the paths of the products, and the one-line method (tool, container,
  how the numbers were obtained).
- The numbers themselves: the per-subject table as text, if the task produced one.
- How you recorded what you did, if you did.
- Up to 5 bullets of **friction**: anything that was ambiguous, missing, contradictory,
  broken or slow — in the task, in the host, or in any instructions you were given —
  **quoting the wording or command at fault**. Be specific and critical; this is the most
  valuable part of your return.
"""

# Stated as a fact about the host, not as an instruction, and identical in
# every arm — what a run *does* with a publishing target is the thing being
# measured. Before this existed, must/016 ("anyone else can obtain it") was
# `unmet` in every repeat on every tier regardless of behaviour, which made one
# of the eleven mechanically checkable MUST items measure the harness.
PUBLISH_PARAGRAPH = (
    "**A publishing target exists:** `{url}` — an empty, writable repository you may use as a "
    "remote. Nothing else will push to it for you."
)
NO_PUBLISH_PARAGRAPH = (
    "There is **no publishing target** on this host: nothing you build here can be pushed anywhere."
)

CONDITION_PARAGRAPH = {
    "bare": "You have no project conventions to follow beyond the task itself.",
    "pointer": (
        "The sandbox root carries a `CLAUDE.md` (and an identical `AGENTS.md`). Read it "
        "before you start and follow it, exactly as a session whose project root held "
        "that file would."
    ),
    # A subagent has no slash-command dispatcher, so "implicit" can only mean
    # the skills are on disk and the run is told it may use what it finds —
    # evals.md §4 records why these numbers are indicative only.
    "skill-implicit": (
        "The sandbox has a `.claude/skills/` directory holding skills that are installed "
        "for you. You may read and use whatever you find there if it is relevant; nothing "
        "obliges you to. (Those files are tooling, not part of the project you are "
        "building: leave them out of what you commit.)"
    ),
    "skill-explicit": (
        "The task above names a skill. It is installed in the sandbox under "
        "`.claude/skills/`, but there is no slash-command dispatcher here, so read its "
        "`SKILL.md` from disk and follow its procedure exactly as written, including the "
        "files it tells you to read. (Those skill files are tooling, not part of the "
        "project you are building: leave them out of what you commit.)"
    ),
}


def sh(cmd: list[str], cwd: pathlib.Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    except FileNotFoundError:
        # An absent tool is an answer, not a crash. `conditions/host-notes.md`
        # tells every run that datalad, git-annex and uv may or may not be on
        # this host's PATH, and the run record's job is to say which — so a
        # `check=False` probe for a version must come back empty rather than
        # take the harness down with it. 127 is what a shell reports.
        if check:
            raise RuntimeError(f"{cmd[0]} not found on PATH")
        return subprocess.CompletedProcess(cmd, 127, "", f"{cmd[0]}: not found")
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}… failed: {(proc.stderr or proc.stdout).strip()[:600]}")
    return proc


def _publish_target(args, bare: pathlib.Path) -> str | None:
    """The URL this run may push to, or None.

    `local` initialises a bare repository beside the sandbox. It is a real
    target — `datalad push` carries annexed content to it, and `git ls-remote`
    answers — but it is a filesystem path, so an honest assessment caps
    must/016 at `partial` ("whoever shares that filesystem, and nobody else").
    Pass a URL to raise that ceiling; a run with credentials for a forge is
    what the v1.0 gate needs.
    """
    if args.publish_target == "none":
        return None
    if args.publish_target != "local":
        return args.publish_target
    if not bare.exists():
        sh(["git", "init", "-q", "--bare", str(bare)])
        # A bare repository with no annex accepts `datalad push`, reports
        # "publish ok" — and receives none of the annexed content, because
        # git-annex has no uuid to copy to. A run hit exactly that: its figure
        # never left the sandbox, and only its own reviewer noticed, because
        # the `git ls-remote` check cannot see it. The harness hands over a
        # target that works; debugging an empty annex is not what is being
        # measured.
        sh(["git", "annex", "init", "stamped-eval publish target"], cwd=bare, check=False)
    return str(bare)


def skill_commit() -> str:
    proc = sh(["git", "rev-parse", "HEAD"], cwd=REPO, check=False)
    return proc.stdout.strip() or "unknown"


def skill_source(root: pathlib.Path, name: str) -> pathlib.Path:
    """Where skill ``name`` lives in the checkout ``root``.

    con/skills publishes one canonical ``skills/`` tree (con/skills#13), but a
    run record pins a skills commit, and the ones already recorded predate the
    move. Preferring the new layout and falling back to the old keeps
    ``--skills-from <old checkout>`` able to replay them.
    """
    nested = root / "skills" / name
    return nested if (nested / "SKILL.md").exists() else root / name


def install_skills(sandbox: pathlib.Path, source: pathlib.Path) -> list[str]:
    target = sandbox / ".claude" / "skills"
    target.mkdir(parents=True, exist_ok=True)
    installed = []
    for name in SKILLS:
        src = skill_source(source, name)
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
    ap.add_argument("--publish-target", default="local",
                    help="'local' (a bare repo beside the sandbox, the default), 'none', or a URL "
                         "the run may push to. must/016 is unreachable without one.")
    ap.add_argument("--timeout", type=int, default=7200)
    ap.add_argument("--execute", action="store_true", help="actually run the agent")
    ap.add_argument("--inner-prompt", action="store_true",
                    help="also write and print the prompt for an inner-loop (subagent) run")
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
        sh(["datalad", "create", str(sandbox)])
        # Filename/size policies work with standalone annex builds that do
        # not include MagicMime (required by DataLad's text2git procedure).
        with (sandbox / ".gitattributes").open("a") as stream:
            stream.write("* annex.largefiles=largerthan=100kb\n")
            for suffix in ("md", "py", "sh", "toml", "yaml", "yml", "json", "lock"):
                stream.write(f"*.{suffix} annex.largefiles=nothing\n")
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

    # The same host notes in every arm, with the one host-specific path filled
    # in: a cache and temporary area for container images, one per run (arms
    # run concurrently, and two apptainer processes populating one cache is a
    # race) and outside the sandbox, so it does not dirty the object.
    cache = args.workdir.resolve() / "cache" / run_id
    cache.mkdir(parents=True, exist_ok=True)
    notes = (EVALS / "conditions" / "host-notes.md").read_text()
    (sandbox / "HOST-NOTES.md").write_text(notes.replace("$STAMPED_CACHE_DIR", str(cache)))
    # Untracked, like `.claude/`: the notes name an absolute cache path, and
    # the first R1 arms both lost must/009 to the probes finding that path in a
    # *tracked* file the run was handed by the harness. The grader must not
    # accuse an object of the harness's own host-specific text.
    gitignore = sandbox / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if "HOST-NOTES.md" not in existing:
        gitignore.write_text(existing + "HOST-NOTES.md\n")

    task = prompt
    if args.condition == "skill-explicit":
        task = EXPLICIT_PREFIX.get(case_id, "/do-full-research-loop ") + prompt
    # The harness's own metadata goes *beside* the sandbox, not inside it: both
    # files name absolute paths, and an R1 arm had to exclude them from its own
    # preflight and override a probe that read them as host dependencies. The
    # object is the agent's work; what the harness asked for belongs with the
    # run record.
    (sandbox.parent / f"{run_id}.prompt.md").write_text(task + "\n")

    meta = {
        "run_id": run_id,
        "use_case": case_id,
        "condition": args.condition,
        "model": args.model,
        "repeat": args.repeat,
        "skills_installed": installed,
        "skill_commit": skill_commit(),
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "publish_target": args.publish_target,
        "host": {
            "uname": sh(["uname", "-a"], check=False).stdout.strip(),
            # Versions, not booleans: "datalad: true" does not let anyone
            # reproduce a run, and it is the must/006 evidence we grade others
            # on. `container_exec` is whether a container can actually *run*
            # here, which is a different question from whether apptainer is
            # installed (see docs/stamped/evals.md §5.1).
            "datalad": sh(["datalad", "--version"], check=False).stdout.strip() or None,
            "git_annex": (sh(["git", "annex", "version"], check=False).stdout.splitlines() or [""])[0] or None,
            "apptainer": sh(["apptainer", "--version"], check=False).stdout.strip() or None,
            "container_exec": pathlib.Path("/dev/fuse").exists() or bool(shutil.which("unsquashfs")),
        },
    }
    meta_path = sandbox.parent / f"{run_id}.run.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    sh(["git", "add", "-A"], cwd=sandbox)
    sh(["git", "-c", "user.name=stamped-evals", "-c", "user.email=evals@example.org",
        "commit", "-q", "-m", f"eval sandbox: {run_id}"], cwd=sandbox)

    outdir = sandbox.parent / f"{run_id}.out"
    outdir.mkdir(parents=True, exist_ok=True)
    publish_url = _publish_target(args, sandbox.parent / f"{run_id}.publish.git")
    inner = INNER_PROMPT.format(
        sandbox=sandbox,
        outdir=outdir,
        publish_paragraph=(PUBLISH_PARAGRAPH.format(url=publish_url) if publish_url
                           else NO_PUBLISH_PARAGRAPH),
        datalad=" (DataLad dataset)" if have_datalad else "",
        task=task,
        condition_paragraph=CONDITION_PARAGRAPH[args.condition],
        repo=REPO,
    )
    if args.inner_prompt:
        (sandbox.parent / f"{run_id}.inner-prompt.md").write_text(inner)

    agent = (
        f'claude -p "$(cat {sandbox.parent / f"{run_id}.prompt.md"})" '
        "--output-format stream-json --verbose "
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
    if args.inner_prompt:
        print(f"inner prompt: {sandbox.parent / f'{run_id}.inner-prompt.md'}")
        print("\n--- paste the following to a fresh subagent ---\n")
        print(inner)
    if not args.execute:
        print("\n(dry run: pass --execute to launch the agent in the outer loop, "
              "or --inner-prompt to drive it as a subagent)")
        return 0
    if not shutil.which("claude"):
        print("error: no `claude` on PATH; this runner needs the CLI for headless runs", file=sys.stderr)
        return 1
    proc = subprocess.run(command, cwd=str(sandbox), timeout=args.timeout)
    meta["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    meta["returncode"] = proc.returncode
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"\nagent exited {proc.returncode}; grade it with:\n"
          f"  python3 {HERE / 'grade.py'} {sandbox} --use-case {use_case} "
          f"--transcript {sandbox / 'transcript.jsonl'} --condition {args.condition} "
          f"--model {args.model} --repeat {args.repeat} -o {sandbox / 'grading.json'}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
