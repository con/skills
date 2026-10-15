# Three repeats of one cell — R0 `skill-explicit`, sonnet, 2026-10-15

[PLAN §10](../../../../docs/stamped/PLAN.md#7-decisions-and-where-we-diverge)
item 14 asked for three repeats of **one** cell rather than one repeat of
three, because on 2026-10-14 the spread within sonnet was wider than the gap
between the tiers. This is that cell. It is also the first round in which
**all eleven mechanically checkable MUST items are reachable**: item 13 gave
every run a publishing target.

| run | MUST | at the sandbox ceiling | oracle | what failed |
|---|---|---|---|---|
| sonnet, repeat 4 | 9/11 | 10/11 | met | must/016, must/009 |
| sonnet, repeat 5 | **10/11** | **11/11** | met | must/016 |
| sonnet, repeat 6 | **10/11** | **11/11** | met | must/016 |

Mean 0.879, spread 0.82–0.91 — against 0.73–0.91 for the same cell the day
before, when two of the items that moved turned out to be probe defects.

**What the ceiling column means.** must/016 asks whether anyone else can
obtain the project. The target these runs were given is a bare repository
beside the sandbox, so the honest verdict is `partial` — "anyone with access
to that filesystem can obtain it and nobody else can" — and `met` needs a URL.
The strict column counts only `met`; the ceiling column counts must/016's
`partial` as the best available answer, and says so in the grading
(`t1.ceiling`). On that reading **two repeats in three pass every item**,
which is the §10.1 criterion for one tier at one rung.

**All three published**, which is the point of item 13: before it, must/016
was `unmet` in every repeat on every tier whatever the run did, so one of the
eleven items measured the harness. Each run registered a sibling, pushed, and
had an independent subagent review a clone of the *published* repository
rather than of the working directory. Repeat 4 lost must/009 for writing the
target's absolute path into its README; repeats 5 and 6 wrote it relative or
as `~/…`. That is a real difference between runs, correctly discriminated.

## The same three defects in all three runs

Independent runs, same prompt, same three findings — which is what makes them
defects rather than accidents.

1. **`datalad push` to a fresh bare repository publishes no content and says
   "ok".** git-annex needs a uuid on the other side and `git init --bare`
   leaves none, so the history lands and every annexed file stays behind.
   `git ls-remote` — which the skill told them to check with — cannot see the
   difference. Two runs found it only because their own reviewer could not
   retrieve the figure from the clone. The harness now hands over an
   annex-initialised target, the publish step verifies with `git annex
   whereis` or a clone, and the stack reference carries the trap.
2. **"Put the URL in the README" collides with must/009** when the target is a
   filesystem path. All three hit it and all three compromised differently.
   The skill now says a path is not a URL: name it as the run's target and as
   a known limitation, and expect the host-path flag, because the flag is
   right.
3. **zsh does not word-split a command built in a variable.** `R='uv run …';
   run-recorded.sh … -- $R code/collect.py` exits 127. The template warned
   about quoted *path lists* and not about the command. It warns about both
   now.

## And two defects in the graders, found by what the runs asked for

- **Re-running the probes threw away the judgement answers.** Every run had to
  fix something the probes found — a LICENSE, a CI workflow, a README section
  — and then wanted the probe verdicts refreshed over a response whose
  nineteen judged items were already answered. One patched two items back by
  hand; another said it had no clean way to do it. `run_probes.py` now keeps
  judged answers (and the run's own `assessor` stamp) across a re-run, flags
  an item where a fresh probe verdict disagrees with the reading that
  overrode it, and takes `--overwrite` for a clean draft.
- **`should/006` could not see the environment a record declares as an
  input.** `run-recorded.sh` declares the tracked specification with `-i`, so
  it lands in a record's `inputs` — and this scan read `cmd` and
  `extra_inputs` only. A run whose CI rebuilt from exactly the lockfile its
  records name was told the environment behind its results "is never tested",
  and reported that as friction. The must/006 fix had been invisible to the
  item next door. (`uv pip sync` was also missing from the rebuild
  vocabulary, which knew only the project-mode `uv sync`.)

One claim did **not** reproduce: a stale in-flight marker after a failed run.
The wrapper clears its marker on datalad's own failure — now covered by a
test, which the suite had missed because its failure case went through the
no-datalad fallback — and in the run that saw it the guard self-healed by
noticing the pid was gone, which is what the pid is for.

## `fresh-rerun` ran for the first time, and failed on its own two bugs

§10.1 asks for every MUST probe "including `fresh-rerun`", and with nowhere to
clone from it had never executed. Pointed at repeat 6's published repository it
found:

- **it deleted 9390 files from the input module.** `**/*.tsv` reaches straight
  into `sourcedata/ds007116`, whose shipped tables are the *comparator*. An
  input module is now never a candidate.
- **its own tidying made the entry point unrunnable.** Removing the shipped
  outputs (so that only re-creation counts) left the tree dirty, and `datalad
  rerun` refuses a dirty tree. The removal is committed now.

`fresh-rerun-r6.json` is the run after both fixes.

## Files

```
inner-prompt.md                       what each repeat was told (identical but for the paths)
explicit-sonnet-r<n>.grading.json     T1 probes + oracle + process metrics + T2
explicit-sonnet-r<n>.assessment.md    that run's own STAMPED report, the T2 input
explicit-sonnet-r<n>.response.json    and its 31 answers
fresh-rerun-r6.json                   the clone-and-re-execute probe on repeat 6
iteration-report.md                   the aggregate, with denominators
```

**Still n=3 on one tier at one rung.** The second tier and R1 are what the
gate still wants, and the publishing target has not been tested with a real
URL — which is the only way must/016 reaches `met`.
