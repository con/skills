# Bounded fresh-replay review

The helper refused the request without an output selection, then successfully
re-created the one explicitly selected generated product in a separate clone.
This is a same-host, local-source replay check, not a full STAMPED assessment or
an assessment of scientific validity or public retrieval.

## Scope and identity

- Source: `/tmp/stamped-output-selection-review/primary-source`, clean at
  `9f415de61bb5806b7edbca1a6bba4ec35e394b6e` before and after replay.
- Skill snapshot revision supplied by the coordinator:
  `4ca147e7060640219c0270fb51d2721a74fcb82c`.
- Read snapshot `assess-alignment-with-stamped-principles` 0.1.0 and sibling
  `stamped-conventions` 0.1.0; checklist pin check passed for 0.3.1, 31 items.
- Execution date: 2026-10-16 UTC, as recorded by the native helper report.
- Harness: Codex subagent. Exact model/runtime versions were not independently
  resolved within this limited read scope; no versions are guessed here.
- Assumed object purpose, from README and analysis code: a synthetic study that
  computes a mean effect from a supplied input table. This was not confirmed
  with a human, and no checklist verdicts are assigned.
- The supplied Pixi manifest was used solely as the operational environment.
  No environment checkout inspection or installation was performed.

## First invocation: no selection

The exact invocation and exit capture are in `commands.sh`. It supplied
`--path`, `--entry 'python analysis.py'`, a dedicated workdir, and `-o`, but no
`--outputs`. It exited 2 with the actual response retained in
`no-selection.stderr`:

> fresh_rerun.py: error: the following arguments are required: --outputs

`no-selection.stdout` is empty. The parser rejected the call before workdir or
clone creation and before writing the requested JSON report; consequently
there is no `no-selection.json`. This is an argument-validation response, not
a replay failure. No source analysis ran on this invocation.

## Explicit selection and replay

After that refusal, I read README.md and analysis.py. The README says:

> The generated product is results/group_summary.csv. The PNG and reference PDF
> are supplied assets, not generated products.

The code reads `input/participants.tsv` and writes only
`results/group_summary.csv`. I therefore selected that exact file, avoiding a
recursive results glob that would include the reference PDF. The exact
selection was `--outputs 'results/group_summary.csv'`. The commands are in
`replay-commands.sh`.

The helper cloned into `selected-workdir/clone`, kept the shipped comparator
under `selected-workdir/shipped`, removed only the selected CSV, committed that
removal in the disposable clone, and ran `python analysis.py` there. The entry
returned 0. Native `selected.json` reports:

> All 1 compared output(s) reproduced from a fresh clone via `python analysis.py`.

Its status is `met`, with one byte-identical product, no tolerance-only match,
no differences, and no missing product. That status is the native probe's
bounded result, not an endorsement of all checklist items in its `items` field.
The CSV SHA-256 is
`a30f49691c25142d9114d2150c55ce809e23019301fdd23c7e08482cfbee0acd`.

## Preservation evidence

`before.json` and `after.json` contain tracked-file SHA-256 hashes and source
Git identity/status. `after.json` confirms `source_unchanged: true` and
`clone_matches_source: true`. The following non-product files remained present
and byte-identical in both the source and the replay clone:

- README.md
- analysis.py
- input/participants.tsv
- results/reference-atlas-cache/manual.pdf
- skills/example/assets/icon.png

The helper's scratch commit
`7d57559a4e3b10849e3c28358e7414804e148c9c` has exactly one changed path:
`D results/group_summary.csv`. The native report records that same sole removal.
Thus the input table, source code, PNG asset and reference PDF were not selected
or removed, including the PDF located under `results/`. The source repository
was never modified. Analysis execution occurred only through the helper in its
clone.

## Instruction and tool friction

The skill's fresh-rerun example includes
`--outputs '<generated-output glob>'`, while the helper describes this argument
as “explicit generated-output glob(s) to compare; selected files are removed
before replay”. The missing-argument refusal was actionable and protected
against silently selecting files by suffix. It did not produce a JSON report,
so retaining stderr and the exit code is necessary to preserve this evidence.

Selection still requires source interpretation: a directory named `results`
contains a supplied reference file as well as the generated CSV. In this case
the README and the actual write target agree, making a precise selection easy.
The parser requires a selection; it does not establish that the caller's
selection is semantically a product. No broader selection was attempted.

The general skill says “Every one of the 31 items gets your answer” and
“validate must pass before you report anything.” Those full-assessment steps
were outside the coordinator's explicit bounded replay request, which also
prohibited inferring a full checklist. Accordingly this review retains native
probe evidence without fabricating a response JSON, checklist URL or unrelated
scientific findings.

The helper documentation cautions: “Exit code 0 means the probe ran, not that
the object reproduced; read status in the JSON.” I checked the native JSON
rather than treating shell success alone as reproduction evidence. There were
no operational blockers after the explicit selection.

## Retained evidence

- `commands.sh`: first invocation and pin-check commands, with exit capture.
- `replay-commands.sh`: before/after verification and selected replay commands.
- `read-commands.txt`: exact read-only inspection commands in order.
- `pin-check.stdout`, `pin-check.stderr`, `pin-check.exit`.
- `no-selection.stdout`, `no-selection.stderr`, `no-selection.exit`.
- `selected.json`: unchanged native helper report.
- `selected.stdout`, `selected.stderr`, `selected.exit`.
- `verify_files.py`, `before.json`, `after.json`.
- `selected-workdir/`: disposable clone and retained shipped comparator.
