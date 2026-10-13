# align-stamped: design notes

Scope decisions for the first version and the work left for separate follow-ups.
`SKILL.md` stays lean because every line of it is loaded into the agent's context; the reasoning lives here.
Notes shared by both STAMPED skills (where they live, frontmatter, why sources are linked rather than restated) are in [`assess-stamped/DESIGN.md`](../assess-stamped/DESIGN.md).

## Scope

`align-stamped` is the intervention half of the pair proposed in [stamped-principles/stamped-agent-skills#3](https://github.com/stamped-principles/stamped-agent-skills/issues/3); `assess-stamped` is the measurement half.
It changes a project's meta-architecture (agent-instruction files, constitution, skills) so the STAMPED principles hold in later sessions, and it proposes options for the gaps the assessment found.
It does not itself close the gaps; the user chooses, and the project's own work tracking holds the choice.

## Decisions

1. **Assess first.** The values are baked in proportionate to the project's goals, and the profile that captures those goals is produced by `assess-stamped`.
   Writing the harness section before assessing would mean deducing the emphasis, which stamped-agent-skills#3 asks to avoid.
2. **Proportionate, not maximal.** The harness section names only the principles and rules the project's goals call for.
   A section that lists every rule for every project is the one that gets skimmed and ignored.
3. **Harness-agnostic.** The section goes into whatever the project's tools already read (`AGENTS.md`, `CLAUDE.md`, a spec-kit constitution, Copilot instructions); the skill never adds a second file of the same kind and asks before creating a first one.
   A pointer in the harness is the distribution mechanism when an agent has no skill-trigger mechanism.
4. **Options, not prescriptions.** Each gap gets two or three options with tradeoffs, always including the smallest change; the user chooses.
5. **Re-assess by offer.** The loop in stamped-agent-skills#3 (align, re-assess, align more) is closed by offering a re-assessment, not by running it unasked.

## Deferred, each as a separate follow-up

- **`create-stamped-project`**: alignment on an empty directory plus a background-gathering prelude. This skill already handles the no-harness case so a create skill can delegate to it.
- **A ReproNim-specific variant**; this skill stays generic.
- **Driving spec-kit's analysis** after a constitution changes; left to the user.
- **Suggesting other skills from this collection** for specific gaps, once there is evidence which gaps recur; a hardcoded mapping now would be a prescription by another name.
- **Measuring the effect** of aligning a project on later sessions; `assess-stamped` before and after is the instrument, and the experiment is planned in [con/skills#24](https://github.com/con/skills/pull/24).
