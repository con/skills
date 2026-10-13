# Ready-to-file PR: add a response schema to stamped-checklist-schema

**Target:** <https://github.com/stamped-principles/stamped-checklist-schema>
**Files to add:** `stamped-checklist-response-schema.yaml` (this directory's
copy, verbatim) and, if the maintainers want an example in-tree,
`examples/response-example.json` (this directory's `example-response.json`).
**Branch suggestion:** `enh-response-schema`.

Upstream conventions checked before drafting (con/skills `AGENTS.md`):

- **PR template:** none — no `.github/PULL_REQUEST_TEMPLATE.md`, no
  `PULL_REQUEST_TEMPLATE/` directory, no `docs/` variant. The body below is
  the skill's default structure.
- **CONTRIBUTING:** none, and no `DEVELOPMENT.md` or `HACKING.md`. The
  observable conventions are the three workflows: `validate.yml`
  (`linkml-validate` of `stamped-checklist.json` against the schema, plus a
  cross-schema referential-integrity script), `check_version_bump.yml` (a PR
  touching `stamped-checklist-schema.yaml` or `stamped-checklist.json` must
  bump that file's version) and `tag_release.yml`.
- **Consequence for this PR:** it adds a *new* file and leaves both versioned
  files untouched, so the version-bump gate does not apply; the new schema
  carries its own `version: 0.1.0`. Adding a `linkml-validate` step for the
  new schema to `validate.yml` is the one change the maintainers may want, and
  it is left to them because it also decides where examples live.

---

## Add a schema for *filled* checklists (`ChecklistResponse`)

### What and why

`stamped-checklist-schema` models the checklist. There is no schema for an
**answered** checklist, so every tool that produces one invents its own shape:
the web app persists one in a URL (`format=3`), `stamped-skills-assessment`
records another, the STAMPED-dl skill wrote a third as a TSV, and the skills in
[con/skills](https://github.com/con/skills) needed a fourth. The ids are
stable and shared; the answers around them are not.

This adds `stamped-checklist-response-schema.yaml`, whose **required core is
exactly what the app already persists**:

```json
{"checklist_version": "0.3.1",
 "responses": {"stamped-checklist:must/009": {"value": "no", "reason": "…"}}}
```

`value` is `yes`, `no` or absent/null; `reason` is a required string of at most
250 characters. Everything else is optional, so:

- a payload taken straight out of an app URL validates unchanged;
- a tool can add evidence and provenance without breaking the app, which
  already ignores keys it does not know.

### The optional part, and the one judgement in it

Per item: `status`, `evidence[]` (`{uri, description, sha256?}` — the same shape
as `Evidence` in `stamped-skills-assessment`) and `source` (`probe:<name>`,
`judgement`, `human:web-app`).
Top level: `schema_version`, `principles_version`, `checklist_source` (repo,
tag, commit, sha256), `object` (url, commit, captured_at, kind), `assessor`
(skill, version, harness, model, date, dependencies), `scope`, and
`extra_items[]` for findings the checklist has no id for.

`status` is the one modelling judgement worth arguing about. Five values:

| `status` | `value` | why it is separate |
|---|---|---|
| `met` | `yes` | |
| `partial` | `no` | holds by design, violated somewhere specific — a MUST is never satisfied by it |
| `unmet` | `no` | checked, and absent |
| `not-checked` | absent | **could not** be checked: tool, cost, access, scope |
| `not-applicable` | absent | cannot apply to this kind of object |

Collapsing `not-checked` into `unmet` is the single most common way an
automated assessment lies, and the app's three values cannot express the
difference. The review of
[K-Dense #265](https://github.com/K-Dense-AI/scientific-agent-skills/pull/265)
made the same point from the other direction: "not checked with the tooling
available" is not "unmet". The five values also reconcile the vocabularies
already in use (`pass/partial/fail/unknown` in the stamped-agent-skills draft,
`met/partial/unmet/restricted/n-a` in STAMPED-dl, and the judgement statuses of
`stamped-skills-assessment`).

### Evidence that it fits

- `linkml-lint` is clean apart from three style warnings, two of which are
  deliberate (see below) and one of which matches this repository's own
  `schema` prefix choice.
- `linkml-validate --target-class ChecklistResponse` passes on three real
  instances: a full 31-item response produced by a tool, the core-only payload
  decoded from an app URL, and the trimmed example in this directory.

```console
linkml-validate --schema stamped-checklist-response-schema.yaml \
    --target-class ChecklistResponse examples/response-example.json
```

### Two things for the maintainers to decide

1. **Enum naming.** `not-checked` and `not-applicable` keep the hyphens
   because they are wire values the app and existing tools already write;
   `linkml-lint` would prefer `not_checked`. Renaming them with `meaning:` or
   aliases is fine by us, as long as the JSON stays as it is.
2. **`format=4`?** The app can keep writing `format=3` forever: this schema is
   a superset, and the app drops what it does not know. If the app ever wants
   to *read* the extras (showing evidence under an item, or rendering
   `not-checked` differently from `no`), that is a new persistence format and
   worth coordinating with
   [stamped-checklist](https://github.com/stamped-principles/stamped-checklist).

### Checklist

- [x] Schema added as a new file; neither versioned file touched, so no
      version bump is required by `check_version_bump.yml`
- [x] `linkml-lint` run (3 warnings, 2 deliberate, documented above)
- [x] `linkml-validate` passes on real instances, including an app-exported one
- [ ] A `validate.yml` step for the new schema — left to the maintainers,
      together with where examples should live
- [ ] Documentation in `README.md` — happy to write it once the file layout
      is settled

### Provenance of this draft

Produced while building the STAMPED skills in
[con/skills](https://github.com/con/skills) (`docs/stamped/PLAN.md` §5), whose
assessor emits this format; the first real responses it validated against are
in that repository under `evals/stamped/gold/`.
