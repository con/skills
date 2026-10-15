---
name: align-with-stamped-principles
version: 0.1.0
description: Assess an existing project against STAMPED, apply scoped improvements to its instructions and executable workflow, and reassess. Use to act on assessment findings while preserving the scientific method and existing stack.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
max-lines: 100
---

# Align a project with STAMPED

Read [stamped-conventions](../stamped-conventions/SKILL.md) and the applicable stack reference.
Run [assess-alignment-with-stamped-principles](../assess-alignment-with-stamped-principles/SKILL.md) against the committed project.
Retain the assessed revision and rubric identity; use the same assessor and checklist for before/after comparisons.
Do not silently change a frozen assessment to suit improvements to the working skills.

## Choose and apply a useful fix

Use the assessment's evidence to select the highest-value gaps within the request.
Name the change, the relevant checklist IDs and why it helps this project.
Apply authorized fixes directly; ask only where a material scope choice or new authorization is needed.
Existing strengths and deliberate tradeoffs do not require replacement.

Prefer executable fixes to additional instructions:

- Repair the existing task, manifest, retrieval route or provenance mechanism.
- Add proportionate guards from [create-stamped-project/templates](../create-stamped-project/templates/) only where a demonstrated gap needs one.
  Compose existing hooks; exercise the guard's allowed and rejected cases.
- Add a short section to the existing `AGENTS.md` or equivalent only for project-specific decisions that future work must retain.
- Reuse a relevant installed skill, such as [datalad-annex](../datalad-annex/SKILL.md), rather than duplicating its operating instructions.
- Amend a spec-kit constitution only when the project already uses one.

Keep the diff to the project's workflow and instructions.
Scientific recomputation or a changed method belongs in [do-full-research-loop](../do-full-research-loop/SKILL.md) and must be within the user's requested scope.
Do not manually patch measurements to make an assessment pass.
Honor the project's environment policy, including separate exact lock snapshots where specified.
Native DataLad run commits retain their machine-readable message; normal authored commits follow the project's commit convention.

## Check and reassess

Validate the actual repaired entry point or retrieval route; a passing syntax check does not establish it works.
Commit coherent changes with the affected checklist IDs, without interrupting an active recorded run.
Reassess the new committed object using the unchanged rubric and report item-level differences with evidence.
Continue while useful in-scope fixes remain; identify unresolved access, method or user-decision dependencies without claiming completion on those items.
