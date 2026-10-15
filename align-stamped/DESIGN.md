# align-stamped: design notes

Scope decisions for the first version and the work left for separate follow-ups.
`SKILL.md` stays lean because every line of it is loaded into the agent's context; the reasoning lives here.
Notes shared by both STAMPED skills (where they live, frontmatter, why sources are linked rather than restated) are in [`assess-stamped/DESIGN.md`](../assess-stamped/DESIGN.md).

## Scope

`align-stamped` is the intervention half of the pair proposed in [stamped-principles/stamped-agent-skills#3](https://github.com/stamped-principles/stamped-agent-skills/issues/3); `assess-stamped` is the measurement half.
It changes a project's meta-architecture (agent-instruction files, constitution, skills) so the STAMPED principles hold in later sessions, and it proposes options for the gaps the assessment found.
It distinguishes advice, standing-instruction changes and implementation.
An implementation request includes scoped fixes, checks and reassessment; earlier user decisions remain authorization.
Scientific-method changes remain separate from improvements to the research object.

## Decisions

1. **Assess first.** The values are baked in proportionate to the project's goals, and the profile that captures those goals is produced by `assess-stamped`.
   Writing the harness section before assessing would mean deducing the emphasis, which stamped-agent-skills#3 asks to avoid.
2. **Proportionate, not maximal.** The harness section names only the principles and rules the project's goals call for.
   A section that lists every rule for every project is the one that gets skimmed and ignored.
3. **Harness-agnostic.** The section goes into whatever the project's tools already read (`AGENTS.md`, `CLAUDE.md`, a spec-kit constitution, Copilot instructions); the skill avoids a second file of the same kind and resolves the harness choice when it is unknown.
   A pointer in the harness is the distribution mechanism when an agent has no skill-trigger mechanism.
4. **Proportionate choices.** Name the smallest effective fix and alternatives where a meaningful tradeoff exists.
   Reuse the chosen stack and authorized scope; do not manufacture choices for routine work.
5. **Close the requested loop.** Advice stops at proposals.
   Implementation includes verification and reassessment of changed properties, preserving before/after object identities and unresolved findings.

## Deferred, each as a separate follow-up

- **Driving spec-kit's analysis** after a constitution changes; left to the user.
- **Suggesting other skills from this collection** for specific gaps, once there is evidence which gaps recur; a hardcoded mapping now would be a prescription by another name.
- **Measuring the effect** of aligning a project on later sessions; `assess-stamped` before and after is the instrument, and the experiment is planned in [con/skills#24](https://github.com/con/skills/pull/24).

## Companion creation skills

`create-stamped-project` and its ReproNim adapter establish a usable project and delegate broader alignment here.
This skill stays tool-neutral.
The revision retains Austin's profile-first, harness-aware approach while allowing requested implementation to finish rather than stopping at recommendations.
