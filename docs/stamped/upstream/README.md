# Ready-to-file upstream drafts

Phase 1 of `../PLAN.md` ends with two items that are not changes to con/skills.
They are drafted here, with their evidence, so filing them is a copy-paste
rather than a rewrite — and so the claims in them stay checkable after the
session that wrote them is gone.

| Draft | Target | State |
|---|---|---|
| [`checklist-response-pr.md`](checklist-response-pr.md) + [`stamped-checklist-response-schema.yaml`](stamped-checklist-response-schema.yaml) + [`example-response.json`](example-response.json) | [stamped-checklist-schema](https://github.com/stamped-principles/stamped-checklist-schema) | Schema written, linted and validated against three real instances. Needs someone with push access to open the PR. |
| [`paper-schema-drift-issue.md`](paper-schema-drift-issue.md) | [stamped-principles-schema](https://github.com/stamped-principles/stamped-principles-schema), cross-linked from the checklist schema | Every claim verified against `main.tex` and the two schemas at their pinned versions, with line numbers. |

## Filing them

Both need push access this repository's sessions do not have, so they are left
as two copy-pastes rather than as prose. In each draft everything above the
first `---` is *about* filing it; the body is everything below.

**The issue** (no fork needed):

```console
gh issue create --repo stamped-principles/stamped-principles-schema \
  --title 'Principles schema 0.2.0 drifts from the paper: three principles missing, one split, one with no checklist item — plus two identical checklist items' \
  --body "$(sed -n '/^---$/,$p' docs/stamped/upstream/paper-schema-drift-issue.md | tail -n +3)"
```

Section 3 (the two identical checklist items) belongs in
`stamped-principles/stamped-checklist-schema` if the maintainers prefer one
issue per repository; cross-link rather than duplicate.

**The PR.** The target has no PR template and no contributing guide — checked,
and recorded at the top of the draft — but it does gate a version bump on the
two existing versioned files, which this PR does not touch:

```console
gh repo fork stamped-principles/stamped-checklist-schema --clone --remote
cd stamped-checklist-schema && git switch -c enh-response-schema
cp <con/skills>/docs/stamped/upstream/stamped-checklist-response-schema.yaml .
mkdir -p examples && cp <con/skills>/docs/stamped/upstream/example-response.json examples/response-example.json
git add -A && git commit -m 'Add ChecklistResponse schema for filled checklists'
git push -u origin enh-response-schema
gh pr create --repo stamped-principles/stamped-checklist-schema \
  --title 'Add a schema for filled checklists (ChecklistResponse)' \
  --body "$(sed -n '/^---$/,$p' <con/skills>/docs/stamped/upstream/checklist-response-pr.md | tail -n +4)"
```

Run the three validation commands below **before** pushing: they are the
evidence the PR body claims.

Reproduce the validation of the response schema (needs `linkml`):

```console
linkml-lint docs/stamped/upstream/stamped-checklist-response-schema.yaml
linkml-validate --schema docs/stamped/upstream/stamped-checklist-response-schema.yaml \
    --target-class ChecklistResponse docs/stamped/upstream/example-response.json
linkml-validate --schema docs/stamped/upstream/stamped-checklist-response-schema.yaml \
    --target-class ChecklistResponse evals/stamped/gold/compression-comparisons-t261-study/response.json
linkml-validate --schema docs/stamped/upstream/stamped-checklist-response-schema.yaml \
    --target-class ChecklistResponse \
    evals/stamped/blind-runs/2026-10-14-r0-explicit-repeats/explicit-haiku-r1.response.json
```

The last two are the ones that matter: real 31-item assessments produced by
`assess-alignment-with-stamped-principles` on two model tiers, validating
against the schema this repository is proposing upstream.

**Re-run them before filing.** On 2026-10-15 they failed: the schema had
fallen three fields behind its own producers (`flags` on an item, `drafted_by`
and `note` on the assessor). A schema proposed for other people's tooling is
only as good as its last validation against ours.
