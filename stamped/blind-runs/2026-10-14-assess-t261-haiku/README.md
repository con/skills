# Cross-tier blind assess: t261 on haiku — 2026-10-14

The model-tier half of [evals.md §7](../../../../docs/stamped/evals.md) step 3:
the same object, the same snapshot, the same prompt as the
[first blind run](../2026-10-13-assess-t261/), on the **smaller tier**. The
done criterion is "≥ 80 % MUST-verdict agreement across model tiers"
([§10.1](../../../../docs/stamped/evals.md#101-done-criteria)).

Object: `dandi/compression-comparisons-t261-study` at `f2f0802`, the commit the
reference answer in [`../../gold/`](../../gold/) was made on. 22 tool calls,
142 k tokens, 4 min.

## Result

| | |
|---|---|
| items answered | 31/31, `validate` clean, app URL encoded |
| agreement with the reference | **27/31** overall |
| **MUST agreement** | **15/17 (88 %)** — above the 80 % gate |
| differences | 4, none of them a pass/fail flip |

Both MUST differences are a difference of **degree between two failures**, not
of direction:

| item | haiku | reference (opus) | classification |
|---|---|---|---|
| must/006 | `unmet` | `partial` | **skill wording** → the probe's reason now states which of container / lockfile / capture it counted (see below) |
| must/016 | `partial` | `unmet` | model limit: haiku credited the tool module's public URL, the reference judged the object's own missing remote. Both are MUST failures |
| should/003 | `partial` | `met` | model limit: haiku required the environment definition to be a module of its own; the item asks only that components live apart |
| should/009 | `not-checked` | `not-applicable` | model limit: it declined to judge an uninstalled module rather than arguing the empty subject. `not-checked` over `not-applicable` is the conservative error, which rule 5 prefers |

No item was answered `met` without a citation, and the run did not touch the
target (`git status` clean, no commits).

## What it changed in the skills — five friction items, four acted on

1. **"`<date>` is the day you made the assessment, in UTC"** — the host clock
   said 2026-10-15 and the session context said 2026-10-14, and nothing said
   which wins. The step now says `date -u +%F`.
2. **`verdicts.md` rule 5** covered "a declared process that has never run"
   (`partial`) but not a process the history shows ran *seventeen* times, which
   is what must/014 and should/008 look like on this object. The rule now has
   all three cases, and `met` is the one with instances to cite.
3. **"clone from its published remote"** (step 4) was unreachable here: the
   tool module's URL is `../..`, and the object records no usable remote. The
   step now says to resolve against the remote the documentation names, and to
   report the recorded URL as the defect rather than leaving must/002
   unchecked.
4. **`run-env-linked` did not say what it had counted.** It degrades
   capture-only evidence to `partial` already, but on a mixed object its reason
   read "N of M name no container or lockfile" and said nothing about the other
   M−N. The run overrode must/006 on exactly that silence. The reason now
   carries the breakdown (`container` / `lockfile` / `capture`), and so does
   `details.by_mechanism`, so an overriding reader can audit the basis instead
   of guessing it.
5. **Links out of the installed directory.** The snapshot's principles card
   pointed at `../../docs/stamped/upstream/...`, which exists in con/skills and
   not in an install; the run reported it and did not follow it. The card now
   links the repository by URL, and the skill says plainly that nothing outside
   its own directory and `../stamped-conventions/` is needed to run it — a
   broken link into the repository is a note, not a stop.

The fifth is the one worth keeping in view: it is the first defect found by
*packaging* rather than by reasoning, and only a run that could not see the
repository could find it.

## Files

```
candidate-response.json   the 31 verdicts, as the run wrote them
candidate-assessment.md   its report
diff-vs-reference.json    per-item diff against ../../gold/
run.json                  snapshot, commit and scope
```
