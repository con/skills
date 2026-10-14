---
name: assess-alignment-with-stamped-principles
description: Assess an existing project, dataset, workflow, or research object against STAMPED for its documented use case, retaining criterion-level evidence and checklist responses. Use for assessment; use an alignment workflow when changes are requested.
version: 0.1.0
---

# Assess STAMPED alignment

Assess the specified object and exact snapshot, not the reputation of its tools.
Establish its intended use, audience, boundary, components, and relevant constraints from documentation and the user.
Distinguish the software that produces research objects from an actual produced object.
Do not infer an undocumented scientific objective merely from filenames.
Record unresolved goals as assumptions or questions while inspecting what is available.

Read [the principles orientation](references/principles.md), then consult the paper and checklist at pinned revisions.
Prefer an existing project reference bundle for longitudinal comparison; report newer-source differences separately.
Use current normative statements without converting SHOULD/MAY guidance into universal requirements.
An operational summary is not a replacement paper.

## Collect evidence proportional to the claim

Define observable criteria and scope before scoring.
Use the checklist's stable item IDs and exact version; add use-case criteria when needed.
Record priority, intended direction (maximize, balance, preserve), rationale, and required evidence-gathering activities.
Lower priority does not erase an unmet normative requirement.

Inspect instructions, component identities, environment definitions, transformation records, module interfaces, access/license conditions, and retained outputs.
Resolve references, retrieve data, construct environments, execute, compare, or independently reproduce when the task and resources authorize those checks.
A read-only review does not authorize executing arbitrary project commands.
State the coverage actually achieved.

Keep observations distinct from judgments.
An attempted operation can finish and reveal a failure; a missing attempt is not an observed access barrier.
Use demonstrated, partial, not_demonstrated, unknown, or not_applicable with criterion-specific reasons and evidence.
Require the planned evidence for a positive judgment.
A successful command, lockfile, container, or repository alone proves no other property.
Ephemerality concerns computation, not discarding valuable results.
Access restrictions need intended-recipient context before concluding that distribution is impossible.

## Return reusable evidence

Produce a seven-property table: criterion, observed implementation/evidence, judgment, uncertainty, remaining gap, and smallest relevant next step.
Preserve all checklist items, marking unassessed items unknown and justified exclusions not_applicable.
Do not aggregate principles into an unqualified compliance score.
Keep scientific correctness separate from research-object quality.

Use [the assessment contract](references/assessment-contract.md) and [the schema](references/research-assessment.schema.json) for a portable JSON record, or the project's established schema with an explicit field crosswalk.
Include the skill version and exact source snapshot/digest, assessor identity, reference versions, observed activities, conditions, evidence, and gaps. Distinguish unreviewed agent assertions from independent human/agent reviews.
Corrections become new records that supersede the old record.

Emit a checklist-compatible side product following [the checklist response reference](references/checklist-responses.md).
Keep rich judgments and evidence in the assessment; the UI's yes/no/null and short reason field cannot represent all states.
Use the bundled export helper only with a pinned checklist and the reviewed per-item answers.
Report source version conflicts rather than silently translating incompatible criteria.

Assessment does not imply mutation.
When changes are requested, hand off the evidence and priorities to an alignment workflow, then reassess the resulting snapshot with the same criteria and explicit additions.
