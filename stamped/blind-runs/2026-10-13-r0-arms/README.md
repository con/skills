# R0, four arms — 2026-10-13/14

The first runs in which an agent **builds** a project from a prompt rather than
being graded on one. One repeat per arm, sonnet, inner loop (subagents of the
orchestrating session), sandboxes from `harness/run.py`.

## Result

| arm | MUST (mechanically checkable) | oracle | what it built |
|---|---|---|---|
| `bare` | **3/11** | **unmet** | A clone, then scripts, table and figure **written into the input dataset** and committed there, with the superdataset pointer moved to follow. |
| `pointer` | **5/11** | met | Input as a proper subdataset, a PEP 723 script, table and figure, 2 commits, clean tree. No README, no run records. |
| `skill-implicit` | **8/11** | met | README, plan, write-up, the three guards from the templates, input as a subdataset, both products through `datalad run` records, 6 commits, and a fresh-subagent review that reproduced the table byte-for-byte. |
| `skill-explicit` | **7/11** | met | The same, plus `requirements.in`/`.lock`, sanity checks, a `LICENSE`, and its own assessment — 12 commits. |

Both skill arms clear both baselines; the remaining failures are real and
listed below. **One repeat per arm proves nothing on its own** — three repeats
and a second model tier are what the done criteria ask for, and raw counts at
n=1 carry no significance whatever.

Numbers are **harness-corrected**: `run.py` committed its own
`.claude/skills/` copies into the sandbox, so the probes were partly assessing
the skills under test (host paths in a vendored checklist, `command -v` in
probe source, 21 platform-specific commands in a probe's own table). The
as-measured numbers were `bare` 3, `pointer` 5, `skill-implicit` 6,
`skill-explicit` 6. `run.py` now gitignores `.claude/`, so this correction is
not needed again.

## What the runs found in the skills — eight defects, all shipped-artifact bugs

The explicit arm used `run-recorded.sh` for real and found **three bugs in it**:

1. `exec datalad run $@` — unquoted `$@` re-splits a multi-word `-m` message,
   so `datalad run` tried to execute the word `per-session`.
2. `exec` replaces the wrapper's process, so `trap cleanup EXIT` never fired:
   the in-flight marker survived every run and the pre-commit guard then
   refused every later commit. **The guard inflicting the exact hazard it
   exists to prevent.**
3. The marker was an untracked worktree file, and `datalad run` refuses to
   start when there are untracked files — so the template's own documented
   usage failed out of the box.

The marker now lives in the git directory, `"$@"` is quoted, `exec` is gone,
and four tests pin all three.

Two more were the skills damaging the object they were helping:

4. `preflight.sh` scanned the whole repository, flagging host paths inside
   `.claude/skills/` that the run was told not to touch — an unfixable FAIL.
   It now excludes installed tooling and takes `PREFLIGHT_EXCLUDE`.
5. The assessor told the run to leave its report **uncommitted inside** the
   object, which fails must/004 (the tree is no longer the whole state). With
   no user available the report now goes outside the object.

And three probe defects:

6. `env-spec-tracked` read `if command -v datalad; then … else fallback`, the
   template's own graceful degradation, as "requires a tool on the host" —
   costing must/010. A failure branch that falls back is not a precondition;
   the window is now the check's own branch, and fallback wording excludes it.
7. PEP 723 inline script metadata is an environment specification, and the
   probe said there was none (found by the `pointer` arm).
8. `inputs-untouched` called the `bare` arm's inputs "clean and at the recorded
   commit" while that commit existed only in the sandbox. It now detects
   commits on a module's HEAD that are on no remote and carry this object's
   products, offline.

## What still fails in the skill arms, and is the object's own doing

- **must/006** (both arms): the `[DATALAD RUNCMD]` records carry empty
  `inputs`/`extra_inputs`, so a rerun works in place but not from a bare clone.
  The explicit arm's own independent reviewer found this before any probe did.
- **must/016** (both): nothing is published, so no specification is obtainable.
- **must/004** (explicit): the uncommitted assessment, now fixed in the skill.
- **must/009** (explicit): its README quotes a `/home/...` path while
  documenting the preflight bug it hit — `partial`, in documentation.
- No CI in either (`should/002`, `should/006`), and no licence in the implicit
  arm.

## Cost

| arm | tool calls | tokens | wall |
|---|---|---|---|
| `bare` | 43 | 78 k | 6 min |
| `pointer` | 25 | 83 k | 4 min |
| `skill-implicit` | 80 | 131 k | 15 min |
| `skill-explicit` | 106 | 159 k | 17 min |

The skills roughly double the tokens and triple the tool calls, and produce an
object that scores two to three times better. Both skill arms also pulled
several GB of annexed content by accident (a too-broad `-i` glob on
`datalad run`), which the use case should warn about.
