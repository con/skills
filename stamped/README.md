# STAMPED skill evaluations

The tests for the STAMPED skills live here, **outside** the skill directories,
following the K-Dense convention and `docs/stamped/PLAN.md` §6.

Only the harness lives here. Run *results* — produced objects, transcripts,
container logs — go to [`con/stamped-skills-evals`](https://hub.centerforopenneuroscience.org/con/stamped-skills-evals)
on the CON hub, where each run is a subdataset and every grading step is a
recorded run. That keeps this repository small and makes every number in a
report or a talk re-executable.

```
conditions/pointer-CLAUDE.md   the `pointer` baseline, verbatim from the issue
fixtures/make_r0_object.py     builds a known-good R0 object (plain git; no datalad or network)
mutants/mutate.py              one injected defect each, with the items it should flip
harness/calibrate.py           fixture + mutants -> per-item sensitivity, false-unmet rate
harness/run.py                 set up one sandboxed run of a use case under a condition
harness/grade.py               T1 probes + science oracle + process metrics -> grading.json
harness/aggregate.py           grading files -> iteration report (always with denominators)
use-cases/<id>/                prompt, use_case.yaml, rubric.yaml, oracle/
tests/                         pytest over the probes, the mutants and the encoder
```

## The loop, in commands

Calibrate the scripted half of the assessor — this is the gate that has to hold
before any skill is graded by it:

```console
python3 evals/stamped/harness/calibrate.py -o calibration.json
```

It builds the clean fixture, probes it (every answered item must come back
`met`), then injects each mutant and checks that exactly the declared items
flip. Exit code 0 means full sensitivity and no false `unmet`.

Run a use case under a condition, then grade it:

```console
python3 evals/stamped/harness/run.py --use-case evals/stamped/use-cases/r0-freesurfer-plot \
    --condition pointer --workdir /scratch/stamped/iter-1          # add --execute to launch
python3 evals/stamped/harness/grade.py <sandbox> \
    --use-case evals/stamped/use-cases/r0-freesurfer-plot \
    --transcript <sandbox>/transcript.jsonl --condition pointer -o <sandbox>/grading.json
python3 evals/stamped/harness/aggregate.py --glob '/scratch/stamped/iter-1/**/grading.json' \
    --markdown iteration-1.md
```

## Rules this harness keeps

- **An agent's success report is not evidence.** Only the committed object and
  the transcript count.
- **Collector failures are kept apart from object defects.** A probe that
  crashes reports `not-checked` with `collector_failure`, and never `unmet`.
- **Unknown is not zero.** A missing transcript means the process metrics are
  unknown; it does not mean the agent behaved.
- **Numerators come with denominators**, per item and per principle. There is
  no single score.
- **A lesson requires a regression artifact.** When a run exposes a gap, add a
  mutant, a probe or a use case first; prose in a `SKILL.md` is the last resort.
- **Hold-outs stay out of the inner loop** (R5, and one ReproNim variant), so
  the skills are not tuned to these fixtures.

## Where each rung is

| Rung | Task | Status |
|---|---|---|
| R0 | Plot from the FreeSurfer tables ds007116 ships | use case and oracle in place |
| R1 | Brain extraction, ≥ 10 subjects → brain size vs age | not started (main development target) |
| R2 | Brain, GM and WM volumes, ~30 sessions | not started |
| R3 | MRIQC motion vs age and time of day | not started; waits for R0–R2 |
| R4 | Whole dataset, NIDM + PROV | demonstration only |
| R5 | DANDI orientation selectivity | hold-out |
