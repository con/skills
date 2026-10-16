# Bounded fresh-replay review

The requested checks distinguish a retrievable annex baseline from an unavailable
unlocked annex pointer. The target reproduces the selected unlocked output, and
then both selected tables, byte-for-byte. The absent source correctly receives
`not-checked` before executing the entry point. A single-file selection exposes
an important scope caveat: the workflow logs errors while writing an unselected
locked table, but still exits zero and reproduces the selected table.

## Scope and identity

- Replay-only; no full STAMPED checklist or scientific evaluation.
- Assumed goal: test the supplied `sh analysis.sh` route against the selected
  committed outputs. This goal came from the task, not inferred project intent.
- Skill snapshot supplied by the caller:
  `24564e88d832fc1c8c0911d92f1b943c86ad9b3c`.
- Read the snapshot assessment skill, its replay helper, sibling conventions and
  required references. Did not inspect the operational environment repository,
  prior reviews, fixture-generation scripts, or unrelated temporary directories.
- Both sources: commit `4b56f4b9a3643d2a79f23d2921f377d3eb70caf6`.
  Before and after the checks, each showed ` M results/unlocked.tsv`.
  This reviewer performed no source edits, repairs or commits. The sources were
  already dirty at first inspection; this review makes no claim of pristine
  source preservation or of their state before this review began.
- Both dirty working copies contained only `4\t8\n` in `results/unlocked.tsv`.
  That is not the committed comparator: their Git blobs name the annex key with
  payload SHA256 `64c3e86a53527c5adf3cffafef3a25abcbe4f1c01cfaf719b743f441d3a5e9f8`.
  The target's retained shipped payload matches that key and includes the header
  and input rows. The absent clone retained only the annex pointer.
- Executed on the same Darwin host, using the supplied Pixi environment, without
  a container. Local source transport was explicitly carried into target clones.
  This establishes local repeatability only, not remote publication access or
  portability to another host.
- UTC execution date: 2026-10-16. Assessment skill and conventions each declare
  version `0.1.0`. Vendored checklist verification returned
  `ok: checklist 0.3.1 (31 items) matches lock.json`.
- Harness: Codex subagent. Exact runtime/model identity was not resolved because
  this bounded task forbids inspecting the host/project provenance sources;
  no identity is guessed and no manually authored commits were made.

## Native results, in execution order

| Invocation | Selected outputs | Native status | Evidence |
| --- | --- | --- | --- |
| target-unlocked | `results/unlocked.tsv` | `met` | Retrieved comparator, removed it, committed scratch-clone removal, ran entry, one identical file. |
| absent-unlocked | `results/unlocked.tsv` | `not-checked` | Retrieval failed; comparator hash null; `unavailable_comparators` names the selected path; no removal or entry step. |
| target-all | `results/*.tsv` | `met` | Retrieved and removed both comparators; entry exited zero without logged errors; both files identical. |

All helper process exit codes were zero. As the helper's help correctly warns:
“Exit code 0 means the probe ran, not that the object reproduced; read `status`
in the JSON.”

The target's upstream retrieval log distinguishes the routes:
`results/locked.tsv` and `input.tsv` arrived “from replay-source-route-1”, while
`results/unlocked.tsv` arrived “from origin”. The copied local transport is
recorded as `route_origin: local-source-git-config` and `host_scope: same-host`.
The absent source supplied no such local routes and all three content gets
failed. No external storage was manually configured or repaired.

The unavailable-comparator report says:
“Published output content was unavailable; no valid baseline exists for
comparison.” This is evidence of an unavailable baseline in this recipient
context, not a demonstrated numerical mismatch or general publication failure.
The pointer's own bytes were not accepted as an output baseline.

Independent reads of retained shipped and rerun files confirm these SHA256s:

- `results/unlocked.tsv`:
  `64c3e86a53527c5adf3cffafef3a25abcbe4f1c01cfaf719b743f441d3a5e9f8`.
- `results/locked.tsv`:
  `741f573250a1a1fe3f8bbb5d17a72575d99c644d589be02a29dd6e31c6578d80`.

No numerical tolerance comparison was needed. These tiny table checks say
nothing about scientific validity.

## Instruction and tool friction

1. **Selected-output success can coexist with workflow errors.** The single-file
   target report contains `entry: sh analysis.sh`, return code `0`, and:

   ```text
   analysis.sh: line 2: results/locked.tsv: Permission denied
   analysis.sh: line 3: results/locked.tsv: Permission denied
   ```

   The committed script first writes `locked.tsv`, then `unlocked.tsv`, without
   `set -e`. The helper removed only the selected unlocked output; the unselected
   locked output remained an annex symlink. The shell continued after its failed
   writes, and the selected output reproduced. The native `met` is supported for
   its one selected comparator but must not be read as a clean full workflow
   execution. The separately requested broader run removed both files and had
   no logged entry errors. This is a concrete scope/reporting caveat, not an
   invented mismatch.

2. **The skill's short execution example hides useful local-scope controls.** Its
   example is `python3 scripts/fresh_rerun.py --url <published url> --entry
   '<documented command>' -o <date>-fresh-rerun.json`. The helper's `--help`
   supplied the necessary `--path`, `--outputs`, `--workdir`, `--timeout`, and
   `--max-get-gb` controls. Its `--path` description expressly says “indicative
   only: does not test D.1”. This was resolved by reading help, with no blocker.

3. **A bounded selection does not bound all retrieval to those paths.** Even the
   one-output check ran the up-front recursive content retrieval. Native reports
   recorded only 59 pending bytes, under the explicitly supplied 0.01 GiB cap.
   Helper code also fetches selected comparators unconditionally after this
   up-front budget decision. No over-budget transfer occurred here; users must
   not interpret `--outputs` or that cap as an unconditional total-download cap.

4. **Full-assessment paperwork does not fit this task's narrower authorization.**
   The skill says “Every one of the 31 items gets your answer” and prescribes four
   assessment files. The explicit task requested replay only, so this report
   preserves the native replay products without fabricating a checklist score,
   project-kind assessment, scientific judgment, or app URL. No clarification
   was needed to maintain that bounded scope.

## Retained evidence and commands

- `commands.sh`: all three exact replay invocations in order.
- `run_checks.py`: small orchestration driver; does not replace the native helper.
- `invocations.json`: argument arrays, rendered commands, times and process exits.
- `target-unlocked.json`, `absent-unlocked.json`, `target-all.json`: unedited native
  reports, including native steps, logs, routes, hashes and decisions.
- Corresponding `.stdout.txt` and `.stderr.txt` files retain invocation streams.
- `target-unlocked/`, `absent-unlocked/`, `target-all/`: retained native workdirs,
  including disposable clones and available shipped payload copies.
- `verification.json`: source commit/status and committed-pointer reads, current
  source working-copy observations, and independent retained-file content/hash
  checks. They document the dirty source states actually observed; they do not
  establish that the shared sources were pristine before this review.

All evidence is under `/tmp/stamped-replay-comparator-review/primary/`.

Coordinator notice received after the replay checks: another reviewer had run
`analysis.sh` directly in the shared sources. That notice explains why these
results should not be presented as a pristine-source test. The recorded facts
above remain the observed evidence: dirty working trees at first inspection,
committed-HEAD clones, baseline hashes matching committed annex keys, and retained
native decisions. This reviewer did not restore or alter either source.
