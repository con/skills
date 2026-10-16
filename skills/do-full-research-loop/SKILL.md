---
name: do-full-research-loop
version: 0.1.0
description: Execute a computational study through a protocol, inspected pilot, bounded batches, figures, scientific checks, proportionate validation and an evidence-linked report. Use when results are requested; preserve planning-only scope.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion, Skill, Task
user-invocable: true
max-lines: 140
---

# Execute the research loop

Produce the requested scientific result and an inspectable research object.
Keep the researcher's existing tools and delivery format when they support the task.
Use [create-stamped-project](../create-stamped-project/SKILL.md) only when the requested work needs a new project structure; available infrastructure is not a mandate to adopt it.
Read [stamped-conventions](../stamped-conventions/SKILL.md); use a supplied [stack reference](../stamped-conventions/references/stacks/) when it matches the project's tools.
Retain an already frozen assessment bundle for comparable judgments.

## Establish the protocol

Extract the question, permitted data, deliverables, limits and stopping conditions from the request and project.
Before analysis, retain the sample and unit of analysis, variables/units, missingness and exclusions, estimand or descriptive target, method, uncertainty and validity checks.
Mark assumptions; resolve consequential scientific ambiguity while continuing independent work.
A recorded protocol supports execution already authorized by the user; it does not introduce another approval gate.

Record exact data, code, parameters and environment identities and their retrieval routes.
Use community analysis packages, domain pipelines and plotting tools; add dependencies through the project's environment manager.
Retain an executable entry point using the project's existing interface; a script, notebook or documented command can suffice.
A shared interpreter is an execution resource, not a reconstruction recipe.
Deliver an environment recipe and the exact identity used for validation, with acquisition and launch instructions; honor the project's lock policy.
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

Preserve the exact executable inputs used for computation through the project's provenance mechanism; regenerate derivatives rather than editing values by hand.
When the chosen mechanism requires committed inputs, commit them before that recorded run.
Use [datalad-annex](../datalad-annex/SKILL.md) when DataLad execution or annex delivery is part of the task.
When duct capture is requested, retain command metadata, stdout/stderr, resource use and the completed summary with the owning experiment; annex large records.
Use an orchestrator's native layout, including MechaBABS, when it already provides provenance.
Native agent history, computation logs and transformation records establish different evidence; link requested records by run identity.

## Review and deliver

Select review and replay by the consequences of an undetected error and the evidence already available.
For a nontrivial scientific claim, an independent reviewer or numerical reference check should challenge the result, not merely inspect file presence.
Give a fresh reviewer the exact delivered state and scientific question without your success narrative; uncommitted and ignored deliverables can be relevant evidence.
Retain specific findings and address supported defects within scope.

When execution uncertainty warrants a fresh replay and the necessary resources are available, use the recorded environment and preserve inputs while removing only explicitly selected generated outputs.
Compare regenerated scientific values, identifiers and declared tolerances; incidental timestamps or prose changes need separate interpretation.
A same-host replay does not establish another platform works; an unavailable adapter or external service is a validation limitation, not proof of a scientific error.

Deliver checked results and useful figures, executable analysis, source and environment identities, validation evidence and a concise interpretation with uncertainties and scope limits.
Keep artifacts supporting the conclusions in the delivered object; temporary scratch paths alone are not a retrieval route.
Do not relabel exploratory choices as prespecified or select results for significance.
Report scientific validity separately from STAMPED properties: a reproducible error remains an error.

Use [assess-alignment-with-stamped-principles](../assess-alignment-with-stamped-principles/SKILL.md) when STAMPED assessment is requested or needed to settle an unresolved delivery question; keep its output separate from the assessed state.
Use [align-with-stamped-principles](../align-with-stamped-principles/SKILL.md) only for remaining in-scope gaps.
Recheck what a correction can affect: code, data or environment changes may require numerical validation; prose-only corrections normally need document review, not another analysis, fresh review and full assessment cycle.
Stop when the requested result and proportionate checks are complete; report unresolved limits instead of extending a repair loop to obtain a passing assessment.
Publish within the requested scope; verify required child objects and payloads before claiming a self-contained deliverable.
Attribute later coordinator preservation separately from the worker's original state and actions.
