# Scoped independent followability check

2026-10-15 UTC. For each fixture: **2/3 requested MUST items met, 1/3 unmet**. These are engineering fixtures, not scientific evidence. No scientific code was executed and no installation or network operation was performed.

**Goal and kind:** The supplied goal is declaring the execution environment for a small numerical Python tool. I treated both objects as components/tools. This is a task-supplied scope, not a purpose inferred from filenames; neither fixture has documentation independently confirming it.

The first useful change is to add a frozen, content-identified environment record for exact replication (must/015). Floating declarations already establish dependency inclusion and tracked specifications within these small object boundaries.

## Objects and evidence

1. `/tmp/stamped-dependency-inclusion-fixtures/test_unpinned_dependency_inclu1/floating`, commit `3604a10db0005bd635a46e041dde64fbc5098d96`. The complete committed tree contains only `pixi.toml`:

   ```toml
   [workspace]
   name = "demo"
   [dependencies]
   python = "*"
   numpy = "*"
   ```

2. `/tmp/stamped-dependency-inclusion-fixtures/test_unpinned_dependency_inclu2/floating`, commit `8318f6c3f26337094fa4febcbd9026e81963ddfa`. The complete committed tree contains only `analysis.py`:

   ```python
   # /// script
   # dependencies = ["numpy"]
   # ///
   import numpy
   ```

Evidence was read with `git show HEAD:<file>` and inventory checked with `git ls-tree -r --name-only HEAD`. Both working trees were clean; `git show-ref` showed only the respective `main` commit. There are no tracked lockfiles, container digests, alternate environment references, data, result records, or retrieval documentation in these exhaustive one-file trees. The first fixture has no computational entry point; the second exposes only the import above. No execution or publication judgment is made outside the three requested items.

## Script suggestions versus judgments

| Object | Item | Script suggestion | Assessor judgment and evidence |
|---|---|---|---|
| Pixi | must/010 | met | **met**: `pixi.toml` declares Python and NumPy. No executable code in the committed object demonstrates an omitted dependency. A wildcard does not remove a dependency from the specification. |
| Pixi | must/013 | met | **met**: `git ls-tree` and `git show` establish that the environment declaration is committed. |
| Pixi | must/015 | not-checked | **unmet**: both dependency versions are `"*"`, and the entire committed boundary has no frozen manifest or immutable environment reference. |
| Inline script | must/010 | met | **met**: the only imported external package, `numpy`, is explicitly listed in the inline script metadata. |
| Inline script | must/013 | met | **met**: `analysis.py`, including its environment metadata, is committed; a separate manifest filename is unnecessary. |
| Inline script | must/015 | not-checked | **unmet**: `dependencies = ["numpy"]` permits version resolution to float; no frozen manifest or other pin is included. |

The pinned checklist separates these properties: must/010 asks whether all software dependencies are included rather than assumed pre-installed; must/013 asks whether specifications are version controlled; must/015 asks whether the specifications permit an attempt to exactly replicate the environment. These judgments do not treat a successful install or scientific run as established.

For must/010 and must/013, source is `probe:env-spec-tracked+judgement`. For both must/015 judgments, source is `probe:run-env-linked+judgement`, flag `probe-overridden`. The probe said **“Nothing names an environment to check for a pin.”** The committed declarations do name environments, and their floating constraints can be judged without run records. The lack of records therefore does not prevent the narrower must/015 judgment here.

Raw probe results are retained in `fixture1-probes.json` and `fixture2-probes.json`. Those bundled probes also emit other item fields; those fields are untouched script output and were not adopted as assessment judgments. In particular, the top-level `env-spec-tracked` status is `unmet` because of its out-of-scope must/016 result: its per-item must/010 and must/013 results are both `met`.

## Followability friction and ambiguity

- The documented `encode_response.py items --level must` failed with `ModuleNotFoundError: No module named 'jsonschema'`. Both documented `run_probes.py ... --only env-spec-tracked run-env-linked -o ...` invocations failed for the same reason, even without requesting response JSON. The snapshot explicitly lists `jsonschema` as a caller-provided dependency, so this is an unmet runtime prerequisite rather than an undisclosed dependency. The no-install constraint prevented using the documented CLI end to end.
- I recovered read-only script evidence by importing `Object` and the two functions from the snapshot's `probes` registry under system Python and serializing their unchanged `asdict()` results. This was an assessor workaround, not the documented workflow and not a validated full response. The report and raw outputs identify that route explicitly. The checklist was read directly from its vendored JSON; `vendor_checklist.py --check` passed.
- The inclusion/pinning separation is explicit in the probe implementation and its must/010 explanation, but the assessor entrypoint does not itself provide a focused decision rule for this pair of floating cases. It does require inspecting probe details and overriding incomplete judgments, which allowed the correct scoped distinction.
- The Pixi fixture contains no tool code, so dependency completeness is bounded by the declared synthetic object and supplied goal. It cannot establish completeness for a larger unstated implementation. For the inline fixture I treated the Python runtime as the script format's inherent runtime and judged the explicitly used external package. The absence of a Python version constraint affects exact replication; no host bootstrap route is documented or tested. If the evaluation intends must/010 to require an explicit interpreter provisioning declaration even for inline Python metadata, the conventions should say so.
- The task explicitly waived the full assessment products and URL. Accordingly no full-record validator was run and no out-of-scope verdicts were authored. The pinned checklist has 31 items, whereas the prompt's waived-full-report phrase says 29; this does not affect the three exact IDs assessed.

## Provenance and independence

Assessor skill `assess-alignment-with-stamped-principles` 0.1.0 and sibling `stamped-conventions` 0.1.0; source snapshot commit `9ef00c19618a168aa2f9d322ff71457fa6b046f2` from `source.json`. All 19 listed snapshot hashes matched `snapshot-sha256.json`. Checklist 0.3.1, upstream commit `af259bad237fa57b856417db8dba45a1b283a527`, confirmed by the supplied pin checker. Harness: Codex subagent; exact runtime/model identity was not independently resolved for this scoped check.

Only the supplied snapshot, its local metadata, and the two target repositories were inspected. No originating repository, tests, prior assessment, plan, or integration record was consulted. The original task prompt is retained verbatim in `prompt.txt`. Target projects were unchanged.

## Harness correction: documented CLI completed

2026-10-15 UTC. The follow-up supplied the already-installed interpreter
`/Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/skills/.tox/stamped-evals/bin/python`.
Only that interpreter and its installed dependencies were used from that location;
no originating repository source, tests, or records were read. No packages were installed.
The initial system-Python failures remain above: the original harness constraint
omitted a runtime prerequisite declared by the skill. This is a **harness correction**,
not evidence that the skill conceals the dependency.

Using that interpreter, the snapshot's documented `encode_response.py items --level must`
and both scoped `run_probes.py <target> --kind component --only env-spec-tracked run-env-linked -o <output>`
commands each exited **0**, with empty stderr. The item listing confirmed the same
three item texts already read from the vendored checklist.
Both probe CLIs printed:

```text
probe                    status          items
env-spec-tracked         unmet           must/010, must/013, must/016
run-env-linked           not-checked     must/006, must/015

probes cover 5/17 MUST items; inspect statuses for completed verdicts
```

The CLI-generated per-probe records exactly match the original direct-API records.
For each target, the item-specific suggestions remain **must/010 met, must/013 met,
must/015 not-checked**. My judgments remain **met, met, unmet**, respectively,
for the evidence and override reasons above. The aggregate `env-spec-tracked`
`unmet` still comes from its bundled, out-of-scope must/016 field.

Complete command argv, stdout, stderr, and exit statuses are retained in
`cli-harness-correction.json`; native CLI outputs are `fixture1-cli-probes.json`
and `fixture2-cli-probes.json`. The follow-up prompt is retained verbatim in
`followup-prompt.txt`. Both target HEADs were rechecked against the original
commits and both working trees remained clean. No new targets or checklist
judgments were added; scientific execution remains unperformed.
