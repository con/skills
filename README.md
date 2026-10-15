# STAMPED skills — eval harness and run records

This branch is the **experimentation half** of the STAMPED skills developed in
[con/skills](https://github.com/con/skills): the graders, the fixtures, the
defect mutants, the use cases, and the record of every blind run. It is a
branch of con/skills itself rather than a second repository, so the whole
effort stays self-contained, and it is consumed as the `evals/` submodule of
the branch that carries the skills.

It is split out so that the pull request introducing the skills can be read.
At the point of the split the skills were 4.6k lines of the diff and this tree
was 41k: run records, transcripts and gradings grow with every iteration and
are append-only, so they would have buried the thing under review.

## Layout

```
stamped/
  README.md            how to run a condition, grade an object, record a run
  harness/             run.py, grade.py, blind_run.py, calibrate.py,
                       judgement_calibrate.py, aggregate.py
  fixtures/            make_r0_object.py — the known-good object
  mutants/             mutate.py (object defects), judgement.py (prose defects)
  use-cases/           R0, R1: prompt, rubric, oracle
  conditions/          the four arms' instructions, and the host notes
  blind-runs/          what each subagent was told and what came back
  gold/                human-anchored reference answers
  tests/               pytest over the probes, plus the pytest-evals cases
```

## Using it

The gate lives in the skills branch and runs from a checkout of it, because
the graders import the skill's own probes — the same scripts the skill ships,
so that a grader and the skill it grades cannot drift apart:

```console
git clone https://github.com/con/skills
cd skills && git switch <skills branch>
git submodule update --init evals
tox -e stamped-evals      # 89 tests, 26 eval cases, 18/18 mutants, 0/17 false
```

Paths inside this tree are unchanged by the split: it is mounted at `evals/`,
so `evals/stamped/harness/grade.py` means the same thing on both branches and
every path quoted in a run record, a plan document or a commit message still
resolves.

## What it is not

Not a package, and not stable: `harness/` is a set of scripts for one
experiment, versioned with the experiment. The skills carry `version:`
frontmatter and a compatibility contract; this tree carries dates.

Results that are too large for git — transcripts, produced objects, container
images — live in the DataLad dataset
[`con/stamped-skills-evals`](https://hub.centerforopenneuroscience.org/con/stamped-skills-evals)
instead, which pins the con/skills commit that produced them.
