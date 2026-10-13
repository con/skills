---
name: align-stamped
description: >
  Align an existing project with the STAMPED principles by baking them into its meta-architecture: the agent-instruction files, constitution, and skills that shape every later session.
  Use when the user asks to make a project STAMPED, add STAMPED to it, make it reproducible or shareable, or set up its AGENTS.md / CLAUDE.md / spec-kit constitution with reproducibility in mind.
  Assesses first (assess-stamped), then writes a proportionate STAMPED section into the harness, then proposes options for each gap without prescribing tools.
version: 0.1.0
user-invocable: true
---

# Align a project with STAMPED

You are helping a project adopt the STAMPED principles (Self-contained, Tracked, Actionable, Modular, Portable, Ephemeral, Distributable) in proportion to its goals.
How deeply each principle is built in depends on what the project is for; a dataset and a compute pipeline do not need the same emphasis.
Your job is to make the principles part of how the project works, so they hold in later sessions when nobody is thinking about reproducibility, and to lay out the remaining gaps with options the user can choose between.

The normative sources are the ones `assess-stamped` lists; read them through that skill, do not paraphrase them from memory.

## Step 1: Assess

Invoke `assess-stamped` via the Skill tool, or reuse an existing report only if its recorded target commit matches the project's current HEAD.
If `assess-stamped` is not installed, stop and ask the user to install it; do not assess from memory.
When the current directory is the project, `assess-stamped` will ask where to write its report.
Everything below depends on its output: the **profile** (what the project does, what kind of object it is, its boundary and stack, which principles its goals emphasize) and the **gaps**.
If the project is new and empty, the profile comes from the user; ask, do not deduce.

## Step 2: Find the harness

Inventory what already shapes agent sessions in this project: `AGENTS.md`, `CLAUDE.md`, `.claude/` (commands, skills, settings), a spec-kit constitution (`.specify/memory/constitution.md`), `.github/copilot-instructions.md`, `CONTRIBUTING.md`, and any project-level skills.
Work within what exists; do not add a second file of the same kind.
If nothing exists, ask the user which file their tools read at session start and create only that one.

## Step 3: Bake the values in

Write one short STAMPED section into the harness, proportionate to the profile.
If a STAMPED section already exists, update it in place rather than adding a second one; if `CLAUDE.md` and `AGENTS.md` are symlinked to each other, edit one.
Show the user the proposed text before writing it; this is their project's standing instructions.
Write only that text: do not commit, and do not touch other files unless asked.

The section says:

1. That the project follows STAMPED, with a pointer to the normative sources (not a paste of them).
2. Which principles this project emphasizes and why, in one or two sentences drawn from the profile.
3. The recorded stack: how code, data, environment, execution, and provenance are handled here, so later sessions work through these tools and do not re-diagnose or introduce parallel ones.
4. The few always-on rules that follow for this project, phrased as behavior ("update the environment spec and realize it from there; never install into the running environment", "every generated file has a re-executable record", "no paths outside the project root").
   Derive each from a principle the profile emphasizes; omit rules the project's goals do not call for.
5. That `assess-stamped` is how to re-check.

Keep it short.
A section longer than the rest of the file will be skimmed, and a rule that does not apply to this project teaches the agent to ignore the section.

If the project uses a spec-kit constitution, the same content belongs there as principles, and the user may then run spec-kit's own analysis to turn them into tasks; do not run it for them.

## Step 4: Propose options for the gaps

For each gap in the assessment, MUST items first:

- State **what** is missing and **why it matters to this project**, in terms of its goals from the profile.
- Offer two or three **options**, with the tradeoff of each.
  The project's recorded stack comes first; where it has nothing for the job, draw options from the examples site's page for that principle and the paper's sample-tools table, which list several tools per principle.
  Do not recommend a single tool as the answer.
  Include the smallest change that closes the gap as one option.
  A larger change (adopting a new tool, a migration) may be another option when the project's goals warrant it; say what it buys beyond closing the gap.
- Let the user choose.
  With their confirmation, record the chosen items where this project already tracks work (issue tracker, spec-kit tasks, a `TODO` file); do not invent a new tracking file.
  If it tracks work nowhere, list the chosen items in your final message and ask where they should go.

## Step 5: Offer to re-assess

Once changes have landed or been planned, offer to run `assess-stamped` again, pointing it at what changed and what is planned, so the next report shows the delta.
If that report surfaces new obvious work, return to Step 4; do not loop without the user.

## Tone

Meet the project where it is and say what it already does well.
Meeting the MUST items is a floor, not a finish line: where the project's goals call for more, name the ideal end of the spectrum for the emphasized principles and encourage the user to keep raising the floor.
Where the goals do not call for it, do not push.
