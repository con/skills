# assess-stamped: design notes

Scope decisions for the first version, and the work deliberately left for separate, drop-in follow-ups.
`SKILL.md` stays lean because every line of it is loaded into the agent's context; the reasoning lives here.
This file also holds the notes shared with [`align-stamped`](../align-stamped/DESIGN.md).

## Scope

`assess-stamped` answers three questions about one target: what does it do (or plan to do), how STAMPED is it, and what gaps remain.
It never modifies the target; its one output, the report, is written outside it so it survives to be compared with a later one.
It is the measurement half of the pair proposed in [stamped-principles/stamped-agent-skills#3](https://github.com/stamped-principles/stamped-agent-skills/issues/3); `align-stamped` is the intervention half and calls this skill first and last.

Both skills live in con/skills first, to reuse its validation CI and conventions and to be used by the people writing them. Whatever proves useful can move to [stamped-principles/stamped-agent-skills](https://github.com/stamped-principles/stamped-agent-skills) later, possibly with an automatic sync.

## Decisions

1. **No condensed STAMPED context in the skill.** The skill links to the published principles JSON, checklist JSON, paper, and examples site, pinned by tag, and tells the agent to read them.
   Three earlier assessors each paraphrased the normative statements inline and each drifted from the published codes: [stamped-examples `/stamped-assess`](https://github.com/stamped-principles/stamped-examples/blob/main/.claude/commands/stamped-assess.md), [the morphometrics `references/assessment.md`](https://github.com/STAMPED-dl-morphometrics-biases/STAMPED-dl_morphometrics_biases/blob/main/skills/stamped-neuroimaging-analysis/references/assessment.md), and the July 2026 draft in stamped-agent-skills.
   A condensed context generated from the JSON sources, so it cannot drift, is a separate optimization.
2. **One answer per checklist item, keyed by the checklist's stable item ID, with evidence for every answer.** The [checklist app](https://github.com/stamped-principles/stamped-checklist) stores `{value: yes | no | null, reason}` per item ID but only shows the reason for a `no`.
   An assessment needs the evidence behind a `yes` as much, so the report is plain markdown rather than that schema, and is not blocked on changing it.
   `unknown` maps to `null`.
3. **Profile before items.** The checklist does not carry the project's goals, but the right reading of every answer depends on them.
   The profile's "emphasis" is a prose form of the `rubric` record in [stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment) (per-principle priority and direction), so the two can converge later without committing to its 0.1 schema.
4. **Two levels of evidence.** Truly settling stampedness can require running the target, but target code is untrusted and costly to run.
   Level 1 (inspection) is unattended and never runs target code, which makes it safe on any target and comparable across runs.
   Level 2 (guided execution) works through the `unknown` items within explicit user authorization.
   An already approved scope can cover multiple identified commands; the skill does not require repeated approval for the same scope.
5. **Gaps name what and why, never which tool.** Options are delegated to the examples site's per-principle pages and the paper's sample-tools table, both of which list several tools per principle.
6. **No `allowed-tools`, in either skill.** The field grants pre-approval while the skill is active and restricts nothing, so a shared skill that sets it widens the installing user's permissions.
   These skills defer to the user's permission setup and carry their safety rules in the text; four skills on `master` already omit the field.
   The separator question for skills that do set it is [con/skills#25](https://github.com/con/skills/issues/25).
7. **Top-level `version:`**, the field APM reads, per the "Skill versions" rule proposed in [con/skills#16](https://github.com/con/skills/pull/16); the report records it.

## Deferred, each as a separate drop-in

Scoped out so this skill can land small and be measured; each can be added without changing the report format.

- **Structured output and the checklist share link.** A converter from the fixed markdown to JSON keyed by item ID, then the app's `format=3` URL; evidence for `yes` answers is dropped there until the app carries it.
- **A stamped-skills-assessment record**, as an adapter over the structured output once that schema is past its pilot.
- **FAIR**, which the stamped-examples assessor also rates; kept out so this skill measures one thing.
- **A generated normative context**; see decision 1.
## Companion workflows

`create-stamped-project`, `create-repronim-stamped-project` and `do-full-research-loop` now use this assessor alongside `align-stamped`.
They adapt the earlier five-workflow collection at `8f3acaa4a7c353b6c8ea6928c278478f95328fc5`; they do not import its custom assessment schema or validators.

The report template lives in `references/report.md`.
Its optional scientific-validation section records separate evidence; it does not extend the checklist vocabulary or make an assessment-only request execute an analysis.
Profile questions reuse supplied facts, with unresolved assumptions labeled.
Missing pinned sources must be obtained, not reconstructed.
