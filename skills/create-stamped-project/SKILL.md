---
name: create-stamped-project
version: 0.1.0
description: Create a computational research project with explicit inputs, an executable entry point, environment and provenance records, and a tested retrieval route. Use for a new project or missing project structure; preserve an existing prepared project.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep, AskUserQuestion, Skill
user-invocable: true
max-lines: 120
---

# Create a STAMPED project

Read [stamped-conventions](../stamped-conventions/SKILL.md), its principles card and project kinds, then the relevant stack reference.
Use the supplied question, inputs, chosen tools, resource limits and deliverables; ask only for consequential missing facts.
Inspect supplied examples before selecting a layout.
Keep documented facts separate from assumptions.

## Create the smallest complete slice

1. Identify the research-object root, input identities and access terms, module boundaries, expected outputs and retrieval route.
   Reuse an existing project; add ordinary experiment directories and root environment dependencies, rather than nesting whole checkouts under experiments.
   Place concurrent writable worktrees outside the tracked project; initialize each child's submodules at their recorded commits.
2. Use the selected stack and established scientific packages.
   Add ordinary missing packages to the project environment; do not silently borrow another project's executable or replace a requested dependency with custom science.
   Expose working entry points through the project's task runner.
   Honor its environment policy and record how a recipient obtains the exact environment used for each run; use [pixi-with-stamped](../pixi-with-stamped/SKILL.md) when Pixi is selected.
3. Link versioned inputs through DataLad subdatasets, Git submodules or persistent source identities with retrieval instructions.
   Retrieve only the needed slice; preserve raw inputs and their metadata.
   Keep reusable code and small specifications in Git; use annex for large inputs, outputs and requested logs.
4. Implement a runnable slice with declared inputs and outputs.
   Reuse [templates](templates/) for the selected stack; adapt existing hooks and entry points instead of replacing them.
   In DataLad projects, use [datalad-annex](../datalad-annex/SKILL.md): leave native run messages intact so native rerun recognizes them.
   Run preparation checks and exercise installed guards before relying on them.
5. Verify the complete path through one computation, output inspection and fresh-checkout replay.
   Confirm actual content retrieval, not just Git refs; for a named publication target, publish required child commits and annex bytes before the parent pointer.
   Publish the annex location records as well as payloads; when history and content use different remotes, document both in the README.
   For shared publication repositories, follow the explicit-refspec recipe in [the DataLad stack reference](../stamped-conventions/references/stacks/datalad.md); do not let annex sync push an unintended branch.
   Where remote delivery or a platform cannot be tested, identify that specific gap.
6. Write a short README: question, declared inputs, existing executable task, environment/replay route, outputs and observed limits.
   Future agent instructions need only decisions specific to this project; do not copy the principles or an incident history into them.

Use [entire-worktrees](../entire-worktrees/SKILL.md) when native agent capture is requested, before launching workers.
A prepared launch route should supply the environment, modules and hooks so the research worker can start its task.
Keep host credential providers and tool locations replaceable and outside tracked project configuration.

## Hand off

Commit the working slice under the project's policy and use [align-with-stamped-principles](../align-with-stamped-principles/SKILL.md) to assess and close scoped gaps.
When results were requested, continue with [do-full-research-loop](../do-full-research-loop/SKILL.md); project creation alone is not that deliverable.
