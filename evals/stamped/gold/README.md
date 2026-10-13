# Gold set: real projects, with reference answers

Mutants ([`../mutants/`](../mutants/)) measure whether the assessor notices a
defect that was put there on purpose. They cannot show whether it is *fair* on
a real project, where evidence is partial, mechanisms are unusual and the
honest verdict is often `partial` or `not-checked`.

That is what this directory is for. Each entry holds one assessment of a real
object, kept as a reference answer:

```
<object-id>/assessment.md    the report, in the layout response-format.md gives
<object-id>/response.json    per-item verdicts, evidence and the pins
<object-id>/probes.json      what the scripted probes said, unedited
```

## How a reference answer is made

1. Run the probes, then fill the judgement items by reading the object
   (`assess-alignment-with-stamped-principles`, steps 3 and 4).
2. Where available, compare against a **human** answer: fill the checklist for
   the same object in the [web app](https://checklist.stamped-principles.org/),
   send the URL, and decode it with
   `stamped-conventions/scripts/encode_response.py decode <url>`. No separate
   labelling tool is needed, and disagreements between the human and the skill
   are the most valuable rows in the set.
3. Record *who* answered in `source` per item (`probe:<name>`, `judgement`,
   `human:web-app`), so a later iteration can tell them apart.

A reference answer is not frozen truth: when a maintainer corrects one, the
correction is committed with the reason, the same way the objects themselves
treat narrative.

## What is here

| Object | Why it is in the set | Assessed |
|---|---|---|
| [compression-comparisons-t261-study](compression-comparisons-t261-study/) | Heavy, real provenance (1216 run records) with two *known* gaps — the `url = ../..` tool module and no published environment specification. It is the object the MIT deck's "So I tried to `rerun` it" slide reports by hand, so the skill's answer can be checked against a human's. | 2026-10-13, probes 0.1.0 |

Planned, from `docs/stamped/PLAN.md` §6.6: STAMPED-dl_morphometrics_biases
(which has its own assessment TSV to compare against), stamped-paper,
ReproNim/simple_workflow, and `dandi/llm-analysis` as a project where STAMPED
was never a goal.

## Caveat that travels with every number here

These are assessments of *committed state at one commit*, by one assessor
version, with the scope each report states. They are evidence about the
assessor, not a grade of anybody's project — and the projects in this set were
chosen because they are good enough to have gaps worth finding.
