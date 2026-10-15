---
name: do-full-research-loop
version: 0.1.0
description: Execute a computational study through a protocol, inspected pilot, bounded batches, figures, scientific checks, fresh replay and an evidence-linked report. Use when results are requested; preserve planning-only scope.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion, Skill, Task
user-invocable: true
max-lines: 140
---

# Execute the research loop

Produce the requested scientific result and an inspectable research object.
Use [create-stamped-project](../create-stamped-project/SKILL.md) only if the required project structure is absent.
Read [stamped-conventions](../stamped-conventions/SKILL.md) and the applicable stack reference; retain an already frozen assessment bundle for comparable judgments.

## Establish the protocol

Extract the question, permitted data, deliverables, limits and stopping conditions from the request and project.
Before analysis, retain the sample and unit of analysis, variables/units, missingness and exclusions, estimand or descriptive target, method, uncertainty and validity checks.
Mark assumptions; resolve consequential scientific ambiguity while continuing independent work.
A recorded protocol supports execution already authorized by the user; it does not introduce another approval gate.

Record exact data, code, parameters and environment identities and their retrieval routes.
Use community analysis packages, domain pipelines and plotting tools; add dependencies through the project's environment manager.
Expose the analysis through the project's task runner.
Respect the chosen lock policy and preserve the exact environment used for validation.
For an explicit skill comparison, read [references/comparisons.md](references/comparisons.md) before either arm.

## Pilot, inspect and scale

1. Run the smallest useful unit through the project's recorded mechanism with explicit inputs and outputs.
   Verify source meanings, units, sample counts and expected output structure.
   Inspect the actual result, execution status and resource use; exit zero is not scientific validation.
2. Diagnose failures before retrying.
   Retain failed attempts and partial outputs separately from accepted results, with interventions and their reasons.
   Bound uncertain retries; change the approach or report the barrier when the bound is reached.
3. Reuse the proven entry point for bounded batches, reviewing failures, QC and values between batches.
   Keep input versions fixed within a trial.
   Record method revisions before the next run and pilot the changed method again.
   A revised method creates a distinguishable derivative rather than overwriting the earlier measurement.
4. Aggregate and plot through the recorded workflow.
   Use a figure when it clarifies the result, variation, QC or study progress; do not defer every useful figure to final presentation.
   Retain its editable source and inspect the rendered figure at intended display size.
5. Test the scientific claim and replay with [references/validation.md](references/validation.md).
   Use independent expected results or controls appropriate to the design; do not impose paired analysis on unpaired data or a null control with no meaningful interpretation.

Commit executable inputs before recorded computation, avoid unrelated commits during it, and regenerate derivatives rather than editing values by hand.
For DataLad execution and annex delivery, use [datalad-annex](../datalad-annex/SKILL.md).
When duct capture is requested, retain command metadata, stdout/stderr, resource use and the completed summary with the owning experiment; annex large records.
Use an orchestrator's native layout, including MechaBABS, when it already provides provenance.
Native agent history, computation logs and transformation records establish different evidence; link requested records by run identity.

## Review and deliver

Have a fresh reviewer inspect the committed object and scientific question without your narrative of what succeeded.
Ask for the work product and specific friction; retain findings and address supported defects.
Replay from a fresh checkout with generated outputs absent and the recorded environment restored.
Compare exact artifacts or declared scientific tolerances; confirm regenerated output so a no-op cannot count as a replay.
A same-host replay does not establish another platform works.

Deliver checked results and useful figures, executable analysis, source and environment identities, replay outcome and a concise interpretation with uncertainties and scope limits.
Do not relabel exploratory choices as prespecified or select results for significance.
Report scientific validity separately from STAMPED properties: a reproducible error remains an error.

Run [assess-alignment-with-stamped-principles](../assess-alignment-with-stamped-principles/SKILL.md) against the finished commit, writing its report outside the assessed tree or in an ignored directory.
Use [align-with-stamped-principles](../align-with-stamped-principles/SKILL.md) for remaining in-scope workflow gaps, then reassess the changed commit.
Publish within the requested scope; required child commits and annex payloads must be retrievable before claiming a self-contained deliverable.
Retain completed work and name unresolved gaps when access or external services prevent a stage from finishing.
