# Portable research assessment contract, draft 0.1.0

Use the adjacent JSON Schema to record one exact object snapshot and assessor assertion.
The schema is a study envelope, not an official STAMPED standard or a replacement for the existing stamped-skills-assessment model.
Structural validation cannot establish truth, comprehensive coverage, or skill efficacy.

Record `schema_version`, unique `assessment_id` and `run_id`, task and object identity, the assessor/instrument, reference sources, conditions, criteria, observations, judgments, metrics, interventions, and limitations. Every source needs an immutable revision or SHA-256 and a retrievable locator; a digest without available bytes establishes identity only. A dirty tree needs a retained snapshot/diff digest in addition to its base commit.

`science` contains question-specific criteria.
`research_object` has separate S/T/A/M/P/E/D arrays.
At least one criterion is needed per property; whole-object coverage still depends on the declared rubric.
Add a reasoned not_applicable criterion when no computation exists instead of manufacturing an execution requirement.
Maintain a separately pinned rubric for cross-run comparisons.

Every criterion has a target, priority/rationale, required activities, actual observations, judgment, and judgment rationale. An activity has a status of completed, blocked, or not_attempted. Completed execution can produce negative evidence. A blocked observation must name an observed barrier; an unattempted activity cannot be called blocked solely because no evidence was captured. Evidence states whether it is direct observation or an assertion and identifies its producer and location/digest.
Required activities must be represented.

Judgment meanings:

- demonstrated: sufficient relevant evidence supports the criterion within its stated scope; all required activities were completed with evidence;
- partial: some but not all of the target was established;
- not_demonstrated: observed evidence establishes an unmet target;
- unknown: the evidence cannot determine the target's state;
- not_applicable: the target does not apply, with a use-case rationale.

Use no aggregate STAMPED/science score.
Report criterion denominators and missingness.
Numeric effort measures need a unit and measurement scope; unavailable measures are null.
Do not sum overlapping agent durations or attribute all session time to a skill.
Keep self-report and independent review separate.
Finalized means the report accounts for its scope, not that the study succeeded.
A review cites the exact assessment digest and does not rewrite the original assertion; corrections use `supersedes`.

Optional `comparison` identifies the experimental protocol, arm, pair/group, shared infrastructure, isolation, and deviations. Both arms must cite the same protocol/task/data/rubric where intended; validators do not prove context isolation.
Separate post-hoc assisted rescue from the original outcome.

## Crosswalk to the existing assessment model

The independently maintained [stamped-skills-assessment](https://github.com/stamped-principles/stamped-skills-assessment/tree/c4c0428e6962a631d910d0becb00b7bb1c3c903c) provides `use_case`, `object`, `rubric`, `assessment`, and `review` records.
Its activity and judgment vocabulary informs this envelope.
For an upstream export, map task/object metadata to use_case/object, pin the exact upstream reference lock, map the seven-property criteria and priorities to rubric, and map observations/judgments to assessment.
Retain science criteria, comparison details, collector coverage, and metrics in a separately linked manifest where upstream has no dedicated field.
Do not invent upstream fields or claim schema compatibility without running its validator.

## Checklist side product

Retain the source-qualified stable checklist ID, version, detailed judgment, and evidence for every item, including unassessed items.
A format-3 UI export uses yes only for demonstrated items, no for observed unmet items, and null for partial/unknown/not_applicable; preserve the richer meaning separately.
The UI reason limit is 250 characters.
A short reason or URL is not the full assessment or its evidence archive.

## Validate before review

The bundled `scripts/validate_assessment.py` requires Python 3.9+ and `jsonschema>=4,<5` in the selected environment.
Run it with the assessment path.
It validates the JSON Schema and checks that every required activity is accounted for, positive judgments have completed evidence, and missing evidence is not reported as an observed failure.
It cannot establish the correctness of the evidence, effective isolation of trial arms, or scientific conclusions.
