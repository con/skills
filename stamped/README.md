# STAMPED skill evaluations

The tests for the STAMPED skills live here, **outside** the skill directories,
following the K-Dense convention and `docs/stamped/PLAN.md` §6.

Only the harness lives here. Run *results* — produced objects, transcripts,
container logs — go to [`con/stamped-skills-evals`](https://hub.centerforopenneuroscience.org/con/stamped-skills-evals)
on the CON hub, where each run is a subdataset and every grading step is a
recorded run. That keeps this repository small and makes every number in a
report or a talk re-executable.

That dataset exists as of 2026-10-13 and holds the first probe calibration;
`datalad clone https://hub.centerforopenneuroscience.org/con/stamped-skills-evals.git`
works anonymously. The exception is [`gold/`](gold/README.md): those reference
answers are *inputs* to development rather than run results, so they are kept
here, beside the mutants they complement.

```
conditions/pointer-CLAUDE.md   the `pointer` baseline, verbatim from the issue
harness/blind_run.py           snapshot a skill + render the subagent prompt; diff what comes back
fixtures/make_r0_object.py     builds a known-good R0 object (plain git; no datalad or network)
mutants/mutate.py              one injected defect each, with the items it should flip
mutants/judgement.py           prose defects no probe can see, graded by a blind subagent
harness/calibrate.py           fixture + mutants -> per-item sensitivity, false-unmet rate
harness/judgement_calibrate.py prepare the judgement mutants, then score what the runs returned
harness/run.py                 set up one sandboxed run of a use case under a condition
harness/grade.py               T1 probes + science oracle + process metrics -> grading.json
harness/aggregate.py           grading files -> iteration report (always with denominators)
use-cases/<id>/                prompt, use_case.yaml, rubric.yaml, oracle/
tests/                         pytest over the probes, the mutants and the encoder
```

## The core test: hand the skill to a stranger

A skill is instructions for somebody else, so the only real test is a **fresh,
blind subagent** given the skill snapshot and a concrete scope — a repository
to work on, a PROMPT to carry out, or both — and nothing else. The authoring
session walking through its own procedure proves nothing. This is the
repo-wide rule in [`../../AGENTS.md`](../../AGENTS.md); `../../docs/stamped/PLAN.md`
§6.2 has the detail.

```console
# 1. snapshot the skill outside the repo and render the prompt
python3 evals/stamped/harness/blind_run.py prepare \
    --skill assess-alignment-with-stamped-principles \
    --object ~/scratch/compression-comparisons-t261-study \
    --workdir ~/scratch/blind-1

# 2. paste the printed prompt into a fresh subagent (the orchestrating session
#    spawns it; the script deliberately does not, so the same prompt can be
#    replayed by hand or on another model)

# 3. diff its answers against the reference, per item
python3 evals/stamped/harness/blind_run.py compare \
    ~/scratch/blind-1/out/response.json \
    evals/stamped/gold/compression-comparisons-t261-study/response.json
```

The prompt it renders carries the three clauses that make the run worth
anything: write outputs outside the target, the user is unavailable so
assumptions must be labelled, and **do not read con/skills** — `gold/` holds
the answer and a helpful agent will find it. It also asks the subagent for its
**friction**: every place the wording was ambiguous, missing or contradictory,
quoting the text at fault. That half is usually more valuable than the
verdicts.

Each difference and each friction item gets a classification — skill wording,
missing artifact, harness fault, model limit, or a defect in the reference —
and only the first two change the skill.

## Two kinds of mutant

A mutant is one deliberately broken copy of the known-good fixture, used to test
the **assessor** rather than the project. They come in two kinds, and the split
matters:

| | `mutants/mutate.py` | `mutants/judgement.py` |
|---|---|---|
| Defect | mechanical: an absolute path, a 50 MB blob in git, `url = ../..` | prose: a `make` target that does not exist, macOS-only install steps, `pixi run` in a `uv` project, impossible step order, a container nobody registered |
| Grader | the probes, in seconds, for free | a blind subagent, in minutes, for tokens |
| Scored on | exactly the declared items flipped, nothing else | one of the candidate items flagged, **the defect named**, no collateral accusations |
| Gate | the clean fixture must stay all-`met` | the **probes must stay green** — a script-catchable defect is not testing judgement |
| Catches | a probe that stopped working | a `SKILL.md` sentence that never worked |

```console
python3 evals/stamped/harness/calibrate.py                        # the scripted half
python3 evals/stamped/harness/judgement_calibrate.py prepare --workdir ~/scratch/j1
# run one blind subagent per printed prompt, then:
python3 evals/stamped/harness/judgement_calibrate.py score --workdir ~/scratch/j1
```

`prepare` builds one object per judgement mutant and **refuses any whose defect
moves a probe verdict**. That gate earned its place immediately: it rejected
`dataset-description-contradicts-layout` because `///openneuro/ds000003` in the
metadata was being read as a host-specific path — a false positive that would
have fired on every ReproNim project.

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
- **The scripts are the fast half, not the test.** The probes make the
  mechanical part cheap, repeatable and identical between the skill and its
  graders, and they tell a reading agent which items deserve its judgement. A
  passing probe suite says nothing about whether anyone can follow the skill.
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
