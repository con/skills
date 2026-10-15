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
| haiku, repeat 1 | **7/11** | met | must/016, must/006, must/013 |
| haiku, repeat 2 | **8/11** | met | must/016, must/006 |

Mean 0.818 on sonnet (spread 0.73–0.91) and 0.682 on haiku (0.64–0.73): the
tiers differ, and **the spread within sonnet is as wide as the gap between
them**, which is why item 14 of the plan's open decisions asks for three
repeats of one cell next rather than one repeat of three.

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

**must/006 was the skill's own.** Two runs in three left no run record naming
an environment, and the mechanism is mechanical: a `datalad run` whose outputs
do not change writes no commit, so declaring the lockfile *after* the work is
done records nothing at all. One run reported exactly that as friction.
`run-recorded.sh` now declares the tracked environment specification as an
input of every plain run — true, and the evidence the item asks for — so this
should stop costing repeats. The next round is the test of that.

## What both tiers did

Both carried the procedure through: a committed plan (with a note that no user
was available to approve it), 222 sessions of FreeSurfer-derived volumes with
per-session ages, a figure with the GM/WM ratio on a secondary axis, a
shuffled-age control, an independent subagent review that reproduced the table
byte-for-byte, and their own STAMPED self-assessment.

The tier difference is in the close-out, not the science: the haiku runs left
the judgement half of their assessment unfinished and wrote no response URL,
while the sonnet runs completed all 31 items. Both tiers hit the same
contradiction — the skill says to write the assessment outside the project, the
run was told to write nothing outside its working directory — and both invented
the same answer, a gitignored directory inside. That is now what the skill
says to do.

## Files

```
inner-prompt.md                     what each arm was told (identical but for the path)
explicit-<model>-r<n>.grading.json  T1 probes + oracle + process metrics
iteration-report.md                 the aggregate, with denominators
```

Objects and gradings are also in the results dataset:
`runs/2026-10-14-r0-explicit-repeats/`.
