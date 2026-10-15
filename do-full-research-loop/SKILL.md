---
name: do-full-research-loop
description: Execute a specified computational research study from question and data through analysis, verification, figures, replay and an evidence-linked report. Use for an end-to-end study or a requested scientific result; preserve a planning-only request's scope.
version: 0.1.0
---

# Carry the study through to results

Use the project's chosen tools and authorized resources.
A plan or scaffold is intermediate when results were requested.
If a project is needed, use [create-stamped-project](../create-stamped-project/SKILL.md); use [assess-stamped](../assess-stamped/SKILL.md) for STAMPED judgments.
Materialize missing declared siblings from the selected collection rather than silently omitting them.

## Plan the calculation

Retain a concise protocol before analysis: question, sample/unit of analysis, variables/units, missingness and exclusions, descriptive target or estimand, method, uncertainty, checks, deliverables, resource limit and stopping condition.
Extract known decisions from the request; resolve only consequential ambiguities.
Label exploratory changes with timing and rationale; do not relabel them as prespecified.

Identify exact data/code/parameter inputs and the evolving task environment.
Reuse maintained scientific packages and community pipelines; declare ordinary missing dependencies and install them in the owning environment.
Do not replace established numerical or plotting tools merely to avoid a dependency.
Follow the project's capture and final environment-snapshot policy without activating unrelated controls.

## Pilot, complete, verify

1. Inspect the smallest useful slice: semantics, units, selection/counts and output contract.
   Run it through the declared entry point; examine its values, QC, exit status and resource use before scaling.
2. Complete the planned analysis within the budget.
   Retain failures and interventions; choose bounded retries and revise the approach when evidence warrants it.
   A method change gets a distinguishable result/version, not a silent overwrite.
3. Apply [references/validation.md](references/validation.md): independent calculations or known cases, relevant edge conditions, appropriate sensitivity checks, rendered figures and fresh replay.
   Reserve time for these checks before optional report expansion.
4. Interpret what the evidence supports, including uncertainty, missingness and causal limits.
   A successful process or reproducible number is not sufficient evidence of scientific correctness.

Continue independent work when a dependency is blocked.
Preserve the useful completed result and report the exact unresolved barrier; do not claim unfinished stages passed.

## Deliver

Retain executable analysis, results, figure source/preview where useful, source identities, final environment evidence, requested execution records, replay command/outcome and concise interpretation.
Prepare publication only within the user's scope.
Assess research-object quality separately from scientific validation, with explicit unchecked items and no universal score.

For a comparison of skill conditions, read [references/comparisons.md](references/comparisons.md) before any arm starts.
Ordinary research does not require that experimental machinery.
