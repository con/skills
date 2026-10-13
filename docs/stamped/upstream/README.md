# Ready-to-file upstream drafts

Phase 1 of `../PLAN.md` ends with two items that are not changes to con/skills.
They are drafted here, with their evidence, so filing them is a copy-paste
rather than a rewrite — and so the claims in them stay checkable after the
session that wrote them is gone.

| Draft | Target | State |
|---|---|---|
| [`checklist-response-pr.md`](checklist-response-pr.md) + [`stamped-checklist-response-schema.yaml`](stamped-checklist-response-schema.yaml) + [`example-response.json`](example-response.json) | [stamped-checklist-schema](https://github.com/stamped-principles/stamped-checklist-schema) | Schema written, linted and validated against three real instances. Needs someone with push access to open the PR. |
| [`paper-schema-drift-issue.md`](paper-schema-drift-issue.md) | [stamped-principles-schema](https://github.com/stamped-principles/stamped-principles-schema), cross-linked from the checklist schema | Every claim verified against `main.tex` and the two schemas at their pinned versions, with line numbers. |

Reproduce the validation of the response schema (needs `linkml`):

```console
linkml-lint docs/stamped/upstream/stamped-checklist-response-schema.yaml
linkml-validate --schema docs/stamped/upstream/stamped-checklist-response-schema.yaml \
    --target-class ChecklistResponse docs/stamped/upstream/example-response.json
linkml-validate --schema docs/stamped/upstream/stamped-checklist-response-schema.yaml \
    --target-class ChecklistResponse evals/stamped/gold/compression-comparisons-t261-study/response.json
```

The second command is the one that matters: it is a real 31-item assessment,
produced by `assess-alignment-with-stamped-principles`, validating against the
schema this repository is proposing upstream.
