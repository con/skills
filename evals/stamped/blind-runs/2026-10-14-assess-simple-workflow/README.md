# Blind assess on a new object: ReproNim/simple_workflow — 2026-10-14

The done criteria ask for **one blind run on an object the loop has not been
tuned against, every iteration**, so the wording is not fitted to the gold set
([evals.md §10.1](../../../../docs/stamped/evals.md#101-done-criteria)). This
is that run: [ReproNim/simple_workflow](https://github.com/ReproNim/simple_workflow)
at `225f1dc`, sonnet, 19 tool calls, 109 k tokens, under 3 minutes.

It is a good object for the purpose — a deliberately re-executable
neuroimaging publication, with a Dockerfile, a conda environment, CircleCI, a
paper PDF and nipype PROV exports — and it is organised nothing like the
fixtures. Which is exactly why it found **five probe defects in one run**, more
than any run on a tuned object has.

## What it answered

| | |
|---|---|
| items | 31/31, `validate` clean |
| MUST | 10 met, 6 partial, 1 unmet |
| SHOULD | 4 met, 3 partial, 1 unmet, 1 n/a |
| MAY | 0 met, 2 partial, 3 unmet |

The MAY column is the interesting one: this object is *not* modular in the
STAMPED sense (no modules, inputs fetched from NITRC by URL at run time, no
navigation doc), and the assessor said so without being asked to be kind about
it. There is no reference answer yet — the user's own checklist for this object
would be the next thing that makes this run worth more.

## The five probe defects, each now fixed and pinned

1. **`entry-point` wanted a Markdown heading.** This README numbers its steps
   (`1. Install FSL`), so must/007 came back `unmet` for an object whose
   instructions are perfectly clear. The item asks whether instructions exist,
   not whether they are under a `#`.
2. **`no-abs-paths` counted `${HOME}` and `${RUNNER_TEMP}`.** Nine hits, every
   one a *variable* in a CI config — the portable way to write those paths.
   must/009 `unmet` on an object whose scripts use `$PWD` and `abspath(args)`.
3. **`env-spec-tracked` said `environment.yml` "pins no versions"** while every
   conda package in it carries a build string (`numpy=1.26.4=py311h64a7726_0`).
   A spec that fixes every version is pinned, whatever its filename.
4. **`derived-have-records` did not know nipype PROV.** The object ships
   `.provn`/`.trig` exports recording the tools and versions behind its
   outputs; the probe reported "no run record" (`unmet`). Rule 7 says name the
   mechanism you found: that is now `partial` — provenance you can read but
   not re-execute — with the artefacts cited.
5. **…and it counted the paper as a product.**
   `AVERYSimpleRe-ExecutableNeuroimagingPublication_v3.pdf` is the
   publication, not an output of the pipeline.

Three of the five are false *failures* — the probe accusing a real, careful
project of defects it does not have. That is the error that matters most here:
an assessor people distrust is worse than no assessor, and only an object
outside the tuning loop finds this class.

## Friction, and what became of it

- **Citing a line you have not opened.** `response-format.md` shows
  `"uri": "code/plot.py#L12"`, and the run cited line numbers it had not
  verified, then stripped them by hand. The format now says to cite the file
  without a fragment unless the line was actually read.
- **`stamp` and the dates.** It did not say whether it overwrites
  `assessor.date`; it does not, and the draft's UTC date stands.
- **must/014 with instances that were not followed.** The history *has*
  regeneration commits, and the Dockerfile and its `.in` template have drifted
  apart anyway. Rule 5 had no case for "a declared process with instances that
  visibly was not followed"; the run chose `partial` by judgement, which is
  what the rule now says.
- **Inputs fetched by URL at run time.** No modules at all, so
  `subdatasets-resolvable` has nothing to say and step 4's table has no row
  for the commonest real-world shape. The run chose must/002 `unmet`,
  must/001 `partial`. **Left open**: this needs a row of its own, and one run
  is not enough to write it.

## Files

```
prompt.md                 what the subagent was given, verbatim
candidate-response.json   its 31 verdicts
candidate-assessment.md   its report
candidate-probes.json     the probe sweep, before the five fixes above
run.json                  snapshot, commit, scope
```
