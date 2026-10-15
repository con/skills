# R1, brain extraction of ten ds007116 subjects — 2026-10-14

The main development target of the ladder, and the first rung where an agent
has to **compute** something: pick a container registered in
`///repronim/containers`, skull-strip the first-session T1w of ten named
subjects, and plot brain size against age. From here on the FreeSurfer
derivatives the dataset ships are the *comparator*; copying them is the R0
shortcut at the wrong rung, and `oracle/check_r1.py` fails a run that does it.

One repeat per arm, sonnet, inner loop. Sandboxes and the exact prompt each arm
was given come from `harness/run.py --inner-prompt` (kept here as
`<arm>.inner-prompt.md`, because the prompt is the one input a reader cannot
reconstruct).

## Result

| arm | MUST (mechanically checkable) | oracle | tool it chose | mean ratio to `mask_maskvol` |
|---|---|---|---|---|
| `bare` | **4/11** | met | SynthStrip 8.2.0, `apptainer exec` inside `datalad run` | 1.065 |
| `pointer` | **8/11** | met | FSL 6.0.7 `bet -R -m` via `datalad containers-run` | 0.979 |
| `skill-implicit` | **10/11** | met | SynthStrip 8.2.0 via `datalad containers-run`, one record per subject | 1.065 |
| `skill-explicit` | still running when this record was written | | SynthStrip, one record per subject (22 commits so far) | |

**The science was right in every arm.** All three finished runs computed ten
real mask volumes, each within the band the two-container pilot measured
(`[0.90, 1.34]` of that subject's shipped `mask_maskvol`), and the two
SynthStrip arms agree to the digit — the same deterministic tool on the same
inputs. BET sits 8% lower than SynthStrip, inside the band, which is why the
band is the union of two tools rather than one tool's spread.

What separates the arms is everything else: `bare` wrote no README, no plan and
no environment specification, and its single remaining failure in the implicit
arm is must/016 — nothing is published, because a sandbox has nowhere to
publish to.

**One repeat per arm proves nothing on its own.** Three repeats and a second
tier are what the done criteria ask for; these numbers are smoke thresholds.

Numbers are **harness-corrected in one documented way**: `HOST-NOTES.md`, which
the harness writes into every sandbox, carries an absolute cache path, and the
probes rightly flagged it (must/009). `harness/correct_object.py` untracks the
harness's own files into a copy, which is what the gradings here describe, and
`run.py` now ignores the file so the correction is not needed again. As
measured, the arms were `bare` 4/11, `pointer` 7/11, `skill-implicit` 9/11.

## What the runs broke — six defects, all in the skills or the harness

1. **`run-recorded.sh` could not run a container.** The implicit arm called
   `run-recorded.sh datalad containers-run …` — the only way to make a record
   name its image, which is what must/006 and must/015 read — and the wrapper
   passed the whole thing to `datalad run`, nesting one record inside another
   with no declared inputs or outputs. `-n NAME` now dispatches, a stray
   subcommand is dropped rather than executed, and three tests pin it.
2. **The oracle could not find the comparator.** The input dataset is a module
   one level below the input directory (`sourcedata/ds007116`), which is how
   both arms laid it out, so looking only at `sourcedata/` found no
   `derivatives/` and the oracle declined to judge two gradeable runs.
3. **The `pointer` arm reported millilitres**, which is good science and
   nothing in the prompt asks otherwise. With the unit ignored its ten volumes
   read as implausible (worst ratio 0.0009) rather than as the same brain in
   other units. The unit now comes from the column name, and the copy check
   compares in mm³ either way.
4. **A table can carry both `mask_voxels` and `brain_volume_mm3`**, and taking
   the first match took the count — right only because these voxels are 1 mm³.
5. **The harness's own notes cost two arms must/009** (see above). Second rung
   in a row where the grader accused an object of the harness's mess.
6. **One arm's `pkill -f 'datalad run'` matched a sibling arm's jobs.** A
   shared host is shared; the host notes say so now, and the stack reference
   says to kill by pid.

Plus two findings that are about the agents rather than the skills, and worth
keeping: the `bare` arm's `-i 'inputs/ds007116/sub-*/…'` glob started fetching
all 128 subjects before it was killed (the host notes warned, and the warning
was right), and `datalad run`'s "clean dataset required to detect changes from
command" fired twice on scratch files, which is why logs belong outside the
object.

## Files

```
<arm>.inner-prompt.md   exactly what that arm was told
<arm>.grading.json      T1 probes + the science oracle + process metrics
iteration-report.md     the aggregate, with denominators and the no-significance caveat
```

The objects themselves, their products and these gradings are in the results
dataset: `runs/2026-10-14-r1-four-arms/` in
[con/stamped-skills-evals](https://hub.centerforopenneuroscience.org/con/stamped-skills-evals).
