---
name: do-full-research-loop
description: Carry out a specified computational research study from question and data through analysis, verification, replay, and an evidence-linked report. Use when the user asks to execute a study end to end; preserve a planning-only request's scope.
version: 0.1.0
---

# Execute the research loop

Produce the requested scientific result and an inspectable research object.
When execution is requested, a plan or scaffold is an intermediate product.
Use the project's chosen tools; this skill requires no particular package manager, provenance system, repository host, or execution service.

Read [the principles orientation](references/principles.md).
Consult and pin the current paper and checklist before making STAMPED judgments.
If the project already pins a reference bundle, retain it for comparable assessments and record newer-source differences separately.

## Establish an executable study

Extract the question, intended audience, permitted data, deliverables, resource limits, and stopping conditions from the request and project.
Identify which facts are documented and which are assumptions.
Resolve only missing facts that change the scientific question or authorization; continue independent work while waiting.
If question selection is delegated, choose a feasible question and record why its data and method can answer it.

Before analysis, retain a concise protocol: population/sample, unit of analysis, variables and units, missingness/exclusions, estimand or descriptive target, method, uncertainty, anticipated confounders, and validity checks.
Exploratory changes remain allowed, but record their timing and rationale; do not relabel them as prespecified or select results for significance.

Identify the research-object boundary and capture exact data, code, environment, parameter, and instruction identities.
Retain retrieval routes and terms as well as hashes.
Give every computation explicit inputs and outputs and a tracked executable entry point.
Establish the project's existing provenance and agent-history capture before delegating work.
Link native agent history, computational logs, and transformation provenance by trial/run identifiers; each establishes different evidence and none substitutes for the others.

## Run, inspect, and extend

1. Check access and semantics on the smallest useful slice.
   Verify columns, units, sample counts, dependencies, and the output contract before scaling.
2. Execute the pilot.
   Inspect its scientific outputs, resource use, exit status, and provenance.
   A process finishing successfully does not establish valid science.
   Diagnose failed attempts and retain their inputs, errors, interventions, and partial results distinctly from accepted outputs.
3. Complete the planned study within the recorded limits.
   Reuse a proven entry point; keep input versions fixed within a trial.
   Do not expand into a larger dataset or expensive pipeline merely because capacity exists.
   Choose a concrete retry bound before an uncertain batch.
   When it is exhausted, change the justified approach, reduce scope transparently, or report the barrier; do not repeat an unchanged failing action.
4. Test the claim with checks appropriate to the method: independent summary calculations, expected ranges, denominator and exclusion audits, simulated known cases, or sensitivity analyses.
   Distinguish technical validity from generalizability, causal interpretation, and external scientific truth.
5. Replay from recorded inputs and environment definitions in a fresh disposable workspace.
   Compare prespecified outputs using exact digests for deterministic artifacts or declared numerical/semantic tolerances.
   A rerun in the original directory is useful but does not establish clean restoration, cross-platform portability, or independent reproduction.

Keep the work moving through these stages.
Only pause dependent work for a real authorization/access dependency or a scientific ambiguity that cannot be resolved honestly.
Retain the useful completed result if some stage is blocked.

## Deliver and assess

Deliver the executable analysis, results/figures, source identities, environment definition, replay instructions and observed replay outcome, and a concise evidence-linked interpretation with limits and unresolved gaps.
Preserve computational evidence before disposable environments are removed.
Sharing an artifact is a separate action from preparing it; follow the user's actual publication scope.

Use [the assessment contract](references/assessment-contract.md) and [the JSON Schema](references/research-assessment.schema.json) for a structured assessment when requested or when this is a skill-evaluation study.
Report scientific validity and the seven STAMPED properties separately.
A reproducible mistake remains a scientific mistake.
A correct number can have an unusable research object.
Neither becomes a universal score.

For comparisons with and without a skill, read [the comparison protocol](references/paired-evaluation.md) before starting either arm.
Do not invent use, outcome, timing, or token measurements.
One exploratory pair illustrates behavior under its conditions; it does not establish general skill efficacy.
