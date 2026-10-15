# Assessment report contract

Use the user's report path or an already authorized external report directory.
Otherwise default to `stamped-assessment-<target-name>-<YYYY-MM-DD>.md` in the current directory; reduce target name to `[A-Za-z0-9._-]`.
If that directory is inside the target, obtain an external location.
Never overwrite an existing report without authorization.

Preserve this structure:

```markdown
# STAMPED assessment

- Target: <URL or path> @ <commit / version / snapshot date>
- Assessed: <date>, by <tool + model>, assess-stamped <skill version>, level 1 | level 1 + 2
- Checklist: <version>; principles: <version>

## Profile

<the six profile points>

## Items

### MUST

#### <exact checklist item ID> (<principle codes>)
- Question: <verbatim checklist question>
- Answer: yes | no | unknown
- Evidence: <paths, revisions, commands/outcomes; inspection or execution>

### SHOULD
<same item structure>

### MAY
<same item structure>

## Gaps

1. <MUST no, then MUST unknown, then SHOULD and MAY; consequence and remedy>
```

Keep counts separate by requirement level; no aggregate score.
Seeming inapplicability belongs in the evidence, not an invented fourth answer.
Do not silently omit an item or change its normative text.

For scientific analyses, append `## Scientific validation` without changing checklist answers: identify source-semantic checks, numerical/edge-case checks, replay and figure review actually observed, with their evidence and limits.
Otherwise state that scientific correctness was not assessed.
A schema check, reproducible output or successful process alone establishes none of the other claims.
Scope a replay to its observed environment; distinguish fresh checkout, recreated environment and another host.

Record assessment-source pins and any access limitations.
A later report names its new target identity and can compare item-level changes without rewriting the earlier assessment.
