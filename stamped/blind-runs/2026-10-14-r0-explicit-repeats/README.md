# R0 repeats: `skill-explicit` on two model tiers — 2026-10-14

The v1.0 gate for `create` / `align` / `do-full-research-loop` asks that the
explicit-skill arm pass every mechanically checkable MUST probe **in ≥ 2 of 3
repeats on two model tiers**
([evals.md §10.1](../../../../docs/stamped/evals.md#101-done-criteria)). The
2026-10-13 round was one repeat on one tier. This is the rest of it: sonnet
repeats 2 and 3, and haiku, on the same R0 prompt and the same use case.

| run | MUST | oracle | what failed |
|---|---|---|---|
| sonnet, repeat 2 | **10/11** | met | must/016 |
| sonnet, repeat 3 | **8/11** | met | must/016, must/006 |
| haiku, repeat 1 | **9/11** | met | must/016, must/006 |
| haiku, repeat 2 | **8/11** | met | must/016, must/006 |

Mean 0.818 on sonnet (spread 0.73–0.91) and 0.773 on haiku (0.73–0.82): the
spread **within** sonnet is wider than the gap between the tiers, which is why
item 14 of the plan's open decisions asks for three repeats of one cell next
rather than one repeat of three.

> **The haiku repeat-1 row was 7/11 when this record was first written.** That
> agent went quiet for about 35 minutes after its last commit and was graded
> there; it then spent the rest of the night finishing its own STAMPED
> assessment, which it wrote outside the tree, so it committed nothing more and
> the grading had in fact been taken at its final state (`4dd6015e`). The whole
> difference is in the probes: re-graded with the probes as of 2026-10-15 it is
> **9/11**, the best haiku run rather than the worst, and the two items that
> moved were both the grader's fault. Its late report is what found them.
>
> Establishing that the old grading had been at the final commit took comparing
> a git-annex key against a fresh bundle, because a grading did not say which
> commit it described. `grade.py` writes the object's HEAD into every grading
> now.

Baselines on the same use case, 2026-10-13: `bare` 3/11, `pointer` 5/11.

## The gate is not met, and both reasons are worth having

**must/016 is unreachable from a sandbox.** The item asks whether anyone else
can obtain the environment specification; these runs have no publishing target
and no credentials, so the honest answer is `unmet` in every repeat, on every
tier, however good the project is. That is a property of the harness, not of
the skill. Two ways out, and the choice belongs in the plan rather than in a
probe: give an outer-loop run somewhere to push (the results dataset's hub can
host one repository per run), or say that must/016 is out of scope for a
sandbox run and record it as `not-checked` with that reason. **Until that is
decided, no R0 or R1 run can score 11/11, and the gate as written cannot be
met by construction.**

**must/006 was the skill's own.** Three runs in four left records that name no
environment, and the mechanism is mechanical: a `datalad run` whose outputs do
not change writes no commit, so declaring the lockfile *after* the work is done
records nothing at all. One run reported exactly that as friction.
`run-recorded.sh` now declares the tracked environment specification as an
input of every plain run — true, and the evidence the item asks for — so this
should stop costing repeats. The next round is the test of that.

The remaining `partial` on haiku repeat 1 is the honest answer: that run
registered a container and re-derived two of its seven products inside it, and
left the other five naming `.venv/bin/python`. It said so itself.

## Two probe defects, both false failures, both from one late report

The report that arrived late was the most useful of the four, because it argued
with its grader and was right. Fixing the second of them exposed a third
weakness, in the item next door.

1. **`run-env-linked` could not see a registered container.**
   `datalad containers-add` copies a locally built image to
   `.datalad/environments/<name>/image` — no extension — and `containers-run`
   records the *expanded* call, so neither the image-suffix regex nor the word
   `containers-run` appears anywhere in the record. must/006 read `unmet` on an
   object with two records naming a tracked, content-addressed image, and
   must/015 was `not-checked` because nothing had been found to check. This is
   the normal layout for a built image, so the probe was blind to the common
   case, not an exotic one. It now reads the registration in `.datalad/config`.
2. **A record is also a place a floating tag can hide.** Having taught must/006
   to credit a bare runtime invocation (`docker run x:v1`), must/015 had to
   learn to read the record bodies too — otherwise broadening the first item
   would have quietly weakened the second.
3. **`entry-point` graded the prose style, not the question.** The README has
   `## Requirements` (host tools, pinned image, lockfile) over `## Entry point
   and reproduce` (five commands), and must/007 came back "neither a README
   with install/usage instructions nor a Makefile" because the probe matched
   its keywords only at the *start* of a line. A heading that contains the word
   now counts, and a README that says nothing about running the project still
   fails.

Each is pinned by a test in `evals/stamped/tests/test_probes.py`. The
2026-10-13 R0 round was graded before all three, and its objects are gone, so
those numbers cannot be restated — a reason to keep objects, which the results
dataset now does.

## What both tiers did

Both carried the procedure through: a committed plan (with a note that no user
was available to approve it), 222 sessions of FreeSurfer-derived volumes with
per-session ages, a figure with the GM/WM ratio on a secondary axis, a
shuffled-age control, an independent subagent review that reproduced the table
byte-for-byte, and their own STAMPED self-assessment.

The tier difference is in the close-out, not the science, and it is one run
rather than a tier: haiku repeat 2 left the judgement half of its assessment
unfinished and wrote no response URL, while the other three — repeat 1 on the
same tier included — completed all 31 items.

Haiku repeat 1's own assessment is merged into its grading as T2, which is the
first time the two tiers of this harness can be read against each other on one
object. **Four items disagree, and every one of them is the division of labour
working.** must/011 and must/012 are `not-checked` by T1 by construction and
the run judged them by reading. must/015 is `met` to the probe (the image is a
tracked, content-addressed file and no `:latest` is referenced anywhere) and
`partial` to the run, which opened the definition and saw the base tag float —
a stricter read the probe cannot reach, and a good argument for not trying to.
must/016 is the one where T2 is *wrong*: it answered `partial` for "there is no
published remote", and `verdicts.md` is explicit that a recorded remote nobody
verified is `partial` while no remote at all is `unmet`. One item in 31,
leniency rather than invention, and it is the item the whole gate is stuck on. Both tiers hit the same
contradiction — the skill says to write the assessment outside the project
("write them outside the object, into the current directory"), the run was told
"do not write outside it" — and both invented the same answer, a directory
inside the object that nothing tracks. Both sides are fixed rather than one:
the harness now gives every run a scratch directory beside its sandbox and
names it in the prompt, and the skill now says what to do when writing outside
is forbidden, including gitignoring the directory and saying in the report
which rule it had to bend.

## Files

```
inner-prompt.md                     what each arm was told (identical but for the path)
explicit-<model>-r<n>.grading.json  T1 probes + oracle + process metrics (+ T2 where there is one)
explicit-haiku-r1.assessment.md     that run's own STAMPED report, the T2 input
explicit-haiku-r1.response.json     and its response JSON, all 31 items answered
iteration-report.md                 the aggregate, with denominators
```

Objects and gradings are also in the results dataset:
`runs/2026-10-14-r0-explicit-repeats/`. The two assessment files are copied in
here because a git bundle carries commits, and this run — forbidden to write
outside the object — put its report in `.git/assessment/`, which no bundle
would have preserved.
